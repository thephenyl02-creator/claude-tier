#!/usr/bin/env python3
"""Run real Codex model × effort calibration and derive efficient frontiers."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from codex_tier import (
    REFERENCE_DIR,
    SKILL_ROOT,
    TierError,
    active_candidate_matrix,
    candidate_matrix_hash,
    command_prefix,
    load_config,
    parse_pair,
    resolve_codex_binary,
    sanitize_error,
)


DEFAULT_SUITE = REFERENCE_DIR / "real-calibration-suite.json"
DEFAULT_RESULTS = REFERENCE_DIR / "real-calibration-results.json"
DEFAULT_MATRIX = REFERENCE_DIR / "candidate-matrix.json"
DEFAULT_FRONTIERS = REFERENCE_DIR / "measured-frontiers.json"
OUTPUT_SCHEMA = REFERENCE_DIR / "real-calibration-output-schema.json"
ROUTER = Path(__file__).with_name("codex_tier.py")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_suite(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TierError(f"Could not load real calibration suite {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("fixtures"), list):
        raise TierError("Real calibration suite must contain a fixtures array")
    return value


def official_cli_version(binary: Path) -> str:
    try:
        completed = subprocess.run(
            command_prefix(binary) + ["--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise TierError(f"Could not launch Codex CLI: {sanitize_error(str(exc))}") from exc
    version = completed.stdout.strip()
    if completed.returncode != 0 or not re.fullmatch(r"codex-cli \d+\.\d+\.\d+", version):
        raise TierError(
            "Real calibration requires an official Codex CLI. "
            f"Version probe returned {version or sanitize_error(completed.stderr)!r}."
        )
    return version


def extract_json_message(value: str) -> dict[str, Any] | None:
    text = value.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        lines = text.splitlines()
        if lines and lines[0].startswith(fence):
            lines = lines[1:]
        if lines and lines[-1].strip() == fence:
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def signature(item: dict[str, Any]) -> tuple[str, str]:
    file_name = str(item.get("file") or "").replace("\\", "/").lower().strip()
    while file_name.startswith("./"):
        file_name = file_name[2:]
    category = str(item.get("category") or "").lower().strip()
    return file_name, category


def signatures_match(actual: tuple[str, str], expected: tuple[str, str]) -> bool:
    actual_file, actual_category = actual
    expected_file, expected_category = expected
    return actual_category == expected_category and (
        actual_file == expected_file or actual_file.endswith("/" + expected_file)
    )


def score_message(message: str, verification: dict[str, Any]) -> dict[str, Any]:
    parsed = extract_json_message(message)
    if parsed is None:
        return {
            "quality_score": 0,
            "verification": "fail",
            "valid_json": False,
            "expected_found": 0,
            "expected_total": len(verification.get("expected", [])),
            "unexpected": 0,
        }
    findings = parsed.get("findings")
    if not isinstance(findings, list):
        findings = []
    actual = {signature(item) for item in findings if isinstance(item, dict)}
    expected = {signature(item) for item in verification.get("expected", [])}
    found = {
        expected_item
        for expected_item in expected
        if any(signatures_match(actual_item, expected_item) for actual_item in actual)
    }
    unexpected = {
        actual_item
        for actual_item in actual
        if not any(signatures_match(actual_item, expected_item) for expected_item in expected)
    }
    recall = len(found) / len(expected) if expected else 1.0
    precision = len(found) / len(actual) if actual else (1.0 if not expected else 0.0)
    has_summary = isinstance(parsed.get("summary"), str) and bool(parsed["summary"].strip())
    score = round(10 + (70 * recall) + (15 * precision) + (5 if has_summary else 0))
    score = max(0, min(100, score))
    required_quality = int(verification.get("required_quality", 0))
    passed = score >= required_quality and not unexpected
    return {
        "quality_score": score,
        "verification": "pass" if passed else "fail",
        "valid_json": True,
        "expected_found": len(found),
        "expected_total": len(expected),
        "unexpected": len(unexpected),
        "observed_signatures": [
            {"file": file_name, "category": category}
            for file_name, category in sorted(actual)
        ],
    }


def exposed_consumption(usage: dict[str, Any]) -> dict[str, Any]:
    input_tokens = usage.get("input_tokens")
    cached_tokens = usage.get("cached_input_tokens")
    output_tokens = usage.get("output_tokens")
    cache_write = usage.get("cache_write_input_tokens")
    total = (
        input_tokens + output_tokens
        if isinstance(input_tokens, int) and isinstance(output_tokens, int)
        else None
    )
    uncached = None
    if isinstance(input_tokens, int):
        uncached = max(0, input_tokens - (cached_tokens if isinstance(cached_tokens, int) else 0))
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "cache_write_input_tokens": cache_write,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": usage.get("reasoning_output_tokens")
        or usage.get("reasoning_tokens"),
        "codex_usage_credits": usage.get("credits") or usage.get("usage_credits"),
        "total_exposed_tokens": total,
        "uncached_input_tokens": uncached,
    }


def run_executor(
    *,
    binary: Path,
    repo: Path,
    model: str,
    effort: str,
    packet: str,
    work_class: str,
    timeout: int,
    log_file: Path,
    output_schema: Path | None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROUTER),
        "execute",
        "--repo",
        str(repo),
        "--model",
        model,
        "--effort",
        effort,
        "--work-class",
        work_class,
        "--sandbox",
        "read-only",
        "--approval-policy",
        "never",
        "--codex-bin",
        str(binary),
        "--log-file",
        str(log_file),
        "--timeout",
        str(timeout),
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
    ]
    if output_schema:
        command.extend(["--output-schema", str(output_schema)])
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            input=packet,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + 45,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "exit_code": 124,
            "duration_seconds": round(time.monotonic() - started, 6),
            "error": "calibration wrapper timed out",
            "usage": {},
            "final_message": "",
            "event_metrics": {"retry_count": 0, "error_event_count": 0, "tool_item_count": 0},
        }
    try:
        summary = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "exit_code": completed.returncode,
            "duration_seconds": round(time.monotonic() - started, 6),
            "error": sanitize_error(completed.stderr or completed.stdout),
            "usage": {},
            "final_message": "",
            "event_metrics": {"retry_count": 0, "error_event_count": 0, "tool_item_count": 0},
        }
    return summary


def probe_pair(
    *,
    binary: Path,
    pair: str,
    packet: str,
    timeout: int,
    log_file: Path,
) -> dict[str, Any]:
    model, effort = parse_pair(pair)
    with tempfile.TemporaryDirectory(prefix="codex-tier-launch-probe-") as temporary:
        summary = run_executor(
            binary=binary,
            repo=Path(temporary),
            model=model,
            effort=effort,
            packet=packet,
            work_class="candidate_launch_probe",
            timeout=timeout,
            log_file=log_file,
            output_schema=None,
        )
    message = str(summary.get("final_message") or "").strip()
    launched = bool(summary.get("success")) and "CODEX_TIER_LAUNCH_OK" in message
    return {
        "pair": pair,
        "model": model,
        "effort": effort,
        "status": "executed" if launched else "unavailable",
        "success": launched,
        "exit_code": summary.get("exit_code"),
        "duration_seconds": summary.get("duration_seconds"),
        "usage": exposed_consumption(summary.get("usage", {})),
        "retry_count": summary.get("event_metrics", {}).get("retry_count", 0),
        "error": None if launched else sanitize_error(str(summary.get("error") or "launch probe failed")),
    }


def calibration_record(
    *,
    binary: Path,
    pair: str,
    fixture: dict[str, Any],
    timeout: int,
    log_file: Path,
) -> dict[str, Any]:
    model, effort = parse_pair(pair)
    fixture_dir = (SKILL_ROOT / fixture["fixture_dir"]).resolve()
    if not fixture_dir.is_dir():
        raise TierError(f"Calibration fixture directory does not exist: {fixture_dir}")
    with tempfile.TemporaryDirectory(prefix="codex-tier-safe-fixture-") as temporary:
        isolated_fixture = Path(temporary) / "fixture"
        shutil.copytree(fixture_dir, isolated_fixture)
        summary = run_executor(
            binary=binary,
            repo=isolated_fixture,
            model=model,
            effort=effort,
            packet=fixture["packet"],
            work_class=fixture["work_class"],
            timeout=timeout,
            log_file=log_file,
            output_schema=OUTPUT_SCHEMA,
        )
    scoring = (
        score_message(str(summary.get("final_message") or ""), fixture["verification"])
        if summary.get("success")
        else {
            "quality_score": 0,
            "verification": "not-run",
            "valid_json": False,
            "expected_found": 0,
            "expected_total": len(fixture["verification"].get("expected", [])),
            "unexpected": 0,
        }
    )
    return {
        "fixture_id": fixture["id"],
        "work_class": fixture["work_class"],
        "pair": pair,
        "model": model,
        "effort": effort,
        "worker_success": bool(summary.get("success")),
        **scoring,
        "usage": exposed_consumption(summary.get("usage", {})),
        "duration_seconds": summary.get("duration_seconds"),
        "retry_count": summary.get("event_metrics", {}).get("retry_count", 0),
        "error_event_count": summary.get("event_metrics", {}).get("error_event_count", 0),
        "tool_item_count": summary.get("event_metrics", {}).get("tool_item_count", 0),
        "error": None if summary.get("success") else sanitize_error(str(summary.get("error") or "")),
    }


def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_usage = left.get("usage", {}).get("total_exposed_tokens")
    right_usage = right.get("usage", {}).get("total_exposed_tokens")
    if not isinstance(left_usage, int) or not isinstance(right_usage, int):
        return False
    left_quality = left.get("quality_score", 0)
    right_quality = right.get("quality_score", 0)
    return (
        left_quality >= right_quality
        and left_usage <= right_usage
        and (left_quality > right_quality or left_usage < right_usage)
    )


def derive_frontiers(records: list[dict[str, Any]], measured_at: str) -> dict[str, Any]:
    profiles: dict[str, Any] = {}
    work_classes = sorted({record["work_class"] for record in records})
    for work_class in work_classes:
        candidates = [
            record
            for record in records
            if record["work_class"] == work_class
            and record.get("worker_success")
            and record.get("verification") == "pass"
            and isinstance(record.get("usage", {}).get("total_exposed_tokens"), int)
        ]
        efficient = [
            candidate
            for candidate in candidates
            if not any(
                other["pair"] != candidate["pair"] and dominates(other, candidate)
                for other in candidates
            )
        ]
        efficient.sort(
            key=lambda item: (
                item["usage"]["total_exposed_tokens"],
                -item["quality_score"],
                item["pair"],
            )
        )
        fixture_ids = sorted({item["fixture_id"] for item in candidates})
        profiles[work_class] = {
            "fixture_id": fixture_ids[0] if len(fixture_ids) == 1 else fixture_ids,
            "evaluated_candidates": len(candidates),
            "candidates": [
                {
                    "model": item["model"],
                    "effort": item["effort"],
                    "quality": item["quality_score"],
                    "relative_usage": item["usage"]["total_exposed_tokens"],
                    "measured_total_exposed_tokens": item["usage"]["total_exposed_tokens"],
                    "measured_uncached_input_tokens": item["usage"]["uncached_input_tokens"],
                    "measured_output_tokens": item["usage"]["output_tokens"],
                    "verification": item["verification"],
                    "usage_source": "real-codex-jsonl",
                }
                for item in efficient
            ],
        }
    return {
        "schema_version": 1,
        "status": "real-codex-measurement",
        "measured_at": measured_at,
        "usage_metric": {
            "primary": "total_exposed_tokens",
            "definition": "input_tokens + output_tokens from real Codex JSONL",
            "codex_credit_mapping": "unknown unless codex_usage_credits is populated",
        },
        "profiles": profiles,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Run real probes and fixtures")
    parser.add_argument("--probe-only", action="store_true", help="Run launch probes but not fixtures")
    parser.add_argument("--suite", default=str(DEFAULT_SUITE))
    parser.add_argument("--models-cache")
    parser.add_argument("--codex-bin")
    parser.add_argument("--candidate", action="append", help="Limit to MODEL/EFFORT; repeatable")
    parser.add_argument("--fixture", action="append", help="Limit to fixture id; repeatable")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--results-file", default=str(DEFAULT_RESULTS))
    parser.add_argument("--matrix-file", default=str(DEFAULT_MATRIX))
    parser.add_argument("--frontiers-file", default=str(DEFAULT_FRONTIERS))
    parser.add_argument("--log-file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cache_path = Path(args.models_cache).expanduser() if args.models_cache else None
        registry, _ = load_config(cache_path=cache_path, include_measured=False)
        matrix = active_candidate_matrix(registry)
        selected_pairs = [item["pair"] for item in matrix]
        if args.candidate:
            requested = set(args.candidate)
            unknown = sorted(requested - set(selected_pairs))
            if unknown:
                raise TierError("Requested candidate is not active: " + ", ".join(unknown))
            selected_pairs = [pair for pair in selected_pairs if pair in requested]
        suite = load_suite(Path(args.suite).expanduser())
        fixtures = suite["fixtures"]
        if args.fixture:
            requested_fixtures = set(args.fixture)
            fixtures = [item for item in fixtures if item["id"] in requested_fixtures]
            missing = sorted(requested_fixtures - {item["id"] for item in fixtures})
            if missing:
                raise TierError("Unknown fixture: " + ", ".join(missing))

        discovery = registry.get("runtime_discovery", {})
        plan = {
            "mode": "run" if args.run else "plan",
            "real_calibration": True,
            "model_discovery": discovery,
            "candidate_count": len(selected_pairs),
            "candidate_matrix_hash": candidate_matrix_hash(matrix),
            "candidates": selected_pairs,
            "fixtures": [item["id"] for item in fixtures],
            "estimated_runs": len(selected_pairs)
            * (1 if args.probe_only else 1 + len(fixtures)),
            "note": "No deterministic substitute is accepted by --run.",
        }
        if not args.run:
            print(json.dumps(plan, indent=2, sort_keys=True))
            return 0

        binary = resolve_codex_binary(args.codex_bin)
        version = official_cli_version(binary)
        log_file = (
            Path(args.log_file).expanduser()
            if args.log_file
            else Path(tempfile.gettempdir()) / "codex-tier-real-calibration-usage.jsonl"
        )
        probe_packet = suite["probe"]["packet"]
        probes: list[dict[str, Any]] = []
        successful_pairs: list[str] = []
        for index, pair in enumerate(selected_pairs, start=1):
            print(f"PROBE {index}/{len(selected_pairs)} {pair}", file=sys.stderr, flush=True)
            probe = probe_pair(
                binary=binary,
                pair=pair,
                packet=probe_packet,
                timeout=args.timeout,
                log_file=log_file,
            )
            probes.append(probe)
            if probe["success"]:
                successful_pairs.append(pair)

        records: list[dict[str, Any]] = []
        if not args.probe_only:
            total = len(successful_pairs) * len(fixtures)
            run_index = 0
            for fixture in fixtures:
                for pair in successful_pairs:
                    run_index += 1
                    print(
                        f"CALIBRATE {run_index}/{total} {fixture['id']} {pair}",
                        file=sys.stderr,
                        flush=True,
                    )
                    records.append(
                        calibration_record(
                            binary=binary,
                            pair=pair,
                            fixture=fixture,
                            timeout=args.timeout,
                            log_file=log_file,
                        )
                    )

        measured_at = utc_now()
        frontiers = derive_frontiers(records, measured_at)
        credits_exposed = any(
            probe.get("usage", {}).get("codex_usage_credits") is not None for probe in probes
        ) or any(
            record.get("usage", {}).get("codex_usage_credits") is not None for record in records
        )
        result = {
            "schema_version": 1,
            "mode": "real-calibration",
            "measured_at": measured_at,
            "codex_cli_version": version,
            "model_discovery": discovery,
            "candidate_matrix_hash": candidate_matrix_hash(matrix),
            "candidate_count": len(selected_pairs),
            "successful_combinations": successful_pairs,
            "unavailable_combinations": [
                probe["pair"] for probe in probes if not probe["success"]
            ],
            "usage_data": {
                "jsonl_tokens_exposed": True,
                "codex_usage_credits_exposed": credits_exposed,
                "primary_frontier_metric": "total_exposed_tokens",
                "savings_percentage_published": False,
            },
            "run_metrics": {
                "launch_probes": len(probes),
                "workload_runs": len(records),
                "verification_failures": sum(
                    record.get("verification") != "pass" for record in records
                ),
                "retries": sum(record.get("retry_count", 0) for record in records),
                "error_events": sum(
                    record.get("error_event_count", 0) for record in records
                ),
                "escalations": 0,
                "escalation_note": (
                    "Candidates are measured independently; routing escalation is triggered "
                    "only after a live task verification failure."
                ),
            },
            "probes": probes,
            "records": records,
            "frontiers": frontiers["profiles"],
            "usage_log": str(log_file),
        }
        matrix_report = {
            "schema_version": 1,
            "generated_at": measured_at,
            "codex_cli_version": version,
            "model_discovery": discovery,
            "candidate_matrix_hash": candidate_matrix_hash(matrix),
            "candidate_count": len(matrix),
            "models": [
                {
                    "id": model["id"],
                    "available": model.get("active_available", True),
                    "supported_efforts": model.get("supported_efforts", []),
                    "availability_evidence": model.get("availability_evidence"),
                }
                for model in registry.get("models", [])
            ],
            "candidates": probes,
        }
        write_json(Path(args.results_file).expanduser(), result)
        write_json(Path(args.matrix_file).expanduser(), matrix_report)
        if records:
            write_json(Path(args.frontiers_file).expanduser(), frontiers)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if not result["unavailable_combinations"] else 2
    except TierError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
