#!/usr/bin/env bash
# Codex Tier installer (macOS / Linux / WSL)
# curl -fsSL https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/install-codex.sh | bash

set -u

REPO="thephenyl02-creator/claude-tier"
MARKETPLACE="codex-tier"
PLUGIN="codex-tier"
TARBALL_URL="https://github.com/$REPO/archive/refs/heads/main.tar.gz"
MARKER=".installed-by-codex-tier-installer"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  +\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m  x\033[0m %s\n' "$*" >&2; }

if [ -z "${HOME:-}" ]; then
  err "HOME is not set; re-run from a normal login shell."
  exit 1
fi

INSTALL_HOME="${CODEX_TIER_INSTALL_HOME:-$HOME}"
SKILLS_ROOT="$INSTALL_HOME/.agents/skills"
DEST="$SKILLS_ROOT/$PLUGIN"
LOCAL_SOURCE="${CODEX_TIER_SOURCE_ROOT:-}"
FORCE_DIRECT="${CODEX_TIER_FORCE_DIRECT:-0}"

find_codex() {
  if [ -n "${CODEX_TIER_CODEX_BIN:-}" ] && [ -x "$CODEX_TIER_CODEX_BIN" ]; then
    printf '%s\n' "$CODEX_TIER_CODEX_BIN"
    return 0
  fi
  if command -v codex >/dev/null 2>&1; then
    command -v codex
    return 0
  fi
  for candidate in "$HOME/.local/bin/codex" /usr/local/bin/codex +                   /opt/homebrew/bin/codex +                   /Applications/Codex.app/Contents/Resources/codex; do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
  elif command -v python >/dev/null 2>&1; then
    command -v python
  else
    return 1
  fi
}

CODEX_BIN="$(find_codex || true)"
if [ -z "$CODEX_BIN" ]; then
  err "Codex was not found. Install the official CLI, then re-run:"
  err "  npm install --global @openai/codex"
  exit 1
fi

PYTHON_BIN="$(find_python || true)"
if [ -z "$PYTHON_BIN" ]; then
  err "Python 3 is required by Codex Tier's deterministic router."
  exit 1
fi

VERSION_OUTPUT="$("$CODEX_BIN" --version 2>&1 || true)"
EXEC_HELP="$("$CODEX_BIN" exec --help 2>&1 || true)"
CLI_COMPATIBLE=1
for required in "--model" "--config" "--json" "--output-last-message" "--sandbox"; do
  if ! printf '%s' "$EXEC_HELP" | grep -q -- "$required"; then
    CLI_COMPATIBLE=0
  fi
done
if [ "$CLI_COMPATIBLE" -ne 1 ]; then
  err "This Codex CLI does not expose the required pinned exec flags."
  err "Update it with: npm install --global @openai/codex"
  exit 1
fi
ok "Codex: ${VERSION_OUTPUT:-$CODEX_BIN}"

safe_remove_stage() {
  target="$1"
  case "$target" in
    "$SKILLS_ROOT/.$PLUGIN.stage."*|"$SKILLS_ROOT/.$PLUGIN.old."*)
      rm -rf -- "$target"
      ;;
    *)
      err "Refusing to remove unexpected path: $target"
      return 1
      ;;
  esac
}

validate_source() {
  source_path="$1"
  [ -f "$source_path/SKILL.md" ] &&
    [ -f "$source_path/scripts/codex_tier.py" ] &&
    "$PYTHON_BIN" "$source_path/scripts/codex_tier.py" validate >/dev/null
}

