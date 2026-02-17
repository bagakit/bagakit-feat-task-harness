#!/usr/bin/env bash
set -euo pipefail

dev_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "${dev_script_dir}/.." && pwd)"
runtime_scripts_dir="${skill_root}/scripts"

tmp="$(mktemp -d -t bagakit-ft-harness.XXXXXX)"
trap 'rm -rf "$tmp"' EXIT

project="$tmp/project"
mkdir -p "$project"

export BAGAKIT_REFERENCE_SKILLS_HOME="$tmp/reference-skills"

echo "[test] docs policy audit"
if ! grep -q "must not hard-depend on external workflow systems" "$skill_root/docs/notes-requirements.md"; then
  echo "[test] missing policy statement in docs/notes-requirements.md" >&2
  exit 1
fi

echo "[test] audit default manifest (no required OpenSpec / url entries)"
python3 - <<PY
import json
from pathlib import Path

manifest = Path(r"$skill_root") / "references" / "required-reading-manifest.json"
data = json.loads(manifest.read_text(encoding="utf-8"))
entries = data.get("entries", [])

bad = []
for e in entries:
    eid = str(e.get("id", ""))
    required = bool(e.get("required", True))
    etype = str(e.get("type", ""))
    location = str(e.get("location", ""))
    if required and (eid.startswith("openspec-") or "openspec" in location):
        bad.append(eid or location)
    if required and etype == "url":
        bad.append(f"url-required:{eid or location}")

if bad:
    raise SystemExit("default manifest has hard external dependencies: " + ", ".join(bad))
PY

echo "[test] audit optional OpenSpec manifest (local-skill only)"
python3 - <<PY
import json
from pathlib import Path

manifest = Path(r"$skill_root") / "references" / "required-reading-manifest-openspec.json"
data = json.loads(manifest.read_text(encoding="utf-8"))
entries = data.get("entries", [])

bad = []
for e in entries:
    required = bool(e.get("required", True))
    etype = str(e.get("type", ""))
    if required and etype == "url":
        bad.append(str(e.get("id", "")) or str(e.get("location", "")))

if bad:
    raise SystemExit("openspec manifest must not require remote url entries: " + ", ".join(bad))
PY

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
bash "$runtime_scripts_dir/ref_read_gate.sh" --root "$project"

echo "[test] openspec manifest should fail before seeding optional refs"
if bash "$runtime_scripts_dir/ref_read_gate.sh" --root "$project" --manifest "$skill_root/references/required-reading-manifest-openspec.json" >/dev/null 2>&1; then
  echo "[test] expected openspec manifest gate to fail before seeding optional refs" >&2
  exit 1
fi

echo "[test] seed openspec compatibility references"
python3 - <<PY
import json
import os
from pathlib import Path

manifest = Path(r"$skill_root") / "references" / "required-reading-manifest-openspec.json"
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

echo "[test] openspec manifest gate"
bash "$runtime_scripts_dir/ref_read_gate.sh" --root "$project" --manifest "$skill_root/references/required-reading-manifest-openspec.json"

echo "[test] re-generate default ref-read report for harness"
bash "$runtime_scripts_dir/ref_read_gate.sh" --root "$project"

echo "[test] apply harness"
bash "$runtime_scripts_dir/apply-ft-harness.sh" --root "$project"

echo "[test] create feat"
feat_out="$(bash "$runtime_scripts_dir/ft_feat_new.sh" --root "$project" --title "Demo Feat" --slug "demo-feat" --goal "Validate full loop")"
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
p = Path(r"$project") / ".bagakit" / "ft-harness" / "config.json"
data = json.loads(p.read_text())
data["gate"]["project_type"] = "non_ui"
data["gate"]["non_ui_commands"] = ["bash -lc 'true'"]
p.write_text(json.dumps(data, indent=2) + "\n")
PY

echo "[test] task loop"
bash "$runtime_scripts_dir/ft_task_start.sh" --root "$project" --feat "$feat_id" --task T-001
bash "$runtime_scripts_dir/ft_task_gate.sh" --root "$project" --feat "$feat_id" --task T-001

# create code change
printf '\nupdate\n' >> "$project/README.md"

echo "[test] generate commit message"
commit_out="$(bash "$runtime_scripts_dir/ft_task_commit.sh" --root "$project" --feat "$feat_id" --task T-001 --summary "Implement T-001")"
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

bash "$runtime_scripts_dir/ft_task_finish.sh" --root "$project" --feat "$feat_id" --task T-001 --result done
bash "$runtime_scripts_dir/ft_feat_close.sh" --root "$project" --feat "$feat_id"

echo "[test] validate + doctor"
bash "$runtime_scripts_dir/validate-ft-harness.sh" --root "$project"
bash "$runtime_scripts_dir/ft_doctor.sh" --root "$project"

echo "[test] query"
python3 "$runtime_scripts_dir/ft_query.py" --root "$project" list >/dev/null

echo "[test] pass: $skill_root"
