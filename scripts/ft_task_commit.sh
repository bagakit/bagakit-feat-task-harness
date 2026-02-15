#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<USAGE
Usage: $(basename "$0") --feat <feat-id> --task <task-id> --summary <text> [--root <dir>] [--task-status done|blocked] [--message-out <file>] [--execute]
USAGE
  exit 1
}

root="."
feat=""
task=""
summary=""
task_status="done"
message_out=""
execute=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      shift; [[ $# -gt 0 ]] || usage; root="$1" ;;
    --feat)
      shift; [[ $# -gt 0 ]] || usage; feat="$1" ;;
    --task)
      shift; [[ $# -gt 0 ]] || usage; task="$1" ;;
    --summary)
      shift; [[ $# -gt 0 ]] || usage; summary="$1" ;;
    --task-status)
      shift; [[ $# -gt 0 ]] || usage; task_status="$1" ;;
    --message-out)
      shift; [[ $# -gt 0 ]] || usage; message_out="$1" ;;
    --execute)
      execute=1 ;;
    -h|--help)
      usage ;;
    *)
      usage ;;
  esac
  shift
done

[[ -n "$feat" && -n "$task" && -n "$summary" ]] || usage
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
args=(task-commit --root "$root" --feat "$feat" --task "$task" --summary "$summary" --task-status "$task_status")
if [[ -n "$message_out" ]]; then args+=(--message-out "$message_out"); fi
if [[ $execute -eq 1 ]]; then args+=(--execute); fi
exec python3 "$script_dir/ft_core.py" "${args[@]}"
