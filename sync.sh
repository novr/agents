#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd -P)"
AGENTS_SKILLS="${HOME}/.agents/skills"
AGENTS_COMMANDS="${HOME}/.agents/commands"
CLAUDE_SKILLS="${HOME}/.claude/skills"

resolve() {
  realpath "$1" 2>/dev/null || true
}

owned_skills() {
  if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$REPO" ls-files -z -- 'skills/*/SKILL.md' |
      while IFS= read -r -d '' f; do
        [ -f "$REPO/$f" ] || continue
        basename "$(dirname "$f")"
      done
    return
  fi
  local s
  for s in "$REPO"/skills/*/; do
    [ -d "$s" ] || continue
    [ -f "${s}SKILL.md" ] || continue
    basename "$s"
  done
}

owned_commands() {
  if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$REPO" ls-files -z -- 'commands/*.md' |
      while IFS= read -r -d '' f; do
        [ -f "$REPO/$f" ] || continue
        basename "$f"
      done
    return
  fi
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

# Do not replace a real directory/file.
link_one() {
  local src="$1"
  local dest="$2"
  local src_abs
  src_abs="$(resolve "$src")"
  if [ -z "$src_abs" ]; then
    echo "missing $src" >&2
    return 1
  fi

  if [ -L "$dest" ]; then
    if [ "$(resolve "$dest")" = "$src_abs" ]; then
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

prune_stale() {
  local dest_dir="$1"
  local root_prefix="$2"
  shift 2
  local path resolved name

  [ -d "$dest_dir" ] || return 0
  shopt -s nullglob
  for path in "$dest_dir"/*; do
    [ -L "$path" ] || continue
    resolved="$(resolve "$path")"
    if [ -z "$resolved" ]; then
      case "$(readlink "$path" || true)" in
        "$root_prefix"|"$root_prefix"/*|"$REPO"|"$REPO"/*) ;;
        *) continue ;;
      esac
    else
      case "$resolved" in
        "$root_prefix"|"$root_prefix"/*) ;;
        *) continue ;;
      esac
    fi
    name="$(basename "$path")"
    if ! is_owned "$name" "$@"; then
      rm -f "$path"
      echo "prune $path"
    fi
  done
}

if [ $# -ne 0 ]; then
  echo "usage: $0" >&2
  exit 1
fi

mkdir -p "$AGENTS_SKILLS" "$AGENTS_COMMANDS" "$CLAUDE_SKILLS"

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

status=0

for name in "${skills[@]+"${skills[@]}"}"; do
  link_one "$REPO/skills/$name" "$AGENTS_SKILLS/$name" || status=1
done
for name in "${commands[@]+"${commands[@]}"}"; do
  link_one "$REPO/commands/$name" "$AGENTS_COMMANDS/$name" || status=1
done

for name in "${skills[@]+"${skills[@]}"}"; do
  link_one "$AGENTS_SKILLS/$name" "$CLAUDE_SKILLS/$name" || status=1
done

prune_stale "$AGENTS_SKILLS" "$REPO" "${skills[@]+"${skills[@]}"}"
prune_stale "$AGENTS_COMMANDS" "$REPO" "${commands[@]+"${commands[@]}"}"
prune_stale "$CLAUDE_SKILLS" "$AGENTS_SKILLS" "${skills[@]+"${skills[@]}"}"

if [ "$status" -ne 0 ]; then
  echo "done with errors" >&2
  exit "$status"
fi
echo "done"
