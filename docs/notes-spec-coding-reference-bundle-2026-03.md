---
title: Spec-Coding Reference Bundle (2026-03)
required: false
summary: An indexed source bundle for the spec-coding / long-running-agent review, with paper attachments and normalized markdown notes for official web sources.
relation_to_skill: This is the evidence pack behind lifecycle and workspace recommendations for bagakit-feat-task-harness; it keeps the external source set reopenable without repeating web research.
sop:
  - Read this doc when you need the source set behind the lifecycle/design conclusions in `notes-spec-coding-lifecycle-research-2026-03.md`.
  - Update this doc when the source bundle, local attachments, or source summaries change materially.
  - Regenerate must-sop.md after updating this doc.
---

# Spec Coding Reference Bundle

Research snapshot date: 2026-03-22

Local bundle root:

- `docs/artifacts/spec-coding-research-2026-03/`

Conventions in this document:

- For papers, the "摘要" below is a local paraphrase of the paper abstract plus the specific reason it matters here.
- For official blog/spec pages, the "摘要" is a local summary written from the downloaded snapshot.
- Every item below has a local attachment path so the research can be re-opened without re-searching the web.
- Legacy raw web snapshots are not part of the reading path anymore. One leftover PDF was moved to `_unused/` only to avoid destructive deletion issues in this environment.

## Bundle Manifest

### Papers

- `docs/artifacts/spec-coding-research-2026-03/papers/2405.15793-swe-agent.pdf`
- `docs/artifacts/spec-coding-research-2026-03/papers/2407.01489-agentless.pdf`
- `docs/artifacts/spec-coding-research-2026-03/papers/2508.12358-nl-spec-verification-failures.pdf`
- `docs/artifacts/spec-coding-research-2026-03/papers/2509.09917-sld-spec.pdf`
- `docs/artifacts/spec-coding-research-2026-03/papers/2509.22908-vericoding-benchmark.pdf`
- `docs/artifacts/spec-coding-research-2026-03/papers/2512.17540-sgcr.pdf`
- `docs/artifacts/spec-coding-research-2026-03/papers/2602.02361-swe-universe.pdf`
- `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`

### Official sources / spec pages

- `docs/artifacts/spec-coding-research-2026-03/web/openai-harness-engineering.md`
- `docs/artifacts/spec-coding-research-2026-03/web/openai-codex-exec-plans.md`
- `docs/artifacts/spec-coding-research-2026-03/web/openai-practical-guide-to-building-agents.md`
- `docs/artifacts/spec-coding-research-2026-03/web/openspec-home.md`
- `docs/artifacts/spec-coding-research-2026-03/web/anthropic-building-effective-agents.md`
- `docs/artifacts/spec-coding-research-2026-03/web/anthropic-effective-harnesses.md`
- `docs/artifacts/spec-coding-research-2026-03/web/anthropic-effective-context-engineering.md`
- `docs/artifacts/spec-coding-research-2026-03/web/anthropic-agent-skills.md`

## Source Matrix

| ID | Type | Title | Date | Local attachment |
| --- | --- | --- | --- | --- |
| P1 | Paper | SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering | 2024-05-06 | `papers/2405.15793-swe-agent.pdf` |
| P2 | Paper | Agentless: Demystifying LLM-based Software Engineering Agents | 2024-07-01 | `papers/2407.01489-agentless.pdf` |
| P3 | Paper | Uncovering Systematic Failures of LLMs in Verifying Code Against Natural Language Specifications | 2025-08-17 | `papers/2508.12358-nl-spec-verification-failures.pdf` |
| P4 | Paper | Enhancing LLM-based Specification Generation via Program Slicing and Logical Deletion | 2025-09-12 | `papers/2509.09917-sld-spec.pdf` |
| P5 | Paper | A benchmark for vericoding: formally verified program synthesis | 2025-09-26 | `papers/2509.22908-vericoding-benchmark.pdf` |
| P6 | Paper | SGCR: A Specification-Grounded Framework for Trustworthy LLM Code Review | 2025-12-19 | `papers/2512.17540-sgcr.pdf` |
| P7 | Paper | SWE-Universe: Scale Real-World Verifiable Environments to Millions | 2026-02-02 | `papers/2602.02361-swe-universe.pdf` |
| O1 | Official | Harness engineering: leveraging Codex in an agent-first world | 2026-02-11 | `web/openai-harness-engineering.md` |
| O2 | Official | Using PLANS.md for multi-hour problem solving | 2025-10-07 | `web/openai-codex-exec-plans.md` |
| O3 | Official | A practical guide to building agents | 2025-04-07 PDF metadata | `web/openai-practical-guide-to-building-agents.md` |
| O4 | Official | OpenSpec - A lightweight spec-driven framework | 2026-03-22 snapshot | `web/openspec-home.md` |
| O5 | Official | Building effective agents | 2024-12-19 | `web/anthropic-building-effective-agents.md` |
| O6 | Official | Effective harnesses for long-running agents | 2025-11-26 | `web/anthropic-effective-harnesses.md` |
| O7 | Official | Effective context engineering for AI agents | 2025-09-29 | `web/anthropic-effective-context-engineering.md` |
| O8 | Official | Equipping agents for the real world with Agent Skills | 2025-10-16 | `web/anthropic-agent-skills.md` |

