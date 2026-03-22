---
title: Spec-Coding Lifecycle Research (2026-03)
required: false
summary: A research-backed review of how recent spec-coding and long-running-agent practices should change feat lifecycle, workspace defaults, and stale-plan cleanup in bagakit-feat-task-harness.
relation_to_skill: This note is a design input for the next version of bagakit-feat-task-harness, especially around proposal-only defaults, discard/supersede flow, and doctor/DAG semantics.
sop:
  - Read this doc before redesigning feat lifecycle, workspace defaults, discard flow, or stale-feat handling.
  - Update this doc when the external research set or design recommendation changes materially.
  - Regenerate must-sop.md after updating this doc.
---

# Spec Coding / Long-Running Agent Research and Harness Review

Research snapshot date: 2026-03-22

Attachment bundle:
- `docs/artifacts/spec-coding-research-2026-03/`

Reference index:
- `docs/notes-spec-coding-reference-bundle-2026-03.md`

## Scope

This note answers one concrete question:

- For `bagakit-feat-task-harness`, what do recent papers and official agent/spec-coding practices imply about feat lifecycle, workspace defaults, stale-plan cleanup, and discard/supersede flows?

The target reader is the maintainer who is about to change:

- feat state machine
- workspace assignment policy
- doctor / stale detection
- archive / discard / supersede workflow

## Executive Judgment

- The current harness is already strong on execution discipline: JSON SSOT, explicit gates, commit protocol, physical archive, and workspace separation are all useful building blocks.
- The weak point is lifecycle modeling rather than task execution. The system has no first-class answer for "this feat is no longer the right plan, but its artifacts still matter".
- Recent long-running-agent practice converges on the same pattern: keep plans/specs as living repo artifacts, delay heavy environment setup until execution is real, and run explicit garbage collection on stale artifacts.
- Recent spec-grounding research supports adding more structure, not less. But it also warns against over-trusting free-form LLM judgments about whether code satisfies natural-language requirements.
- For this repo, the strongest near-term design move is: default new feats to `proposal_only`, add `discard` / `supersede` close outcomes, and teach doctor / DAG / next-step output to treat `done` as "implemented but not closed", not as "fully complete".

## What Frontier Practice Actually Says

## Start simple, delay heavy orchestration

Anthropic's "Building effective agents" argues that the most successful teams use simple, composable patterns rather than complex frameworks. OpenAI's practical guide to building agents makes a similar point from the product side: start from a narrow workflow, add tools and guardrails, and only pay the complexity cost when the workflow genuinely needs it.

For this repo, that directly pushes against "create feat => immediately create dedicated worktree" as the default. A worktree is an execution isolation mechanism. It is not free:

- branch and worktree cleanup become mandatory
- archive becomes coupled to merge state
- tentative ideas now allocate real execution resources
- stale ideas create stale worktrees

The frontier pattern is to keep planning light until real execution starts.

## Long-running agents need carry-forward artifacts

Anthropic's "Effective harnesses for long-running agents" is explicit that long-running agents do not persist memory across context windows. Their answer is not "hope the model remembers". Their answer is:

- initialize the environment explicitly
- make each session leave clean structured artifacts
- make the next session start from those artifacts

OpenAI's "Harness engineering" reaches the same conclusion from a different direction:

- repository knowledge becomes the system of record
- `AGENTS.md` should be a map, not an encyclopedia
- stale docs require explicit garbage collection

OpenAI's `PLANS.md` / ExecPlans guidance goes one step further:

- plans are living documents
- decision log is mandatory
- the plan must be restartable from the repo artifact alone

Implication for this repo:

- feat closure must be explicit
- stale feats need explicit disposal semantics
- "we might still want the old reasoning as reference" is not an argument for leaving a stale feat open forever

The right move is to preserve the artifact while closing the lifecycle.

## Specs should be reviewable before code, and remain co-located

OpenSpec pushes "review intent, not just code". OpenAI's ExecPlans and harness article also treat design/plans as repo-local and continuously revised. The consistent pattern is:

- put the plan/spec next to the code
- make design changes reviewable before implementation
- update the plan as discoveries happen

