#!/bin/sh
# Fusion installer — https://github.com/bluewaves-creations/fusion
# Usage:  curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
# Env:    FUSION_VERSION, FUSION_PACKAGE_SPEC, FUSION_SKILLS_DIR,
#         FUSION_NO_AGENTS, FUSION_NO_MODIFY_PATH
# It ensures uv (which brings Python), installs fusion-cli from PyPI, and
# hands off to `fusion setup` for the skills. No sudo. Idempotent.
set -u

say()  { printf '%s\n' "$*" >&2; }
err()  { say "fusion install: error: $*"; exit 1; }

command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 \
  || err "need curl or wget. install one, or install by hand:
  1) https://docs.astral.sh/uv/  2) uv tool install fusion-cli  3) fusion setup"

[ -n "${HOME:-}" ] || err "HOME is not set"

fetch() {  # fetch URL > stdout
  if command -v curl >/dev/null 2>&1; then curl -fsSL "$1"
  else wget -qO- "$1"; fi
}

# 1 — uv (brings its own Python; PyPI hashes verified by uv itself)
if command -v uv >/dev/null 2>&1; then
  UV=uv
else
  say "installing uv (Astral's official installer)…"
  TMP_UV_SH="$(mktemp)"
  fetch https://astral.sh/uv/install.sh > "$TMP_UV_SH" \
    || err "could not download uv's installer — check your network, or install uv yourself: https://docs.astral.sh/uv/"
  if [ "${FUSION_NO_MODIFY_PATH:-}" = "1" ]; then
    UV_NO_MODIFY_PATH=1 sh "$TMP_UV_SH" \
      || err "uv install failed — see https://docs.astral.sh/uv/"
  else
    sh "$TMP_UV_SH" \
      || err "uv install failed — see https://docs.astral.sh/uv/"
  fi
  rm -f "$TMP_UV_SH"
  UV="$HOME/.local/bin/uv"
  [ -x "$UV" ] || UV="${XDG_BIN_HOME:-$HOME/.local/bin}/uv"
  [ -x "$UV" ] || err "uv installed but not found at $HOME/.local/bin/uv —
  restart your shell and re-run, or run: uv tool install fusion-cli && fusion setup"
fi

# 2 — the CLI
SPEC="${FUSION_PACKAGE_SPEC:-fusion-cli${FUSION_VERSION:+==$FUSION_VERSION}}"
say "installing ${SPEC}…"
# --refresh: skip uv's cached PyPI index, so an install minutes after a
# release still lands the release, not the cache's idea of "latest"
"$UV" tool install --force --refresh "$SPEC" \
  || err "uv tool install failed. manual step: $UV tool install --force --refresh '$SPEC'"

# 3 — hand off to the brain
BIN="$("$UV" tool dir --bin)" \
  || err "could not resolve uv's tool bin dir — run by hand: $UV tool dir --bin, then <that dir>/fusion setup"
[ -x "$BIN/fusion" ] \
  || err "fusion not found in $BIN after install — run by hand: $BIN/fusion setup (or check: $UV tool list)"
exec "$BIN/fusion" setup
