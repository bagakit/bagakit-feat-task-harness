#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "${script_dir}/.." && pwd)"

tmp="$(mktemp -d -t bagakit-ft-harness.XXXXXX)"
trap 'rm -rf "$tmp"' EXIT

project="$tmp/project"
mkdir -p "$project"

export BAGAKIT_REFERENCE_SKILLS_HOME="$tmp/reference-skills"

echo "[test] seed required references"
python3 - <<PY
import json
import os
from pathlib import Path

manifest = Path(r"$skill_root") / "references" / "required-reading-manifest.json"
data = json.loads(manifest.read_text(encoding="utf-8"))
for entry in data.get("entries", []):
    if entry.get("type") != "file":
        continue
    raw = str(entry.get("location", "")).strip()
    if not raw:
        continue
    p = Path(os.path.expanduser(os.path.expandvars(raw)))
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("# seeded by test\n", encoding="utf-8")
PY

pushd "$project" >/dev/null
git init -q
git config user.email "bagakit-bot@example.com"
git config user.name "Bagakit Bot"
echo "hello" > README.md
git add README.md
git commit -q -m "init"
popd >/dev/null

echo "[test] ref read gate"
bash "$script_dir/ref_read_gate.sh" --root "$project"

echo "[test] apply harness"
bash "$script_dir/apply-ft-harness.sh" --root "$project"

echo "[test] create feat"
feat_out="$(bash "$script_dir/ft_feat_new.sh" --root "$project" --title "Demo Feat" --slug "demo-feat" --goal "Validate full loop")"
echo "$feat_out"
feat_id="$(printf '%s\n' "$feat_out" | awk -F': ' '/^feat_id:/ {print $2}')"

if [[ -z "$feat_id" ]]; then
  echo "[test] failed to parse feat_id" >&2
  exit 1
fi

echo "[test] configure non-ui gate command"
python3 - <<PY
import json
from pathlib import Path
p = Path(r"$project") / ".bagakit-ft" / "config.json"
data = json.loads(p.read_text())
data["gate"]["project_type"] = "non_ui"
data["gate"]["non_ui_commands"] = ["bash -lc 'true'"]
p.write_text(json.dumps(data, indent=2) + "\n")
PY

echo "[test] task loop"
bash "$script_dir/ft_task_start.sh" --root "$project" --feat "$feat_id" --task T-001
bash "$script_dir/ft_task_gate.sh" --root "$project" --feat "$feat_id" --task T-001

# create code change
printf '\nupdate\n' >> "$project/README.md"

echo "[test] generate commit message"
commit_out="$(bash "$script_dir/ft_task_commit.sh" --root "$project" --feat "$feat_id" --task T-001 --summary "Implement T-001")"
echo "$commit_out"
msg_file="$(printf '%s\n' "$commit_out" | awk -F': ' '/^message_file:/ {print $2}')"

if [[ -z "$msg_file" ]]; then
  echo "[test] failed to parse message_file" >&2
  exit 1
fi

pushd "$project" >/dev/null
git add -A
git commit -q -F "$msg_file"
popd >/dev/null

bash "$script_dir/ft_task_finish.sh" --root "$project" --feat "$feat_id" --task T-001 --result done
bash "$script_dir/ft_feat_close.sh" --root "$project" --feat "$feat_id"

echo "[test] validate + doctor"
bash "$script_dir/validate-ft-harness.sh" --root "$project"
bash "$script_dir/ft_doctor.sh" --root "$project"

echo "[test] query"
python3 "$script_dir/ft_query.py" --root "$project" list >/dev/null

echo "[test] pass: $skill_root"
