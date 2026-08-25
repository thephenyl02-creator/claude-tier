from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "plugins" / "codex-tier" / "skills" / "codex-tier"
ROUTER_PATH = SKILL_ROOT / "scripts" / "codex_tier.py"
BENCHMARK_PATH = SKILL_ROOT / "scripts" / "benchmark.py"
FAKE_CODEX = Path(__file__).with_name("fake_codex.py")
FAKE_CODEX_CMD = Path(__file__).with_name("fake-codex.cmd")
FAKE_CODEX_SH = Path(__file__).with_name("fake-codex.sh")

SPEC = importlib.util.spec_from_file_location("codex_tier", ROUTER_PATH)
assert SPEC and SPEC.loader
codex_tier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codex_tier)


def route(**overrides):
    values = {
        "work_class": "routine_refactor",
        "complexity": "routine",
        "volume": "moderate",
        "risk": "ordinary",
        "context": "multi-file",
    }
    values.update(overrides)
    return codex_tier.route_work_unit(**values)


class RoutingTests(unittest.TestCase):
    def test_registry_and_frontiers_validate(self):
        registry, frontiers = codex_tier.load_config()
        self.assertEqual([], codex_tier.validate_config(registry, frontiers))
        self.assertEqual(
            ["none", "low", "medium", "high", "xhigh", "max"],
            registry["effort_order"],
        )
        self.assertEqual(3, len(registry["models"]))

    def test_deterministic_work_uses_tool(self):
        decision = route(complexity="deterministic", risk="production-critical")
        self.assertEqual("TOOL", decision["execution_mode"])
        self.assertIsNone(decision["selected"])

    def test_tiny_local_work_uses_direct(self):
        decision = route(volume="tiny", context="local", risk="low")
        self.assertEqual("DIRECT", decision["execution_mode"])
        self.assertFalse(decision["requires_parent"])

    def test_high_volume_mechanical_work_stays_in_luna_region(self):
        decision = route(
            work_class="bulk_repository_scan",
            complexity="mechanical",
            volume="repetitive/high-volume",
            risk="low",
            context="repository-wide",
        )
        self.assertEqual("WORKER", decision["execution_mode"])
        self.assertEqual("gpt-5.6-luna/high", decision["selected"]["pair"])

    def test_ordinary_refactor_uses_luna_high(self):
        decision = route()
        self.assertEqual("gpt-5.6-luna/high", decision["selected"]["pair"])

    def test_difficult_debugging_uses_terra_xhigh(self):
        decision = route(
            work_class="difficult_debugging",
            complexity="substantial",
            risk="correctness-sensitive",
            context="repository-wide",
        )
        self.assertEqual("gpt-5.6-terra/xhigh", decision["selected"]["pair"])

    def test_high_risk_review_uses_strong_sol(self):
        decision = route(
            work_class="security_review",
            complexity="frontier/ambiguous",
            volume="small",
            risk="security-sensitive",
            context="large-context",
        )
        self.assertEqual("gpt-5.6-sol/high", decision["selected"]["pair"])

    def test_model_unavailable_selects_another_frontier_candidate(self):
        decision = route(
            work_class="bulk_repository_scan",
            complexity="mechanical",
            volume="large",
            risk="low",
            context="repository-wide",
            unavailable_pairs=["gpt-5.6-luna/high"],
        )
        self.assertEqual("gpt-5.6-terra/low", decision["selected"]["pair"])

    def test_effort_unavailable_selects_adjacent_candidate(self):
        decision = route(unavailable_pairs=["gpt-5.6-luna/high"])
        self.assertEqual("gpt-5.6-luna/xhigh", decision["selected"]["pair"])

    def test_no_viable_worker_keeps_quality_on_parent(self):
        decision = route(
            work_class="security_review",
            complexity="frontier",
            risk="security-sensitive",
            context="large-context",
            available_models=["gpt-5.6-luna"],
        )
        self.assertEqual("DIRECT", decision["execution_mode"])
        self.assertTrue(decision["requires_parent"])

    def test_selective_escalation_is_workload_specific(self):
        decision = route(escalate_from="gpt-5.6-luna/high")
        self.assertEqual("gpt-5.6-luna/xhigh", decision["selected"]["pair"])
        architecture = route(
            work_class="architecture",
            complexity="substantial",
            risk="ordinary",
            context="repository-wide",
        )
        self.assertEqual("gpt-5.6-terra/xhigh", architecture["selected"]["pair"])


