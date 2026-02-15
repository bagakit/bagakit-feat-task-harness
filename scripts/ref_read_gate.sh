#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") [--root <dir>] [--manifest <path>]" >&2
  exit 1
}

root="."
manifest=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      shift; [[ $# -gt 0 ]] || usage; root="$1" ;;
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
args=(ref-read-gate --root "$root" --skill-dir "$skill_dir")
if [[ -n "$manifest" ]]; then args+=(--manifest "$manifest"); fi
exec python3 "$script_dir/ft_core.py" "${args[@]}"
