---
name: tier
description: Install the model/effort-tiering working preference into the CURRENT project's CLAUDE.md so this project runs tiered — quality-first, cost-efficient — on every device. Use when the user wants to make a project/session model-tiered, "add the tiering rule", or types /tier.
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
2. If it ALREADY contains the tiering block (search for the marker
   `model & effort tiering`), tell the user it is already tiered and STOP — do
   not duplicate.
3. Otherwise insert the CANONICAL BLOCK below verbatim, near the top (after the
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
  refresh → Sonnet (low/med) · substantive builds + adversarial-verifier
  fan-outs → Opus (high) · delicate correctness, consent/security reviews,
  research synthesis, final judgment → the top model available (high/xhigh).
- **Per-task main-model fit:** DOWNGRADE — act directly, no need to ask
  (delegate clearly-mechanical work to a cheaper sub-agent so the expensive
  model isn't wasted). UPGRADE — always inform/ask first (stop before a
  lower-quality result; recommend the user /model up or delegate the hard part
  to a stronger agent). **HARD RULE, overrides all: never compromise quality**
  — any doubt whether a downgrade would hurt = do NOT downgrade.
```
