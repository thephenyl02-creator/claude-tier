#!/usr/bin/env python3
"""Add two Sol/max observations to each ambiguous lightweight comparison."""

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
DEFAULT_CONFIG = HERE / "sol-max-comparison-extension-suite.json"
DEFAULT_RESULTS = HERE / "sol-max-comparison-final-results.json"
DEFAULT_REPORT = HERE / "sol-max-comparison-final-report.md"
DEFAULT_SCHEMA = HERE / "verifier-schema.json"
ARCHITECTURE_ID = "real-distribution-architecture"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise benchmark.BenchmarkError(message)


def relative(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base.parent / path).resolve()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--run", action="store_true")
    result.add_argument("--resume", action="store_true")
    result.add_argument("--status", action="store_true")
    result.add_argument("--repo")
    result.add_argument("--codex-bin")
    result.add_argument("--config", default=str(DEFAULT_CONFIG))
    result.add_argument("--results-file", default=str(DEFAULT_RESULTS))
    result.add_argument("--report-file", default=str(DEFAULT_REPORT))
    result.add_argument("--verifier-schema", default=str(DEFAULT_SCHEMA))
    result.add_argument("--timeout", type=int, default=600)
    return result


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    config_path = Path(args.config).resolve()
    config = benchmark.load_json(config_path)
    suite_path = relative(config_path, config["source_suite"])
    tier_path = relative(config_path, config["source_results"])
    prior_path = relative(config_path, config["prior_comparison_results"])
    suite = benchmark.load_json(suite_path)
    tier_results = benchmark.load_json(tier_path)
    prior = benchmark.load_json(prior_path)
    require(tier_results["run_status"] == prior["run_status"] == "complete", "A source artifact is incomplete")
    require(prior["new_primary_runs"] == 5 and prior["tier_primary_runs"] == 0, "Prior comparison scope changed")
    require(prior["verifier_protocol_version"] == benchmark.VERIFIER_PROTOCOL_VERSION, "Prior verifier protocol differs")
    require(tier_results["verifier_protocol_version"] == benchmark.VERIFIER_PROTOCOL_VERSION, "Tier verifier protocol differs")
    require(prior["usage_metric"] == tier_results["usage_metric"] == config["usage_metric"], "Usage metric differs")
    pair = f"{config['comparison_pair']['model']}/{config['comparison_pair']['effort']}"
    verifier_pair = f"{config['verifier']['model']}/{config['verifier']['effort']}"
    require(prior["comparison_pair"] == pair, "Comparison pair differs")
    require(prior["verifier_pair"] == verifier_pair, "Verifier pair differs")
    require(args.repo is not None, "--repo is required")
    repo = Path(args.repo).resolve()
    state = benchmark.assert_repository_state(repo, config["repository_commit"])
    require(state == prior["repository_state"] == tier_results["repository_state"], "Repository state differs")

    all_workloads = {item["id"]: item for item in suite["workloads"]}
    extension_ids = list(config["workload_ids"])
    require(len(extension_ids) == len(set(extension_ids)) == 4, "Exactly four unique extension workloads are required")
    require(ARCHITECTURE_ID not in extension_ids, "Architecture must not be rerun")
    require(set(extension_ids) == set(all_workloads) - {ARCHITECTURE_ID}, "Extension workload scope is invalid")
    require(config["repetitions"] == [2, 3], "Only repetitions 2 and 3 are allowed")
    evidence, evidence_metadata = benchmark.freeze_workload_evidence(repo, all_workloads, state["commit"])
    identities: dict[str, Any] = {}
    for workload_id, workload in all_workloads.items():
        frozen_sha = benchmark.sha256_text(evidence[workload_id])
        task_sha = benchmark.sha256_text(workload["task"])
        packet_sha = benchmark.sha256_text(
            benchmark.canonical_packet(workload, state["commit"], evidence[workload_id])
        )
        expected = tier_results["selected_hashes"][workload_id]
        require(frozen_sha == expected["frozen_evidence_sha256"], f"Evidence changed for {workload_id}")
        require(task_sha == expected["task_sha256"], f"Task changed for {workload_id}")
        require(packet_sha == expected["canonical_packet_sha256"], f"Packet changed for {workload_id}")
        require(prior["identity"][workload_id] == {
            "task_sha256": task_sha,
            "canonical_packet_sha256": packet_sha,
            "frozen_evidence_sha256": frozen_sha,
        }, f"Prior comparison identity changed for {workload_id}")
        identities[workload_id] = copy.deepcopy(prior["identity"][workload_id])

    require(len(prior["records"]) == 5, "Prior comparison must contain five records")
    require({item["workload_id"] for item in prior["records"]} == set(all_workloads), "Prior workload coverage differs")
    require(all(item["benchmark_state"] == "complete" for item in prior["records"]), "Prior comparison record is incomplete")
    schedule = [
        {
            "run_id": f"{workload_id}--always-sol-max--r{repetition}",
            "workload_id": workload_id,
            "repetition": repetition,
        }
        for workload_id in extension_ids
        for repetition in config["repetitions"]
    ]
    random.Random(int(config["random_seed"])).shuffle(schedule)
    for position, item in enumerate(schedule, start=1):
        item["randomized_position"] = position
    return {
        "config": config,
        "config_path": config_path,
        "suite_path": suite_path,
        "tier_path": tier_path,
        "prior_path": prior_path,
        "tier_results": tier_results,
        "prior": prior,
        "workloads": all_workloads,
        "evidence": evidence,
        "evidence_metadata": evidence_metadata,
        "identities": identities,
        "repo": repo,
        "state": state,
        "schedule": schedule,
        "pair": pair,
        "verifier_pair": verifier_pair,
    }