install_direct() {
  source_path="$1"
  if ! validate_source "$source_path"; then
    err "Codex Tier source validation failed at $source_path"
    return 1
  fi
  mkdir -p "$SKILLS_ROOT" || return 1
  stage="$SKILLS_ROOT/.$PLUGIN.stage.$$"
  old="$SKILLS_ROOT/.$PLUGIN.old.$$"
  safe_remove_stage "$stage" 2>/dev/null || true
  safe_remove_stage "$old" 2>/dev/null || true
  if ! cp -R "$source_path" "$stage"; then
    safe_remove_stage "$stage" 2>/dev/null || true
    return 1
  fi
  : > "$stage/$MARKER" || {
    safe_remove_stage "$stage" 2>/dev/null || true
    return 1
  }

  backup=""
  if [ -e "$DEST" ]; then
    if [ -f "$DEST/$MARKER" ]; then
      if ! mv "$DEST" "$old"; then
        safe_remove_stage "$stage" 2>/dev/null || true
        return 1
      fi
    else
      backup="$INSTALL_HOME/.agents/codex-tier-backup.$(date +%Y%m%d%H%M%S)"
      if ! mv "$DEST" "$backup"; then
        safe_remove_stage "$stage" 2>/dev/null || true
        err "Could not preserve the existing hand-authored skill at $DEST"
        return 1
      fi
      warn "Existing hand-authored skill moved to $backup"
    fi
  fi

  if ! mv "$stage" "$DEST"; then
    [ -e "$old" ] && mv "$old" "$DEST" 2>/dev/null || true
    [ -n "$backup" ] && [ -e "$backup" ] && mv "$backup" "$DEST" 2>/dev/null || true
    safe_remove_stage "$stage" 2>/dev/null || true
    return 1
  fi
  if ! validate_source "$DEST"; then
    mv "$DEST" "$stage" 2>/dev/null || true
    [ -e "$old" ] && mv "$old" "$DEST" 2>/dev/null || true
    safe_remove_stage "$stage" 2>/dev/null || true
    err "Installed copy failed validation; the previous installer-owned copy was restored."
    return 1
  fi
  [ -e "$old" ] && safe_remove_stage "$old"
  ok "Standalone skill installed at $DEST"
  return 0
}

plugin_route() {
  "$CODEX_BIN" plugin marketplace add "$REPO" >/dev/null 2>&1 || true
  "$CODEX_BIN" plugin marketplace upgrade "$MARKETPLACE" >/dev/null 2>&1 || true
  "$CODEX_BIN" plugin add "$PLUGIN@$MARKETPLACE" >/dev/null 2>&1 || return 1
  "$CODEX_BIN" plugin list --json 2>/dev/null |
    grep -Eq '"name"[[:space:]]*:[[:space:]]*"codex-tier"'
}

if [ -n "$LOCAL_SOURCE" ]; then
  SOURCE_SKILL="$LOCAL_SOURCE/plugins/codex-tier/skills/codex-tier"
  info "Installing Codex Tier from local source..."
  install_direct "$SOURCE_SKILL" || {
    err "Local Codex Tier install failed."
    exit 1
  }
elif [ "$FORCE_DIRECT" != "1" ] && plugin_route; then
  ok "Plugin installed: $PLUGIN@$MARKETPLACE"
  if [ -f "$DEST/$MARKER" ]; then
    old="$SKILLS_ROOT/.$PLUGIN.old.$$"
    mv "$DEST" "$old" && safe_remove_stage "$old" || true
  fi
else
  warn "Plugin route unavailable; installing the standalone skill."
  if ! command -v curl >/dev/null 2>&1 || ! command -v tar >/dev/null 2>&1; then
    err "curl and tar are required for the standalone fallback."
    exit 1
  fi
  TMP="$(mktemp -d)" || {
    err "Could not create a temporary directory."
    exit 1
  }
  cleanup() { rm -rf -- "$TMP"; }
  trap cleanup EXIT
  if ! curl -fsSL "$TARBALL_URL" -o "$TMP/source.tar.gz"; then
    err "Could not download $TARBALL_URL"
    exit 1
  fi
  if ! tar -xzf "$TMP/source.tar.gz" -C "$TMP"; then
    err "Could not extract the Codex Tier archive."
    exit 1
  fi
  SOURCE_SKILL="$TMP/claude-tier-main/plugins/codex-tier/skills/codex-tier"
  install_direct "$SOURCE_SKILL" || {
    err "Standalone Codex Tier install failed."
    exit 1
  }
fi

printf '\n'
ok 'Done. Start a new Codex task, then invoke: $codex-tier'
