#!/usr/bin/env python3
"""Five-run always-Sol/max comparison using frozen corrected-final evidence."""

from __future__ import annotations

import argparse
import copy
import json
import random
import statistics
import sys
import uuid
from pathlib import Path
from typing import Any

import e2e_benchmark as benchmark


HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "sol-max-comparison-suite.json"
DEFAULT_RESULTS = HERE / "sol-max-comparison-results.json"
DEFAULT_REPORT = HERE / "sol-max-comparison-report.md"
DEFAULT_SCHEMA = HERE / "verifier-schema.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise benchmark.BenchmarkError(message)


def load_relative(config_path: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (config_path.parent / path).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--repo")
    parser.add_argument("--codex-bin")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--results-file", default=str(DEFAULT_RESULTS))
    parser.add_argument("--report-file", default=str(DEFAULT_REPORT))
    parser.add_argument("--verifier-schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--timeout", type=int, default=600)
    return parser


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    config_path = Path(args.config).resolve()
    config = benchmark.load_json(config_path)
    source_suite_path = load_relative(config_path, config["source_suite"])
    source_results_path = load_relative(config_path, config["source_results"])
    source_suite = benchmark.load_json(source_suite_path)
    source_results = benchmark.load_json(source_results_path)
    require(source_results.get("run_status") == "complete", "Corrected final source is incomplete")
    require(source_results.get("credits_exposed") is False, "Source unexpectedly exposes credits")
    require(source_results["usage_metric"] == config["usage_metric"], "Usage metric differs")
    require(
        source_results["verifier_protocol_version"] == benchmark.VERIFIER_PROTOCOL_VERSION,
        "Verifier protocol differs from the corrected final benchmark",
    )
    require(args.repo is not None, "--repo is required")
    repo = Path(args.repo).resolve()
    state = benchmark.assert_repository_state(repo, config["repository_commit"])
    require(state["commit"] == source_results["repository_state"]["commit"], "Repository commit differs")
    require(state["tree"] == source_results["repository_state"]["tree"], "Repository tree differs")

    suite_workloads = {item["id"]: item for item in source_suite["workloads"]}
    workload_ids = list(config["workload_ids"])
    require(len(workload_ids) == len(set(workload_ids)) == 5, "Exactly five unique workloads are required")
    require(set(workload_ids) == set(suite_workloads), "Comparison must cover exactly the corrected five workloads")
    workloads = {workload_id: suite_workloads[workload_id] for workload_id in workload_ids}
    evidence, evidence_metadata = benchmark.freeze_workload_evidence(repo, workloads, state["commit"])
    identity: dict[str, Any] = {}
    tier_reference: dict[str, Any] = {}
    for workload_id in workload_ids:
        workload = workloads[workload_id]
        frozen_sha = benchmark.sha256_text(evidence[workload_id])
        task_sha = benchmark.sha256_text(workload["task"])
        packet_sha = benchmark.sha256_text(
            benchmark.canonical_packet(workload, state["commit"], evidence[workload_id])
        )
        expected = source_results["selected_hashes"][workload_id]
        require(frozen_sha == expected["frozen_evidence_sha256"], f"Evidence changed for {workload_id}")
        require(task_sha == expected["task_sha256"], f"Task changed for {workload_id}")
        require(packet_sha == expected["canonical_packet_sha256"], f"Packet changed for {workload_id}")
        tier_rows = [
            item for item in source_results["records"]
            if item["workload_id"] == workload_id and item["condition"] == "tiered"
        ]
        require(len(tier_rows) == 3, f"Expected three frozen Tier records for {workload_id}")
        require(all(item["quality"]["valid"] for item in tier_rows), f"Invalid Tier verdict for {workload_id}")
        tier_reference[workload_id] = {
            "runs": 3,
            "tokens": [item["aggregate"]["usage"]["total_exposed_tokens"] for item in tier_rows],
            "median_tokens": source_results["analysis"]["workloads"][workload_id]["conditions"]["tiered"]["median_total_exposed_tokens"],
            "median_quality": source_results["analysis"]["workloads"][workload_id]["conditions"]["tiered"]["median_quality_score"],
            "quality_pass_rate": source_results["analysis"]["workloads"][workload_id]["conditions"]["tiered"]["quality_pass_rate"],
            "median_latency_seconds": source_results["analysis"]["workloads"][workload_id]["conditions"]["tiered"]["median_execution_latency_seconds"],
            "route_pairs": sorted({
                choice["pair"]
                for item in tier_rows
                for choice in item["aggregate"]["worker_choices"]
            }),
        }
        identity[workload_id] = {
            "task_sha256": task_sha,
            "canonical_packet_sha256": packet_sha,
            "frozen_evidence_sha256": frozen_sha,
        }

    schedule = [
        {
            "run_id": f"{workload_id}--always-sol-max--r1",
            "workload_id": workload_id,
            "repetition": 1,
        }
        for workload_id in workload_ids
    ]
    random.Random(int(config["random_seed"])).shuffle(schedule)
    for position, item in enumerate(schedule, start=1):
        item["randomized_position"] = position
    pair = f"{config['comparison_pair']['model']}/{config['comparison_pair']['effort']}"
    verifier_pair = f"{config['verifier']['model']}/{config['verifier']['effort']}"
    return {
        "config": config,
        "config_path": config_path,
        "source_suite_path": source_suite_path,
        "source_results_path": source_results_path,
        "source_results": source_results,
        "repo": repo,
        "state": state,
        "workloads": workloads,
        "evidence": evidence,
        "evidence_metadata": evidence_metadata,
        "identity": identity,
        "tier_reference": tier_reference,
        "schedule": schedule,
        "pair": pair,
        "verifier_pair": verifier_pair,
    }


def plan(prepared: dict[str, Any]) -> dict[str, Any]:
    return {
        "comparison_id": prepared["config"]["comparison_id"],
        "new_primary_runs": 5,
        "tier_primary_runs": 0,
        "comparison_pair": prepared["pair"],
        "verifier_pair": prepared["verifier_pair"],
        "verifier_protocol_version": benchmark.VERIFIER_PROTOCOL_VERSION,
        "repository_state": prepared["state"],
        "schedule": prepared["schedule"],
        "identity": prepared["identity"],
        "frozen_evidence": prepared["evidence_metadata"],
        "source_results_sha256": benchmark.sha256_file(prepared["source_results_path"]),
        "usage_metric": prepared["config"]["usage_metric"],
        "credits_exposed": False,
    }


def status(results: dict[str, Any]) -> dict[str, Any]:
    records = results.get("records", [])
    return {
        "comparison_id": results.get("comparison_id"),
        "run_status": results.get("run_status"),
        "stop_reason": results.get("stop_reason"),
        "usage_limit_reset_hint": results.get("usage_limit_reset_hint"),
        "primary_runs_completed": sum(bool(item.get("attempt")) for item in records),
        "fully_verified": sum(item.get("benchmark_state") == "complete" for item in records),
        "infrastructure_events": sum(len(item.get("infrastructure_attempts", [])) for item in records),
        "started_at": results.get("started_at"),
        "completed_at": results.get("completed_at"),
    }


def analyze(results: dict[str, Any], prepared: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    reductions: list[tuple[str, float]] = []
    minimum_change = float(prepared["config"]["clarity_minimum_absolute_reduction_percent"])
    quality_margin = float(prepared["config"]["maximum_quality_regression_points"])
    for workload_id, workload in prepared["workloads"].items():
        record = next(item for item in results["records"] if item["workload_id"] == workload_id)
        require(record["benchmark_state"] == "complete", f"Incomplete record for {workload_id}")
        max_tokens = record["attempt"]["usage"]["total_exposed_tokens"]
        tier = prepared["tier_reference"][workload_id]
        reduction = round((1 - float(tier["median_tokens"]) / float(max_tokens)) * 100, 6)
        tier_quality_preserved = (
            tier["quality_pass_rate"] == 1.0
            and tier["median_quality"] >= record["quality"]["score"] - quality_margin
        )
        tier_range = [min(tier["tokens"]), max(tier["tokens"])]
        nonoverlap = max_tokens > tier_range[1] or max_tokens < tier_range[0]
        clear = bool(tier_quality_preserved and nonoverlap and abs(reduction) >= minimum_change)
        reasons = []
        if not tier_quality_preserved:
            reasons.append("quality is not comparable under the frozen quality margin")
        if not nonoverlap:
            reasons.append("the single Max observation overlaps the three Tier observations")
        if abs(reduction) < minimum_change:
            reasons.append(f"absolute reduction is below the {minimum_change:g}% clarity threshold")
        if clear:
            reasons.append("quality is comparable and the Max observation is separated from all Tier observations")
        comparisons[workload_id] = {
            "work_class": workload["work_class"],
            "sol_max_tokens": max_tokens,
            "tier_median_tokens": tier["median_tokens"],
            "tier_vs_max_exposed_token_reduction_percent": reduction,
            "sol_max_quality": record["quality"]["score"],
            "sol_max_passed": record["quality"]["passed"],
            "tier_median_quality": tier["median_quality"],
            "tier_pass_rate": tier["quality_pass_rate"],
            "sol_max_latency_seconds": record["attempt"]["latency_seconds"],
            "tier_median_latency_seconds": tier["median_latency_seconds"],
            "tier_route_pairs": tier["route_pairs"],
            "tier_observed_token_range": tier_range,
            "comparison": "clear" if clear else "ambiguous",
            "comparison_reason": "; ".join(reasons),
        }
        reductions.append((workload_id, reduction))
    values = [item[1] for item in reductions]
    best = max(reductions, key=lambda item: item[1])
    worst = min(reductions, key=lambda item: item[1])
    ambiguous = [workload_id for workload_id, item in comparisons.items() if item["comparison"] == "ambiguous"]
    return {
        "workloads": comparisons,
        "overall": {
            "median_exposed_token_reduction_vs_always_sol_max_percent": round(statistics.median(values), 6),
            "mean_exposed_token_reduction_vs_always_sol_max_percent": round(statistics.mean(values), 6),
            "best_case": {"workload_id": best[0], "reduction_percent": best[1]},
            "worst_case": {"workload_id": worst[0], "reduction_percent": worst[1]},
            "clear_workloads": len(comparisons) - len(ambiguous),
            "ambiguous_workloads": ambiguous,
            "more_repetitions_needed_for_clear_workload_claims": bool(ambiguous),
            "more_repetitions_needed_for_publishable_aggregate_claim": True,
            "note": "Each Sol/max workload has one observation; aggregate percentages are lightweight directional comparisons, not a repeated-run economic benchmark.",
            "credits_exposed": False,
        },
    }


def render_report(results: dict[str, Any]) -> str:
    analysis = results["analysis"]
    overall = analysis["overall"]
    lines = [
        "# Codex Tier v1 vs always-Sol/max — lightweight comparison",
        "",
        "Five new direct `gpt-5.6-sol/max` runs were compared with the existing corrected-final Tier medians. Tier was not rerun.",
        "",
        "| Workload | Sol/max tokens | Tier median tokens | Tier reduction vs Max | Quality Max/Tier | Latency Max/Tier | Assessment |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in analysis["workloads"].values():
        lines.append(
            f"| {item['work_class']} | {item['sol_max_tokens']:,} | {item['tier_median_tokens']:,.0f} | "
            f"{item['tier_vs_max_exposed_token_reduction_percent']:+.2f}% | "
            f"{item['sol_max_quality']}/{item['tier_median_quality']:.1f} | "
            f"{item['sol_max_latency_seconds']:.1f}s/{item['tier_median_latency_seconds']:.1f}s | "
            f"{item['comparison']} |"
        )
    lines.extend([
        "",
        f"- Median exposed-token reduction vs always-Sol/max: **{overall['median_exposed_token_reduction_vs_always_sol_max_percent']:+.2f}%**.",
        f"- Mean exposed-token reduction vs always-Sol/max: **{overall['mean_exposed_token_reduction_vs_always_sol_max_percent']:+.2f}%**.",
        f"- Best case: `{overall['best_case']['workload_id']}` at {overall['best_case']['reduction_percent']:+.2f}%.",
        f"- Worst case: `{overall['worst_case']['workload_id']}` at {overall['worst_case']['reduction_percent']:+.2f}%.",
        f"- Clear/ambiguous workloads: {overall['clear_workloads']}/{len(analysis['workloads']) - overall['clear_workloads']}.",
        f"- More repetitions needed for clear workload claims: {'yes' if overall['more_repetitions_needed_for_clear_workload_claims'] else 'no'}.",
        "- More repetitions are required before treating the five-run aggregate as a publishable repeated-run estimate.",
        "- Codex credits, billing, dollars, and 5-hour quota consumption were not exposed and are not claimed.",
        "",
        "A comparison is marked clear only when quality is comparable, the single Sol/max observation lies outside all three existing Tier observations, and the absolute difference is at least 5%. Otherwise it is conservatively marked ambiguous.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results_path = Path(args.results_file).resolve()
    if args.status:
        require(results_path.exists(), f"No checkpoint exists: {results_path}")
        print(json.dumps(status(benchmark.load_json(results_path)), indent=2, sort_keys=True))
        return 0
    prepared = prepare(args)
    comparison_plan = plan(prepared)
    if not args.run:
        print(json.dumps(comparison_plan, indent=2, sort_keys=True))
        return 0
    require(args.codex_bin is not None, "--codex-bin is required for real execution")
    binary = benchmark.codex_tier.resolve_codex_binary(args.codex_bin)
    cli_version = benchmark.official_cli_version(binary)
    report_path = Path(args.report_file).resolve()
    schema_path = Path(args.verifier_schema).resolve()
    usage_log = results_path.with_name("sol-max-comparison-task-usage.jsonl")
    verifier_log = results_path.with_name("sol-max-comparison-verifier-usage.jsonl")

    if results_path.exists():
        require(args.resume, f"Results already exist: {results_path}; use --resume")
        results = benchmark.load_json(results_path)
        require(results["config_sha256"] == benchmark.sha256_file(prepared["config_path"]), "Config changed")
        require(results["source_results_sha256"] == comparison_plan["source_results_sha256"], "Source results changed")
        require(results["repository_state"] == prepared["state"], "Repository state changed")
        require(results["identity"] == prepared["identity"], "Frozen task/evidence identity changed")
        results["run_status"] = "running"
        results.pop("stop_reason", None)
        results.pop("usage_limit_reset_hint", None)
        benchmark.write_json_atomic(results_path, results)
    else:
        results = {
            "schema_version": 1,
            **comparison_plan,
            "config_sha256": benchmark.sha256_file(prepared["config_path"]),
            "codex_cli_version": cli_version,
            "started_at": benchmark.utc_now(),
            "completed_at": None,
            "run_status": "running",
            "records": [],
            "tier_reference": prepared["tier_reference"],
            "analysis": None,
            "verifier_usage_included_in_reduction": False,
            "credit_savings_published": False,
        }
        benchmark.write_json_atomic(results_path, results)

    records = {item["run_id"]: item for item in results["records"]}
    for scheduled in prepared["schedule"]:
        workload_id = scheduled["workload_id"]
        workload = prepared["workloads"][workload_id]
        evidence = prepared["evidence"][workload_id]
        packet = benchmark.canonical_packet(workload, prepared["state"]["commit"], evidence)
        record = records.get(scheduled["run_id"])
        if record is None:
            record = {
                **scheduled,
                "work_class": workload["work_class"],
                "pair": prepared["pair"],
                "task_prompt_sha256": prepared["identity"][workload_id]["task_sha256"],
                "canonical_packet_sha256": prepared["identity"][workload_id]["canonical_packet_sha256"],
                "frozen_evidence_sha256": prepared["identity"][workload_id]["frozen_evidence_sha256"],
                "benchmark_state": "awaiting_primary",
                "attempt": None,
                "infrastructure_attempts": [],
                "verification_attempts": [],
                "quality": None,
            }
            results["records"].append(record)
            records[record["run_id"]] = record
            benchmark.write_json_atomic(results_path, results)
        if record["benchmark_state"] != "awaiting_primary":
            continue
        if record.get("attempt") is None:
            print(
                f"PRIMARY {scheduled['randomized_position']}/5 {scheduled['run_id']} {prepared['pair']}",
                file=sys.stderr,
                flush=True,
            )
            benchmark.assert_repository_state(prepared["repo"], prepared["config"]["repository_commit"])
            attempt = benchmark.run_attempt(
                repo=prepared["repo"],
                binary=binary,
                packet=packet,
                pair=prepared["pair"],
                parent_pair=prepared["pair"],
                work_class=workload["work_class"],
                run_id=f"{record['run_id']}--attempt-1",
                timeout=args.timeout,
                log_file=usage_log,
                reason="always-sol-max-comparison",
            )
            benchmark.assert_repository_state(prepared["repo"], prepared["config"]["repository_commit"])
            if not attempt.get("success"):
                record["infrastructure_attempts"].append(attempt)
                benchmark.write_json_atomic(results_path, results)
                if attempt.get("failure_kind") == "usage_limit":
                    benchmark.checkpoint_usage_limit(results, results_path, attempt, "primary")
                raise benchmark.BenchmarkError(f"Primary execution failed for {record['run_id']}; checkpoint saved")
            record["attempt"] = attempt
            benchmark.write_json_atomic(results_path, results)
        record["benchmark_state"] = "awaiting_verification"
        benchmark.write_json_atomic(results_path, results)

    verification_order = copy.deepcopy(prepared["schedule"])
    random.Random(int(prepared["config"]["random_seed"]) + 1).shuffle(verification_order)
    for position, scheduled in enumerate(verification_order, start=1):
        record = records[scheduled["run_id"]]
        if record["benchmark_state"] == "complete":
            continue
        workload_id = scheduled["workload_id"]
        workload = prepared["workloads"][workload_id]
        evidence = prepared["evidence"][workload_id]
        minimum_score = int(prepared["config"]["minimum_quality_score"])
        verdict = benchmark.checkpointed_verdict(record, "initial", minimum_score)
        if verdict is None:
            blind_id = uuid.uuid4().hex
            print(f"VERIFY {position}/5 {blind_id} {workload_id}", file=sys.stderr, flush=True)

            def persist(attempt: dict[str, Any]) -> None:
                record["verification_attempts"].append(attempt)
                benchmark.write_json_atomic(results_path, results)

            verdict, _ = benchmark.run_verification(
                repo=prepared["repo"],
                binary=binary,
                workload=workload,
                response=record["attempt"]["response"],
                commit=prepared["state"]["commit"],
                minimum_score=minimum_score,
                verifier_pair=prepared["verifier_pair"],
                parent_pair=prepared["pair"],
                run_id=blind_id,
                timeout=args.timeout,
                log_file=verifier_log,
                schema=schema_path,
                evidence=evidence,
                phase="initial",
                on_attempt=persist,
            )
        if not verdict.get("valid"):
            usage_attempt = next(
                (item for item in reversed(record["verification_attempts"]) if item.get("failure_kind") == "usage_limit"),
                None,
            )
            if usage_attempt:
                benchmark.checkpoint_usage_limit(results, results_path, usage_attempt, "verifier")
            raise benchmark.BenchmarkError(f"Verifier failed for {record['run_id']}; checkpoint saved")
        record["quality"] = verdict
        record["benchmark_state"] = "complete"
        benchmark.write_json_atomic(results_path, results)

    results["analysis"] = analyze(results, prepared)
    results["run_status"] = "complete"
    results["completed_at"] = benchmark.utc_now()
    benchmark.write_json_atomic(results_path, results)
    report_path.write_text(render_report(results), encoding="utf-8", newline="\n")
    print(json.dumps(results["analysis"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except benchmark.UsageLimitReached as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(75)
