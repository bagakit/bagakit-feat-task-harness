#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") --feat <feat-id> [--root <dir>]" >&2
  exit 1
}

root="."
feat=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      shift; [[ $# -gt 0 ]] || usage; root="$1" ;;
    --feat)
      shift; [[ $# -gt 0 ]] || usage; feat="$1" ;;
    -h|--help)
      usage ;;
    *)
      usage ;;
  esac
  shift
done

[[ -n "$feat" ]] || usage
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"
exec python3 "$script_dir/ft_core.py" feat-close --root "$root" --skill-dir "$skill_dir" --feat "$feat"
