#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<USAGE
Usage: $(basename "$0") --title <title> --goal <goal> [--slug <slug>] [--root <dir>] [--strict|--no-strict] [--manifest <path>]
USAGE
  exit 1
}

root="."
strict=1
manifest=""
slug=""
title=""
goal=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      shift; [[ $# -gt 0 ]] || usage; root="$1" ;;
    --strict)
      strict=1 ;;
    --no-strict)
      strict=0 ;;
    --manifest)
      shift; [[ $# -gt 0 ]] || usage; manifest="$1" ;;
    --slug)
      shift; [[ $# -gt 0 ]] || usage; slug="$1" ;;
    --title)
      shift; [[ $# -gt 0 ]] || usage; title="$1" ;;
    --goal)
      shift; [[ $# -gt 0 ]] || usage; goal="$1" ;;
    -h|--help)
      usage ;;
    *)
      usage ;;
  esac
  shift
done

[[ -n "$title" && -n "$goal" ]] || usage

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"

args=(feat-new --root "$root" --skill-dir "$skill_dir" --title "$title" --goal "$goal")
if [[ -n "$slug" ]]; then args+=(--slug "$slug"); fi
if [[ $strict -eq 1 ]]; then args+=(--strict); else args+=(--no-strict); fi
if [[ -n "$manifest" ]]; then args+=(--manifest "$manifest"); fi

exec python3 "$script_dir/ft_core.py" "${args[@]}"