## Papers

### P1. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering

- Original URL: `https://arxiv.org/abs/2405.15793`
- Local attachment: `docs/artifacts/spec-coding-research-2026-03/papers/2405.15793-swe-agent.pdf`
- Metadata source: `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`
- 摘要:
  - The paper argues that coding-agent quality depends heavily on the agent-computer interface, not only on the base model.
  - Its result is a purpose-built interface for navigating repos, editing files, and running programs, which materially improves SWE task performance.
  - For ft-harness, the relevance is direct: lifecycle and workspace flows are part of the agent interface. If the interface makes stale plans and cleanup ambiguous, model quality alone will not fix it.

### P2. Agentless: Demystifying LLM-based Software Engineering Agents

- Original URL: `https://arxiv.org/abs/2407.01489`
- Local attachment: `docs/artifacts/spec-coding-research-2026-03/papers/2407.01489-agentless.pdf`
- Metadata source: `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`
- 摘要:
  - Agentless tests whether complex autonomous software agents are actually necessary, and finds that a simpler three-phase pipeline can perform surprisingly well.
  - The paper is important as a counterweight to over-engineering pressure: more autonomy and more machinery are not automatically better.
  - For ft-harness, this supports delaying `worktree` and other heavy execution mechanisms until a feat truly needs them.

### P3. Uncovering Systematic Failures of LLMs in Verifying Code Against Natural Language Specifications

- Original URL: `https://arxiv.org/abs/2508.12358`
- Local attachment: `docs/artifacts/spec-coding-research-2026-03/papers/2508.12358-nl-spec-verification-failures.pdf`
- Metadata source: `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`
- 摘要:
  - The paper shows that LLMs systematically misjudge whether code satisfies natural-language requirements.
  - More elaborate prompting can even increase misclassification rates.
  - For ft-harness, this is a warning against letting a free-form agent decide feat closure or correctness without deterministic state gates and explicit evidence.

### P4. Enhancing LLM-based Specification Generation via Program Slicing and Logical Deletion

- Original URL: `https://arxiv.org/abs/2509.09917`
- Local attachment: `docs/artifacts/spec-coding-research-2026-03/papers/2509.09917-sld-spec.pdf`
- Metadata source: `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`
- 摘要:
  - `SLD-Spec` improves specification generation by decomposing target programs into slices and filtering candidate specs with an additional logical stage.
  - The core lesson is that better spec workflows come from more structure and decomposition, not from a single opaque model pass.
  - For ft-harness, this reinforces the value of explicit proposal/tasks/spec-delta artifacts and argues against collapsing planning into chat-only state.

### P5. A benchmark for vericoding: formally verified program synthesis

- Original URL: `https://arxiv.org/abs/2509.22908`
- Local attachment: `docs/artifacts/spec-coding-research-2026-03/papers/2509.22908-vericoding-benchmark.pdf`
- Metadata source: `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`
- 摘要:
  - This benchmark separates formally specified code generation from ordinary natural-language "vibe coding".
  - It shows that strong results are possible when the target is grounded in formal specs, and that extra natural-language description does not automatically help.
  - For ft-harness, the takeaway is that structured spec artifacts are worth carrying, but they should complement rather than replace executable checks.

### P6. SGCR: A Specification-Grounded Framework for Trustworthy LLM Code Review

- Original URL: `https://arxiv.org/abs/2512.17540`
- Local attachment: `docs/artifacts/spec-coding-research-2026-03/papers/2512.17540-sgcr.pdf`
- Metadata source: `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`
- 摘要:
  - `SGCR` grounds LLM code review in human-authored specifications and combines deterministic rule enforcement with heuristic issue discovery.
  - In an industrial deployment, this substantially improved developer adoption over a baseline LLM reviewer.
  - For ft-harness, this is the strongest research support for "spec-grounding helps", but it also implies that deterministic and heuristic paths should stay separate in the design.

### P7. SWE-Universe: Scale Real-World Verifiable Environments to Millions

