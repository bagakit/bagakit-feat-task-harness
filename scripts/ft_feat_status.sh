#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") [--root <dir>] [--feat <feat-id>] [--json]" >&2
  exit 1
}

root="."
feat=""
as_json=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      shift; [[ $# -gt 0 ]] || usage; root="$1" ;;
    --feat)
      shift; [[ $# -gt 0 ]] || usage; feat="$1" ;;
    --json)
      as_json=1 ;;
    -h|--help)
      usage ;;
    *)
      usage ;;
  esac
  shift
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
args=(feat-status --root "$root")
if [[ -n "$feat" ]]; then args+=(--feat "$feat"); fi
if [[ $as_json -eq 1 ]]; then args+=(--json); fi
exec python3 "$script_dir/ft_core.py" "${args[@]}"
