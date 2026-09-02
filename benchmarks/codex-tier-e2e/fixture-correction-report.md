# Normal Codex vs Codex Tier — controlled end-to-end benchmark

Measured 2026-09-02T02:35:01.602151Z with `codex-cli 0.149.1` against real repository commit `75c2c69`.

## Method

- 2 realistic read-only repository workloads, 3 repetition(s) per condition (12 primary task runs).
- Same canonical prompt, repository path/tree, and parent pair `gpt-5.6-sol/low` for both conditions.
- Randomized primary order with seed `20260902`.
- Blinded independent verification by `gpt-5.6-sol/max`; verifier usage is excluded from task savings.
- Quality preservation requires a tiered pass rate of 100%, tiered pass rate no worse than baseline, and median score within 3 points.
- Usage metric is input tokens + output tokens. Cached, uncached, reasoning, latency, retries, escalations, and worker choices remain separately recorded.
- Codex credits were not exposed; no credit-savings claim is made.

## Results

| Workload | Baseline median tokens | Tiered median tokens | Baseline quality | Tiered quality | Quality preserved | Raw usage difference | Publishable savings |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| bulk_repository_scan | 155,373 | 155,369 | 96.0 (100%) | 94.0 (100%) | yes | 0.00% | 0.00% |
| difficult_debugging | 53,112 | 62,424 | 94.0 (100%) | 93.0 (100%) | yes | -17.53% | -17.53% |

## Summary

- Quality-preserved workloads: 2/2.
- Overall median quality-preserving savings: -8.77%.
- Overall mean quality-preserving savings: -8.77%.
- Diagnostic raw workload savings: median -8.77%, mean -8.77% (not a quality-preserving claim).
- Pooled median usage: baseline 104,242, tiered 109,178 tokens (-4.74% raw difference).
- Quality: baseline median 94.5, tiered median 94.0; pass rates 100% vs 100%.
- Best quality-preserving case: `real-bulk-release-audit` at 0.00%.
- Worst quality-preserving case: `real-probe-scope-debugging` at -17.53%.
- Best/worst raw cases: `real-bulk-release-audit` at 0.00% and `real-probe-scope-debugging` at -17.53% (diagnostic only).

## Execution and validity

- Baseline: 6 runs, 6 successful task attempts, 0 quality retries, 0 escalations, and 0 separately recorded policy/infrastructure failure attempt.
- Tiered: 6 runs, 6 successful task attempts, 0 same-pair retries, 0 requested escalations, and 0 separately recorded policy/infrastructure failure attempts.
- Independent verifier: 12 attempts (12 successful); all 12 final verdicts were valid. Its usage is excluded from savings.
- The managed Windows shell blocked some worker repository-inspection commands. Those real reliability failures materially depressed quality and are preserved in the JSON; they are not normalized away.
- All successful task attempts exposed input, cached input, cache-write input, output, reasoning-output, uncached-input, and total-token fields. Codex credits were not exposed.

All individual outputs, blinded verdicts, usage fields, latency, retries, escalations, randomized positions, and worker choices are preserved in `benchmark-results.json`.
