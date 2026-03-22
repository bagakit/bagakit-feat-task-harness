---
title: Anthropic Building Effective Agents
required: false
summary: Anthropic argues that successful agent implementations usually rely on simple, composable patterns rather than complex frameworks, and that teams should use heavier agent structures only when justified.
relation_to_skill: Directly relevant because it argues for changing the default feat creation path from worktree-heavy to proposal-first and activation-later.
source_type: official_article
source_url: https://www.anthropic.com/engineering/building-effective-agents
source_date: 2024-12-19
sop:
  - Re-open this note when revisiting the source without the original web page.
  - Update this note if the local summary or relevance judgment changes materially.
---

# Anthropic Building Effective Agents

## Source

- URL: `https://www.anthropic.com/engineering/building-effective-agents`
- Source family: Anthropic engineering article

## Structured Summary

- Anthropic distinguishes workflows from agents and argues that teams should not assume full autonomy is always the right answer.
- The strongest operational theme is simplicity: use composable patterns and only add heavier machinery when it materially helps.
- The article is an argument against making the default path more complicated than the common case requires.

## Why It Matters For ft-harness

- Default `worktree` is a complexity cost. It should be justified, not automatic.
- `proposal_only` is the simpler default for the real-world case where many feats stay exploratory or get replaced.
- The source also supports keeping discard and supersede as explicit control points instead of letting stale feats linger.

