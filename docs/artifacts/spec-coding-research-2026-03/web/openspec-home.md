---
title: OpenSpec Home Summary
required: false
summary: OpenSpec positions itself as a lightweight spec-driven framework where spec deltas, proposals, and tasks live next to the code and make intent reviewable before implementation.
relation_to_skill: Highly relevant because bagakit-feat-task-harness already has proposal/tasks/spec-delta primitives and can evolve toward clearer intent review and replacement/discard flows.
source_type: official_spec_framework
source_url: https://openspec.dev/
source_date: 2026-03-22
sop:
  - Re-open this note when revisiting the source without the original web page.
  - Update this note if the local summary or relevance judgment changes materially.
---

# OpenSpec Home Summary

## Source

- URL: `https://openspec.dev/`
- Source family: OpenSpec project homepage

## Structured Summary

- OpenSpec emphasizes reviewing intent, not only code.
- It keeps specs in the repository alongside implementation code so the agent and the reviewer can reopen the same capability context later.
- Its visible artifacts are proposal, design, tasks, and spec deltas, which make it easier to review a planned change before code is written.

## Why It Matters For ft-harness

- The current feat harness already points in this direction but needs stronger lifecycle semantics around stale and superseded plans.
- This source supports preserving old feat reasoning as a repo artifact while still closing the feat explicitly.
- It also supports separating planning objects from execution environments.

