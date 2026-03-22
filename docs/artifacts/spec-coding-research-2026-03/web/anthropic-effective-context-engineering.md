---
title: Anthropic Effective Context Engineering
required: false
summary: Anthropic reframes prompt engineering as context engineering, where the finite context budget must be actively curated, refreshed, and structured for reliable agent behavior.
relation_to_skill: Relevant because bagakit-feat-task-harness uses docs, proposals, and state files as context objects; this source supports shorter maps plus deeper modular documents instead of monolithic instructions.
source_type: official_article
source_url: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
source_date: 2025-09-29
sop:
  - Re-open this note when revisiting the source without the original web page.
  - Update this note if the local summary or relevance judgment changes materially.
---

# Anthropic Effective Context Engineering

## Source

- URL: `https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents`
- Source family: Anthropic engineering article

## Structured Summary

- The article treats context as a finite engineering resource rather than a passive prompt dump.
- The practical advice is to curate, stage, and maintain context so the model sees the right artifacts at the right time.
- It favors modular, task-relevant context over giant universal instruction blobs.

## Why It Matters For ft-harness

- It supports keeping `AGENTS.md` short and feat artifacts focused.
- It supports proposal-first flow because many feats are not yet worth expanding into heavy execution context.
- It also supports explicit stale cleanup so dead context does not crowd active work.

