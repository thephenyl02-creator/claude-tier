# Claude Tier + Codex Tier

Quality-first model and effort routing for Claude Code and OpenAI Codex.

Two small, independent routers that cut model spend without lowering quality.
They install separately, share no routing logic, and each ships its own guide,
changelog, and installers.

| | Claude Tier | Codex Tier |
| --- | --- | --- |
| Runs in | Claude Code | Codex |
| What it does | Installs one durable model/effort-tiering rule into a project | Routes each work unit to a tool, the current session, or a pinned model x reasoning-effort worker, then verifies |
| Invoke | `/tier` | `$codex-tier` |
| Guide | [docs/claude-tier](docs/claude-tier/README.md) | [docs/codex-tier](docs/codex-tier/README.md) |
| Changelog | [CHANGELOG](docs/claude-tier/CHANGELOG.md) | [CHANGELOG](docs/codex-tier/CHANGELOG.md) |

Installable versions are on the [releases page](https://github.com/thephenyl02-creator/claude-codex-tier/releases).
Each product owns its own directories: Claude Tier in `skills/tier/` and
`docs/claude-tier/`; Codex Tier in `plugins/codex-tier/`, `docs/codex-tier/`,
`tests/codex-tier/`, and `benchmarks/codex-tier-e2e/`. The four `install*`
scripts at the root are the installers.

## Claude Tier

One command installs Claude Code if it is missing, adds the plugin, and falls
back to a plain skill copy when the plugin route is blocked. Safe to re-run.

macOS / Linux / WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/thephenyl02-creator/claude-codex-tier/main/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/thephenyl02-creator/claude-codex-tier/main/install.ps1 | iex
```

Already have Claude Code? Two commands:

```
claude plugin marketplace add thephenyl02-creator/claude-codex-tier
claude plugin install tier@claude-tier
```

Then, in any project, run `/tier`. The rule lands in a machine-local
`CLAUDE.local.md`, so your repo stays clean; `/tier repo` writes the committed
`CLAUDE.md` instead, which also covers web and mobile sessions.

The rule in one line: plan and judge on the session's model, execute through
pinned sub-agents, route work by its shape, treat model as the strong lever
and effort as the weak one, and never trade quality for cost. The
[guide](docs/claude-tier/README.md) has the full rule, every install path
(desktop app, cloud, git-free), troubleshooting, and the measurements behind
each number.

## Codex Tier

Needs Codex already installed (`npm install --global @openai/codex`). The
installer detects the CLI or the Windows app, prefers the plugin marketplace,
and falls back to a standalone skill copy. Safe to re-run.

macOS / Linux / WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/thephenyl02-creator/claude-codex-tier/main/install-codex.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/thephenyl02-creator/claude-codex-tier/main/install-codex.ps1 | iex
```

Already have Codex? Two commands:

```
codex plugin marketplace add thephenyl02-creator/claude-codex-tier
codex plugin add codex-tier@codex-tier
```

Then start a new Codex task and begin it with `$codex-tier`. You never pick a
model, effort, worker count, or escalation path: the router chooses the
cheapest calibrated model x reasoning-effort pair expected to meet the
quality bar, verifies the result, and escalates only the affected unit.

Measured on five workloads: a 9.83% median exposed-token reduction versus
always Sol/max at a 100% quality-gate pass rate (13.82% derived for the final
routes). Exposed tokens are not credits, billing, dollars, or quota. The
[guide](docs/codex-tier/README.md) covers architecture, worker enforcement,
configuration, logging, tests, and current limitations; the
[benchmark report](benchmarks/codex-tier-e2e/CONSOLIDATED-BENCHMARK-REPORT.md)
holds the evidence and its limits.

## Feedback

Notes, questions, and measured results go in
[Discussions](https://github.com/thephenyl02-creator/claude-codex-tier/discussions).
Something broken?
[Report a bug](https://github.com/thephenyl02-creator/claude-codex-tier/issues/new?template=bug_report.yml).

## Keywords

Claude Code plugin, Claude Code skill, Claude Code cost optimization, reduce
Claude Code cost, Claude Code model tiering, Opus vs Sonnet routing, model
selection for coding agents, reasoning effort router, sub-agent pinning,
CLAUDE.md working preferences, Codex plugin, Codex skill, Codex model routing,
reduce Codex usage, LLM model routing, AI coding agent cost, quality-first
routing, Opus, Sonnet, Haiku.

## License

MIT (c) Fenil K Ventures LLC
