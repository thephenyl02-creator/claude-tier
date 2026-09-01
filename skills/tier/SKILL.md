---
name: tier
description: Install the model/effort-tiering working preference into the CURRENT project — by default into a machine-local CLAUDE.local.md kept untracked via .git/info/exclude, so the user's repo stays clean; with "repo" into the committed CLAUDE.md so web + mobile sessions load it too. Outside any git repo, installs into the current directory's CLAUDE.md. Use when the user wants to make a project/session model-tiered, "add the tiering rule", or types /tier, /tier repo, or /tier local. If the project carries an OLDER version of the rule, upgrade it in place automatically.
---

# Make this project model-tiered

When invoked, install the standing model/effort-tiering rule for the CURRENT
project. There are two install modes — the default keeps the user's repo clean:

- **local (DEFAULT)** — write to `CLAUDE.local.md` at the working tree's root
  and keep it untracked. The rule is a PERSONAL working preference; it must
  never be forced into a shared repo where every collaborator inherits it.
  Local sessions load the file automatically alongside `CLAUDE.md`; web
  (claude.ai/code) + mobile will NOT see it — those surfaces read only
  committed repo files.
- **repo (only on explicit request)** — the user said "repo" or asked for
  web/mobile coverage → write to the committed root `CLAUDE.md`. This is the
  only way the rule reaches web + mobile sessions, and it makes the block
  visible to everyone who clones the repo. State that trade-off in one line
  when installing this way.

Outside a git repo (home directory, scratch space, unversioned code) there is
no repo to keep clean: install into the current working directory's
`CLAUDE.md`. That is machine-local by nature. Do not refuse or skip the
install just because there is no repo — the user asked for tiering where they
are.

The canonical block is written for the model, not for human prose style:
compact, imperative, unambiguous. Install it verbatim — do not paraphrase,
prettify, or reformat it.

## Steps
0. **Global-coverage guard.** Before anything else, check the user-level
   `~/.claude/CLAUDE.md` for the marker `model & effort tiering` and its
   `tier-rule vX.Y.Z` tag (skip this check in a cloud sandbox — no user home
   config there):
   - Global tag SAME or NEWER than this skill's canonical block, and LOCAL
     mode → the user is already covered in every local session; a project
     install would load the same ~900-token rule TWICE every turn for zero
     benefit. Say so and STOP. Mention that `/tier repo` is the one reason to
     install anyway (web/mobile sessions read only committed repo files).
   - Global tag OLDER than the canonical block → offer to upgrade the GLOBAL
     file in place instead of installing locally — one copy, every project.
     If the user declines, proceed with the normal install below.
   - REPO mode → proceed regardless (web/mobile coverage is the point), but
     note in one line that local sessions in this project will load both the
     global and the repo copy — the accepted price of that coverage.
   - No global block → proceed normally.
1. Pick the mode: the word "repo" (or an explicit ask for web/mobile
   coverage) → repo mode. Otherwise — including an explicit "local" — local
   mode. EXCEPTION: if THIS session is itself running in a cloud sandbox
   (claude.ai/code web or mobile — typical signs: an ephemeral fresh-clone
   workspace path, no user home config; if unsure, ask the user where they
   are running) a local install is not durable — the clone is ephemeral and
   untracked files die with the session. Say so and offer repo mode instead;
   if the user declines, install locally anyway and warn in one line that it
   will not survive the session.
2. Locate the targets at the CURRENT working tree's root, via
   `git rev-parse --show-toplevel` — in a linked worktree that is the
   worktree's OWN root, never the main checkout's:
   - In a git repo → LOCAL target is `<root>/CLAUDE.local.md`; REPO target
     is `<root>/CLAUDE.md`. Always pass the FULL `<root>/...` path to git
     commands below — a bare `CLAUDE.local.md` pathspec silently misses when
     the session's cwd is a subdirectory. In local mode, first check whether
     the file is already TRACKED:
     `git ls-files --error-unmatch -- "<root>/CLAUDE.local.md"` — exit 0 =
     tracked (a tracked file cannot be excluded, so edits to it WILL show as
     a repo change — surface that and ask the user how to proceed before
     writing anything); exit 1 with a "did not match" message is the normal
     untracked answer, NOT an error.
   - NOT in a git repo → the single target is the current working
     directory's `CLAUDE.md`; treat it as local mode, skip step 4, and in
     step 3 ignore the other-file branches (there is only one file — upgrade
     in place there).