This matches ft-harness in spirit, but the current implementation stops short in two places:

- feat state is not modeled as revisable/supersedable lifecycle state
- the plan object is still too tightly coupled to execution environment allocation

## Verification needs structure, not only prose

The paper set is unusually consistent here:

- `SWE-agent` shows that interface design matters a lot for coding-agent performance.
- `Agentless` shows a simple, interpretable three-stage pipeline can beat more elaborate agent stacks.
- `SGCR` shows specification-grounding can materially improve adoption and trust in code review.
- `Uncovering Systematic Failures of LLMs in Verifying Code Against Natural Language Specifications` shows LLMs systematically misjudge requirement satisfaction when the spec is only natural language.
- `SLD-Spec` and the `VeriCoding` benchmark both reinforce the value of more structured specification workflows.

The conclusion is not "drop deterministic checks and let the agent decide". It is the opposite:

- keep deterministic state transitions
- keep explicit gates
- keep review artifacts
- add spec-grounding where possible
- do not assume free-form LLM review is enough to decide closure or correctness

## Current Implementation Review

## What is already good

- `scripts/feat-task-harness.py` keeps runtime state in JSON SSOT under `.bagakit/ft-harness/`.
- `archive-feat` is physical, not cosmetic: it moves the feat directory, cleans worktrees, and writes a summary.
- `proposal_only`, `current_tree`, and `worktree` are already separated in the model.
- task gate and commit protocol are deterministic rather than chat-state-based.

These are strong foundations. The problem is not lack of structure. The problem is missing lifecycle states above that structure.

## Where the model is currently too weak

### 1. No discardable close outcome

The feat status set is currently:

- `proposal`
- `ready`
- `in_progress`
- `blocked`
- `done`
- `archived`

Source:

- `scripts/feat-task-harness.py:24`

There is no status for:

- stale
- cancelled
- superseded
- explicitly discarded while still worth keeping as reference

That forces stale feats into the wrong buckets:

- left open forever
- marked `blocked` and never revisited
- marked `done` even when the final plan moved elsewhere

### 2. Default workspace is still `worktree`

The default runtime policy template still sets:

- `workspace.default_mode = "worktree"`

Source:

- `references/tpl/runtime-policy-template.json`
- `scripts/feat-task-harness.py:253-261`

This means a tentative planning object allocates execution resources too early.

### 3. `proposal_only` is a hard stop, not a guided transition

`start-task` currently rejects `proposal_only` feats and tells the operator to manually assign a workspace first.

Source:

- `scripts/feat-task-harness.py:1089-1100`

What is missing is the recommendation layer:

- tree is clean => recommend `current_tree`
- tree is dirty or parallel work is active => recommend `worktree`
- feat is still exploratory => keep `proposal_only`

### 4. `done` is treated as completed by the DAG

`feat_is_completed` currently returns true for both `done` and `archived`.

Source:

- `scripts/feat-task-harness.py:2069-2070`

That is the wrong semantic merge. `done` means "implementation claims to be finished". `archived` means "the lifecycle has been closed and cleaned up". These are different.

### 5. Doctor does not warn on stale or half-closed feats

`diagnose-harness` checks:

- gate fail streak
- no progress rounds
- round count
- in-progress mismatch
- archived summary existence

It does not check:

- `done` but not closed
- old `proposal` / `ready` feats with no activity
- worktree assigned but never executed
- `blocked` feats that should be discarded or superseded
- configured session age thresholds

Sources:

- `scripts/feat-task-harness.py:1988-2037`
- `references/tpl/runtime-policy-template.json` contains `max_session_minutes`, but there is no active consumer for it in the Python implementation.

### 6. The code/document contract is inconsistent about completion

The skill doc says do not mark completion until archive succeeds. The implementation of `finish-task` does not emit a deterministic next-step command and does not enforce the close-out hop.

Sources:

- `SKILL.md` "Archive Gate (Completion Handoff)"
- `scripts/feat-task-harness.py:1487-1529`

This is a large reason why "feat is done but not archived" happens in practice.

