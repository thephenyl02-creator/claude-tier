# Codex Tier targeted tuning

Fixed repository commit: `75c2c69`. Scheduled records: 6; new primary runs: 6; reused baselines: 0.

This tuning batch is not the final benchmark and publishes no savings claim.

| Workload | Candidate | Median tokens | Median quality | Pass rate | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| security_review | baseline `gpt-5.6-sol/low` | 30,278 | 84.5 | 50% | reference |
| security_review | `gpt-5.6-terra/max` | 42,242 | 82.0 | 50% | failed absolute quality gate |
| security_review | `gpt-5.6-sol/medium` | 30,389 | 81.5 | 50% | failed absolute quality gate |

Deterministic clear failures: 0. Strong-verifier attempts: 7.
