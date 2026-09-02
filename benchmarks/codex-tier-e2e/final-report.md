# Normal Codex vs Codex Tier — controlled end-to-end benchmark

Measured 2026-09-01T22:43:14.395799Z with `codex-cli 0.149.1` against real repository commit `75c2c69`.

## Method

- 5 realistic read-only repository workloads, 3 repetition(s) per condition (30 primary task runs).
- Same canonical prompt, repository path/tree, and parent pair `gpt-5.6-sol/low` for both conditions.
- Randomized primary order with seed `20260901`.
- Blinded independent verification by `gpt-5.6-sol/max`; verifier usage is excluded from task savings.
- Quality preservation requires a tiered pass rate of 100%, tiered pass rate no worse than baseline, and median score within 3 points.
- Usage metric is input tokens + output tokens. Cached, uncached, reasoning, latency, retries, escalations, and worker choices remain separately recorded.
- Codex credits were not exposed; no credit-savings claim is made.

## Results

| Workload | Baseline median tokens | Tiered median tokens | Baseline quality | Tiered quality | Quality preserved | Raw usage difference | Publishable savings |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| bulk_repository_scan | 52,857 | 109,777 | 94.0 (100%) | 94.0 (67%) | no | -107.69% | not published |
| routine_refactor | 22,004 | 22,020 | 88.0 (100%) | 89.0 (100%) | yes | -0.07% | -0.07% |
| difficult_debugging | 22,452 | 46,777 | 87.0 (100%) | 86.0 (67%) | no | -108.34% | not published |
| security_review | 28,773 | 28,861 | 84.0 (100%) | 85.0 (100%) | yes | -0.31% | -0.31% |
| architecture | 45,814 | 45,756 | 94.0 (100%) | 93.0 (100%) | yes | 0.13% | 0.13% |

## Summary

- Quality-preserved workloads: 3/5.
- Overall median quality-preserving savings: -0.07%.
- Overall mean quality-preserving savings: -0.08%.
- Diagnostic raw workload savings: median -0.31%, mean -43.26% (not a quality-preserving claim).
- Pooled median usage: baseline 28,993, tiered 45,756 tokens (-57.82% raw difference).
- Quality: baseline median 88.0, tiered median 89.0; pass rates 100% vs 87%.
- Best quality-preserving case: `real-distribution-architecture` at 0.13%.
- Worst quality-preserving case: `real-security-trust-review` at -0.31%.
- Best/worst raw cases: `real-distribution-architecture` at 0.13% and `real-probe-scope-debugging` at -108.34% (diagnostic only).

## Execution and validity

- Baseline: 15 runs, 17 successful task attempts, 2 quality retries, 0 escalations, and 0 separately recorded policy/infrastructure failure attempt.
- Tiered: 15 runs, 20 successful task attempts, 0 same-pair retries, 5 requested escalations, and 0 separately recorded policy/infrastructure failure attempts.
- Independent verifier: 37 attempts (37 successful); all 30 final verdicts were valid. Its usage is excluded from savings.
- The managed Windows shell blocked some worker repository-inspection commands. Those real reliability failures materially depressed quality and are preserved in the JSON; they are not normalized away.
- All successful task attempts exposed input, cached input, cache-write input, output, reasoning-output, uncached-input, and total-token fields. Codex credits were not exposed.

All individual outputs, blinded verdicts, usage fields, latency, retries, escalations, randomized positions, and worker choices are preserved in `benchmark-results.json`.
