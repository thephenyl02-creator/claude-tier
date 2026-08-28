"""Independently validate the checked-in end-to-end benchmark artifact."""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "uncached_input_tokens",
    "total_exposed_tokens",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def schedule(suite: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        {
            "run_id": f"{workload['id']}--{condition}--r{repetition}",
            "workload_id": workload["id"],
            "condition": condition,
            "repetition": repetition,
        }
        for workload in suite["workloads"]
        for repetition in range(1, int(suite["repetitions_per_condition"]) + 1)
        for condition in ("baseline", "tiered")
    ]
    random.Random(int(suite["random_seed"])).shuffle(items)
    for position, item in enumerate(items, 1):
        item["randomized_position"] = position
    return items


def calculate(results: dict[str, Any], suite: dict[str, Any]) -> dict[str, Any]:
    records = results["records"]
    gate = suite["quality_gate"]
    calculations: dict[str, Any] = {}
    for workload in suite["workloads"]:
        rows = [item for item in records if item["workload_id"] == workload["id"]]
        per_condition = {
            condition: [item for item in rows if item["condition"] == condition]
            for condition in ("baseline", "tiered")
        }
        usage_medians = {
            condition: float(statistics.median(
                item["aggregate"]["usage"]["total_exposed_tokens"]
                for item in condition_rows
            ))
            for condition, condition_rows in per_condition.items()
        }
        quality_medians = {
            condition: float(statistics.median(item["quality"]["score"] for item in condition_rows))
            for condition, condition_rows in per_condition.items()
        }
        pass_rates = {
            condition: statistics.mean(bool(item["quality"]["passed"]) for item in condition_rows)
            for condition, condition_rows in per_condition.items()
        }
        raw = round(
            (1 - usage_medians["tiered"] / usage_medians["baseline"]) * 100,
            6,
        )
        relative = (
            quality_medians["tiered"]
            >= quality_medians["baseline"] - gate["maximum_median_regression_points"]
            and (
                not gate["require_tiered_pass_rate_at_least_baseline"]
                or pass_rates["tiered"] >= pass_rates["baseline"]
            )
        )
        absolute = pass_rates["tiered"] >= float(
            gate.get("minimum_tiered_pass_rate_for_publication", 1.0)
        )
        calculations[workload["id"]] = {
            "baseline_median_total_exposed_tokens": usage_medians["baseline"],
            "tiered_median_total_exposed_tokens": usage_medians["tiered"],
            "raw_median_usage_savings_percent": raw,
            "relative_quality_preserved": relative,
            "absolute_quality_met": absolute,
            "quality_preserving_savings_percent": raw if relative and absolute else None,
        }
    return calculations


def validate(results: dict[str, Any], suite: dict[str, Any]) -> dict[str, Any]:
    records = results["records"]
    expected_schedule = schedule(suite)
    actual_schedule = sorted(
        (
            {
                key: item[key]
                for key in ("run_id", "workload_id", "condition", "repetition", "randomized_position")
            }
            for item in records
        ),
        key=lambda item: item["randomized_position"],
    )
    calculated = calculate(results, suite)
    reported = results["analysis"]
    raw_values = [item["raw_median_usage_savings_percent"] for item in calculated.values()]
    expected_count = len(suite["workloads"]) * int(suite["repetitions_per_condition"]) * 2
    checks = {
        "record_count": len(records) == expected_count,
        "schedule_exact": actual_schedule == expected_schedule == results["schedule"],
        "states_complete": all(item.get("benchmark_state") == "complete" for item in records),
        "positions_complete": sorted(item["randomized_position"] for item in records)
        == list(range(1, expected_count + 1)),
        "five_repetitions_per_condition": all(
            len([
                item for item in records
                if item["workload_id"] == workload["id"] and item["condition"] == condition
            ])
            == int(suite["repetitions_per_condition"])
            for workload in suite["workloads"]
            for condition in ("baseline", "tiered")
        ),
        "prompts_and_packets_stable": all(
            len({item["task_prompt_sha256"] for item in records if item["workload_id"] == workload["id"]}) == 1
            and len({item["canonical_packet_sha256"] for item in records if item["workload_id"] == workload["id"]}) == 1
            for workload in suite["workloads"]
        ),
        "repository_state_equal": (
            results["repository_state"]["commit"] == results["repository_state_after"]["commit"]
            and results["repository_state"]["tree"] == results["repository_state_after"]["tree"]
            and results["repository_state"]["clean"] is True
            and results["repository_state_after"]["clean"] is True
        ),
        "final_verdicts_valid": all(item["quality"].get("valid") is True for item in records),
        "successful_task_usage_complete": all(
            all(isinstance(attempt["usage"].get(field), int) for field in USAGE_FIELDS)
            for item in records
            for attempt in item["attempts"]
            if attempt.get("success")
        ),
        "worker_choices_recorded": all(
            all(attempt.get("model") and attempt.get("effort") and attempt.get("pair") for attempt in item["attempts"])
            for item in records
        ),
        "formula_matches_report": all(
            calculated[workload_id][field] == reported["workloads"][workload_id][field]
            for workload_id in calculated
            for field in (
                "raw_median_usage_savings_percent",
                "relative_quality_preserved",
                "absolute_quality_met",
                "quality_preserving_savings_percent",
            )
        ),
        "overall_raw_aggregates_match": (
            round(statistics.median(raw_values), 6)
            == reported["overall"]["raw_workload_median_savings_percent"]
            and round(statistics.mean(raw_values), 6)
            == reported["overall"]["raw_workload_mean_savings_percent"]
        ),
        "no_credit_claim": (
            results["credits_exposed"] is False
            and results["credit_savings_published"] is False
            and reported["overall"]["credit_savings_published"] is False
        ),
    }
    best = max(calculated.items(), key=lambda item: item[1]["raw_median_usage_savings_percent"])
    worst = min(calculated.items(), key=lambda item: item[1]["raw_median_usage_savings_percent"])
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "independent_calculation": calculated,
        "raw_workload_median_savings_percent": round(statistics.median(raw_values), 6),
        "raw_workload_mean_savings_percent": round(statistics.mean(raw_values), 6),
        "best_raw_case": {"workload_id": best[0], "savings_percent": best[1]["raw_median_usage_savings_percent"]},
        "worst_raw_case": {"workload_id": worst[0], "savings_percent": worst[1]["raw_median_usage_savings_percent"]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default=str(ROOT / "benchmark-results.json"))
    parser.add_argument("--suite", default=str(ROOT / "suite.json"))
    args = parser.parse_args()
    summary = validate(load(Path(args.results)), load(Path(args.suite)))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
