# Model registry maintenance

Read this reference only for availability, compatibility, or calibration
maintenance.

`model-registry.json` is the maintained compatibility layer. At runtime,
`scripts/codex_tier.py` overlays the current Codex client's
`models_cache.json`; active candidates are the visible eligible coding models
times each model's own exposed efforts. Routing code must not encode a fixed
model ladder.

`frontiers.json` contains workload-specific candidates. Each candidate has:

- model and effort;
- conservative quality score for that work class;
- relative usage prior.

The relative usage values are comparison weights, not subscription credits or
API invoices. Actual Codex usage and token fields win whenever exposed.

## Runtime availability

Treat documentation and registry entries as metadata, not account
entitlements. Prefer this order:

1. native surface reports available models or accepts an explicit pin;
2. a matching real launch-probe artifact shows the callable Codex CLI accepted
   the model and effort;
3. registry entry remains `probe-at-runtime`.

Do not probe every pair in normal use. A full sweep is appropriate only during
explicit calibration. If a selected pair is rejected later, exclude that pair
and choose the next viable candidate for the same work class.

The August 25, 2026 client catalog exposed:

- gpt-5.4-mini: low, medium, high, xhigh
- gpt-5.4: low, medium, high, xhigh
- gpt-5.5: low, medium, high, xhigh
- gpt-5.6-luna: low, medium, high, xhigh, max
- gpt-5.6-terra: low, medium, high, xhigh, max, ultra
- gpt-5.6-sol: low, medium, high, xhigh, max, ultra

`none` is excluded because the current Codex surface does not expose it.
`ultra` is client-specific and may delegate automatically; it is not recorded
as an API reasoning-effort value.

## Updating

When models change:

1. verify current official model and Codex documentation;
2. update model IDs, efforts, and compatibility in the registry;
3. launch probe every advertised pair during an authorized calibration;
4. run real identical fixtures and update affected class frontiers;
5. validate with `scripts/codex_tier.py validate`;
6. keep the routing architecture unchanged.

Never infer fixed cross-model equivalence such as Luna/high = Terra/low.
