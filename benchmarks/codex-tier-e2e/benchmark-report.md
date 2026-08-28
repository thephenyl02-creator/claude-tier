# Normal Codex vs Codex Tier — controlled end-to-end benchmark

Measured 2026-08-28T10:43:01.308574Z with `codex-cli 0.149.1` against real repository commit `75c2c69`.

## Method

- Five realistic read-only repository workloads, 5 repetitions per condition (50 primary task runs).
- Same canonical prompt, repository path/tree, and parent pair `gpt-5.6-sol/low` for both conditions.
- Randomized primary order with seed `20260825`.
- Blinded independent verification by `gpt-5.6-sol/max`; verifier usage is excluded from task savings.
- Quality preservation requires a tiered pass rate of 100%, tiered pass rate no worse than baseline, and median score within 3 points.
- Usage metric is input tokens + output tokens. Cached, uncached, reasoning, latency, retries, escalations, and worker choices remain separately recorded.
- Codex credits were not exposed; no credit-savings claim is made.

## Results

| Workload | Baseline median tokens | Tiered median tokens | Baseline quality | Tiered quality | Quality preserved | Raw usage difference | Publishable savings |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| bulk_repository_scan | 1,276,488 | 652,475 | 9.0 (0%) | 10.0 (0%) | no | 48.89% | not published |
| routine_refactor | 788,522 | 2,962,969 | 46.0 (0%) | 1.0 (0%) | no | -275.76% | not published |
| difficult_debugging | 761,374 | 507,544 | 29.0 (0%) | 30.0 (0%) | no | 33.34% | not published |
| security_review | 1,279,044 | 837,729 | 21.0 (0%) | 39.0 (0%) | no | 34.50% | not published |
| architecture | 1,039,478 | 2,323,144 | 56.0 (0%) | 64.0 (0%) | no | -123.49% | not published |

## Summary

- Quality-preserved workloads: 0/5.
- Overall median quality-preserving savings: not publishable.
- Overall mean quality-preserving savings: not publishable.
- Diagnostic raw workload savings: median 33.34%, mean -56.51% (not a quality-preserving claim).
- Pooled median usage: baseline 1,007,035, tiered 837,729 tokens (16.81% raw difference).
- Quality: baseline median 30.0, tiered median 24.0; pass rates 0% vs 0%.
- Best/worst raw cases: `real-bulk-release-audit` at 48.89% and `real-router-refactor-plan` at -275.76% (diagnostic only).

## Execution and validity

- Baseline: 25 runs, 50 successful task attempts, 25 quality retries, 0 escalations, and 1 separately recorded policy/infrastructure failure attempt.
- Tiered: 25 runs, 46 successful task attempts, 0 same-pair retries, 25 requested escalations, and 9 separately recorded policy/infrastructure failure attempts.
- Independent verifier: 96 attempts (94 successful); all 50 final verdicts were valid. Its usage is excluded from savings.
- The managed Windows shell blocked some worker repository-inspection commands. Those real reliability failures materially depressed quality and are preserved in the JSON; they are not normalized away.
- All successful task attempts exposed input, cached input, cache-write input, output, reasoning-output, uncached-input, and total-token fields. Codex credits were not exposed.

All individual outputs, blinded verdicts, usage fields, latency, retries, escalations, randomized positions, and worker choices are preserved in `benchmark-results.json`.
