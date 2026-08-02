# tier - model & effort tiering for Claude Code

A tiny, opinionated Claude Code skill: run **`/tier`** in any project and it
installs a standing *model/effort-tiering* working preference into that
project's `CLAUDE.md`. From then on, that project runs **quality-first and
cost-efficient** - automatically, on desktop, web, and mobile.

Simple on purpose. It doesn't hook, poll, or call anything - it writes one
clear rule into the file Claude Code always reads, and gets out of the way.

## What the rule does

- **Plan on the highest model available**; every plan assigns a model tier
  **and** an effort level (low to max) per work item.
- **Routes work to the right tier:** deterministic batteries (tests, builds,
  linters) run with no model at all; mechanical gathering to Sonnet;
  substantive builds, verifiers, correctness/security reviews, and final
  judgment to Opus - since Opus 5, Opus is the default top tier.
- **Fable is an escalation, not a default:** roughly 2x Opus cost and heavier
  token use for an overall lead that is now marginal (Opus 5 wins several
  areas outright). The rule reserves Fable for the longest, hardest
  frontier-reasoning work, high-stakes deep research, large or high-stakes
  work in the domains where Fable actually benchmarks ahead (long-horizon
  software engineering, legal/compliance-critical analysis, deep security
  analysis), tie-break adjudication after strong models disagree, or an
  explicit request.
- **Subscription-aware:** on plans without Fable (e.g. Claude Pro), Opus is
  simply the top tier - would-be escalations run on Opus at max effort, and
  the rule never stalls on an unavailable model. No configuration needed; it
  adapts to whatever models the session actually has.
- **Routing is free:** the rule is a lookup table, not a deliberation. The
  routing decision must never cost more tokens than it can save - small tasks
  skip routing entirely and just run on the current model.
- **Written for the model:** the installed block is compact, imperative
  markdown optimized for Claude to follow (and cheap to load every session),
  not prose for humans to study.
- **Per-task fit:** *downgrade* to a cheaper model directly when the work is
  clearly mechanical; *upgrade* only after asking you first.
- **Hard rule that overrides everything: never compromise quality.** Any doubt
  whether a downgrade would hurt = don't downgrade.

## Install

```
/plugin marketplace add thephenyl02-creator/claude-tier
/plugin install tier@claude-tier
```

Then, in any project:

```
/tier
```

It adds the rule to that project's `CLAUDE.md` (creating it if needed). If the
project already carries an **older version** of the rule, `/tier` upgrades the
block in place automatically; if it's already current, it skips. Either way it
offers to commit `CLAUDE.md` so web + mobile sessions pick it up too.

Not inside a git repo? `/tier` still works: the rule lands in the current
directory's `CLAUDE.md` as a machine-local install (sessions launched there
load it; web + mobile only read committed repo config).

## Why "simple is best"

Other routers auto-switch your model via hooks, or ship complex config
profiles. This one is deliberately minimal: one command, one durable rule, no
moving parts to break. You stay in control of the actual model; the rule just
keeps every session honest about tiering - and never trades quality for cost.

## Release notes

- **1.3.0** - Anti-drift rules, learned from a long session where the routing
  silently decayed. Three additions: **pin every sub-agent** (an unpinned
  agent inherits the session model, so mechanical fan-out silently runs at
  frontier prices with no visible signal); a **capacity-error repair rule**
  (a rate-limited tier means retry that agent elsewhere, never strip pins
  globally - and restore them immediately if you do); and **state the routing
  before spending it** (any 3+ agent fan-out announces "6 x Sonnet/medium"
  first, so a mis-route is caught before the tokens, not after). Block tag is
  now `tier-rule v1.3`; `/tier` auto-upgrades older installs in place.
- **1.2.1** - `/tier` now handles non-repo directories (home folder, scratch
  space, unversioned code): it installs into the current directory's
  `CLAUDE.md` as a machine-local rule instead of skipping. Installed block
  unchanged (still `tier-rule v1.2`) - existing installs need nothing.
- **1.2.0** - Subscription-aware (plans without Fable treat Opus as the top
  tier automatically); Fable escalation triggers now cover its benchmarked
  strengths (high-stakes deep research, long-horizon software engineering,
  legal/compliance-critical and deep security analysis); canonical block
  rewritten model-first (compact, imperative, cheaper per session); versioned
  upgrade tag (`tier-rule v1.2`) so `/tier` upgrades reliably across future
  releases.
- **1.1.0** - Opus 5 era routing. Opus is now the default top tier (including
  reviews, synthesis, and final judgment); Fable becomes an explicit
  escalation with named triggers. New "routing is free" principle. `/tier`
  now auto-upgrades older installed blocks in place.
- **1.0.0** - Initial release.

## License

MIT (c) Fenil K Ventures LLC
