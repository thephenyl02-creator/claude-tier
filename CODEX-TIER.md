# Codex Tier v1

Codex Tier is a local, explicit, quality-constrained compute router for Codex.
It is designed to reduce Codex usage without lowering the required quality.

The permanent rule is:

> Quality first. Among all model × reasoning-effort combinations expected to
> meet the required quality, choose the cheapest one with a confidence margin.
> Verify, and escalate only when needed.

Claude Tier remains a separate product. Codex Tier does not modify Claude's
plugin metadata, skill, installers, or routing rules.

## Install

macOS, Linux, or WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/install-codex.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/install-codex.ps1 | iex
```

The installers:

- detect a callable Codex CLI or the Windows Codex app;
- validate the pinned `codex exec` flags when a CLI is callable;
- prefer the repo's Codex plugin marketplace;
- fall back to an idempotent standalone copy under
  `~/.agents/skills/codex-tier`;
- preserve unrelated configuration and hand-authored skill copies;
- validate the deterministic routing configuration;
- never modify global Git settings or Claude Tier.

If Codex is missing, install the official CLI first:

```bash
npm install --global @openai/codex
```

For local plugin development:

```text
codex plugin marketplace add <repository-root>
codex plugin add codex-tier@codex-tier
```

Start a new task after installing or updating so Codex reloads the skill.

## Use

```text
$codex-tier

<normal task>
```

The skill is explicit-only in v1. Its `agents/openai.yaml` sets
`allow_implicit_invocation: false`.

## Routing

```text
quality requirement
  → workload class
  → reasoning × volume × risk × context
  → workload-specific calibrated frontier
  → cheapest reliable model × effort with margin
  → execute
  → verify
  → selective escalation when needed
```

Codex Tier has three execution modes:

- **TOOL** — deterministic commands such as search, build, tests, lint,
  type checking, schema validation, rendering, and exact transformations.
- **DIRECT** — the current parent for tiny work when worker startup would
  cost more, or when no available pinned worker safely clears the quality bar.
- **WORKER** — a bounded worker with an actually enforced model and reasoning
  effort.

Routing is deterministic and cheap. It does not benchmark multiple candidates
during a live task and does not use a fixed Luna → Terra → Sol escalation
ladder.

## Model registry and frontiers

The registry currently prefers:

- `gpt-5.6-luna`
- `gpt-5.6-terra`
- `gpt-5.6-sol`

Each declares `none`, `low`, `medium`, `high`, `xhigh`, and
`max` reasoning effort, subject to runtime availability.

Model IDs, supported efforts, compatibility, relative capability, and relative
usage priors live in
`plugins/codex-tier/skills/codex-tier/references/model-registry.json`.
Workload-specific candidates live in `frontiers.json`. Future model changes
update configuration and calibration rather than routing architecture.

Relative usage values are routing priors, not Codex subscription-credit
prices. Runtime usage fields are recorded when Codex exposes them.

## Worker enforcement

Current Codex documentation and the active native tool contract both support
explicit subagent model and reasoning-effort pins. Codex Tier therefore
prefers a native pinned worker when the current surface exposes both values.
Unpinned workers are forbidden because they inherit the parent.

When native pins are unavailable, the bundled executor uses the current
documented non-interactive syntax:

```text
codex exec
  --cd <repository-root>
  --model <selected-model>
  --config 'model_reasoning_effort="<selected-effort>"'
  --sandbox <read-only|workspace-write>
  --json
  --ephemeral
  --output-last-message <file>
  -
```

The worker receives a bounded packet with only objective, scope, relevant
paths, known facts, constraints, quality/risk, expected output, definition of
done, and verification.

Codex Tier never claims a selected pair ran unless the native spawn or actual
`codex exec` command enforced it.

## Verification and escalation

Deterministic verification comes first. Strong-model verification is reserved
for security, architecture, subtle concurrency, ambiguous correctness, or
creative judgment that tools cannot prove.

A passed unit is accepted without a stronger rerun. A failed or uncertain unit
is routed through the next stronger candidate in that work class's frontier.
Successful sibling units are not repeated.

## Usage logging

The default content-free JSONL log is:

```text
$CODEX_HOME/codex-tier/usage.jsonl
```

or `~/.codex/codex-tier/usage.jsonl` when `CODEX_HOME` is unset.

Where available, events record run ID, timestamp, work class, execution mode,
selected model and effort, parent model, token fields, Codex credits, worker
count, duration, verification, escalation, and success. Prompts, source files,
credentials, private form responses, and raw transcripts are never logged.

## Validate and test

```text
python plugins/codex-tier/skills/codex-tier/scripts/codex_tier.py validate
python -m unittest discover -s tests/codex-tier -p "test_*.py" -v
python plugins/codex-tier/skills/codex-tier/scripts/benchmark.py
```

The first command validates registry/frontier integrity. The tests cover mode
selection, multiple model/effort regions, unavailable candidates, selective
escalation, bounded worker pin enforcement, usage capture, worker failure, and
representative workload routing. The benchmark command is plan-only by
default.

## Benchmarking

The benchmark manifest covers:

1. high-volume, low-reasoning work;
2. mixed creative and execution work;
3. ordinary implementation;
4. difficult debugging;
5. high-risk review.

It compares only adjacent or economically competing candidates for each
workload. A live run requires a callable Codex CLI and a controlled fixture
repository:

```text
python plugins/codex-tier/skills/codex-tier/scripts/benchmark.py \
  --run \
  --repo <fixture-repository> \
  --results-file <results.json>
```

Raw quality, verification, tokens, credits, retries, escalations, and latency
are reported. Codex Tier does not publish a savings percentage until comparable
verified runs support one.

## Current environment findings

As verified on August 25, 2026:

- Official OpenAI model guidance lists GPT-5.6 Luna, Terra, and Sol with
  `none` through `max` reasoning effort.
- Current Codex documentation supports explicit subagent `model` and
  `model_reasoning_effort` pins.
- Current `codex exec` supports `--model`, repeated `--config`,
  `--json`, `--output-last-message`, and explicit sandbox selection.
- The Windows app package inspected during development was build
  `26.818.8289.0`. Its bundled `codex.exe` was not callable from the
  managed shell sandbox, so real native-worker execution is the primary app
  path and the independent CLI wrapper remains the fallback.
- Codex surfaces do not guarantee that every documented model is enabled for
  every workspace or account. Availability is confirmed at execution time.

Official references:

- [Codex developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [Build Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Build Codex plugins](https://learn.chatgpt.com/docs/build-plugins)
- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
