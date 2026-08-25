#!/usr/bin/env python3
"""Plan or run a bounded, workload-specific model × effort benchmark manifest."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from codex_tier import TierError, parse_pair, route_work_unit


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = SCRIPT_DIR.parent / "references" / "benchmark-suite.json"


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TierError(f"Could not load benchmark manifest {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("cases"), list):
        raise TierError("Benchmark manifest must contain a cases array")
    return value


def verify_result(case: dict[str, Any], final_message: str) -> str:
    verification = case.get("verification", {"type": "manual"})
    kind = verification.get("type", "manual")
    if kind == "manual":
        return "manual-review-required"
    if kind == "contains_all":
        values = verification.get("values", [])
        return "pass" if all(str(value) in final_message for value in values) else "fail"
    if kind == "valid_json":
        try:
            parsed = json.loads(final_message)
        except json.JSONDecodeError:
            return "fail"
        required = verification.get("required_keys", [])
        return "pass" if isinstance(parsed, dict) and all(key in parsed for key in required) else "fail"
    raise TierError(f"Unsupported benchmark verification type: {kind}")


def plan_case(case: dict[str, Any]) -> dict[str, Any]:
    classification = case["classification"]
    decision = route_work_unit(
        work_class=case["work_class"],
        complexity=classification["complexity"],
        volume=classification["volume"],
        risk=classification["risk"],
        context=classification["context"],
    )
    return {
        "id": case["id"],
        "work_class": case["work_class"],
        "router_mode": decision["execution_mode"],
        "router_selection": decision.get("selected"),
        "benchmark_candidates": case.get("candidates", []),
        "verification": case.get("verification", {"type": "manual"}),
    }


def run_candidate(
    *,
    case: dict[str, Any],
    candidate: str,
    repo: Path,
    codex_bin: str | None,
    log_file: Path,
    timeout: int,
) -> dict[str, Any]:
    model, effort = parse_pair(candidate)
    command = [
        sys.executable,
        str(SCRIPT_DIR / "codex_tier.py"),
        "execute",
        "--repo",
        str(repo),
        "--model",
        model,
        "--effort",
        effort,
        "--work-class",
        case["work_class"],
        "--sandbox",
        case.get("sandbox", "read-only"),
        "--log-file",
        str(log_file),
        "--timeout",
        str(timeout),
    ]
    if codex_bin:
        command.extend(["--codex-bin", codex_bin])
    completed = subprocess.run(
        command,
        input=case["packet"],
        capture_output=True,
        text=True,
        timeout=timeout + 30,
        check=False,
    )
    try:
        summary = json.loads(completed.stdout)
    except json.JSONDecodeError:
        summary = {
            "success": False,
            "exit_code": completed.returncode,
            "error": completed.stderr[:1000],
        }
    final_message = str(summary.get("final_message") or "")
    return {
        "case_id": case["id"],
        "work_class": case["work_class"],
        "candidate": candidate,
        "worker_success": bool(summary.get("success")),
        "verification": verify_result(case, final_message) if summary.get("success") else "not-run",
        "duration_seconds": summary.get("duration_seconds"),
        "usage": summary.get("usage", {}),
        "error": summary.get("error"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--run", action="store_true", help="Execute listed candidates; default is plan-only")
    parser.add_argument("--repo")
    parser.add_argument("--codex-bin")
    parser.add_argument("--log-file")
    parser.add_argument("--results-file")
    parser.add_argument("--timeout", type=int, default=1800)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = load_manifest(Path(args.manifest).expanduser())
        plans = [plan_case(case) for case in manifest["cases"]]
        if not args.run:
            print(json.dumps({"mode": "plan", "cases": plans}, indent=2, sort_keys=True))
            return 0
        if not args.repo:
            raise TierError("--repo is required with --run")
        repo = Path(args.repo).expanduser().resolve()
        if not repo.is_dir():
            raise TierError(f"Repository does not exist: {repo}")
        log_file = (
            Path(args.log_file).expanduser()
            if args.log_file
            else Path(tempfile.gettempdir()) / "codex-tier-benchmark-usage.jsonl"
        )
        records: list[dict[str, Any]] = []
        for case in manifest["cases"]:
            for candidate in case.get("candidates", []):
                records.append(
                    run_candidate(
                        case=case,
                        candidate=candidate,
                        repo=repo,
                        codex_bin=args.codex_bin,
                        log_file=log_file,
                        timeout=args.timeout,
                    )
                )
        result = {
            "mode": "run",
            "note": "Raw usage is reported without inventing a savings percentage.",
            "records": records,
            "usage_log": str(log_file),
        }
        rendered = json.dumps(result, indent=2, sort_keys=True)
        if args.results_file:
            Path(args.results_file).expanduser().write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0 if all(record["worker_success"] for record in records) else 2
    except TierError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