- Original URL: `https://arxiv.org/abs/2602.02361`
- Local attachment: `docs/artifacts/spec-coding-research-2026-03/papers/2602.02361-swe-universe.pdf`
- Metadata source: `docs/artifacts/spec-coding-research-2026-03/papers/arxiv-metadata.xml`
- 摘要:
  - SWE-Universe focuses on generating real-world, verifiable software engineering environments at scale.
  - The paper's practical relevance is the emphasis on reliable verifiers, iterative self-checks, and environment fidelity.
  - For ft-harness, this supports continued investment in explicit doctor/gate/cleanup logic and cautions against open-ended stale states that are hard to verify mechanically.

## Official sources and spec pages

### O1. OpenAI - Harness engineering: leveraging Codex in an agent-first world

- Original URL: `https://openai.com/index/harness-engineering/`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/openai-harness-engineering.md`
- 摘要:
  - OpenAI's article documents a repo where Codex writes all code, but humans invest heavily in harness design, docs, and feedback loops.
  - The most relevant sections for ft-harness are "repository knowledge as system of record", "agent legibility", per-worktree isolated environments, and "entropy and garbage collection".
  - This source is the clearest official argument that stale artifacts should be actively gardened rather than passively left to accumulate.

### O2. OpenAI Cookbook - Using PLANS.md for multi-hour problem solving

- Original URL: `https://developers.openai.com/cookbook/articles/codex_exec_plans`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/openai-codex-exec-plans.md`
- 摘要:
  - The article treats `PLANS.md` / ExecPlans as living documents that must carry decision log, progress, surprises, and retrospective state.
  - A plan should be restartable from the document alone, without hidden context.
  - For ft-harness, this is a direct push toward explicit carry-forward feat artifacts and away from keeping lifecycle-critical information only in status flags or chat history.

### O3. OpenAI - A practical guide to building agents

- Original URL: `https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/openai-practical-guide-to-building-agents.md`
- 摘要:
  - The guide gives product and engineering teams a staged way to build their first agent: start with a bounded workflow, define tools and guardrails, and only then scale complexity.
  - It frames agents as systems that control workflow execution and can stop or hand control back when needed.
  - For ft-harness, this supports defaulting new feats to a lightweight planning mode and allocating isolated execution environments only when execution really starts.

### O4. OpenSpec - A lightweight spec-driven framework

- Original URL: `https://openspec.dev/`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/openspec-home.md`
- 摘要:
  - OpenSpec emphasizes reviewing intent, not just code, and keeping specs alongside the repository as persistent context.
  - The home page highlights spec deltas, proposal/design/tasks artifacts, and repo-local capability specs that agents can reopen later.
  - For ft-harness, this is close to the intended direction: feat plans should be revisable design artifacts, not disposable scaffolding.

### O5. Anthropic - Building effective agents

- Original URL: `https://www.anthropic.com/engineering/building-effective-agents`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-building-effective-agents.md`
- 摘要:
  - Anthropic's core claim is that successful teams usually win with simple, composable patterns instead of complex frameworks.
  - It distinguishes workflows from agents and argues for restraint in when to use heavier agent structures.
  - For ft-harness, this is strong support for changing the default from `worktree` to `proposal_only` and treating worktree allocation as an explicit escalation step.

### O6. Anthropic - Effective harnesses for long-running agents

- Original URL: `https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-effective-harnesses.md`
- 摘要:
  - This article focuses on the context-window problem: long-running agents work in sessions and need artifacts that survive handoff.
  - Anthropic's answer is an initializer agent plus coding agents that leave clear structured updates and keep the environment clean.
  - For ft-harness, this maps directly to "proposal first, activation second, explicit progress artifacts, explicit close-out, no zombie feats".

### O7. Anthropic - Effective context engineering for AI agents

- Original URL: `https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-effective-context-engineering.md`
- 摘要:
  - The article reframes prompt engineering as a broader context-engineering problem: finite context must be curated and maintained intentionally.
  - The operational takeaway is that context should be selected, refreshed, and structured, not dumped wholesale into a model.
  - For ft-harness, this supports short `AGENTS.md` + deeper docs, selective feat activation, and explicit stale-artifact cleanup.

### O8. Anthropic / Claude - Equipping agents for the real world with Agent Skills

- Original URL: `https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills`
- Local note: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-agent-skills.md`
- 摘要:
  - This article argues for modular skills that package task-specific instructions and resources rather than stuffing every rule into one giant prompt.
  - The practical effect is better specialization and less monolithic context.
  - For ft-harness, the relevance is architectural: feat lifecycle guidance, workspace assignment heuristics, and close-out rules should remain explicit, modular, and inspectable rather than collapsing into one giant control document.

## Source Set Conclusions

Across papers and official practice, the shared message is stable:

- keep planning artifacts in the repo
- let plans survive across sessions
- delay heavy execution isolation until needed
- make stale plans closeable without losing reference value
- keep deterministic gates even when using more spec-grounding

That is the source base behind the recommendations in:

- `docs/notes-spec-coding-lifecycle-research-2026-03.md`
