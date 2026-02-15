#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") [--root <dir>] [--strict|--no-strict] [--manifest <path>]" >&2
  exit 1
}

root="."
strict=1
manifest=""

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
    -h|--help)
      usage ;;
    *)
      usage ;;
  esac
  shift
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"

args=(apply --root "$root" --skill-dir "$skill_dir")
if [[ $strict -eq 1 ]]; then args+=(--strict); else args+=(--no-strict); fi
if [[ -n "$manifest" ]]; then args+=(--manifest "$manifest"); fi

exec python3 "$script_dir/ft_core.py" "${args[@]}"
