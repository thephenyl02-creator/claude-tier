# Codex Tier targeted tuning

Fixed repository commit: `75c2c69`. Scheduled records: 18; new primary runs: 18; reused baselines: 0.

This tuning batch is not the final benchmark and publishes no savings claim.

| Workload | Candidate | Median tokens | Median quality | Pass rate | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| bulk_repository_scan | baseline `gpt-5.6-sol/low` | 54,778 | 94.5 | 100% | reference |
| bulk_repository_scan | `gpt-5.4-mini/high` | 56,276 | 79.0 | 50% | failed absolute quality gate |
| bulk_repository_scan | `gpt-5.6-terra/low` | 56,610 | 90.5 | 100% | failed relative quality gate |
| difficult_debugging | baseline `gpt-5.6-sol/low` | 22,380 | 83.5 | 50% | reference |
| difficult_debugging | `gpt-5.6-terra/xhigh` | 26,634 | 89.0 | 100% | frontier |
| difficult_debugging | `gpt-5.6-terra/max` | 30,733 | 89.0 | 100% | dominated by gpt-5.6-terra/xhigh |
| security_review | baseline `gpt-5.6-sol/low` | 32,610 | 0.0 | 0% | reference |
| security_review | `gpt-5.6-terra/max` | 43,519 | 0.0 | 0% | failed absolute quality gate |
| security_review | `gpt-5.6-sol/medium` | 31,144 | 0.0 | 0% | failed absolute quality gate |

Deterministic clear failures: 6. Strong-verifier attempts: 12.
