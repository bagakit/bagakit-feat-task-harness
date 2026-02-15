---
name: bagakit-feat-task-harness
description: Build and run a feat/task long-running harness with OpenSpec-style change semantics, per-feat git worktree isolation, JSON SSOT state transitions, strict task-level commit protocol, and optional Bagakit living-doc memory sync. Use when work spans multiple sessions, requires auditable small commits, or needs deterministic orchestration without an SDK runner.
---

# Bagakit Feat Task Harness

## Overview

Use this skill for long-running engineering work that needs strict orchestration and high traceability.

This skill enforces:
- two-level planning (`feat` -> `task`)
- one worktree per feat (`.worktrees/`)
- JSON single source of truth (SSOT)
- task-level structured commits (`Plan/Check/Learn` + trailers)
- deterministic script-driven transitions (no ad-hoc state edits)

## Workflow

1) Generate reference-read report (strict gate)

```bash
export BAGAKIT_FT_SKILL_DIR="${BAGAKIT_FT_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/bagakit-feat-task-harness}"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ref_read_gate.sh" --root .
```

2) Apply harness files into project

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/apply-ft-harness.sh" --root .
```

3) Create a feat (+ branch + worktree)

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_feat_new.sh" --root . --title "<feat-title>" --slug "<feat-slug>" --goal "<goal>"
```

4) Execute task loop

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_start.sh" --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_gate.sh" --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_commit.sh" --root . --feat <feat-id> --task T-001 --summary "<summary>"
# run git commit manually using generated message path (or pass --execute)
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_task_finish.sh" --root . --feat <feat-id> --task T-001 --result done
```

5) Close feat

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_feat_close.sh" --root . --feat <feat-id>
```

6) Validate and diagnose

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/validate-ft-harness.sh" --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/ft_doctor.sh" --root .
```

## Public Commands

- `apply-ft-harness.sh`
- `ft_feat_new.sh`
- `ft_feat_status.sh`
- `ft_task_start.sh`
- `ft_task_gate.sh`
- `ft_task_commit.sh`
- `ft_task_finish.sh`
- `ft_feat_close.sh`
- `validate-ft-harness.sh`
- `ft_doctor.sh`
- `ft_query.py`
- `ref_read_gate.sh`
- `ft_import_openspec.py`
- `ft_export_openspec.py`

## JSON SSOT Model

Runtime state is stored under `.bagakit-ft/`:
- `.bagakit-ft/index/feats.json`
- `.bagakit-ft/feats/<feat-id>/state.json`
- `.bagakit-ft/feats/<feat-id>/tasks.json`

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
- Non-UI projects: run configured or auto-detected test command(s); at least one command must execute successfully.

Gate outcomes are written into task/state JSON and used by doctor thresholds.

## Living Docs Soft Integration

If living docs are detected (`docs/must-*.md` + `docs/.bagakit/`), feat close writes inbox summaries:
- `decision-<feat-id>.md`
- `gotcha-<feat-id>.md` (when blocked or repeated failures)
- `howto-<feat-id>-result.md`

If not detected, workflow continues without memory sync.
