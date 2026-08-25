# Model registry maintenance

Read this reference only for availability, compatibility, or calibration
maintenance.

`model-registry.json` is the compatibility layer. It records model IDs,
supported efforts, relative capability, relative usage cost, availability
status, and supported executors. Routing code must not encode Luna, Terra, or
Sol names directly.

`frontiers.json` contains workload-specific candidates. Each candidate has:

- model and effort;
- conservative quality score for that work class;
- relative usage prior.

The relative usage values are comparison weights, not subscription credits or
API invoices. Actual Codex usage and token fields win whenever exposed.

## Runtime availability

Treat documentation and registry entries as candidates, not account
entitlements. Prefer this order:

1. native surface reports available models or accepts an explicit pin;
2. callable Codex CLI accepts the model and effort;
3. registry entry remains `probe-at-runtime`.

Do not probe every pair in normal use. If a selected pair is rejected, exclude
that pair and choose the next viable candidate for the same work class.

Current preferred registry entries are:

- gpt-5.6-luna
- gpt-5.6-terra
- gpt-5.6-sol

Each currently declares none, low, medium, high, xhigh, and max. Older models
belong in the registry only as compatibility fallbacks or measured
alternatives.

## Updating

When models change:

1. verify current official model and Codex documentation;
2. update model IDs, efforts, and compatibility in the registry;
3. benchmark only nearby competing points for affected work classes;
4. update those class frontiers;
5. validate with `scripts/codex_tier.py validate`;
6. keep the routing architecture unchanged.

Never infer fixed cross-model equivalence such as Luna/high = Terra/low.
