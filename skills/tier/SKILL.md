---
name: tier
description: Install the model/effort-tiering working preference into the CURRENT project's CLAUDE.md so this project runs tiered — quality-first, cost-efficient — on every device. Use when the user wants to make a project/session model-tiered, "add the tiering rule", or types /tier. If the project carries an OLDER version of the rule, upgrade it in place automatically.
---

# Make this project model-tiered

When invoked, install the standing model/effort-tiering rule into the CURRENT
project's `CLAUDE.md` so it is always loaded here. Because it goes into the
COMMITTED repo `CLAUDE.md`, the result applies on desktop + web (claude.ai/code)
+ mobile for this project (those surfaces only read a project's committed
config, never local machine config).

## Steps
1. Locate the project's `CLAUDE.md` at the repo/project root. If you are in a
   git worktree, target the main checkout's root `CLAUDE.md`. If no `CLAUDE.md`
   exists, create one at the project root.
2. Search it for the marker `model & effort tiering`:
   - **Not found** → fresh install; go to step 3.
   - **Found, and the block contains `Fable is an escalation`** → the project
     is already on the current rule. Tell the user it is already tiered and
     STOP — do not duplicate.
   - **Found, but WITHOUT `Fable is an escalation`** → an older version of the
     rule is installed. REPLACE the entire old block in place — from its
     `## Working preferences — model & effort tiering` heading through its
     last line (up to the next `##` heading or end of file) — with the
     CANONICAL BLOCK below. Do this automatically, no need to ask. Say in one
     line that you upgraded it, then continue at step 4.
3. Insert the CANONICAL BLOCK below verbatim, near the top (after the
   project's title/intro paragraph if there is one).
4. If the project is a git repo, remind the user to commit `CLAUDE.md` so web +
   mobile sessions pick it up (`git add CLAUDE.md && git commit`). Offer to do
   the commit.
5. Confirm in one line what you did.

## Canonical block (append verbatim)

```markdown
## Working preferences — model & effort tiering (committed here so it applies on desktop, web, AND mobile)

Quality is the highest priority; efficiency comes only from routing genuinely
mechanical work to cheaper tiers, never from downgrading work that needs a
strong model.
- **Plan on the highest model available** in the session; every plan assigns,
  per work item, BOTH a model tier AND an effort level (low→max) it needs.
- **Routing:** deterministic batteries (tests/builds/linters/migrations) →
  local, no model · mechanical evidence-gathering / research fan-out / doc
  refresh → Sonnet (low/med) · substantive builds, adversarial verifiers,
  correctness/security reviews, research synthesis, final judgment → Opus
  (high/xhigh) — since Opus 5, Opus is the default top tier.
- **Fable is an escalation, not a default** (≈2× Opus cost, heavier token use,
  only a marginal overall lead — Opus 5 wins several areas outright): escalate
  ONLY for (a) the longest/hardest frontier-reasoning work — Fable's lead
  grows with task length, (b) tie-break adjudication after strong models
  disagree or an Opus-level attempt fails, or (c) explicit user request.
- **Routing must be free:** decide from this table, never by deliberation —
  the routing decision must never cost more than it can save. For small/short
  tasks, skip routing and do the work on the current model.
- **Per-task main-model fit:** DOWNGRADE — act directly, no need to ask
  (delegate clearly-mechanical work to a cheaper sub-agent so the expensive
  model isn't wasted). UPGRADE — always inform/ask first (stop before a
  lower-quality result; recommend the user /model up or delegate the hard part
  to a stronger agent). **HARD RULE, overrides all: never compromise quality**
  — any doubt whether a downgrade would hurt = do NOT downgrade.
```
