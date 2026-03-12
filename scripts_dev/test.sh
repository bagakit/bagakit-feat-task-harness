#!/usr/bin/env bash
set -euo pipefail

dev_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "${dev_script_dir}/.." && pwd)"
runtime_scripts_dir="${skill_root}/scripts"
harness_cli="${runtime_scripts_dir}/feat-task-harness.sh"
skill_maker_cmd="${skill_root}/../bagakit-skill-maker/scripts/bagakit-skill-maker.sh"

echo "[test] runtime hard gates"
sh "${skill_maker_cmd}" runtime-gate --skill-dir "${skill_root}" >/dev/null

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

echo "[test] audit default manifest (local ft-harness only)"
python3 - <<PY
import json
import re
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
    if required and etype == "url":
        bad.append(f"url-required:{eid or location}")
    if location.startswith("/") or re.match(r"^[A-Za-z]:[\\\\/]", location):
        bad.append(f"absolute-path:{eid or location}")
    if "BAGAKIT_REFERENCE_SKILLS_HOME" in location:
        bad.append(f"external-skill-home:{eid or location}")
    if "openspec" in eid.lower() or "openspec" in location.lower():
        bad.append(f"openspec-in-default:{eid or location}")

if bad:
    raise SystemExit("default manifest must be local-only and standalone: " + ", ".join(bad))
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

pushd "$project" >/dev/null
git init -q
git config user.email "bagakit-bot@example.com"
git config user.name "Bagakit Bot"
echo "hello" > README.md
git add README.md
git commit -q -m "init"
popd >/dev/null

echo "[test] ref read gate"
bash "$harness_cli" check-reference-readiness --root "$project"

echo "[test] ref report must avoid absolute paths"
python3 - <<PY
import json
import re
from pathlib import Path

report = Path(r"$project") / ".bagakit" / "ft-harness" / "artifacts" / "ref-read-report.json"
data = json.loads(report.read_text(encoding="utf-8"))
entries = data.get("entries", [])

def is_abs(value: str) -> bool:
    return value.startswith("/") or bool(re.match(r"^[A-Za-z]:[\\\\/]", value))

checks = [
    ("project_root", str(data.get("project_root", ""))),
    ("manifest_path", str(data.get("manifest_path", ""))),
]
for item in entries:
    checks.append((f"entry:{item.get('id', '')}:location", str(item.get("location", ""))))
    checks.append((f"entry:{item.get('id', '')}:resolved_location", str(item.get("resolved_location", ""))))

violations = [f"{k}={v}" for k, v in checks if v and is_abs(v)]
if violations:
    raise SystemExit("ref report leaks absolute paths: " + ", ".join(violations))
PY

echo "[test] openspec manifest should fail before seeding optional refs"
if bash "$harness_cli" check-reference-readiness --root "$project" --manifest "$skill_root/references/required-reading-manifest-openspec.json" >/dev/null 2>&1; then
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
bash "$harness_cli" check-reference-readiness --root "$project" --manifest "$skill_root/references/required-reading-manifest-openspec.json"

echo "[test] re-generate default ref-read report for harness"
bash "$harness_cli" check-reference-readiness --root "$project"

echo "[test] apply harness"
bash "$harness_cli" initialize-harness --root "$project"

if [[ ! -f "$project/.bagakit/ft-harness/runtime-policy.json" ]]; then
  echo "[test] runtime-policy.json was not generated" >&2
  exit 1
fi
if [[ ! -f "$project/.bagakit/ft-harness/index/FEATS_DAG.json" ]]; then
  echo "[test] FEATS_DAG.json was not generated" >&2
  exit 1
fi

echo "[test] configure runtime policy"
python3 - <<PY
import json
from pathlib import Path
p = Path(r"$project") / ".bagakit" / "ft-harness" / "runtime-policy.json"
data = json.loads(p.read_text())
data["git"]["branch_prefix"] = "codex/"
data["workspace"]["default_mode"] = "worktree"
data["gate"]["project_type"] = "non_ui"
data["gate"]["non_ui_commands"] = ["bash -lc 'true'"]
p.write_text(json.dumps(data, indent=2) + "\n")
PY

