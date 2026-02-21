---
name: bagakit-feat-task-harness
description: Build and run a feat/task long-running harness with per-feat worktree isolation, JSON SSOT transitions, strict task-level commit protocol, physical feat archive, and optional adapter contracts. Use when engineering delivery needs deterministic orchestration and traceability.
---

# Bagakit Feat Task Harness

## Standalone-First Contract

- This skill is standalone-first: core feat/task orchestration works without other skills.
- Cross-skill integration is optional and contract/signal based (for example optional OpenSpec import/export adapters).
- Runtime state transitions must be script-driven from this skill, not manual edits.

## When to Use

- You need deterministic feat/task lifecycle with strict JSON SSOT.
- You need one isolated worktree per feat and explicit archive cleanup.
- You need structured commit protocol and gate evidence for long-running delivery.

## When NOT to Use

- The change is tiny and does not need feat/task orchestration overhead.
- You only need docs/memory workflow and no worktree/state machine.
- You require hard coupling to a specific external skill flow as mandatory behavior.

## Overview

Use this skill for long-running engineering work that needs deterministic orchestration and traceability.

This skill enforces:
- two-level planning (`feat` -> `task`)
- one worktree per feat (`.worktrees/`)
- JSON single source of truth (SSOT)
- task-level structured commits (`Plan/Check/Learn` + trailers)
- script-driven transitions only (no manual state edits)

Repository reference layout:
- `references/tpl/`: scaffolding templates used by runtime scripts
- `references/`: non-template references (for example required-reading manifests)

## Workflow

1) Generate reference-read report (strict gate)

```bash
export BAGAKIT_FT_SKILL_DIR="${BAGAKIT_FT_SKILL_DIR:-${BAGAKIT_HOME:-$HOME/.bagakit}/skills/bagakit-feat-task-harness}"
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" check-reference-readiness --root .
```

Default manifest is local harness-only:
- `references/required-reading-manifest.json`

Optional OpenSpec profile:

```bash
BAGAKIT_REFERENCE_SKILLS_HOME="${BAGAKIT_REFERENCE_SKILLS_HOME:-$HOME/.bagakit/skills}" \
  bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" check-reference-readiness --root . \
  --manifest "$BAGAKIT_FT_SKILL_DIR/references/required-reading-manifest-openspec.json"
```

`check-reference-readiness` auto-detects `BAGAKIT_REFERENCE_SKILLS_HOME` from:
- `$BAGAKIT_REFERENCE_SKILLS_HOME` (if set)
- `${BAGAKIT_HOME}/skills`
- `$HOME/.bagakit/skills`

Standalone policy for ref-read:
- default manifest must not require any external/prebuilt skills
- external skill references are allowed only in explicit opt-in manifests

2) Initialize harness files into project

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" initialize-harness --root .
```

3) Create feat (+ branch + worktree)

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" create-feat --root . --title "<feat-title>" --slug "<feat-slug>" --goal "<goal>"
```

4) Execute task loop

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" start-task --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" run-task-gate --root . --feat <feat-id> --task T-001
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" prepare-task-commit --root . --feat <feat-id> --task T-001 --summary "<summary>"
# run git commit manually using generated message path (or pass --execute)
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" finish-task --root . --feat <feat-id> --task T-001 --result done
```

5) Archive feat (finalize)

```bash
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" archive-feat --root . --feat <feat-id>
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
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" validate-harness --root .
bash "$BAGAKIT_FT_SKILL_DIR/scripts/feat-task-harness.sh" diagnose-harness --root .
```

## Public Commands

- `feat-task-harness.sh check-reference-readiness`
- `feat-task-harness.sh validate-reference-report`
- `feat-task-harness.sh initialize-harness`
- `feat-task-harness.sh create-feat`
- `feat-task-harness.sh show-feat-status`
- `feat-task-harness.sh start-task`
- `feat-task-harness.sh run-task-gate`
- `feat-task-harness.sh prepare-task-commit`
- `feat-task-harness.sh finish-task`
- `feat-task-harness.sh archive-feat`
- `feat-task-harness.sh validate-harness`
- `feat-task-harness.sh diagnose-harness`
- `feat-task-harness.sh list-feats`
- `feat-task-harness.sh get-feat`
- `feat-task-harness.sh filter-feats`
- `import-openspec-change.py`
- `export-feat-to-openspec.py`

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

## Output Routes and Default Mode

- Deliverable type: process-driver execution harness with deterministic task execution outputs.
- Action handoff output (default route): feat/task status progression in `.bagakit/ft-harness/` plus operator next command from harness scripts.
- Memory handoff output (default route): feat summary artifacts under `.bagakit/ft-harness/feats-archived/<feat-id>/summary.md`.
- Optional adapter route: when living-docs signal is available, sync summary notes into `docs/.bagakit/inbox/` using optional contract behavior.
- Adapter policy: optional routes only; core workflow remains standalone-first with no mandatory external system.

## Archive Gate (Completion Handoff)

- Archive completion requires explicit destination evidence for `action_handoff` (archived feat status + paths) and `memory_handoff` (summary destination path, or explicit `none` rationale).
- Do not mark completion until archive command succeeds, destination path/id is written, and cleanup checks (worktree/branch guardrails) are verified.

## `[[BAGAKIT]]` Footer Contract

```text
[[BAGAKIT]]
- FTHarness: Feat=<feat-id>; Task=<task-id|none>; Status=<in_progress|done|blocked|archived>; Evidence=<gate/commit/archive checks>; Next=<one deterministic command>
```

## Fallback Path

- If reference readiness or task gates fail, stop transition, report blocker evidence, and continue only after an explicit recovery plan is recorded.
