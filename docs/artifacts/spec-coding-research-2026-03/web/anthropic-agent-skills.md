---
title: Anthropic Agent Skills
required: false
summary: Anthropic presents modular skills as reusable, task-specific capability bundles that reduce monolithic prompts and improve agent reliability on real-world tasks.
relation_to_skill: Relevant because bagakit-feat-task-harness is itself a skill; this source supports making lifecycle rules, workspace heuristics, and close-out behavior explicit and modular rather than hidden in one large control prompt.
source_type: official_article
source_url: https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills
source_date: 2025-10-16
sop:
  - Re-open this note when revisiting the source without the original web page.
  - Update this note if the local summary or relevance judgment changes materially.
---

# Anthropic Agent Skills

## Source

- URL: `https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills`
- Source family: Anthropic / Claude article

## Structured Summary

- The article argues for packaging reusable capability patterns into modular skills rather than relying on one giant prompt.
- Skills make behavior more inspectable, more specialized, and easier to maintain as the system grows.
- The overall direction is progressive disclosure: load the minimum capability set needed for the current task.

## Why It Matters For ft-harness

- ft-harness is already a skill, so its lifecycle and workspace behavior should be explicit, inspectable, and versioned.
- This source supports separating feat-planning behavior from feat-execution behavior instead of binding them together by default.
- It also supports adding discard/supersede flows as named, documented lifecycle operations rather than informal operator conventions.
