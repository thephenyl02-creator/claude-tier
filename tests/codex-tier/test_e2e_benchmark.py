from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = ROOT / "benchmarks" / "codex-tier-e2e" / "e2e_benchmark.py"
SPEC = importlib.util.spec_from_file_location("codex_tier_e2e_benchmark", HARNESS_PATH)
assert SPEC and SPEC.loader
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


def attempt(total_tokens: int, pair: str) -> dict:
    model, effort = pair.rsplit("/", 1)
    return {
        "success": True,
        "pair": pair,
        "model": model,
        "effort": effort,
        "reason": "test",
        "latency_seconds": 1.0,
        "wall_seconds": 1.0,
        "internal_retry_count": 0,
        "error_event_count": 0,
        "tool_item_count": 0,
        "usage": {
            "input_tokens": total_tokens - 10,
            "cached_input_tokens": 0,
            "cache_write_input_tokens": 0,
            "output_tokens": 10,
            "reasoning_output_tokens": 5,
            "uncached_input_tokens": total_tokens - 10,
            "total_exposed_tokens": total_tokens,
        },
    }


def record(condition: str, position: int, total_tokens: int, score: int, passed: bool) -> dict:
    pair = "gpt-5.6-sol/low" if condition == "baseline" else "gpt-5.4-mini/low"
    attempts = [attempt(total_tokens, pair)]
    return {
        "benchmark_state": "complete",
        "workload_id": "workload",
        "work_class": "test",
        "condition": condition,
        "randomized_position": position,
        "task_prompt_sha256": "task",
        "canonical_packet_sha256": "packet",
        "attempts": attempts,
        "verification_attempts": [],
        "infrastructure_attempts": [],
        "aggregate": benchmark.aggregate_attempts(attempts),
        "quality": {"score": score, "passed": passed, "valid": True},
        "external_retry_count": 0,
        "escalation_count": 0,
    }


def suite() -> dict:
    return {
        "repetitions_per_condition": 1,
        "workloads": [{"id": "workload", "work_class": "test"}],
        "quality_gate": {
            "minimum_individual_score": 80,
            "minimum_tiered_pass_rate_for_publication": 1.0,
            "maximum_median_regression_points": 3,
            "require_tiered_pass_rate_at_least_baseline": True,
        },
    }


class BenchmarkPublicationGateTests(unittest.TestCase):
    def test_equal_absolute_failure_does_not_publish_savings(self) -> None:
        results = {
            "records": [
                record("baseline", 1, 100, 50, False),
                record("tiered", 2, 50, 52, False),
            ]
        }

        analysis = benchmark.analyze(results, suite())
        workload = analysis["workloads"]["workload"]

        self.assertTrue(workload["relative_quality_preserved"])
        self.assertFalse(workload["absolute_quality_met"])
        self.assertFalse(workload["quality_preserved"])
        self.assertIsNone(workload["quality_preserving_savings_percent"])
        self.assertEqual(50.0, workload["raw_median_usage_savings_percent"])
        self.assertIsNone(analysis["overall"]["median_quality_preserving_savings_percent"])

    def test_publishes_when_absolute_and_relative_gates_pass(self) -> None:
        results = {
            "records": [
                record("baseline", 1, 100, 82, True),
                record("tiered", 2, 80, 81, True),
            ]
        }

        analysis = benchmark.analyze(results, suite())
        workload = analysis["workloads"]["workload"]

        self.assertTrue(workload["absolute_quality_met"])
        self.assertTrue(workload["quality_preserved"])
        self.assertEqual(20.0, workload["quality_preserving_savings_percent"])
        self.assertEqual(20.0, analysis["overall"]["median_quality_preserving_savings_percent"])

    def test_confirmation_mode_never_publishes_single_run_savings(self) -> None:
        confirmation_suite = suite()
        confirmation_suite["publish_savings"] = False
        results = {
            "records": [
                record("baseline", 1, 100, 85, True),
                record("tiered", 2, 80, 85, True),
            ]
        }

        analysis = benchmark.analyze(results, confirmation_suite)
        workload = analysis["workloads"]["workload"]

        self.assertTrue(workload["quality_preserved"])
        self.assertEqual(20.0, workload["raw_median_usage_savings_percent"])
        self.assertIsNone(workload["quality_preserving_savings_percent"])
        self.assertFalse(analysis["overall"]["savings_publication_allowed"])