3. Search BOTH targets (where they exist) for the marker
   `model & effort tiering`, then take exactly one branch:
   - **Found in BOTH files** → never finish with two copies. Local mode →
     ask the migrate/keep question below, and EITHER WAY delete the losing
     copy: migrate ⇒ the CANONICAL BLOCK replaces any existing block in
     `CLAUDE.local.md` and the block is REMOVED from `CLAUDE.md`; keep ⇒ the
     old block in `CLAUDE.md` is replaced in place with the CANONICAL BLOCK
     and the block is REMOVED from `CLAUDE.local.md`. Repo mode → install
     the CANONICAL BLOCK into `CLAUDE.md` (replacing its old block) and
     DELETE the block from `CLAUDE.local.md`.
   - **Found only in the file matching the chosen mode** → version check:
     · block contains the tag `tier-rule v1.9.0` → already current. In local
       mode in a git repo, still run step 4 first (verify/repair the
       exclusion — it may be missing even when the block is current), then
       say the project is already tiered and STOP — do not duplicate.
     · older tag, or no tag → REPLACE the entire old block in place — from
       its `## Working preferences — model & effort tiering` heading (any
       heading-suffix variant) through its last line (up to the next `##`
       heading or end of file) — with the CANONICAL BLOCK below. Do this
       automatically, no need to ask; say in one line that you upgraded it.
   - **Found only in the OTHER file:**
     · Local mode in a git repo, block in the committed `CLAUDE.md` (a
       pre-1.6 install) → ASK the user:
       — migrate (recommended): write the CANONICAL BLOCK into
         `CLAUDE.local.md` (replacing any existing tiering block there),
         DELETE the old block from `CLAUDE.md`, run step 4, and note that
         the `CLAUDE.md` edit is a repo change they will want to commit
         (web/mobile coverage is lost);
       — keep: REPLACE the old block in `CLAUDE.md` with the CANONICAL
         BLOCK in place (upgrading it) and follow step 5's repo-mode commit
         reminder.
     · Repo mode, block in `CLAUDE.local.md` → install the CANONICAL BLOCK
       into `CLAUDE.md` and DELETE the old block from `CLAUDE.local.md`.
   - **Found in neither** → fresh install: insert the CANONICAL BLOCK below
     verbatim into the chosen mode's target, near the top (after the
     project's title/intro paragraph if there is one). Create the file if it
     doesn't exist.
4. Local mode in a git repo — keep `CLAUDE.local.md` untracked with ZERO
   repo footprint. Do NOT edit the repo's `.gitignore` — that would itself
   be an uncommitted repo change the user never asked for. Instead:
   - If `git check-ignore -q -- "<root>/CLAUDE.local.md"` exits 0, it is
     already excluded — nothing to do. (Exit 1 is the normal "not ignored
     yet" answer, NOT an error; only exit 128 means the command itself
     failed.)
   - Otherwise resolve the exclude file with
     `git rev-parse --path-format=absolute --git-path info/exclude`, create
     it if absent, make sure it ends with a newline, and append the line
     `CLAUDE.local.md` if it is not already present.
   - Note in passing: `CLAUDE.local.md` itself is per-clone/per-worktree —
     re-run /tier in other clones or worktrees — while the exclude entry is
     per-clone and already covers every worktree of this clone.
5. Repo mode → remind the user to commit `CLAUDE.md` so web + mobile
   sessions pick it up (`git add CLAUDE.md && git commit`), and offer to do
   the commit. Non-repo install → say the install is local to this
   machine/directory, and that repo-mode inside a git repo covers web +
   mobile too.
6. Confirm in one line what you did and into which file.

Maintainer note: any future edit to the canonical block MUST bump the
`tier-rule vX.Y` version tag here AND in step 3's version check, or
auto-upgrade breaks.

## Canonical block (install verbatim)

