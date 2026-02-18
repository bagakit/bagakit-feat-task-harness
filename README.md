# bagakit-feat-task-harness

A Bagakit skill for multi-session feat/task orchestration with:

- one worktree per feat (`.worktrees/`)
- JSON SSOT state machine
- task-level structured commit protocol
- physical archive (`feats-archived/`) on feat close
- optional OpenSpec import/export helpers
- optional living-doc memory sync

## Install skill locally

```bash
make install-skill BAGAKIT_HOME=~/.bagakit
```

Restart Bagakit Agent after installation.

## Initialize in target project

```bash
export BAGAKIT_FT_SKILL_DIR="${BAGAKIT_FT_SKILL_DIR:-${BAGAKIT_HOME:-$HOME/.bagakit}/skills/bagakit-feat-task-harness}"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" check-reference-readiness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" initialize-harness --root .
```

`check-reference-readiness` auto-detects `BAGAKIT_REFERENCE_SKILLS_HOME` from:
- `$BAGAKIT_REFERENCE_SKILLS_HOME` (if set)
- `${BAGAKIT_HOME}/skills`
- `$HOME/.bagakit/skills`

For one-shot shell invocations, pass override inline:

```bash
BAGAKIT_REFERENCE_SKILLS_HOME=/absolute/path/to/skills \
  bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" check-reference-readiness --root .
```

## Optional ref-read manifests

- Default strict gate: `references/required-reading-manifest.json`
- Optional OpenSpec profile: `references/required-reading-manifest-openspec.json`

```bash
BAGAKIT_REFERENCE_SKILLS_HOME=/absolute/path/to/skills \
  bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" check-reference-readiness --root . \
  --manifest "$BAGAKIT_FT_SKILL_DIR/references/required-reading-manifest-openspec.json"
```

When `--strict` is enabled, pass the same manifest to `initialize-harness` / `create-feat`.

## Core loop

```bash
# Create feat + worktree
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" create-feat --root . --title "Add feature" --slug "add-feature" --goal "Deliver X"

# Task execution
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" start-task --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" run-task-gate --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" prepare-task-commit --root . --feat <feat-id> --task T-001 --summary "Implement T-001"
# run git commit with generated message
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" finish-task --root . --feat <feat-id> --task T-001 --result done
```

## Archive feat (finalize)

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" archive-feat --root . --feat <feat-id>
```

`archive-feat` performs final-state archive actions:
- set status to `archived`
- move `.bagakit/ft-harness/feats/<feat-id>` -> `.bagakit/ft-harness/feats-archived/<feat-id>`
- remove feat worktree directory
- delete feat branch when merged into base branch

Guardrails:
- if feat status is `done`, the feat branch must already be merged into base branch
- worktree must be clean (no uncommitted changes)

## Validate / diagnose / query

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" validate-harness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" diagnose-harness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" list-feats --root .
```

## OpenSpec helpers (optional)

```bash
python3 "$BAGAKIT_FT_SKILL_DIR/scripts/import_openspec_change.py" --root . --change <change-name>
python3 "$BAGAKIT_FT_SKILL_DIR/scripts/export_feat_to_openspec.py" --root . --feat <feat-id>
```

## Package

```bash
make package-skill
```
