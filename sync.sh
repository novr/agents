#!/usr/bin/env bash
# Link this repo's skills/commands into ~/.agents (runtime).
# ~/.agents stays a real directory so third-party installs do not touch the repo.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
AGENTS_SKILLS="${HOME}/.agents/skills"
AGENTS_COMMANDS="${HOME}/.agents/commands"

usage() {
  echo "usage: $0" >&2
  exit 1
}

owned_skills() {
  local s
  for s in "$REPO"/skills/*/; do
    [ -d "$s" ] || continue
    [ -f "${s}SKILL.md" ] || continue
    basename "$s"
  done
}

owned_commands() {
  local c
  shopt -s nullglob
  for c in "$REPO"/commands/*.md; do
    basename "$c"
  done
}

is_owned() {
  local needle="$1"
  shift
  local name
  for name in "$@"; do
    [ "$name" = "$needle" ] && return 0
  done
  return 1
}

# Dest may be missing or a symlink. Never replace a real directory/file (third-party).
link_one() {
  local src="$1"
  local dest="$2"
  local src_abs
  src_abs="$(realpath "$src")"

  if [ -L "$dest" ]; then
    if [ "$(realpath "$dest")" = "$src_abs" ]; then
      echo "ok   $dest"
      return 0
    fi
    rm -f "$dest"
  elif [ -e "$dest" ]; then
    echo "skip $dest (exists, not a symlink)" >&2
    return 0
  fi

  ln -s "$src_abs" "$dest"
  echo "link $dest -> $src_abs"
}

# Drop symlinks that still point into this repo but are no longer owned.
prune_stale() {
  local dest_dir="$1"
  shift
  local path target name

  shopt -s nullglob
  for path in "$dest_dir"/*; do
    [ -L "$path" ] || continue
    target="$(readlink "$path" || true)"
    case "$target" in
      "$REPO"/*) ;;
      *) continue ;;
    esac
    name="$(basename "$path")"
    if ! is_owned "$name" "$@"; then
      rm -f "$path"
      echo "prune $path"
    fi
  done
}

[ $# -eq 0 ] || usage

mkdir -p "$AGENTS_SKILLS" "$AGENTS_COMMANDS"

skills=()
commands=()
while IFS= read -r name; do
  [ -n "$name" ] || continue
  skills+=("$name")
done < <(owned_skills)
while IFS= read -r name; do
  [ -n "$name" ] || continue
  commands+=("$name")
done < <(owned_commands)

for name in "${skills[@]+"${skills[@]}"}"; do
  link_one "$REPO/skills/$name" "$AGENTS_SKILLS/$name"
done
for name in "${commands[@]+"${commands[@]}"}"; do
  link_one "$REPO/commands/$name" "$AGENTS_COMMANDS/$name"
done

prune_stale "$AGENTS_SKILLS" "${skills[@]+"${skills[@]}"}"
prune_stale "$AGENTS_COMMANDS" "${commands[@]+"${commands[@]}"}"

echo "done"