```markdown
## Working preferences — model & effort tiering
<!-- tier-rule v1.9.0 -->

Quality first. Efficiency comes ONLY from routing mechanical work to cheaper
tiers — never from downgrading work that needs a strong model.
**HARD RULE: any doubt whether a downgrade would hurt → do NOT downgrade.**

**Routing** (a lookup, never a deliberation; small task → skip it, use the
current model):
· tests / builds / linters / migrations → local, no model
· mechanical gathering, search fan-out, doc refresh → Sonnet (low/medium)
· the SAME simple operation repeated over many items → Haiku (200K window;
  Claude Code sends NO effort for Haiku sub-agents — treat the dial as absent).
  A one-off check is cheaper inline — see the boot floor
· substantive builds, synthesis, final judgment → Opus (measured: LOW effort
  held full quality on build-from-spec where Sonnet/high did not; xhigh only
  for demanding agentic work) — the default top tier since Opus 5
· **verification / correctness review → Fable 5.1 at LOW effort.** Measured
  on a planted-bug review: Fable found the subtle bug 7/8 runs at any effort;
  Opus 1/9 across low→max; Sonnet 1/8. Pick the MODEL for verification —
  effort bought Opus nothing there.
· Fable 5.1 = escalation ONLY (≈2× Opus on output, though its cache reads
  are HALF of Opus's, so long cache-bound sessions narrow the gap): the
  longest/hardest frontier reasoning,
  high-stakes research, tie-break after an Opus attempt fails, or explicit
  request. Unavailable? Opus at max IS the ceiling — never stall on it.
· **Never `max` by default.** Measured: Sonnet/max spent 33K output tokens for
  the result Sonnet/low reached with 2K, same score; Opus and Fable at max
  cost 3-5× their low cell for no quality gain. `max` is for problems that
  demonstrably failed at xhigh.
· **Within a tier, always the NEWEST model** — same or lower price, better
  model (today: Fable 5.1, Opus 5, Sonnet 5, Haiku 4.5). Older versions cost
  the same or more for less; Opus/Sonnet 4.6 also lack `xhigh`. Pin by FULL
  ID where a short alias lags — `fable` still resolves to Fable 5, which has
  4× dearer cache reads than 5.1 for the same price.

**Main session — model AND effort are frozen at session start**
- The cache is keyed by both. Measured: changing either drops cache_read to
  ZERO, and the next identical turn costs 20× more. Pick both at the start
  and hold them; vary them ACROSS sessions, never within one. Switch
  mid-session only if the whole REST of the session needs it.
- Thrashing is worse than losing a discount: a cache WRITE costs ~20× a READ
  for the same tokens, so a session that keeps invalidating pays roughly
  DOUBLE list price.
- **Model fit:** DOWNGRADE clearly-mechanical work to a cheaper sub-agent
  directly, no permission needed. UPGRADE only after informing/asking —
  never silently deliver a weaker result.

**Sub-agents — the only tier lever once a session is running**
- A sub-agent runs at its own model and effort in its own context, costing
  the main cache nothing — but it pays to BOOT first: ~10K on Haiku, ~44K on
  Opus (≈$0.28 before any work happens). Boot tracks the MODEL, not the
  agent's `tools:` list. So small one-shot work is cheaper INLINE, however
  cheap the model.
- Delegate when the work is big enough to clear that boot AND either the tier
  drops meaningfully or the material would otherwise sit in the main context
  being re-read every later turn. A real tier drop can make delegation net
  CHEAPER than inline; same-tier delegation buys only the context benefit.
- **PIN EVERY SUB-AGENT.** An unpinned agent inherits the session model, so a
  frontier main model turns mechanical work into frontier-priced work with no
  visible signal. Rate-limited? Retry THAT agent on another tier — never drop
  pins globally. Weak or wrong result? Re-run THAT agent one tier UP: a bad
  cheap answer costs more than the right tier would have.
- The `Agent` tool has **no effort parameter**. Pin effort in the agent's
  `.claude/agents/*.md` frontmatter (model, effort, tools), or via
  `Workflow`'s `agent(prompt, {model, effort})`.
- **Batch by configuration.** Dispatch INDEPENDENT same-tier agents in ONE
  parallel batch — a fan-out shares the prefix the first agent cached (~39%
  less boot). Never parallelise steps that depend on each other.
- Announce any fan-out of 3+ in one line first ("6 × Sonnet/medium") so a
  mis-route is visible BEFORE the tokens are spent.
- Give a sub-agent the DECISION explicitly — it did not watch it being made.

**If the session model changes on its own** (usage limits, provider fallback —
unpredictable, and `/model` is user-only so the assistant cannot restore it):
announce it, pause judgment-heavy work, ask the user to restore, then
re-verify anything quality-critical decided during that window.
```
