# bagakit-feat-task-harness

A Bagakit skill for multi-session feat/task orchestration with:

- explicit feat workspace modes (`worktree`, `current_tree`, `proposal_only`)
- JSON SSOT state machine
- task-level structured commit protocol
- physical archive (`feats-archived/`) and discard (`feats-discarded/`) on feat close
- optional OpenSpec import/export helpers
- optional living-doc memory sync

## Install skill locally

```bash
make install-skill
```

Restart Bagakit Agent after installation.

## Initialize in target project

```bash
export BAGAKIT_FT_SKILL_DIR="<path-to-bagakit-feat-task-harness-skill>"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" check-reference-readiness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" initialize-harness --root .
```

Default `check-reference-readiness` is local and standalone-first:
- it reads local ft-harness references from `references/required-reading-manifest.json`
- it does not require any external/prebuilt skill install

Repo convention:
- `references/tpl/`: runtime templates (feat/task scaffolding, inbox note templates)
- `references/`: non-template references (manifests, policy lists)

## Optional ref-read manifests

- Default strict gate: `references/required-reading-manifest.json` (local ft-harness docs only)
- Optional OpenSpec profile: `references/required-reading-manifest-openspec.json` (explicit opt-in)

```bash
BAGAKIT_REFERENCE_SKILLS_HOME="<path-to-installed-skills-root>" \
  bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" check-reference-readiness --root . \
  --manifest "$BAGAKIT_FT_SKILL_DIR/references/required-reading-manifest-openspec.json"
```

`BAGAKIT_REFERENCE_SKILLS_HOME` must be set explicitly for manifests that reference external skills.

When `--strict` is enabled, pass the same manifest to `initialize-harness` / `create-feat`.

Runtime policy file:
- required: `.bagakit/ft-harness/runtime-policy.json`
- `git.branch_prefix` controls worktree-mode branch names
- `workspace.default_mode` controls default feat workspace mode
- `lifecycle.*_stale_days` controls doctor warnings for stale or unclosed feats

Version policy:
- no backward compatibility shims for old runtime schema/files
- old projects must migrate manually by comparing `SKILL.md` and updating local runtime layout

## Feat DAG planning

```bash
# Recompute DAG and archive previous plan snapshot
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" replan-feats --root . --execution-mode auto --max-parallel 2

# Optional dependency override: <feat-id>:<dep1>,<dep2>
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" replan-feats --root . --dependency "<feat-id>:<dep-id>"

# Show current DAG
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" show-feat-dag --root .
```

DAG files:
- current: `.bagakit/ft-harness/index/FEATS_DAG.json`
- history snapshots: `.bagakit/ft-harness/index/archive/<ts>.json`

## Core loop

```bash
# Create feat (default is proposal_only)
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" create-feat --root . --title "Add feature" --slug "add-feature" --goal "Deliver X"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" create-feat --root . --title "Add feature" --slug "add-feature" --goal "Deliver X" --workspace-mode worktree
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" create-feat --root . --title "Dirty tree follow-up" --slug "dirty-tree-follow-up" --goal "Continue current branch work" --workspace-mode current_tree
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" create-feat --root . --title "Plan only" --slug "plan-only" --goal "Register proposal first" --workspace-mode proposal_only

# Assign workspace later for proposal_only feats
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" assign-feat-workspace --root . --feat <feat-id> --workspace-mode current_tree

# Task execution
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" start-task --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" run-task-gate --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" prepare-task-commit --root . --feat <feat-id> --task T-001 --summary "Implement T-001"
# run git commit with generated message
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" finish-task --root . --feat <feat-id> --task T-001 --result done
# if the feat becomes done, the command prints the next close step
```

## Close feat

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" archive-feat --root . --feat <feat-id>
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" discard-feat --root . --feat <feat-id> --reason stale
```

`archive-feat` performs final-state archive actions:
- set status to `archived`
- move `.bagakit/ft-harness/feats/<feat-id>` -> `.bagakit/ft-harness/feats-archived/<feat-id>`
- remove feat worktree directory + `git worktree prune` (`worktree` mode only)
- delete feat branch when merged into base branch (`worktree` mode only)

`discard-feat` performs final-state discard actions:
- set status to `discarded`
- move `.bagakit/ft-harness/feats/<feat-id>` -> `.bagakit/ft-harness/feats-discarded/<feat-id>`
- export unstaged patch, staged patch, untracked archive, and branch diff artifacts when available (`worktree` mode only)
- remove feat worktree directory + `git worktree prune` (`worktree` mode only)
- delete feat branch even when unmerged after artifact export (`worktree` mode only)

Guardrails:
- if feat status is `done` in `worktree` mode, the feat branch must already be merged into base branch
- worktree must be clean (no uncommitted changes, `worktree` mode only)
- archive fails if stale worktree registration still exists after cleanup (`worktree` mode only)
- doctor warns when a feat stays `proposal`, `ready`, `in_progress`, `blocked`, or `done` beyond lifecycle thresholds

## Validate / diagnose / query

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" validate-harness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" diagnose-harness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" list-feats --root .
```

## OpenSpec helpers (optional)

```bash
python3 "$BAGAKIT_FT_SKILL_DIR/scripts/import-openspec-change.py" --root . --change <change-name>
python3 "$BAGAKIT_FT_SKILL_DIR/scripts/export-feat-to-openspec.py" --root . --feat <feat-id>
```

## Package

```bash
make package-skill
```
