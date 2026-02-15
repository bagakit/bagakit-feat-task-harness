#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") [--root <dir>]" >&2
  exit 1
}

root="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      shift; [[ $# -gt 0 ]] || usage; root="$1" ;;
    -h|--help)
      usage ;;
    *)
      usage ;;
  esac
  shift
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/ft_core.py" doctor --root "$root"
