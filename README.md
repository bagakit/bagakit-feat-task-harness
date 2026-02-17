# bagakit-feat-task-harness

A Bagakit skill implementing feat/task long-running orchestration with:

- OpenSpec-style change semantics
- one worktree per feat (`.worktrees/`)
- JSON SSOT state machine
- task-level structured commit protocol
- optional living-docs memory sync

## Install skill locally

```bash
make install-skill BAGAKIT_HOME=~/.bagakit
```

Restart Bagakit Agent after installation.

## Initialize in target project

```bash
export BAGAKIT_FT_SKILL_DIR="${BAGAKIT_FT_SKILL_DIR:-${BAGAKIT_HOME:-$HOME/.bagakit}/skills/bagakit-feat-task-harness}"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ref_read_gate.sh" --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/apply-ft-harness.sh" --root .
```

`ref_read_gate.sh` auto-detects `BAGAKIT_REFERENCE_SKILLS_HOME` from common locations (`$BAGAKIT_HOME/skills`, `$HOME/.bagakit/skills`, `$HOME/.claude/skills`, `$HOME/.codex/skills`).

For one-shot shell invocations, pass override inline:

```bash
BAGAKIT_REFERENCE_SKILLS_HOME=/absolute/path/to/skills \
  bash "$BAGAKIT_FT_SKILL_DIR/scripts/ref_read_gate.sh" --root .
```

### Optional ref-read manifests

- Default strict gate uses:
  - `references/required-reading-manifest.json`
- For OpenSpec workflows, pass the OpenSpec manifest explicitly:
  - `references/required-reading-manifest-openspec.json` (local-skill checks only; no required remote URL fetch)

```bash
BAGAKIT_REFERENCE_SKILLS_HOME=/absolute/path/to/skills \
  bash "$BAGAKIT_FT_SKILL_DIR/scripts/ref_read_gate.sh" --root . \
  --manifest "$BAGAKIT_FT_SKILL_DIR/references/required-reading-manifest-openspec.json"
```

Then pass the same `--manifest ...openspec.json` to `apply-ft-harness.sh` / `ft_feat_new.sh` when running in `--strict` mode.

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

`project_type=auto` uses rule-driven detection from `.bagakit/ft-harness/config.json` (`gate.project_type_rules`).

## OpenSpec Compatibility Helpers

These helpers are optional. The harness does not require OpenSpec unless you opt in via a manifest.

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
