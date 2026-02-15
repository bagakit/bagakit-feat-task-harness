#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") --feat <feat-id> --task <task-id> --result done|blocked [--root <dir>]" >&2
  exit 1
}

root="."
feat=""
task=""
result=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      shift; [[ $# -gt 0 ]] || usage; root="$1" ;;
    --feat)
      shift; [[ $# -gt 0 ]] || usage; feat="$1" ;;
    --task)
      shift; [[ $# -gt 0 ]] || usage; task="$1" ;;
    --result)
      shift; [[ $# -gt 0 ]] || usage; result="$1" ;;
    -h|--help)
      usage ;;
    *)
      usage ;;
  esac
  shift
done

[[ -n "$feat" && -n "$task" && -n "$result" ]] || usage
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/ft_core.py" task-finish --root "$root" --feat "$feat" --task "$task" --result "$result"
