# tier — model & effort tiering for Claude Code

A tiny, opinionated Claude Code skill: run **`/tier`** in any project and it
installs a standing *model/effort-tiering* working preference into that
project's `CLAUDE.md`. From then on, that project runs **quality-first and
cost-efficient** — automatically, on desktop, web, and mobile.

Simple on purpose. It doesn't hook, poll, or call anything — it writes one
clear rule into the file Claude Code always reads, and gets out of the way.

## What the rule does

- **Plan on the highest model available**; every plan assigns a model tier
  **and** an effort level (low→max) per work item.
- **Routes work to the right tier:** deterministic batteries (tests, builds,
  linters) run with no model at all; mechanical gathering → Sonnet; substantive
  builds → Opus; delicate correctness / security reviews / research synthesis /
  final judgment → the top model.
- **Per-task fit:** *downgrade* to a cheaper model directly when the work is
  clearly mechanical; *upgrade* only after asking you first.
- **Hard rule that overrides everything: never compromise quality.** Any doubt
  whether a downgrade would hurt → don't downgrade.

## Install

```
/plugin marketplace add thephenyl02-creator/claude-tier
/plugin install tier@claude-tier
```

Then, in any project:

```
/tier
```

It adds the rule to that project's `CLAUDE.md` (creating it if needed), skips
if it's already there, and offers to commit it so web + mobile sessions pick it
up too.

## Why "simple is best"

Other routers auto-switch your model via hooks, or ship complex config
profiles. This one is deliberately minimal: one command, one durable rule, no
moving parts to break. You stay in control of the actual model; the rule just
keeps every session honest about tiering — and never trades quality for cost.

## License

MIT © Fenil K