def smoke_attempt(run_id: str, pair: str, *, success: bool, usage_limit: bool = False) -> dict:
    model, effort = pair.rsplit("/", 1)
    response = ("blocked by policy while inspecting the repository " * 20) if success else ""
    error = "Codex usage limit reached; resets in 5 hours" if usage_limit else None
    return {
        "attempt_id": run_id,
        "pair": pair,
        "model": model,
        "effort": effort,
        "reason": "smoke",
        "success": success,
        "exit_code": 0 if success else 1,
        "latency_seconds": 1.0,
        "wall_seconds": 1.0,
        "usage": {
            "input_tokens": 100 if success else None,
            "cached_input_tokens": 20 if success else None,
            "cache_write_input_tokens": 0 if success else None,
            "output_tokens": 30 if success else None,
            "reasoning_output_tokens": 10 if success else None,
            "uncached_input_tokens": 80 if success else None,
            "total_exposed_tokens": 130 if success else None,
        },
        "internal_retry_count": 0,
        "error_event_count": 0 if success else 1,
        "tool_item_count": 0,
        "response": response,
        "response_sha256": benchmark.sha256_text(response),
        "error": error,
        "failure_kind": "usage_limit" if usage_limit else (None if success else "infrastructure"),
        "usage_limit_reset_hint": error if usage_limit else None,
    }


class BenchmarkTuningSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tuning_suite_path = ROOT / "benchmarks" / "codex-tier-e2e" / "tuning-suite.json"
        cls.tuning_suite = json.loads(cls.tuning_suite_path.read_text(encoding="utf-8"))
        cls.confirmation_suite_path = (
            ROOT / "benchmarks" / "codex-tier-e2e" / "confirmation-suite.json"
        )
        cls.confirmation_suite = json.loads(
            cls.confirmation_suite_path.read_text(encoding="utf-8")
        )
        cls.recovery_suite_path = (
            ROOT / "benchmarks" / "codex-tier-e2e" / "quality-recovery-tuning-suite.json"
        )
        cls.recovery_suite = json.loads(
            cls.recovery_suite_path.read_text(encoding="utf-8")
        )
        cls.security_repair_suite_path = (
            ROOT / "benchmarks" / "codex-tier-e2e" / "security-gate-repair-suite.json"
        )
        cls.security_repair_suite = json.loads(
            cls.security_repair_suite_path.read_text(encoding="utf-8")
        )
        cls.final_suite_path = ROOT / "benchmarks" / "codex-tier-e2e" / "final-suite.json"
        cls.final_suite = json.loads(cls.final_suite_path.read_text(encoding="utf-8"))
        cls.fixture_correction_suite_path = (
            ROOT / "benchmarks" / "codex-tier-e2e" / "fixture-correction-suite.json"
        )
        cls.fixture_correction_suite = json.loads(
            cls.fixture_correction_suite_path.read_text(encoding="utf-8")
        )

    def test_frozen_evidence_is_identical_and_task_packet_hides_rubric(self) -> None:
        workload = self.tuning_suite["workloads"][0]
        evidence = "FROZEN COMMIT: abc\nL1: def route_work_unit():"
        baseline_packet = benchmark.canonical_packet(workload, "abc", evidence)
        tier_packet = benchmark.canonical_packet(workload, "abc", evidence)

        self.assertEqual(baseline_packet, tier_packet)
        self.assertIn(evidence, baseline_packet)
        self.assertNotIn(workload["rubric"][0], baseline_packet)

    def test_atomic_checkpoint_retries_a_transient_windows_file_lock(self) -> None:
        original_replace = Path.replace
        replace_calls = 0

        def flaky_replace(source: Path, target: Path) -> Path:
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls == 1:
                raise PermissionError("checkpoint file is temporarily locked")
            return original_replace(source, target)

        with tempfile.TemporaryDirectory() as temporary:
            results_path = Path(temporary) / "results.json"
            with (
                patch.object(Path, "replace", new=flaky_replace),
                patch.object(benchmark.time, "sleep") as sleep,
            ):
                benchmark.write_json_atomic(results_path, {"run_status": "complete"})

            self.assertEqual(2, replace_calls)
            sleep.assert_called_once_with(0.1)
            self.assertEqual(
                {"run_status": "complete"},
                json.loads(results_path.read_text(encoding="utf-8")),
            )

    def test_targeted_schedule_is_randomized_and_has_twelve_primary_runs(self) -> None:
        schedule = benchmark.create_schedule(self.tuning_suite)

        self.assertEqual(12, len(schedule))
        self.assertEqual(list(range(1, 13)), sorted(item["randomized_position"] for item in schedule))
        self.assertEqual(4, sum(item["condition"] == "baseline" for item in schedule))
        self.assertEqual(8, sum(item["condition"] == "tiered" for item in schedule))
        self.assertEqual(
            {"real-router-refactor-plan", "real-distribution-architecture"},
            {item["workload_id"] for item in schedule},
        )

    def test_confirmation_schedule_has_only_six_requested_primary_runs(self) -> None:
        schedule = benchmark.create_schedule(self.confirmation_suite)

        self.assertEqual(6, len(schedule))
        self.assertEqual(3, sum(item["condition"] == "baseline" for item in schedule))
        self.assertEqual(3, sum(item["condition"] == "tiered" for item in schedule))
        self.assertEqual(
            {
                "real-bulk-release-audit",
                "real-probe-scope-debugging",
                "real-security-trust-review",
            },
            {item["workload_id"] for item in schedule},
        )
        self.assertTrue(self.confirmation_suite["single_pass_verification"])
        self.assertFalse(self.confirmation_suite["publish_savings"])

    def test_recovery_tuning_schedule_has_eighteen_records_before_reuse(self) -> None:
        schedule = benchmark.create_schedule(self.recovery_suite)

        self.assertEqual(18, len(schedule))
        self.assertEqual(6, sum(item["condition"] == "baseline" for item in schedule))
        self.assertEqual(12, sum(item["condition"] == "tiered" for item in schedule))
        self.assertTrue(all(
            len(workload["tuning_candidates"]) == 2
            for workload in self.recovery_suite["workloads"]
        ))
        packet = benchmark.canonical_packet(
            self.recovery_suite["workloads"][0], "abc", "frozen evidence"
        )
        self.assertIn("Do not use repository or shell tools", packet)

    def test_security_gate_uses_surface_groups_not_exact_helper_names(self) -> None:
        workload = self.security_repair_suite["workloads"][0]
        response = (
            "The Windows installer and Unix installer constrain their destination paths. "
            "The plugin marketplace establishes a separate source-trust boundary. "
            "The bounded Codex exec wrapper preserves sandbox approval settings. "
            "Model-cache launch-probe evidence is scoped locally. "
            "Content-free usage logging excludes prompts and credentials. "
        ) * 4

        screen = benchmark.deterministic_quality_screen(workload, response)

        self.assertEqual("needs_judgment", screen["decision"])
        self.assertEqual(6, len(screen["matched_required_groups"]))
        self.assertEqual([], screen["missing_required_groups"])
        self.assertEqual([], screen["matched_required_terms"])

    def test_security_gate_rejects_clear_surface_grounding_failure(self) -> None:
        workload = self.security_repair_suite["workloads"][0]
        response = (
            "The Windows installer and Unix installer deserve a security review. "
            "The plugin marketplace is also a trust boundary. "
        ) * 10

        screen = benchmark.deterministic_quality_screen(workload, response)

        self.assertEqual("clear_fail", screen["decision"])
        self.assertIn(
            "only 3/5 required grounding groups were covered",
            screen["failures"],
        )

    def test_security_gate_repair_schedule_has_exactly_six_security_records(self) -> None:
        schedule = benchmark.create_schedule(self.security_repair_suite)

        self.assertEqual(6, len(schedule))
        self.assertEqual(2, sum(item["condition"] == "baseline" for item in schedule))
        self.assertEqual(4, sum(item["condition"] == "tiered" for item in schedule))
        self.assertEqual(
            {"real-security-trust-review"},
            {item["workload_id"] for item in schedule},
        )
        self.assertEqual(
            {"gpt-5.6-terra/max", "gpt-5.6-sol/medium"},
            {
                item["candidate_pair"]
                for item in schedule
                if item["condition"] == "tiered"
            },
        )

    def test_final_schedule_is_fixed_to_thirty_frozen_evidence_records(self) -> None:
        schedule = benchmark.create_schedule(self.final_suite)

        self.assertEqual(30, len(schedule))
        self.assertEqual(15, sum(item["condition"] == "baseline" for item in schedule))
        self.assertEqual(15, sum(item["condition"] == "tiered" for item in schedule))
        self.assertEqual(
            {1, 2, 3},
            {item["repetition"] for item in schedule},
        )
        self.assertEqual(
            {"model": "gpt-5.6-sol", "effort": "low"},
            self.final_suite["parent"],
        )
        self.assertTrue(self.final_suite["deterministic_screening"])
        self.assertTrue(all(
            workload["frozen_evidence_only"]
            for workload in self.final_suite["workloads"]
        ))

    def test_fixture_correction_schedule_has_exactly_twelve_records(self) -> None:
        schedule = benchmark.create_schedule(self.fixture_correction_suite)

        self.assertEqual(12, len(schedule))
        self.assertEqual(6, sum(item["condition"] == "baseline" for item in schedule))
        self.assertEqual(6, sum(item["condition"] == "tiered" for item in schedule))
        self.assertEqual(
            {"real-bulk-release-audit", "real-probe-scope-debugging"},
            {item["workload_id"] for item in schedule},
        )
        self.assertEqual(
            {"model": "gpt-5.6-sol", "effort": "low"},
            self.fixture_correction_suite["parent"],
        )

    @unittest.skipUnless(
        (ROOT / ".benchmark-state" / "repo").exists(),
        "needs the frozen benchmark checkout under .benchmark-state/repo",
    )
    def test_repaired_fixtures_are_complete_and_mechanically_consistent(self) -> None:
        workloads = {
            item["id"]: item for item in self.fixture_correction_suite["workloads"]
        }
        evidence, metadata = benchmark.freeze_workload_evidence(
            ROOT / ".benchmark-state" / "repo",
            workloads,
            "75c2c6926bb317803e66946f72194788cac16ebe",
        )

        bulk = metadata["real-bulk-release-audit"]
        debugging = metadata["real-probe-scope-debugging"]
        self.assertTrue(bulk["fixture_validation"]["valid"])
        self.assertTrue(bulk["fixture_validation"]["all_tracked_files_included"])
        self.assertEqual(50, len(bulk["paths"]))
        self.assertTrue(debugging["fixture_validation"]["valid"])
        self.assertIn(
            'current["candidates"] = copy.deepcopy(profile["candidates"])',
            evidence["real-probe-scope-debugging"],
        )
        self.assertNotIn(
            "inspect the repository with tools",
            workloads["real-bulk-release-audit"]["task"].lower(),
        )

    def test_fixture_validation_rejects_contradictory_tool_requirement(self) -> None:
        workload = {
            "id": "contradictory",
            "task": "Inspect the repository with tools.",
            "rubric": [],
            "fixture_validation": {
                "forbidden_task_or_rubric_phrases": ["inspect the repository with tools"]
            },
        }

        with self.assertRaises(benchmark.BenchmarkError):
            benchmark.validate_frozen_fixture(workload, "evidence", [], 0)

    def test_usage_limit_classification_and_verifier_checkpoint_recovery(self) -> None:
        limited = {"success": False, "error": "Usage limit reached; resets at 3:15 PM", "response": ""}
        self.assertEqual("usage_limit", benchmark.classify_attempt_failure(limited))
        verdict = {
            "score": 85,
            "passed": True,
            "dimensions": {"correctness": 35, "evidence": 20, "completeness": 17, "actionability": 13},
            "critical_errors": [],
            "summary": "pass",
        }
        record_with_verifier = {
            "verification_attempts": [{
                "success": True,
                "response": json.dumps(verdict),
                "verification_phase": "initial",
            }]
        }
        self.assertEqual(
            85,
            benchmark.checkpointed_verdict(record_with_verifier, "initial", 80)["score"],
        )

    def test_usage_limit_checkpoint_and_resume_do_not_repeat_attempt(self) -> None:
        state = {
            "commit": "75c2c6926bb317803e66946f72194788cac16ebe",
            "tree": "tree",
            "clean": True,
            "path": "smoke",
        }
        evidence = {
            workload["id"]: f"frozen evidence for {workload['id']}"
            for workload in self.tuning_suite["workloads"]
        }
        metadata = {
            workload_id: {
                "paths": [],
                "characters": len(value),
                "packet_sha256": benchmark.sha256_text(value),
                "extraction": "smoke",
                "shared_by_baseline_and_tier": True,
                "contains_task_rubric": False,
            }
            for workload_id, value in evidence.items()
        }
        calls: list[str] = []

        def limited_attempt(**kwargs: object) -> dict:
            run_id = str(kwargs["run_id"])
            calls.append(run_id)
            return smoke_attempt(run_id, str(kwargs["pair"]), success=False, usage_limit=True)

        def successful_attempt_call(**kwargs: object) -> dict:
            run_id = str(kwargs["run_id"])
            calls.append(run_id)
            return smoke_attempt(run_id, str(kwargs["pair"]), success=True)

        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            results_path = temp / "tuning-results.json"
            report_path = temp / "tuning-report.md"
            arguments = [
                "--tuning",
                "--run",
                "--repo",
                str(temp),
                "--codex-bin",
                str(temp / "codex.exe"),
                "--suite",
                str(self.tuning_suite_path),
                "--results-file",
                str(results_path),
                "--report-file",
                str(report_path),
            ]
            shared_patches = (
                patch.object(benchmark, "assert_repository_state", return_value=state),
                patch.object(benchmark, "freeze_workload_evidence", return_value=(evidence, metadata)),
                patch.object(benchmark, "validate_tuning_candidates"),
                patch.object(benchmark.codex_tier, "resolve_codex_binary", return_value=temp / "codex.exe"),
                patch.object(benchmark, "official_cli_version", return_value="codex-cli 0.149.1"),
            )
            for active_patch in shared_patches:
                active_patch.start()
            try:
                with patch.object(benchmark, "run_attempt", side_effect=limited_attempt):
                    with self.assertRaises(benchmark.UsageLimitReached):
                        benchmark.main(arguments)
                checkpoint = json.loads(results_path.read_text(encoding="utf-8"))
                first_record = checkpoint["records"][0]
                first_attempt_id = first_record["infrastructure_attempts"][0]["attempt_id"]
                self.assertEqual("waiting_for_usage_reset", checkpoint["run_status"])
                self.assertEqual("usage_limit", first_record["infrastructure_attempts"][0]["failure_kind"])
                self.assertEqual(1, calls.count(first_attempt_id))
                status_output = io.StringIO()
                with contextlib.redirect_stdout(status_output):
                    benchmark.main([
                        "--tuning", "--status", "--results-file", str(results_path)
                    ])
                self.assertEqual(
                    "waiting_for_usage_reset",
                    json.loads(status_output.getvalue())["run_status"],
                )

                with patch.object(benchmark, "run_attempt", side_effect=successful_attempt_call):
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        benchmark.main(arguments + ["--resume"])
                resumed = json.loads(results_path.read_text(encoding="utf-8"))
                resumed_first = next(
                    item for item in resumed["records"] if item["run_id"] == first_record["run_id"]
                )
                self.assertEqual("complete", resumed["run_status"])
                self.assertEqual(12, len(resumed["records"]))
                self.assertEqual(1, calls.count(first_attempt_id))
                self.assertTrue(resumed_first["attempts"][0]["attempt_id"].endswith("--attempt-2"))
                self.assertEqual(12, benchmark.status_summary(resumed)["fully_completed_records"])
            finally:
                for active_patch in reversed(shared_patches):
                    active_patch.stop()

    def test_candidate_pruning_removes_quality_failures_and_dominated_pair(self) -> None:
        workload = {
            "id": "tuning-workload",
            "work_class": "routine_refactor",
            "tuning_candidates": [
                {"pair": "cheap/high", "historical_basis": "test"},
                {"pair": "expensive/high", "historical_basis": "test"},
                {"pair": "bad/low", "historical_basis": "test"},
                {"pair": "relative/low", "historical_basis": "test"},
            ],
            "pre_pruned_candidates": [],
        }
        tuning_suite = {
            "mode": "tuning",
            "random_seed": 1,
            "repetitions_per_condition": 1,
            "candidate_pruning": {"minimum_pass_rate": 1.0},
            "workloads": [workload],
        }

        def tuning_record(condition: str, pair: str | None, tokens: int, score: int, passed: bool) -> dict:
            item = record(condition, 1, tokens, score, passed)
            item["workload_id"] = workload["id"]
            item["run_id"] = f"run-{condition}-{pair}"
            if pair:
                item["candidate_pair"] = pair
            return item

        records = [
            tuning_record("baseline", None, 120, 85, True),
            tuning_record("tiered", "cheap/high", 80, 90, True),
            tuning_record("tiered", "expensive/high", 100, 90, True),
            tuning_record("tiered", "bad/low", 40, 20, False),
            tuning_record("tiered", "relative/low", 30, 80, True),
        ]
        analysis = benchmark.analyze_tuning({"records": records}, tuning_suite)
        candidates = analysis["workloads"][workload["id"]]["candidates"]

        self.assertEqual("failed absolute quality gate", candidates["bad/low"]["prune_reason"])
        self.assertEqual("failed relative quality gate", candidates["relative/low"]["prune_reason"])
        self.assertEqual("dominated by cheap/high", candidates["expensive/high"]["prune_reason"])
        self.assertEqual(["cheap/high"], analysis["workloads"][workload["id"]]["efficient_frontier"])


if __name__ == "__main__":
    unittest.main()
