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
     · block contains the tag `tier-rule v1.6` → already current. In local
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
<!-- tier-rule v1.6 -->

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
- **Keep raw bulk content out of the frontier context.** Web pages, large
  logs, scraped text, long raw files: delegate the fetching/reading to a
  Sonnet/Haiku sub-agent and let only distilled findings return. Justify this
  as ROUTING (it is Sonnet-tier work), not as a safety measure.
- **Model downgrades are UNPREDICTABLE — do not claim to prevent them.**
  A session's model can change mid-task for reasons outside the routing plan
  (usage limits; provider-side fallbacks that fire even on innocuous work
  such as a routine doc edit). The target model varies. Any rule promising to
  avoid them is false comfort; the defense is DETECTION and RESPONSE.
- **Downgrade protocol — the assistant CANNOT restore the model** (/model is
  user-only; the change does not self-revert):
  1. Announce it the moment it is noticed or the user reports it.
  2. PAUSE judgment-heavy work (design, review, synthesis, final calls).
     Mechanical work may continue.
  3. Ask the user to restore with /model.
  4. After restore, RE-VERIFY any quality-critical output produced during
     the downgrade window. A silent tier loss is only harmless if nothing
     important was decided inside it — check, do not assume.
- **HARD RULE (overrides all): never compromise quality.** Any doubt whether a
  downgrade would hurt → do NOT downgrade.
```
