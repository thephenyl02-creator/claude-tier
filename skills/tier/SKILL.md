---
name: tier
description: Install the model/effort-tiering working preference into the CURRENT project's CLAUDE.md (or, outside any git repo, the current directory's CLAUDE.md) so this project runs tiered — quality-first, cost-efficient — on every device. Use when the user wants to make a project/session model-tiered, "add the tiering rule", or types /tier. If the project carries an OLDER version of the rule, upgrade it in place automatically.
---

# Make this project model-tiered

When invoked, install the standing model/effort-tiering rule into the CURRENT
project's `CLAUDE.md` so it is always loaded here. Because it goes into the
COMMITTED repo `CLAUDE.md`, the result applies on desktop + web (claude.ai/code)
+ mobile for this project (those surfaces only read a project's committed
config, never local machine config).

Outside a git repo (home directory, scratch space, unversioned code) the skill
still works: install into the current working directory's `CLAUDE.md` instead.
That is a machine-local install — sessions launched from that directory load
it; web/mobile won't see it. Do not refuse or skip the install just because
there is no repo — the user asked for tiering where they are.

The canonical block is written for the model, not for human prose style:
compact, imperative, unambiguous. Install it verbatim — do not paraphrase,
prettify, or reformat it.

## Steps
1. Locate the target `CLAUDE.md`:
   - In a git repo → the repo root's `CLAUDE.md` (in a git worktree, target
     the main checkout's root).
   - NOT in a git repo → the current working directory's `CLAUDE.md` — a
     machine-local install is exactly what a non-repo directory can get.
   If the file doesn't exist at the target, create it.
2. Search it for the marker `model & effort tiering`:
   - **Not found** → fresh install; go to step 3.
   - **Found, and the block contains the version tag `tier-rule v1.4`** → the
     project is already on the current rule. Tell the user it is already
     tiered and STOP — do not duplicate.
   - **Found, WITHOUT `tier-rule v1.4`** (older version, including blocks with
     no version tag at all) → REPLACE the entire old block in place — from its
     `## Working preferences — model & effort tiering` heading through its
     last line (up to the next `##` heading or end of file) — with the
     CANONICAL BLOCK below. Do this automatically, no need to ask. Say in one
     line that you upgraded it, then continue at step 4.
3. Insert the CANONICAL BLOCK below verbatim, near the top (after the
   project's title/intro paragraph if there is one).
4. If the project is a git repo, remind the user to commit `CLAUDE.md` so web +
   mobile sessions pick it up (`git add CLAUDE.md && git commit`). Offer to do
   the commit. If it is NOT a repo, say instead that the install is local to
   this machine/directory, and that running /tier inside any git repo covers
   that project on web + mobile too.
5. Confirm in one line what you did.

Maintainer note: any future edit to the canonical block MUST bump the
`tier-rule vX.Y` version tag here AND in step 2, or auto-upgrade breaks.

## Canonical block (install verbatim)

```markdown
## Working preferences — model & effort tiering (committed: applies on desktop, web, AND mobile)
<!-- tier-rule v1.4 -->

Quality first. Efficiency comes ONLY from routing genuinely mechanical work to
cheaper tiers — never from downgrading work that needs a strong model.
- **Plan on the session's strongest model.** Every plan annotates each work
  item with BOTH a model tier AND an effort level (low→max).
- **Routing table** (a lookup, never a deliberation — the routing decision
  must never cost more tokens than it can save; small/short task → skip
  routing, do it on the current model):
  · tests / builds / linters / migrations → local, no model
  · mechanical evidence-gathering, search fan-out, doc refresh → Sonnet (low/med)
  · substantive builds, adversarial verifiers, correctness/security reviews,
    research synthesis, final judgment → Opus (high/xhigh), the default top
    tier since Opus 5
- **Fable is an escalation, not a default** (≈2× Opus cost, heavier token use,
  marginal overall lead). Escalate ONLY for: the longest/hardest
  frontier-reasoning work (Fable's lead grows with task length + complexity) ·
  high-stakes deep research where a wrong conclusion is costly · large or
  high-stakes tasks in Fable's benchmarked-lead domains — long-horizon
  software-engineering marathons, legal/compliance-critical analysis, deep
  security analysis · tie-break adjudication after strong models disagree or
  an Opus attempt fails · explicit user request.
- **Fable unavailable in this session** (subscription tier, e.g. Claude Pro)?
  → Opus IS the top tier: run would-be escalations on Opus at max effort;
  never stall on, or demand, an unavailable model.
- **Main-model fit:** DOWNGRADE clearly-mechanical work to a cheaper sub-agent
  directly, no permission needed. UPGRADE only after informing/asking — never
  silently deliver a weaker result.
- **PIN EVERY SUB-AGENT — never let one inherit the session model.** Fan-out
  readers/searchers/gatherers get an explicit cheap tier on every call. An
  unpinned agent silently runs on the session model, so a frontier main model
  turns mechanical work into frontier-priced work without any visible signal.
- **Capacity-error repair rule:** if a pinned tier fails on a rate/usage limit,
  retry THAT agent on another tier. Never respond by removing pins globally —
  and if you ever do, restore them on the very next fan-out. Silent
  un-pinning is the most common way this whole rule decays in a long session.
- **State the routing before spending it.** Any fan-out of 3+ agents announces
  its plan in one line first (count × tier/effort, e.g. "6 × Sonnet/medium"),
  so a mis-route is visible to the user BEFORE the tokens are spent, not after.
- **A frontier main model never reads raw web content.** Web search/fetch is
  Sonnet-tier evidence-gathering anyway — and raw pages in a Fable/Opus
  context can trip safety fallbacks that silently switch the session model
  (e.g. Fable → Opus 4.8), degrading everything after. Delegate fetches to a
  Sonnet/Haiku sub-agent; only distilled findings enter the main context.
- **Safeguard-downgrade watch.** The assistant CANNOT switch the session model
  back — /model is user-only, and a safeguard switch does NOT revert on its
  own. When a downgrade is noticed or reported (harness banner, user mention):
  say so immediately, pause judgment-heavy work, and prompt the user to
  restore with /model. Never silently continue frontier-grade work on the
  fallback model; mechanical work may proceed meanwhile.
- **HARD RULE (overrides all): never compromise quality.** Any doubt whether a
  downgrade would hurt → do NOT downgrade.
```
