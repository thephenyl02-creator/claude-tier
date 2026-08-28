from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


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


if __name__ == "__main__":
    unittest.main()
