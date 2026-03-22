---
title: OpenAI Harness Engineering
required: false
summary: OpenAI treats repository knowledge as the system of record, uses isolated worktrees for execution rather than default planning, and explicitly runs garbage collection on stale docs and patterns.
relation_to_skill: Directly relevant to bagakit-feat-task-harness because it supports repo-local feat artifacts, explicit cleanup, and on-demand isolation instead of default worktree allocation.
source_type: official_article
source_url: https://openai.com/index/harness-engineering/
source_date: 2026-02-11
sop:
  - Re-open this note when revisiting the source without the original web page.
  - Update this note if the local summary or relevance judgment changes materially.
---

# OpenAI Harness Engineering

## Source

- URL: `https://openai.com/index/harness-engineering/`
- Source family: OpenAI engineering article

## Structured Summary

- The article describes an "agent-first" repository where Codex writes all code, but humans shape the harness, docs, and feedback loops.
- The repository knowledge base lives in structured `docs/`; `AGENTS.md` is a map rather than a giant instruction blob.
- Worktrees are used as isolated execution environments for concrete changes. The examples are about per-change execution, debugging, observability, and validation, not about pre-allocating worktrees for every idea.
- OpenAI explicitly calls out entropy and garbage collection: stale docs and bad patterns need continuous cleanup instead of passive accumulation.

## Why It Matters For ft-harness

- It supports making feat docs and summaries the durable system of record.
- It supports keeping `worktree` as an execution tool, not the default lifecycle starting point.
- It strongly supports adding doctor rules for stale feats, stale docs, and "done but not closed" states.