class ExecutorTests(unittest.TestCase):
    def run_router(self, arguments, *, packet="", environment=None):
        return subprocess.run(
            [sys.executable, str(ROUTER_PATH), *arguments],
            input=packet,
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )

    def test_bounded_worker_enforces_model_effort_and_captures_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            log_file = temp / "usage.jsonl"
            completed = self.run_router(
                [
                    "execute",
                    "--repo",
                    str(REPO_ROOT),
                    "--model",
                    "gpt-5.6-luna",
                    "--effort",
                    "high",
                    "--sandbox",
                    "read-only",
                    "--codex-bin",
                    str(FAKE_CODEX),
                    "--log-file",
                    str(log_file),
                    "--work-class",
                    "bulk_repository_scan",
                ],
                packet="OBJECTIVE\nReturn a compact repository inventory.",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertTrue(result["success"])
            self.assertIn("MODEL=gpt-5.6-luna EFFORT=high", result["final_message"])
            self.assertEqual(100, result["usage"]["input_tokens"])
            event = json.loads(log_file.read_text(encoding="utf-8"))
            self.assertEqual("gpt-5.6-luna", event["selected_model"])
            self.assertEqual("high", event["selected_effort"])
            self.assertEqual(30, event["reasoning_tokens"])
            self.assertNotIn("repository inventory", log_file.read_text(encoding="utf-8"))

    def test_worker_failure_is_logged_without_raw_packet(self):
        with tempfile.TemporaryDirectory() as temporary:
            log_file = Path(temporary) / "usage.jsonl"
            completed = self.run_router(
                [
                    "execute",
                    "--repo",
                    str(REPO_ROOT),
                    "--model",
                    "gpt-5.6-terra",
                    "--effort",
                    "medium",
                    "--codex-bin",
                    str(FAKE_CODEX),
                    "--log-file",
                    str(log_file),
                ],
                packet="OBJECTIVE\nFORCE_FAILURE secret-packet-content",
            )
            self.assertEqual(42, completed.returncode)
            event = json.loads(log_file.read_text(encoding="utf-8"))
            self.assertFalse(event["success"])
            self.assertEqual("worker_failure", event["error_type"])
            self.assertNotIn("secret-packet-content", log_file.read_text(encoding="utf-8"))

    def test_record_sanitizes_all_string_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            log_file = Path(temporary) / "usage.jsonl"
            completed = self.run_router(
                [
                    "record",
                    "--execution-mode",
                    "DIRECT",
                    "--work-class",
                    "Authorization: Bearer super-secret-token",
                    "--error-type",
                    "Bearer sk-abcdefghijklmnopqrstuvwxyz",
                    "--log-file",
                    str(log_file),
                ]
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            contents = log_file.read_text(encoding="utf-8")
            self.assertNotIn("super-secret-token", contents)
            self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz", contents)
            self.assertIn("[REDACTED]", contents)

    def test_sanitizer_covers_common_credential_forms(self):
        samples = {
            "Authorization: Bearer TOPSECRET": "TOPSECRET",
            "Bearer TOPSECRET": "TOPSECRET",
            "api_key=TOPSECRET": "TOPSECRET",
            "password: TOPSECRET": "TOPSECRET",
            "token=TOPSECRET": "TOPSECRET",
        }
        for value, secret in samples.items():
            with self.subTest(value=value):
                sanitized = codex_tier.sanitize_error(value)
                self.assertNotIn(secret, sanitized)
                self.assertIn("[REDACTED]", sanitized)

    def test_workspace_write_and_read_only_are_enforced(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temporary:
            temp = Path(temporary)
            relative = temp.relative_to(REPO_ROOT) / "sentinel.txt"
            log_file = temp / "usage.jsonl"
            read_only = self.run_router(
                [
                    "execute",
                    "--repo",
                    str(REPO_ROOT),
                    "--model",
                    "gpt-5.6-luna",
                    "--effort",
                    "low",
                    "--sandbox",
                    "read-only",
                    "--codex-bin",
                    str(FAKE_CODEX),
                    "--log-file",
                    str(log_file),
                ],
                packet=f"OBJECTIVE\nWRITE_SENTINEL={relative.as_posix()}",
            )
            self.assertEqual(0, read_only.returncode, read_only.stderr)
            self.assertFalse((REPO_ROOT / relative).exists())
            writable = self.run_router(
                [
                    "execute",
                    "--repo",
                    str(REPO_ROOT),
                    "--model",
                    "gpt-5.6-luna",
                    "--effort",
                    "low",
                    "--sandbox",
                    "workspace-write",
                    "--codex-bin",
                    str(FAKE_CODEX),
                    "--log-file",
                    str(log_file),
                ],
                packet=f"OBJECTIVE\nWRITE_SENTINEL={relative.as_posix()}",
            )
            self.assertEqual(0, writable.returncode, writable.stderr)
            self.assertTrue((REPO_ROOT / relative).exists())

    def test_cli_inspection_with_callable_fake(self):
        completed = self.run_router(["inspect", "--codex-bin", str(FAKE_CODEX)])
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(0, result["version_probe"]["exit_code"])
        self.assertIn("--output-last-message", result["exec_probe"]["stdout"])
        self.assertEqual("verify-on-active-surface", result["native_subagents"]["status"])


class PackagingAndInstallerTests(unittest.TestCase):
    def test_benchmark_plan_covers_representative_workloads(self):
        completed = subprocess.run(
            [sys.executable, str(BENCHMARK_PATH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(5, len(result["cases"]))
        self.assertEqual(
            {"bulk_repository_scan", "creative_planning", "routine_refactor",
             "difficult_debugging", "security_review"},
            {case["work_class"] for case in result["cases"]},
        )

    def test_benchmark_live_harness_covers_models_efforts_and_raw_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(BENCHMARK_PATH),
                    "--run",
                    "--repo",
                    str(REPO_ROOT),
                    "--codex-bin",
                    str(FAKE_CODEX),
                    "--log-file",
                    str(temp / "usage.jsonl"),
                    "--results-file",
                    str(temp / "results.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(14, len(result["records"]))
            self.assertEqual(
                {"gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"},
                {record["candidate"].rsplit("/", 1)[0] for record in result["records"]},
            )
            self.assertTrue(
                {"low", "medium", "high", "xhigh", "max"}.issubset(
                    {record["candidate"].rsplit("/", 1)[1] for record in result["records"]}
                )
            )
            self.assertTrue(all(record["worker_success"] for record in result["records"]))
            self.assertTrue(all(record["usage"] for record in result["records"]))
            self.assertNotIn("savings_percent", result)

    def test_windows_installer_is_idempotent_and_preserves_unrelated_files(self):
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if not powershell:
            self.skipTest("PowerShell is unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            install_home = Path(temporary)
            unrelated = install_home / ".agents" / "unrelated.txt"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("keep\n", encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "CODEX_TIER_INSTALL_HOME": str(install_home),
                    "CODEX_TIER_SOURCE_ROOT": str(REPO_ROOT),
                    "CODEX_TIER_FORCE_DIRECT": "1",
                    "CODEX_TIER_CODEX_BIN": str(FAKE_CODEX_CMD),
                }
            )
            command = [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(REPO_ROOT / "install-codex.ps1"),
            ]
            first = subprocess.run(command, capture_output=True, text=True, env=environment, check=False)
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)
            second = subprocess.run(command, capture_output=True, text=True, env=environment, check=False)
            self.assertEqual(0, second.returncode, second.stdout + second.stderr)
            installed = install_home / ".agents" / "skills" / "codex-tier"
            self.assertTrue((installed / "SKILL.md").exists())
            self.assertTrue((installed / ".installed-by-codex-tier-installer").exists())
            self.assertEqual("keep\n", unrelated.read_text(encoding="utf-8"))

    def test_unix_installer_syntax(self):
        git_bash = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
        bash = str(git_bash) if git_bash.exists() else shutil.which("bash")
        if not bash or str(bash).lower().endswith(r"windows\system32\bash.exe"):
            self.skipTest("bash is unavailable")
        completed = subprocess.run(
            [bash, "-n", str(REPO_ROOT / "install-codex.sh")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_unix_installer_is_idempotent_with_local_source(self):
        git_bash = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
        if not git_bash.exists():
            self.skipTest("Git Bash is unavailable")

        def posix_path(path: Path) -> str:
            environment = os.environ.copy()
            environment["WINDOWS_PATH"] = str(path)
            converted = subprocess.run(
                [str(git_bash), "-lc", 'cygpath -u "$WINDOWS_PATH"'],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(0, converted.returncode, converted.stderr)
            return converted.stdout.strip()

        with tempfile.TemporaryDirectory() as temporary:
            install_home = Path(temporary)
            unrelated = install_home / ".agents" / "unrelated.txt"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("keep\n", encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "CODEX_TIER_INSTALL_HOME": posix_path(install_home),
                    "CODEX_TIER_SOURCE_ROOT": posix_path(REPO_ROOT),
                    "CODEX_TIER_FORCE_DIRECT": "1",
                    "CODEX_TIER_CODEX_BIN": posix_path(FAKE_CODEX_SH),
                }
            )
            command = [str(git_bash), posix_path(REPO_ROOT / "install-codex.sh")]
            first = subprocess.run(command, capture_output=True, text=True, env=environment, check=False)
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)
            second = subprocess.run(command, capture_output=True, text=True, env=environment, check=False)
            self.assertEqual(0, second.returncode, second.stdout + second.stderr)
            installed = install_home / ".agents" / "skills" / "codex-tier"
            self.assertTrue((installed / "SKILL.md").exists())
            self.assertTrue((installed / ".installed-by-codex-tier-installer").exists())
            self.assertEqual("keep\n", unrelated.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
