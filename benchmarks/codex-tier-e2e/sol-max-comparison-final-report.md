# Codex Tier v1 vs always-Sol/max — completed comparison

The four formerly ambiguous workloads now have three Sol/max observations each. Architecture retains its previously clear single Sol/max observation. Existing Tier results were not rerun.

| Workload | Max runs | Median Max tokens | Median Tier tokens | Tier reduction vs Max | Median quality Max/Tier | Pass Max/Tier | Median latency Max/Tier | Assessment |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| bulk_repository_scan | 3 | 163,721 | 155,369 | +5.10% | 96.0/94.0 | 100%/100% | 130.2s/36.1s | clear |
| routine_refactor | 3 | 25,532 | 22,020 | +13.76% | 89.0/89.0 | 100%/100% | 81.7s/32.0s | clear |
| difficult_debugging | 3 | 63,883 | 62,424 | +2.28% | 94.0/93.0 | 100%/100% | 165.1s/138.4s | ambiguous |
| security_review | 3 | 42,378 | 28,861 | +31.90% | 91.0/85.0 | 100%/100% | 207.3s/36.6s | ambiguous |
| architecture | 1 | 50,746 | 45,756 | +9.83% | 96.0/93.0 | 100%/100% | 141.9s/33.0s | clear |

- Median exposed-token reduction vs always-Sol/max: **+9.83%**.
- Mean exposed-token reduction vs always-Sol/max: **+12.57%**.
- Best case: `real-security-trust-review` at +31.90%.
- Worst case: `real-probe-scope-debugging` at +2.28%.
- Positive reductions: 5/5; quality thresholds passed: 5/5.
- Defensible exposed-token reduction vs always-Sol/max: yes.
- Defensible quality-equivalent reduction claim: no.
- Architecture remains based on one Max observation because it was already clear and was explicitly excluded from further runs.
- Codex credits, billing, dollars, and 5-hour quota consumption were not exposed and are not claimed.
