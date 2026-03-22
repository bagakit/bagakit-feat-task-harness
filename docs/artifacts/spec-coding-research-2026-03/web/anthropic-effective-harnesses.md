---
title: Anthropic Effective Harnesses For Long-Running Agents
required: false
summary: Anthropic recommends initializer plus coding-agent handoff, structured progress artifacts, and leaving every session in a clean state so long-running work can resume across context windows.
relation_to_skill: This is one of the closest external matches to bagakit-feat-task-harness, especially for activation flow, progress carry-forward, and explicit stale-feat closure.
source_type: official_article
source_url: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
source_date: 2025-11-26
sop:
  - Re-open this note when revisiting the source without the original web page.
  - Update this note if the local summary or relevance judgment changes materially.
---

# Anthropic Effective Harnesses For Long-Running Agents

## Source

- URL: `https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents`
- Source family: Anthropic engineering article

## Structured Summary

- Long-running agents work across multiple context windows and need durable handoff artifacts rather than implicit model memory.
- Anthropic recommends a first-run initializer plus later coding-agent sessions that make incremental progress and leave structured updates.
- The clean-state requirement is important: each session should end in a state another engineer or another agent can continue from.

## Why It Matters For ft-harness

- It supports explicit activation of a feat into an execution environment rather than allocating everything at creation time.
- It supports progress logs, summaries, and explicit replacement/discard semantics for stale plans.
- It also supports doctor-style rules that detect feats which are open but no longer in a clean, resumable state.

