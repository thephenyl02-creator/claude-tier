# Codex Tier targeted tuning

Fixed repository commit: `75c2c69`. Primary runs: 12.

This tuning batch is not the final benchmark and publishes no savings claim.

| Workload | Candidate | Median tokens | Median quality | Pass rate | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| routine_refactor | baseline `gpt-5.6-sol/low` | 70,412 | 88.0 | 100% | reference |
| routine_refactor | `gpt-5.4-mini/medium` | 40,810 | 77.0 | 0% | failed absolute quality gate |
| routine_refactor | `gpt-5.6-terra/low` | 59,964 | 87.0 | 100% | frontier |
| architecture | baseline `gpt-5.6-sol/low` | 94,208 | 92.5 | 100% | reference |
| architecture | `gpt-5.6-sol/medium` | 142,142 | 91.5 | 100% | frontier |
| architecture | `gpt-5.5/medium` | 69,845 | 82.5 | 50% | failed absolute quality gate |

Deterministic clear failures: 0. Strong-verifier attempts: 12.