def plan(prepared: dict[str, Any]) -> dict[str, Any]:
    return {
        "comparison_id": prepared["config"]["comparison_id"],
        "new_primary_runs": 8,
        "prior_max_primary_runs": 5,
        "tier_primary_runs": 0,
        "architecture_new_primary_runs": 0,
        "comparison_pair": prepared["pair"],
        "verifier_pair": prepared["verifier_pair"],
        "verifier_protocol_version": benchmark.VERIFIER_PROTOCOL_VERSION,
        "repository_state": prepared["state"],
        "schedule": prepared["schedule"],
        "identity": prepared["identities"],
        "frozen_evidence": prepared["evidence_metadata"],
        "prior_comparison_sha256": benchmark.sha256_file(prepared["prior_path"]),
        "tier_results_sha256": benchmark.sha256_file(prepared["tier_path"]),
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
        "new_primary_runs_completed": sum(bool(item.get("attempt")) for item in records),
        "fully_verified": sum(item.get("benchmark_state") == "complete" for item in records),
        "infrastructure_events": sum(len(item.get("infrastructure_attempts", [])) for item in records),
        "started_at": results.get("started_at"),
        "completed_at": results.get("completed_at"),
    }


def observation(record: dict[str, Any]) -> dict[str, Any]:
    attempt = record.get("attempt") or record["attempts"][-1]
    return {
        "run_id": record["run_id"],
        "repetition": record["repetition"],
        "tokens": attempt["usage"]["total_exposed_tokens"],
        "quality": record["quality"]["score"],
        "passed": record["quality"]["passed"],
        "latency_seconds": attempt["latency_seconds"],
    }


