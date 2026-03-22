---
title: OpenAI Practical Guide To Building Agents
required: false
summary: OpenAI recommends starting with bounded workflows, explicit tools, and guardrails, and paying orchestration complexity only when the workflow genuinely needs it.
relation_to_skill: Relevant because it argues against eager default worktree creation and in favor of lightweight planning states before execution is real.
source_type: official_guide
source_url: https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
source_date: 2025-04-07
sop:
  - Re-open this note when revisiting the source without the original PDF.
  - Update this note if the local summary or relevance judgment changes materially.
---

# OpenAI Practical Guide To Building Agents

## Source

- URL: `https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf`
- Source family: OpenAI guide PDF

## Structured Summary

- The guide defines agents as systems that manage workflow execution, use tools, and can stop or hand control back when needed.
- Its practical advice is to start from a bounded workflow, add tools and guardrails, and avoid unnecessary complexity in the first version.
- The guide treats safe stop conditions and explicit control transfer as first-class design concerns.

## Why It Matters For ft-harness

- New feats should begin as lightweight planning objects.
- Heavy execution isolation should be allocated only when execution actually starts.
- Explicit close outcomes such as archive and discard are aligned with the guide's emphasis on controlled workflow termination.

