---
title: OpenAI Codex Exec Plans
required: false
summary: OpenAI presents PLANS.md / ExecPlans as living documents that must stay self-contained, carry a decision log, and remain restartable from repo state alone.
relation_to_skill: Strongly relevant because bagakit-feat-task-harness already has feat proposal/tasks/spec artifacts; this source argues those artifacts should stay revisable and restartable across long sessions.
source_type: official_article
source_url: https://developers.openai.com/cookbook/articles/codex_exec_plans
source_date: 2025-10-07
sop:
  - Re-open this note when revisiting the source without the original web page.
  - Update this note if the local summary or relevance judgment changes materially.
---

# OpenAI Codex Exec Plans

## Source

- URL: `https://developers.openai.com/cookbook/articles/codex_exec_plans`
- Source family: OpenAI Cookbook

## Structured Summary

- ExecPlans are not static checklists. They are living documents that must be revised as work progresses.
- A plan should include decision log, progress, discoveries, and retrospective state.
- The plan should be self-contained enough that work can restart from the repo artifact alone, without hidden chat context.

## Why It Matters For ft-harness

- Feat proposals should be treated as living execution artifacts rather than one-shot scaffolding.
- "Old but useful" feats should not stay open forever; they should be closed explicitly and left behind as readable history.
- This source supports adding discard/supersede metadata instead of relying on vague open states.

