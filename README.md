# bagakit-feat-task-harness

A Bagakit skill implementing feat/task long-running orchestration with:

- OpenSpec-style change semantics
- one worktree per feat (`.worktrees/`)
- JSON SSOT state machine
- task-level structured commit protocol
- optional living-docs memory sync

## Install skill locally

```bash
make install-skill CODEX_HOME=~/.codex
```

Restart Codex after installation.

## Initialize in target project

```bash
export BAGAKIT_FT_SKILL_DIR="${BAGAKIT_FT_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/bagakit-feat-task-harness}"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ref_read_gate.sh" --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/apply-ft-harness.sh" --root .
```

## Core loop

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_feat_new.sh" --root . --title "Add feature" --slug "add-feature" --goal "Deliver X"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_start.sh" --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_gate.sh" --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_commit.sh" --root . --feat <feat-id> --task T-001 --summary "Implement T-001"
# run git commit with generated message
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_finish.sh" --root . --feat <feat-id> --task T-001 --result done
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_feat_close.sh" --root . --feat <feat-id>
```

## Validate

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/validate-ft-harness.sh" --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_doctor.sh" --root .
```

## OpenSpec Compatibility Helpers

```bash
# Import an existing OpenSpec change into feat/task harness
python3 "$BAGAKIT_FT_SKILL_DIR/scripts/ft_import_openspec.py" --root . --change <change-name>

# Export a feat back into openspec/changes/
python3 "$BAGAKIT_FT_SKILL_DIR/scripts/ft_export_openspec.py" --root . --feat <feat-id>
```

## Package

```bash
make package-skill
```
