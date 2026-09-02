#!/usr/bin/env python3
"""Merge the two corrected fixtures with the three valid final workloads.

This does not execute Codex.  It verifies source provenance and hashes, retains
each source batch's randomized position, and recomputes the five-workload
analysis from the selected records.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import e2e_benchmark as benchmark


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FINAL_SUITE_PATH = HERE / "final-suite.json"
FINAL_RESULTS_PATH = HERE / "final-results.json"
CORRECTION_SUITE_PATH = HERE / "fixture-correction-suite.json"
CORRECTION_RESULTS_PATH = HERE / "fixture-correction-results.json"
OUTPUT_SUITE_PATH = HERE / "corrected-final-suite.json"
OUTPUT_RESULTS_PATH = HERE / "corrected-final-results.json"
OUTPUT_REPORT_PATH = HERE / "corrected-final-report.md"

PRESERVED_IDS = {
    "real-router-refactor-plan",
    "real-security-trust-review",
    "real-distribution-architecture",
}
CORRECTED_IDS = {
    "real-bulk-release-audit",
    "real-probe-scope-debugging",
}
EXPECTED_ROUTES = {
    "real-bulk-release-audit": "gpt-5.6-sol/low",
    "real-router-refactor-plan": "gpt-5.6-terra/low",
    "real-probe-scope-debugging": "gpt-5.6-terra/xhigh",
    "real-security-trust-review": "gpt-5.6-sol/low",
    "real-distribution-architecture": "gpt-5.6-sol/low",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise benchmark.BenchmarkError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def workload_map(suite: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in suite["workloads"]}


def records_for(results: dict[str, Any], workload_id: str) -> list[dict[str, Any]]:
    return [item for item in results["records"] if item["workload_id"] == workload_id]


def verify_common_provenance(final: dict[str, Any], correction: dict[str, Any]) -> None:
    require(final["run_status"] == correction["run_status"] == "complete", "Source run is incomplete")
    for field in (
        "repository_state",
        "parent_pair",
        "verifier_pair",
        "verifier_protocol_version",
        "usage_metric",
        "primary_sandbox",
        "verifier_sandbox",
        "verifier_approval_policy",
    ):
        require(final[field] == correction[field], f"Source provenance differs for {field}")
    require(final.get("credits_exposed") is False, "Original final run unexpectedly exposes credits")
    require(correction.get("credits_exposed") is False, "Correction run unexpectedly exposes credits")


def verify_selected_workload(
    source: dict[str, Any], workload: dict[str, Any], repo: Path, commit: str,
) -> dict[str, Any]:
    rows = records_for(source, workload["id"])
    require(len(rows) == 6, f"Expected six source records for {workload['id']}")
    require(
        {(item["condition"], item["repetition"]) for item in rows}
        == {(condition, repetition) for condition in ("baseline", "tiered") for repetition in (1, 2, 3)},
        f"Condition/repetition coverage is invalid for {workload['id']}",
    )
    frozen, metadata = benchmark.freeze_workload_evidence(
        repo, {workload["id"]: workload}, commit
    )
    evidence = frozen[workload["id"]]
    evidence_sha = benchmark.sha256_text(evidence)
    task_sha = benchmark.sha256_text(workload["task"])
    packet_sha = benchmark.sha256_text(
        benchmark.canonical_packet(workload, commit, evidence)
    )
    require(
        source["frozen_evidence"][workload["id"]]["packet_sha256"] == evidence_sha,
        f"Frozen evidence changed for {workload['id']}",
    )
    require(
        {item["frozen_evidence_sha256"] for item in rows} == {evidence_sha},
        f"Record evidence hash drift for {workload['id']}",
    )
    require(
        {item["task_prompt_sha256"] for item in rows} == {task_sha},
        f"Task hash drift for {workload['id']}",
    )
    require(
        {item["canonical_packet_sha256"] for item in rows} == {packet_sha},
        f"Canonical packet hash drift for {workload['id']}",
    )
    require(
        all(item["benchmark_state"] == "complete" for item in rows),
        f"Incomplete selected record for {workload['id']}",
    )
    require(
        all(item["quality"].get("valid") is True for item in rows),
        f"Invalid verifier record for {workload['id']}",
    )
    actual_tier_pairs = {
        choice["pair"]
        for item in rows if item["condition"] == "tiered"
        for choice in item["aggregate"]["worker_choices"]
    }
    require(
        actual_tier_pairs == {EXPECTED_ROUTES[workload["id"]]},
        f"Frozen route mismatch for {workload['id']}: {sorted(actual_tier_pairs)}",
    )
    return {
        "task_sha256": task_sha,
        "canonical_packet_sha256": packet_sha,
        "frozen_evidence_sha256": evidence_sha,
        "fixture_validation": metadata[workload["id"]].get("fixture_validation"),
    }


def signed_change(savings_percent: float) -> float:
    return -float(savings_percent)


def render_corrected_report(
    results: dict[str, Any], suite: dict[str, Any], selected_hashes: dict[str, Any],
) -> str:
    analysis = results["analysis"]
    overall = analysis["overall"]
    lines = [
        "# Corrected final Codex Tier benchmark",
        "",
        "This composite preserves 18 valid primary records from the original final batch and replaces only the 12 invalid bulk/debugging records with the fixture-correction batch.",
        "",
        "## Validity and provenance",
        "",
        f"- Repository commit: `{results['repository_state']['commit']}`; tree: `{results['repository_state']['tree']}`.",
        f"- Parent/baseline: `{results['parent_pair']}`; blinded verifier: `{results['verifier_pair']}`.",
        "- Original valid source batch: seed `20260831`, 18 selected records (routine refactor, security review, architecture).",
        "- Corrected source batch: seed `20260902`, 12 selected records (bulk scan, difficult debugging).",
        "- Each workload has one task hash, one canonical-packet hash, and one frozen-evidence hash shared by baseline and Tier.",
        "- Bulk mechanically includes all 50 tracked files. Debugging mechanically includes the full merge implementation and named call-flow dependencies.",
        "- Codex credits and 5-hour quota consumption are not exposed; no such savings claim is made.",
        "",
        "## Corrected five-workload result",
        "",
        "| Workload | Frozen Tier route | Baseline median tokens | Tier median tokens | Token change | Baseline quality/pass | Tier quality/pass | Preserved | Median latency B/T (s) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | :---: | ---: |",
    ]
    for workload in suite["workloads"]:
        item = analysis["workloads"][workload["id"]]
        baseline = item["conditions"]["baseline"]
        tiered = item["conditions"]["tiered"]
        change = signed_change(item["raw_median_usage_savings_percent"])
        lines.append(
            f"| {workload['work_class']} | `{EXPECTED_ROUTES[workload['id']]}` | "
            f"{baseline['median_total_exposed_tokens']:,.0f} | {tiered['median_total_exposed_tokens']:,.0f} | "
            f"{change:+.3f}% | {baseline['median_quality_score']:.1f}/{baseline['quality_pass_rate']:.0%} | "
            f"{tiered['median_quality_score']:.1f}/{tiered['quality_pass_rate']:.0%} | "
            f"{'yes' if item['quality_preserved'] else 'no'} | "
            f"{baseline['median_execution_latency_seconds']:.1f}/{tiered['median_execution_latency_seconds']:.1f} |"
        )
    lines.extend([
        "",
        "Token change is `Tier / baseline - 1`; negative means an exposed-token reduction.",
        "",
        "## Twelve correction runs",
        "",
        "| Position | Workload | Condition | Worker | Tokens | Quality | Pass | Latency (s) | Retries | Escalations | Infra failures |",
        "| ---: | --- | --- | --- | ---: | ---: | :---: | ---: | ---: | ---: | ---: |",
    ])
    corrected_rows = [
        item for item in results["records"]
        if item["source_batch_id"] == "fixture-correction"
    ]
    for item in sorted(corrected_rows, key=lambda row: row["source_randomized_position"]):
        usage = item["aggregate"]["usage"]["total_exposed_tokens"]
        pair = item["aggregate"]["worker_choices"][-1]["pair"]
        retries = item["external_retry_count"] + item["aggregate"]["internal_retries"]
        lines.append(
            f"| {item['source_randomized_position']} | {item['work_class']} | {item['condition']} | "
            f"`{pair}` | {usage:,} | {item['quality']['score']} | "
            f"{'yes' if item['quality']['passed'] else 'no'} | "
            f"{item['aggregate']['execution_latency_seconds']:.1f} | {retries} | "
            f"{item['escalation_count']} | {len(item.get('infrastructure_attempts', []))} |"
        )
    lines.extend([
        "",
        "## Overall",
        "",
        f"- Quality preserved: {overall['quality_preserved_workloads']}/{overall['total_workloads']} workload classes; baseline/Tier pass rates {overall['baseline_pass_rate']:.0%}/{overall['tiered_pass_rate']:.0%}.",
        f"- Workload-median exposed-token usage reduction: {overall['raw_workload_median_savings_percent']:+.3f}% (negative means an increase).",
        f"- Workload-mean exposed-token usage reduction: {overall['raw_workload_mean_savings_percent']:+.3f}%.",
        f"- Pooled median exposed-token change: {signed_change(overall['pooled_raw_median_usage_savings_percent']):+.3f}%.",
        f"- Task execution retries/escalations/infrastructure failures: baseline {overall['task_execution']['baseline']['external_retries']}/{overall['task_execution']['baseline']['escalations']}/{overall['task_execution']['baseline']['infrastructure_failure_attempts']}; Tier {overall['task_execution']['tiered']['external_retries']}/{overall['task_execution']['tiered']['escalations']}/{overall['task_execution']['tiered']['infrastructure_failure_attempts']}.",
        "- All fixture-correction primaries and verifier judgments completed on their first attempt.",
        "",
        "## Hash proof",
        "",
    ])
    for workload in suite["workloads"]:
        hashes = selected_hashes[workload["id"]]
        lines.append(
            f"- `{workload['id']}`: task `{hashes['task_sha256']}`, packet `{hashes['canonical_packet_sha256']}`, evidence `{hashes['frozen_evidence_sha256']}`."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    final_suite = load(FINAL_SUITE_PATH)
    final = load(FINAL_RESULTS_PATH)
    correction_suite = load(CORRECTION_SUITE_PATH)
    correction = load(CORRECTION_RESULTS_PATH)
    verify_common_provenance(final, correction)
    require(final_suite["quality_gate"] == correction_suite["quality_gate"], "Quality gates differ")
    require(final_suite["parent"] == correction_suite["parent"], "Suite parent differs")
    require(final_suite["verifier"] == correction_suite["verifier"], "Suite verifier differs")

    original_workloads = workload_map(final_suite)
    repaired_workloads = workload_map(correction_suite)
    require(PRESERVED_IDS <= original_workloads.keys(), "Original valid workloads are missing")
    require(CORRECTED_IDS == repaired_workloads.keys(), "Correction suite workload scope changed")

    combined_suite = copy.deepcopy(final_suite)
    combined_suite["benchmark_id"] = "codex-tier-v1-corrected-final"
    combined_suite["report_title"] = "Corrected final Codex Tier benchmark"
    combined_suite["repository_description"] = (
        "Composite final result: three unchanged valid workloads plus the two repaired fixture reruns."
    )
    combined_suite["workloads"] = [
        copy.deepcopy(repaired_workloads[item["id"]])
        if item["id"] in CORRECTED_IDS else copy.deepcopy(item)
        for item in final_suite["workloads"]
    ]
    combined_suite["composite_source_batches"] = [
        {
            "id": "original-final",
            "suite": FINAL_SUITE_PATH.name,
            "random_seed": final_suite["random_seed"],
            "selected_workloads": sorted(PRESERVED_IDS),
            "selected_primary_runs": 18,
        },
        {
            "id": "fixture-correction",
            "suite": CORRECTION_SUITE_PATH.name,
            "random_seed": correction_suite["random_seed"],
            "selected_workloads": sorted(CORRECTED_IDS),
            "selected_primary_runs": 12,
        },
    ]

    repo = Path(final["repository_state"]["path"])
    commit = final["repository_state"]["commit"]
    selected_hashes: dict[str, Any] = {}
    records: list[dict[str, Any]] = []
    for workload in combined_suite["workloads"]:
        source = correction if workload["id"] in CORRECTED_IDS else final
        source_id = "fixture-correction" if workload["id"] in CORRECTED_IDS else "original-final"
        selected_hashes[workload["id"]] = verify_selected_workload(
            source, workload, repo, commit
        )
        for row in records_for(source, workload["id"]):
            selected = copy.deepcopy(row)
            selected["source_batch_id"] = source_id
            selected["source_randomized_position"] = selected["randomized_position"]
            records.append(selected)

    require(len(records) == 30, "Corrected final selection must contain 30 primary records")
    analysis_input = copy.deepcopy(records)
    for position, row in enumerate(analysis_input, start=1):
        row["randomized_position"] = position
    analysis_results = {"records": analysis_input}
    analysis = benchmark.analyze(analysis_results, combined_suite)

    selected_evidence = {}
    selected_verifier_evidence = {}
    selected_routing = {}
    for workload in combined_suite["workloads"]:
        source = correction if workload["id"] in CORRECTED_IDS else final
        workload_id = workload["id"]
        selected_evidence[workload_id] = copy.deepcopy(source["frozen_evidence"][workload_id])
        selected_verifier_evidence[workload_id] = copy.deepcopy(source["verifier_evidence"][workload_id])
        selected_routing[workload_id] = copy.deepcopy(source["routing"][workload_id])

    schedule = [
        {
            "source_batch_id": item["source_batch_id"],
            "randomized_position": item["source_randomized_position"],
            "run_id": item["run_id"],
            "workload_id": item["workload_id"],
            "condition": item["condition"],
            "repetition": item["repetition"],
        }
        for item in records
    ]
    combined = {
        "schema_version": 1,
        "benchmark_id": combined_suite["benchmark_id"],
        "run_status": "complete",
        "started_at": final["started_at"],
        "completed_at": correction["completed_at"],
        "codex_cli_version": correction["codex_cli_version"],
        "mode": "composite-final-after-fixture-correction",
        "parent_pair": final["parent_pair"],
        "verifier_pair": final["verifier_pair"],
        "primary_runs": 30,
        "new_primary_runs": 12,
        "reused_primary_runs": 18,
        "independent_verifications": 30,
        "repository_state": copy.deepcopy(final["repository_state"]),
        "repository_state_after": copy.deepcopy(correction["repository_state_after"]),
        "usage_metric": final["usage_metric"],
        "credits_exposed": False,
        "credit_savings_published": False,
        "verifier_protocol_version": final["verifier_protocol_version"],
        "verification_policy": final["verification_policy"],
        "primary_sandbox": final["primary_sandbox"],
        "verifier_sandbox": final["verifier_sandbox"],
        "verifier_approval_policy": final["verifier_approval_policy"],
        "verifier_usage_included_in_savings": False,
        "composite_randomization": (
            "Randomized positions retain their scope within each authenticated source batch; "
            "no synthetic cross-batch order is asserted."
        ),
        "source_batches": [
            {
                "id": "original-final",
                "results_file": FINAL_RESULTS_PATH.name,
                "results_sha256": benchmark.sha256_file(FINAL_RESULTS_PATH),
                "suite_file": FINAL_SUITE_PATH.name,
                "suite_sha256": benchmark.sha256_file(FINAL_SUITE_PATH),
                "random_seed": final_suite["random_seed"],
                "selected_workloads": sorted(PRESERVED_IDS),
                "selected_primary_runs": 18,
            },
            {
                "id": "fixture-correction",
                "results_file": CORRECTION_RESULTS_PATH.name,
                "results_sha256": benchmark.sha256_file(CORRECTION_RESULTS_PATH),
                "suite_file": CORRECTION_SUITE_PATH.name,
                "suite_sha256": benchmark.sha256_file(CORRECTION_SUITE_PATH),
                "random_seed": correction_suite["random_seed"],
                "selected_workloads": sorted(CORRECTED_IDS),
                "selected_primary_runs": 12,
            },
        ],
        "selected_hashes": selected_hashes,
        "schedule": schedule,
        "records": records,
        "frozen_evidence": selected_evidence,
        "verifier_evidence": selected_verifier_evidence,
        "routing": selected_routing,
        "analysis": analysis,
    }
    report = render_corrected_report(combined, combined_suite, selected_hashes)
    benchmark.write_json_atomic(OUTPUT_SUITE_PATH, combined_suite)
    benchmark.write_json_atomic(OUTPUT_RESULTS_PATH, combined)
    OUTPUT_REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps({
        "valid": True,
        "selected_primary_runs": len(records),
        "new_primary_runs": 12,
        "reused_primary_runs": 18,
        "quality_preserved_workloads": analysis["overall"]["quality_preserved_workloads"],
        "analysis": analysis,
        "output_results": str(OUTPUT_RESULTS_PATH),
        "output_report": str(OUTPUT_REPORT_PATH),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
