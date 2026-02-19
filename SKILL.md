---
name: bagakit-feat-task-harness
description: Build and run a feat/task long-running harness with per-feat git worktree isolation, JSON SSOT state transitions, strict task-level commit protocol, physical feat archive, and optional OpenSpec adapters.
---

# Bagakit Feat Task Harness

## Overview

Use this skill for long-running engineering work that needs deterministic orchestration and traceability.

This skill enforces:
- two-level planning (`feat` -> `task`)
- one worktree per feat (`.worktrees/`)
- JSON single source of truth (SSOT)
- task-level structured commits (`Plan/Check/Learn` + trailers)
- script-driven transitions only (no manual state edits)

## Workflow

1) Generate reference-read report (strict gate)

```bash
export BAGAKIT_FT_SKILL_DIR="${BAGAKIT_FT_SKILL_DIR:-${BAGAKIT_HOME:-$HOME/.bagakit}/skills/bagakit-feat-task-harness}"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" check-reference-readiness --root .
```

Default manifest is Bagakit-only:
- `references/required-reading-manifest.json`

Optional OpenSpec profile:

```bash
BAGAKIT_REFERENCE_SKILLS_HOME=/absolute/path/to/skills \
  bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" check-reference-readiness --root . \
  --manifest "$BAGAKIT_FT_SKILL_DIR/references/required-reading-manifest-openspec.json"
```

`check-reference-readiness` auto-detects `BAGAKIT_REFERENCE_SKILLS_HOME` from:
- `$BAGAKIT_REFERENCE_SKILLS_HOME` (if set)
- `${BAGAKIT_HOME}/skills`
- `$HOME/.bagakit/skills`

2) Initialize harness files into project

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" initialize-harness --root .
```

3) Create feat (+ branch + worktree)

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" create-feat --root . --title "<feat-title>" --slug "<feat-slug>" --goal "<goal>"
```

4) Execute task loop

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" start-task --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" run-task-gate --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" prepare-task-commit --root . --feat <feat-id> --task T-001 --summary "<summary>"
# run git commit manually using generated message path (or pass --execute)
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" finish-task --root . --feat <feat-id> --task T-001 --result done
```

5) Archive feat (finalize)

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" archive-feat --root . --feat <feat-id>
```

Archive semantics are physical + cleanup:
- move feat runtime dir into `feats-archived/`
- remove feat worktree + prune worktree registry
- delete feat branch when merged
- set feat status to `archived`

Guardrails:
- `done` feat must be merged before archive
- feat worktree must be clean before archive
- archive fails if stale worktree registration remains after cleanup

6) Validate and diagnose

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" validate-harness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat_task_harness.sh" diagnose-harness --root .
```

## Public Commands

- `feat_task_harness.sh check-reference-readiness`
- `feat_task_harness.sh validate-reference-report`
- `feat_task_harness.sh initialize-harness`
- `feat_task_harness.sh create-feat`
- `feat_task_harness.sh show-feat-status`
- `feat_task_harness.sh start-task`
- `feat_task_harness.sh run-task-gate`
- `feat_task_harness.sh prepare-task-commit`
- `feat_task_harness.sh finish-task`
- `feat_task_harness.sh archive-feat`
- `feat_task_harness.sh validate-harness`
- `feat_task_harness.sh diagnose-harness`
- `feat_task_harness.sh list-feats`
- `feat_task_harness.sh get-feat`
- `feat_task_harness.sh filter-feats`
- `import_openspec_change.py`
- `export_feat_to_openspec.py`

## JSON SSOT Model

Runtime state is stored under `.bagakit/ft-harness/`:
- `.bagakit/ft-harness/index/feats.json`
- `.bagakit/ft-harness/feats/<feat-id>/state.json` (active)
- `.bagakit/ft-harness/feats-archived/<feat-id>/state.json` (archived)
- `.bagakit/ft-harness/feats*/<feat-id>/tasks.json`

Markdown files (`proposal.md`, `tasks.md`, `spec-deltas/*.md`) are human-readable views.

## Commit Protocol

Required subject format:

`feat(<feat-id>): task(<task-id>) <summary>`

Required body sections:
- `Plan:`
- `Check:`
- `Learn:`

Required trailers:
- `Feat-ID: <feat-id>`
- `Task-ID: <task-id>`
- `Gate-Result: pass|fail`
- `Task-Status: done|blocked`

`Task-Status: done` requires `Gate-Result: pass`.

## Quality Gates

- UI projects: require browser-verification evidence file (`ui-verification.md`) and optional commands.
- Non-UI projects: run configured test command(s); at least one command must execute successfully.
- `project_type=auto` is rule-driven via `gate.project_type_rules` in `.bagakit/ft-harness/config.json`.

Gate outcomes are written into task/state JSON and used by doctor thresholds.

## Living Docs Soft Integration

If living docs are detected (`docs/must-*.md` + `docs/.bagakit/`), feat archive writes inbox summaries:
- `decision-<feat-id>.md`
- `gotcha-<feat-id>.md` (when blocked or repeated failures)
- `howto-<feat-id>-result.md`

If not detected, workflow continues without memory sync.