## Research-to-Design Mapping

## Design principle 1: a feat is a planning object first

Recommended default:

- `create-feat` should default to `proposal_only`

Rationale:

- aligned with simple-first agent practice
- aligned with long-running harness practice
- reduces accidental resource allocation
- matches real product behavior: many ideas never enter execution

## Design principle 2: execution environment is assigned only at activation time

Recommended workflow:

1. `create-feat` registers the planning object only.
2. `activate-feat` or enhanced `start-task` decides execution mode.
3. The command recommends:
   - `current_tree` if the tree is clean and the change is single-threaded
   - `worktree` if the tree is dirty, high-risk, or parallelized
   - `proposal_only` if the feat is still not ready

The system should recommend. It should not silently pre-allocate.

## Design principle 3: close outcome must be explicit

The current single `status` field is overloaded. The cleanest model is to split:

- `execution_status`: `proposal|ready|in_progress|blocked|implemented`
- `close_outcome`: `open|archived|discarded`

If a minimal migration is preferred, at least add:

- `discarded`
- `discard_reason`
- `replacement_feat_id`
- `discarded_at`

Recommended discard reasons:

- `stale`
- `superseded`
- `cancelled`
- `invalid`

## Design principle 4: stale plans should be preserved as artifacts, not preserved as open work

The right behavior for a stale feat is not deletion. It is:

- close the lifecycle
- preserve summary and references
- link to its replacement when applicable

That means adding:

- `discard-feat --reason <...> [--replacement <feat-id>]`
- `supersede-feat --feat <old> --replacement <new>`

Archive and discard should be siblings, not hacks on top of `blocked`.

## Design principle 5: garbage collection must be visible

OpenAI's harness article is explicit about doc gardening and garbage collection. For this repo, `doctor` should surface at least these warnings:

- feat in `done` for too long without archive or discard
- feat in `proposal` / `ready` with no activity beyond threshold
- feat in `blocked` beyond threshold
- worktree assigned but no task ever started
- stale replacement chain missing explicit `replacement_feat_id`

This repo already has the right instinct in `max_session_minutes`; it just has not wired the signal into the doctor flow yet.

## Concrete Recommendation for This Repo

## Recommended target model

Near-term target:

- default `create-feat` => `proposal_only`
- add explicit discard flow
- add supersede flow
- stop treating `done` as DAG-complete
- add doctor warnings for stale open feats
- emit deterministic `next:` from `finish-task`

## Suggested command surface

Minimal version:

- `create-feat`
- `assign-feat-workspace`
- `start-task`
- `finish-task`
- `archive-feat`
- `discard-feat`
- `supersede-feat`

Cleaner version:

- `create-feat`
- `activate-feat`
- `finish-task`
- `close-feat --outcome archived|discarded`
- `supersede-feat`

## Suggested rollout order

1. Change default workspace mode to `proposal_only`.
2. Add `discard-feat`.
3. Add doctor warnings for stale feats and `done but open`.
4. Split DAG "implementation complete" from lifecycle "closed".
5. Add `supersede-feat` and replacement tracking.

This order delivers the largest user-facing improvement earliest without requiring a full state-model rewrite on day one.

## Recommended Non-Goals

- Do not auto-create worktrees for every tentative feat.
- Do not use `blocked` as a dumping ground for stale plans.
- Do not rely on LLM free-form reasoning alone to decide whether a feat is safe to close.
- Do not treat archive as the only close path. Some feats should end in discard, not archive.

## Bottom Line

The most important design correction is conceptual:

- a feat is not the same thing as a worktree
- implemented is not the same thing as closed
- preserved for reference is not the same thing as kept open

Once those three distinctions are made explicit in the state model and CLI, the recurring problems around stale feats, over-eager worktree creation, and missing archive cleanup become much easier to solve.

## Related Files

- Current implementation: `scripts/feat-task-harness.py`
- Runtime policy template: `references/tpl/runtime-policy-template.json`
- Current requirements: `docs/notes-requirements.md`
- Reference bundle: `docs/notes-spec-coding-reference-bundle-2026-03.md`