def analyze(results: dict[str, Any], prepared: dict[str, Any]) -> dict[str, Any]:
    prior_by_workload = {item["workload_id"]: item for item in prepared["prior"]["records"]}
    new_by_workload: dict[str, list[dict[str, Any]]] = {}
    for item in results["records"]:
        new_by_workload.setdefault(item["workload_id"], []).append(item)
    comparisons: dict[str, Any] = {}
    reductions: list[tuple[str, float]] = []
    min_reduction = float(prepared["config"]["clarity_minimum_absolute_reduction_percent"])
    quality_margin = float(prepared["config"]["maximum_quality_regression_points"])
    minimum_quality = int(prepared["config"]["minimum_quality_score"])
    for workload_id, workload in prepared["workloads"].items():
        max_records = [prior_by_workload[workload_id], *new_by_workload.get(workload_id, [])]
        expected = 1 if workload_id == ARCHITECTURE_ID else 3
        require(len(max_records) == expected, f"Expected {expected} Max observations for {workload_id}")
        max_observations = [observation(item) for item in max_records]
        tier_rows = [
            item for item in prepared["tier_results"]["records"]
            if item["workload_id"] == workload_id and item["condition"] == "tiered"
        ]
        require(len(tier_rows) == 3, f"Expected three Tier observations for {workload_id}")
        max_tokens = [item["tokens"] for item in max_observations]
        tier_tokens = [item["aggregate"]["usage"]["total_exposed_tokens"] for item in tier_rows]
        max_quality = [item["quality"] for item in max_observations]
        tier_quality = [item["quality"]["score"] for item in tier_rows]
        max_pass_rate = sum(item["passed"] for item in max_observations) / len(max_observations)
        tier_pass_rate = sum(item["quality"]["passed"] for item in tier_rows) / len(tier_rows)
        median_max_tokens = statistics.median(max_tokens)
        median_tier_tokens = statistics.median(tier_tokens)
        median_max_quality = statistics.median(max_quality)
        median_tier_quality = statistics.median(tier_quality)
        reduction = round((1 - median_tier_tokens / median_max_tokens) * 100, 6)
        quality_gate_met = (
            max_pass_rate == tier_pass_rate == 1.0
            and median_max_quality >= minimum_quality
            and median_tier_quality >= minimum_quality
        )
        quality_comparable = quality_gate_met and median_tier_quality >= median_max_quality - quality_margin
        direction_support = sum(value > median_tier_tokens for value in max_tokens)
        required_support = 1 if workload_id == ARCHITECTURE_ID else 2
        clear = bool(
            quality_comparable
            and reduction >= min_reduction
            and direction_support >= required_support
        )
        reasons = []
        if not quality_gate_met:
            reasons.append("one condition did not pass the frozen quality threshold in every observation")
        if quality_gate_met and not quality_comparable:
            reasons.append("Tier median quality is more than three points below Max")
        if reduction < min_reduction:
            reasons.append(f"median reduction is below the {min_reduction:g}% clarity threshold")
        if direction_support < required_support:
            reasons.append("the Max observations do not support the median token direction consistently")
        if clear:
            reasons.append("quality is comparable and the token direction/effect threshold is met")
        comparisons[workload_id] = {
            "work_class": workload["work_class"],
            "max_observations": max_observations,
            "max_runs": len(max_observations),
            "tier_runs": 3,
            "median_max_tokens": median_max_tokens,
            "median_tier_tokens": median_tier_tokens,
            "tier_exposed_token_reduction_vs_always_sol_max_percent": reduction,
            "median_max_quality": median_max_quality,
            "median_tier_quality": median_tier_quality,
            "max_pass_rate": round(max_pass_rate, 6),
            "tier_pass_rate": round(tier_pass_rate, 6),
            "median_max_latency_seconds": round(statistics.median(item["latency_seconds"] for item in max_observations), 6),
            "median_tier_latency_seconds": round(statistics.median(item["aggregate"]["execution_latency_seconds"] for item in tier_rows), 6),
            "quality_gate_met": quality_gate_met,
            "quality_comparable_within_three_points": quality_comparable,
            "comparison": "clear" if clear else "ambiguous",
            "comparison_reason": "; ".join(reasons),
        }
        reductions.append((workload_id, reduction))
    values = [item[1] for item in reductions]
    best = max(reductions, key=lambda item: item[1])
    worst = min(reductions, key=lambda item: item[1])
    ambiguous = [key for key, value in comparisons.items() if value["comparison"] == "ambiguous"]
    positive = [key for key, value in comparisons.items() if value["tier_exposed_token_reduction_vs_always_sol_max_percent"] > 0]
    all_quality_passed = all(value["quality_gate_met"] for value in comparisons.values())
    directional_claim = bool(
        len(positive) == len(comparisons)
        and all_quality_passed
        and statistics.median(values) > 0
        and statistics.mean(values) > 0
    )
    quality_equivalent_claim = directional_claim and not ambiguous
    return {
        "workloads": comparisons,
        "overall": {
            "median_exposed_token_reduction_vs_always_sol_max_percent": round(statistics.median(values), 6),
            "mean_exposed_token_reduction_vs_always_sol_max_percent": round(statistics.mean(values), 6),
            "best_case": {"workload_id": best[0], "reduction_percent": best[1]},
            "worst_case": {"workload_id": worst[0], "reduction_percent": worst[1]},
            "positive_reduction_workloads": len(positive),
            "quality_gate_passed_workloads": sum(value["quality_gate_met"] for value in comparisons.values()),
            "clear_workloads": len(comparisons) - len(ambiguous),
            "ambiguous_workloads": ambiguous,
            "defensible_exposed_token_reduction_vs_always_sol_max": directional_claim,
            "defensible_quality_equivalent_reduction_claim": quality_equivalent_claim,
            "architecture_max_repetitions": 1,
            "other_max_repetitions": 3,
            "credits_exposed": False,
        },
    }


