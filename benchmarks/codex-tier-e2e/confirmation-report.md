# Codex Tier — targeted route confirmation

Measured 2026-08-29T19:05:01.741457Z with `codex-cli 0.149.1` against real repository commit `75c2c69`.

## Method

- 3 realistic read-only repository workloads, 1 repetition(s) per condition (6 primary task runs).
- Same canonical prompt, repository path/tree, and parent pair `gpt-5.6-sol/low` for both conditions.
- Randomized primary order with seed `20260829`.
- Blinded independent verification by `gpt-5.6-sol/max`; verifier usage is excluded from task savings.
- Quality preservation requires a tiered pass rate of 100%, tiered pass rate no worse than baseline, and median score within 3 points.
- Usage metric is input tokens + output tokens. Cached, uncached, reasoning, latency, retries, escalations, and worker choices remain separately recorded.
- Codex credits were not exposed; no credit-savings claim is made.

## Results

| Workload | Baseline median tokens | Tiered median tokens | Baseline quality | Tiered quality | Quality preserved | Raw usage difference | Publishable savings |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| bulk_repository_scan | 157,901 | 55,038 | 92.0 (100%) | 84.0 (0%) | no | 65.14% | not published |
| difficult_debugging | 88,359 | 73,769 | 92.0 (100%) | 66.0 (0%) | no | 16.51% | not published |
| security_review | 85,557 | 30,107 | 89.0 (100%) | 45.0 (0%) | no | 64.81% | not published |

## Summary

- Quality-preserved workloads: 0/3.
- Overall median quality-preserving savings: not publishable.
- Overall mean quality-preserving savings: not publishable.
- Diagnostic raw workload savings: median 64.81%, mean 48.82% (not a quality-preserving claim).
- Pooled median usage: baseline 88,359, tiered 55,038 tokens (37.71% raw difference).
- Quality: baseline median 92.0, tiered median 66.0; pass rates 100% vs 0%.
- Best/worst raw cases: `real-bulk-release-audit` at 65.14% and `real-probe-scope-debugging` at 16.51% (diagnostic only).

## Execution and validity

- Baseline: 3 runs, 3 successful task attempts, 0 quality retries, 0 escalations, and 0 separately recorded policy/infrastructure failure attempt.
- Tiered: 3 runs, 3 successful task attempts, 0 same-pair retries, 0 requested escalations, and 0 separately recorded policy/infrastructure failure attempts.
- Independent verifier: 6 attempts (6 successful); all 6 final verdicts were valid. Its usage is excluded from savings.
- All successful task attempts exposed input, cached input, cache-write input, output, reasoning-output, uncached-input, and total-token fields. Codex credits were not exposed.

All individual outputs, blinded verdicts, usage fields, latency, retries, escalations, randomized positions, and worker choices are preserved in `confirmation-results.json`.