echo "[test] create feat-1"
feat1_out="$(bash "$harness_cli" create-feat --root "$project" --title "Demo Feat 1" --slug "demo-feat-1" --goal "Validate full loop")"
echo "$feat1_out"
feat_id="$(printf '%s\n' "$feat1_out" | awk -F': ' '/^feat_id:/ {print $2}')"
worktree_path="$(printf '%s\n' "$feat1_out" | awk -F': ' '/^worktree:/ {print $2}')"
branch_name="$(printf '%s\n' "$feat1_out" | awk -F': ' '/^branch:/ {print $2}')"

if [[ -z "$feat_id" || -z "$worktree_path" || -z "$branch_name" ]]; then
  echo "[test] failed to parse feat1 outputs" >&2
  exit 1
fi
if [[ "$branch_name" != codex/* ]]; then
  echo "[test] expected branch prefix codex/, got: $branch_name" >&2
  exit 1
fi

echo "[test] create feat-2 (current_tree)"
feat2_out="$(bash "$harness_cli" create-feat --root "$project" --workspace-mode current_tree --title "Demo Feat 2" --slug "demo-feat-2" --goal "Validate current-tree execution")"
echo "$feat2_out"
feat2_id="$(printf '%s\n' "$feat2_out" | awk -F': ' '/^feat_id:/ {print $2}')"

if [[ -z "$feat2_id" ]]; then
  echo "[test] failed to parse feat2_id" >&2
  exit 1
fi

python3 - <<PY
import json
from pathlib import Path
p = Path(r"$project") / ".bagakit" / "ft-harness" / "feats" / r"$feat2_id" / "state.json"
data = json.loads(p.read_text())
assert data["workspace_mode"] == "current_tree", data
assert data["branch"] == "", data
assert data["worktree_path"] == "", data
PY

echo "[test] create feat-3 (proposal_only)"
feat3_out="$(bash "$harness_cli" create-feat --root "$project" --workspace-mode proposal_only --title "Demo Feat 3" --slug "demo-feat-3" --goal "Validate proposal-only flow")"
echo "$feat3_out"
feat3_id="$(printf '%s\n' "$feat3_out" | awk -F': ' '/^feat_id:/ {print $2}')"

if [[ -z "$feat3_id" ]]; then
  echo "[test] failed to parse feat3_id" >&2
  exit 1
fi

echo "[test] proposal_only blocks task start"
if bash "$harness_cli" start-task --root "$project" --feat "$feat3_id" --task T-001 >/dev/null 2>&1; then
  echo "[test] expected proposal_only feat to reject start-task" >&2
  exit 1
fi

echo "[test] assign worktree to proposal_only feat"
assign_out="$(bash "$harness_cli" assign-feat-workspace --root "$project" --feat "$feat3_id" --workspace-mode worktree)"
echo "$assign_out"
feat3_branch="$(printf '%s\n' "$assign_out" | awk -F': ' '/^branch:/ {print $2}')"
feat3_worktree="$(printf '%s\n' "$assign_out" | awk -F': ' '/^worktree:/ {print $2}')"
if [[ -z "$feat3_branch" || -z "$feat3_worktree" ]]; then
  echo "[test] failed to parse feat3 workspace assignment" >&2
  exit 1
fi
if [[ "$feat3_branch" != codex/* ]]; then
  echo "[test] expected assigned branch prefix codex/, got: $feat3_branch" >&2
  exit 1
fi

python3 - <<PY
import json
from pathlib import Path
p = Path(r"$project") / ".bagakit" / "ft-harness" / "feats" / r"$feat3_id" / "state.json"
data = json.loads(p.read_text())
assert data["workspace_mode"] == "worktree", data
assert data["branch"].startswith("codex/"), data
assert data["worktree_path"], data
PY

echo "[test] replan DAG with dependency"
bash "$harness_cli" replan-feats --root "$project" --execution-mode parallel --max-parallel 2 --dependency "${feat2_id}:${feat_id}"
bash "$harness_cli" show-feat-dag --root "$project" --json >/dev/null

echo "[test] replan DAG archive snapshot"
bash "$harness_cli" replan-feats --root "$project" --execution-mode auto --max-parallel 2 --clear-dependencies "$feat2_id"
if [[ ! -d "$project/.bagakit/ft-harness/index/archive" ]]; then
  echo "[test] DAG archive directory missing" >&2
  exit 1
fi
if [[ -z "$(find "$project/.bagakit/ft-harness/index/archive" -type f -name '*.json' -print -quit)" ]]; then
  echo "[test] expected at least one archived DAG snapshot" >&2
  exit 1
fi

echo "[test] task loop"
bash "$harness_cli" start-task --root "$project" --feat "$feat_id" --task T-001
bash "$harness_cli" run-task-gate --root "$project" --feat "$feat_id" --task T-001

# create code change in feat worktree branch
printf '\nupdate\n' >> "$worktree_path/README.md"

echo "[test] generate commit message"
commit_out="$(bash "$harness_cli" prepare-task-commit --root "$project" --feat "$feat_id" --task T-001 --summary "Implement T-001")"
echo "$commit_out"
msg_file="$(printf '%s\n' "$commit_out" | awk -F': ' '/^message_file:/ {print $2}')"

if [[ -z "$msg_file" ]]; then
  echo "[test] failed to parse message_file" >&2
  exit 1
fi

pushd "$worktree_path" >/dev/null
git add -A
git commit -q -F "$msg_file"
popd >/dev/null

bash "$harness_cli" finish-task --root "$project" --feat "$feat_id" --task T-001 --result done

echo "[test] merge feat branch into base branch"
pushd "$project" >/dev/null
git merge --no-ff -m "merge ${feat_id}" "$branch_name"
popd >/dev/null

echo "[test] archive feat + cleanup worktree"
bash "$harness_cli" archive-feat --root "$project" --feat "$feat_id"

if [[ -d "$project/.bagakit/ft-harness/feats/$feat_id" ]]; then
  echo "[test] active feat directory still exists after archive" >&2
  exit 1
fi
if [[ ! -d "$project/.bagakit/ft-harness/feats-archived/$feat_id" ]]; then
  echo "[test] archived feat directory missing" >&2
  exit 1
fi
if [[ -d "$worktree_path" ]]; then
  echo "[test] worktree directory still exists after archive" >&2
  exit 1
fi
if git -C "$project" worktree list --porcelain | grep -q "worktree $worktree_path"; then
  echo "[test] worktree registry still contains archived worktree path" >&2
  exit 1
fi
if git -C "$project" show-ref --verify --quiet "refs/heads/$branch_name"; then
  echo "[test] feat branch still exists after archive" >&2
  exit 1
fi

echo "[test] legacy config is rejected"
cp "$project/.bagakit/ft-harness/runtime-policy.json" "$project/.bagakit/ft-harness/config.json"
rm -f "$project/.bagakit/ft-harness/runtime-policy.json"
if bash "$harness_cli" validate-harness --root "$project" >/dev/null 2>&1; then
  echo "[test] expected validate-harness to fail without runtime-policy.json" >&2
  exit 1
fi
cp "$project/.bagakit/ft-harness/config.json" "$project/.bagakit/ft-harness/runtime-policy.json"
rm -f "$project/.bagakit/ft-harness/config.json"

echo "[test] validate + doctor"
bash "$harness_cli" validate-harness --root "$project"
bash "$harness_cli" diagnose-harness --root "$project"

echo "[test] query"
bash "$harness_cli" list-feats --root "$project" >/dev/null

echo "[test] pass: $skill_root"
