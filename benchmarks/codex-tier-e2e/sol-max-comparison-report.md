# Codex Tier v1 vs always-Sol/max — lightweight comparison

Five new direct `gpt-5.6-sol/max` runs were compared with the existing corrected-final Tier medians. Tier was not rerun.

| Workload | Sol/max tokens | Tier median tokens | Tier reduction vs Max | Quality Max/Tier | Latency Max/Tier | Assessment |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| bulk_repository_scan | 159,672 | 155,369 | +2.69% | 95/94.0 | 130.2s/36.1s | ambiguous |
| routine_refactor | 28,804 | 22,020 | +23.55% | 93/89.0 | 81.7s/32.0s | ambiguous |
| difficult_debugging | 63,883 | 62,424 | +2.28% | 95/93.0 | 169.5s/138.4s | ambiguous |
| security_review | 42,401 | 28,861 | +31.93% | 92/85.0 | 244.4s/36.6s | ambiguous |
| architecture | 50,746 | 45,756 | +9.83% | 96/93.0 | 141.9s/33.0s | clear |

- Median exposed-token reduction vs always-Sol/max: **+9.83%**.
- Mean exposed-token reduction vs always-Sol/max: **+14.06%**.
- Best case: `real-security-trust-review` at +31.93%.
- Worst case: `real-probe-scope-debugging` at +2.28%.
- Clear/ambiguous workloads: 1/4.
- More repetitions needed for clear workload claims: yes.
- More repetitions are required before treating the five-run aggregate as a publishable repeated-run estimate.
- Codex credits, billing, dollars, and 5-hour quota consumption were not exposed and are not claimed.

A comparison is marked clear only when quality is comparable, the single Sol/max observation lies outside all three existing Tier observations, and the absolute difference is at least 5%. Otherwise it is conservatively marked ambiguous.
