---
title: Bagakit Feat Task Harness - Requirements
required: true
sop:
  - Read this doc before changing strict gates, manifests, or external integration helpers.
  - Update this doc when adding/removing integration profiles (for example OpenSpec).
  - After updates, run `./scripts_dev/test.sh`.
---

# Requirements

## Compatibility, Not Dependency

- Bagakit core must not hard-depend on external workflow systems (for example OpenSpec).
- External ecosystems are supported via explicit, opt-in adapters:
  - optional manifests (ref-read profiles)
  - optional import/export helpers

## Strict Ref-Read Gate Policy

- Default strict gate uses: `references/required-reading-manifest.json`
  - local ft-harness references only
  - no required external/prebuilt skills
  - no required URL entries
- OpenSpec workflows are opt-in via: `references/required-reading-manifest-openspec.json`
  - local-skill checks only (no required remote URL fetch)

## Enforced By

- `scripts_dev/test.sh` audits the default manifest and the optional OpenSpec manifest contract.

## Runtime Policy Naming

- Required runtime policy file is `.bagakit/ft-harness/runtime-policy.json`.
- Backward compatibility for legacy `.bagakit/ft-harness/config.json` is intentionally disabled.
- Existing projects must migrate manually by comparing current `SKILL.md` and updating local runtime files.
- Runtime policy must define the final-version workspace contract:
  - `git.branch_prefix` for dedicated feat branches
  - `workspace.default_mode` in `worktree|current_tree|proposal_only`
  - `lifecycle.*_stale_days` and `lifecycle.done_close_due_days` for doctor warnings

## Workspace Contract

- Every feat state must declare `workspace_mode`.
- `worktree` mode owns a dedicated branch + `.worktrees/` entry.
- `current_tree` mode runs in the repository root and must not track dedicated worktree fields.
- `proposal_only` is planning-only and must be assigned before `start-task`.
- Default workspace mode should remain lightweight (`proposal_only`) so speculative feats do not allocate worktrees by default.
- `doctor` must warn on stale `proposal`, `ready`, `in_progress`, `blocked`, and unclosed `done` feats via lifecycle thresholds.

## Close Contract

- Feats may close as `archived` or `discarded`.
- `archived` means the feat was intentionally retained as a completed/closed result.
- `discarded` means the feat is closed but preserved as a reference because it became stale, invalid, or superseded.
- `done` is not a final close outcome; doctor should warn if a feat stays `done` without being archived or discarded.
- `discard-feat` on a dirty worktree must preserve unstaged diff, staged diff, and untracked files before forcing worktree removal.

## Feat DAG Snapshot Contract

- Current DAG SSOT lives at `.bagakit/ft-harness/index/FEATS_DAG.json`.
- Every explicit replan must archive the previous DAG snapshot to:
  - `.bagakit/ft-harness/index/archive/<ts>.json`
