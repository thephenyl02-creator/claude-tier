# Corrected final Codex Tier benchmark

This composite preserves 18 valid primary records from the original final batch and replaces only the 12 invalid bulk/debugging records with the fixture-correction batch.

## Validity and provenance

- Repository commit: `75c2c6926bb317803e66946f72194788cac16ebe`; tree: `dd890aa87fa6d8aab33f868f2ec54acf3f3fb382`.
- Parent/baseline: `gpt-5.6-sol/low`; blinded verifier: `gpt-5.6-sol/max`.
- Original valid source batch: seed `20260831`, 18 selected records (routine refactor, security review, architecture).
- Corrected source batch: seed `20260902`, 12 selected records (bulk scan, difficult debugging).
- Each workload has one task hash, one canonical-packet hash, and one frozen-evidence hash shared by baseline and Tier.
- Bulk mechanically includes all 50 tracked files. Debugging mechanically includes the full merge implementation and named call-flow dependencies.
- Codex credits and 5-hour quota consumption are not exposed; no such savings claim is made.

## Corrected five-workload result

| Workload | Frozen Tier route | Baseline median tokens | Tier median tokens | Token change | Baseline quality/pass | Tier quality/pass | Preserved | Median latency B/T (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | :---: | ---: |
| bulk_repository_scan | `gpt-5.6-sol/low` | 155,373 | 155,369 | -0.003% | 96.0/100% | 94.0/100% | yes | 36.9/36.1 |
| routine_refactor | `gpt-5.6-terra/low` | 22,004 | 22,020 | +0.073% | 88.0/100% | 89.0/100% | yes | 31.8/32.0 |
| difficult_debugging | `gpt-5.6-terra/xhigh` | 53,112 | 62,424 | +17.533% | 94.0/100% | 93.0/100% | yes | 31.7/138.4 |
| security_review | `gpt-5.6-sol/low` | 28,773 | 28,861 | +0.306% | 84.0/100% | 85.0/100% | yes | 36.7/36.6 |
| architecture | `gpt-5.6-sol/low` | 45,814 | 45,756 | -0.127% | 94.0/100% | 93.0/100% | yes | 32.9/33.0 |

Token change is `Tier / baseline - 1`; negative means an exposed-token reduction.

## Twelve correction runs

| Position | Workload | Condition | Worker | Tokens | Quality | Pass | Latency (s) | Retries | Escalations | Infra failures |
| ---: | --- | --- | --- | ---: | ---: | :---: | ---: | ---: | ---: | ---: |
| 1 | bulk_repository_scan | tiered | `gpt-5.6-sol/low` | 160,131 | 94 | yes | 45.6 | 0 | 0 | 0 |
| 2 | difficult_debugging | tiered | `gpt-5.6-terra/xhigh` | 58,674 | 93 | yes | 139.7 | 0 | 0 | 0 |
| 3 | difficult_debugging | baseline | `gpt-5.6-sol/low` | 53,028 | 89 | yes | 29.5 | 0 | 0 | 0 |
| 4 | difficult_debugging | baseline | `gpt-5.6-sol/low` | 53,112 | 94 | yes | 31.7 | 0 | 0 | 0 |
| 5 | bulk_repository_scan | baseline | `gpt-5.6-sol/low` | 155,316 | 97 | yes | 34.5 | 0 | 0 | 0 |
| 6 | difficult_debugging | tiered | `gpt-5.6-terra/xhigh` | 63,045 | 88 | yes | 138.4 | 0 | 0 | 0 |
| 7 | difficult_debugging | baseline | `gpt-5.6-sol/low` | 53,169 | 94 | yes | 33.5 | 0 | 0 | 0 |
| 8 | bulk_repository_scan | tiered | `gpt-5.6-sol/low` | 155,312 | 95 | yes | 35.1 | 0 | 0 | 0 |
| 9 | bulk_repository_scan | baseline | `gpt-5.6-sol/low` | 155,373 | 95 | yes | 36.9 | 0 | 0 | 0 |
| 10 | bulk_repository_scan | tiered | `gpt-5.6-sol/low` | 155,369 | 94 | yes | 36.1 | 0 | 0 | 0 |
| 11 | difficult_debugging | tiered | `gpt-5.6-terra/xhigh` | 62,424 | 94 | yes | 115.4 | 0 | 0 | 0 |
| 12 | bulk_repository_scan | baseline | `gpt-5.6-sol/low` | 155,432 | 96 | yes | 39.5 | 0 | 0 | 0 |

## Overall

- Quality preserved: 5/5 workload classes; baseline/Tier pass rates 100%/100%.
- Workload-median exposed-token usage reduction: -0.073% (negative means an increase).
- Workload-mean exposed-token usage reduction: -3.556%.
- Pooled median exposed-token change: +8.366%.
- Task execution retries/escalations/infrastructure failures: baseline 0/0/0; Tier 0/1/0.
- All fixture-correction primaries and verifier judgments completed on their first attempt.

## Hash proof

- `real-bulk-release-audit`: task `f6051c13d80aaf038c8a3642a8fe919f293a81375ea0790184bb184456f84bcb`, packet `bdfeed061995066ea55c47c3b89fa8e8c081b06efbaae8dfc466f6ae710f3c42`, evidence `0c9202f0009664a4dba0cf261fcc56ad6c93161c321132706cb7da4f1450532b`.
- `real-router-refactor-plan`: task `a191901633f37acc6d40fef4b865b3e9b7985bf189b0e014976504a6cfbf7ee7`, packet `079c6be3b6125c8fd52d3e3e0b98fe0fef089ea636b7b7b6523ddd139d539745`, evidence `292e453d80a69a8f965b517a8c02f4c09d28ff291d1253ddc447be547b65138e`.
- `real-probe-scope-debugging`: task `306b1a65954c41abc1f0dd61b1d01efa3ae2ef7c25424908c8a538c6c8075373`, packet `a7fd1507e9d9c042b3c8216278584af6d725b3d68ab1d33552d1fe0d86fbc3e3`, evidence `edf52fc6661381911aad36014aed547ab5b5cff7c63eeab3c8f2e5ba536dff42`.
- `real-security-trust-review`: task `a45a9d405e8943850f1d5c4f6f9739e705026a6734b3b270c3cc21da25497aec`, packet `591d5947266dbb9453817e5eb1384e5443f57bb3769a6bd1d2258d6bf6e43807`, evidence `d6637b4aae0915b803d412a5fdf7e144f813960c25db987a76fc7a0815bc6b51`.
- `real-distribution-architecture`: task `0d642676d8b2f5599e73a35de2dd77a5e8ea6bd6a4396742502ee2b2e4a4af4f`, packet `53392f37ba730b1a136a13b2868b37b4feeadca5fc99c4a3c73ee021653c0973`, evidence `1848996766b540b4e3612c86d3b6c2ee0f1cf77f10a6d136852da294472e7954`.