def render(results: dict[str, Any]) -> str:
    analysis = results["analysis"]
    overall = analysis["overall"]
    lines = [
        "# Codex Tier v1 vs always-Sol/max — completed comparison",
        "",
        "The four formerly ambiguous workloads now have three Sol/max observations each. Architecture retains its previously clear single Sol/max observation. Existing Tier results were not rerun.",
        "",
        "| Workload | Max runs | Median Max tokens | Median Tier tokens | Tier reduction vs Max | Median quality Max/Tier | Pass Max/Tier | Median latency Max/Tier | Assessment |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in analysis["workloads"].values():
        lines.append(
            f"| {item['work_class']} | {item['max_runs']} | {item['median_max_tokens']:,.0f} | "
            f"{item['median_tier_tokens']:,.0f} | {item['tier_exposed_token_reduction_vs_always_sol_max_percent']:+.2f}% | "
            f"{item['median_max_quality']:.1f}/{item['median_tier_quality']:.1f} | "
            f"{item['max_pass_rate']:.0%}/{item['tier_pass_rate']:.0%} | "
            f"{item['median_max_latency_seconds']:.1f}s/{item['median_tier_latency_seconds']:.1f}s | {item['comparison']} |"
        )
    lines.extend([
        "",
        f"- Median exposed-token reduction vs always-Sol/max: **{overall['median_exposed_token_reduction_vs_always_sol_max_percent']:+.2f}%**.",
        f"- Mean exposed-token reduction vs always-Sol/max: **{overall['mean_exposed_token_reduction_vs_always_sol_max_percent']:+.2f}%**.",
        f"- Best case: `{overall['best_case']['workload_id']}` at {overall['best_case']['reduction_percent']:+.2f}%.",
        f"- Worst case: `{overall['worst_case']['workload_id']}` at {overall['worst_case']['reduction_percent']:+.2f}%.",
        f"- Positive reductions: {overall['positive_reduction_workloads']}/5; quality thresholds passed: {overall['quality_gate_passed_workloads']}/5.",
        f"- Defensible exposed-token reduction vs always-Sol/max: {'yes' if overall['defensible_exposed_token_reduction_vs_always_sol_max'] else 'no'}.",
        f"- Defensible quality-equivalent reduction claim: {'yes' if overall['defensible_quality_equivalent_reduction_claim'] else 'no'}.",
        "- Architecture remains based on one Max observation because it was already clear and was explicitly excluded from further runs.",
        "- Codex credits, billing, dollars, and 5-hour quota consumption were not exposed and are not claimed.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    results_path = Path(args.results_file).resolve()
    if args.status:
        require(results_path.exists(), f"No checkpoint exists: {results_path}")
        print(json.dumps(status(benchmark.load_json(results_path)), indent=2, sort_keys=True))
        return 0
    prepared = prepare(args)
    current_plan = plan(prepared)
    if not args.run:
        print(json.dumps(current_plan, indent=2, sort_keys=True))
        return 0
    require(args.codex_bin is not None, "--codex-bin is required for real execution")
    binary = benchmark.codex_tier.resolve_codex_binary(args.codex_bin)
    cli_version = benchmark.official_cli_version(binary)
    report_path = Path(args.report_file).resolve()
    schema_path = Path(args.verifier_schema).resolve()
    usage_log = results_path.with_name("sol-max-comparison-extension-task-usage.jsonl")
    verifier_log = results_path.with_name("sol-max-comparison-extension-verifier-usage.jsonl")
    if results_path.exists():
        require(args.resume, f"Results already exist: {results_path}; use --resume")
        results = benchmark.load_json(results_path)
        require(results["config_sha256"] == benchmark.sha256_file(prepared["config_path"]), "Config changed")
        require(results["prior_comparison_sha256"] == current_plan["prior_comparison_sha256"], "Prior comparison changed")
        require(results["tier_results_sha256"] == current_plan["tier_results_sha256"], "Tier source changed")
        require(results["identity"] == prepared["identities"], "Frozen identity changed")
        results["run_status"] = "running"
        results.pop("stop_reason", None)
        results.pop("usage_limit_reset_hint", None)
        benchmark.write_json_atomic(results_path, results)
    else:
        results = {
            "schema_version": 1,
            **current_plan,
            "config_sha256": benchmark.sha256_file(prepared["config_path"]),
            "codex_cli_version": cli_version,
            "started_at": benchmark.utc_now(),
            "completed_at": None,
            "run_status": "running",
            "records": [],
            "analysis": None,
            "verifier_usage_included_in_reduction": False,
            "credit_savings_published": False,
        }
        benchmark.write_json_atomic(results_path, results)
    records = {item["run_id"]: item for item in results["records"]}
    for scheduled in prepared["schedule"]:
        workload_id = scheduled["workload_id"]
        workload = prepared["workloads"][workload_id]
        packet = benchmark.canonical_packet(workload, prepared["state"]["commit"], prepared["evidence"][workload_id])
        record = records.get(scheduled["run_id"])
        if record is None:
            record = {
                **scheduled,
                "work_class": workload["work_class"],
                "pair": prepared["pair"],
                "task_prompt_sha256": prepared["identities"][workload_id]["task_sha256"],
                "canonical_packet_sha256": prepared["identities"][workload_id]["canonical_packet_sha256"],
                "frozen_evidence_sha256": prepared["identities"][workload_id]["frozen_evidence_sha256"],
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
            print(f"PRIMARY {scheduled['randomized_position']}/8 {scheduled['run_id']} {prepared['pair']}", file=sys.stderr, flush=True)
            benchmark.assert_repository_state(prepared["repo"], prepared["config"]["repository_commit"])
            attempt = benchmark.run_attempt(
                repo=prepared["repo"], binary=binary, packet=packet,
                pair=prepared["pair"], parent_pair=prepared["pair"],
                work_class=workload["work_class"], run_id=f"{record['run_id']}--attempt-1",
                timeout=args.timeout, log_file=usage_log, reason="always-sol-max-comparison-extension",
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
        verdict = benchmark.checkpointed_verdict(record, "initial", int(prepared["config"]["minimum_quality_score"]))
        if verdict is None:
            blind_id = uuid.uuid4().hex
            print(f"VERIFY {position}/8 {blind_id} {workload_id}", file=sys.stderr, flush=True)

            def persist(attempt: dict[str, Any]) -> None:
                record["verification_attempts"].append(attempt)
                benchmark.write_json_atomic(results_path, results)

            verdict, _ = benchmark.run_verification(
                repo=prepared["repo"], binary=binary, workload=workload,
                response=record["attempt"]["response"], commit=prepared["state"]["commit"],
                minimum_score=int(prepared["config"]["minimum_quality_score"]),
                verifier_pair=prepared["verifier_pair"], parent_pair=prepared["pair"],
                run_id=blind_id, timeout=args.timeout, log_file=verifier_log,
                schema=schema_path, evidence=prepared["evidence"][workload_id],
                phase="initial", on_attempt=persist,
            )
        if not verdict.get("valid"):
            usage_attempt = next((item for item in reversed(record["verification_attempts"]) if item.get("failure_kind") == "usage_limit"), None)
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
    report_path.write_text(render(results), encoding="utf-8", newline="\n")
    print(json.dumps(results["analysis"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except benchmark.UsageLimitReached as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(75)
