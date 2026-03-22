# Project SOP

This SOP is generated from docs frontmatter. Do not edit manually.

## Update Requirements
- When a document with SOP frontmatter changes, regenerate this file and commit the result:
  - `export BAGAKIT_LIVING_DOCS_SKILL_DIR="<path-to-bagakit-living-docs-skill>"`
  - `sh "$BAGAKIT_LIVING_DOCS_SKILL_DIR/scripts/living-docs-generate-sop.sh" .`
- Add new SOP items by updating the `sop` list in the source document frontmatter.
- Keep SOP items small and actionable; use the source document for details.

## SOP Items

### Anthropic Agent Skills
Source: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-agent-skills.md`
- Re-open this note when revisiting the source without the original web page.
- Update this note if the local summary or relevance judgment changes materially.

### Anthropic Building Effective Agents
Source: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-building-effective-agents.md`
- Re-open this note when revisiting the source without the original web page.
- Update this note if the local summary or relevance judgment changes materially.

### Anthropic Effective Context Engineering
Source: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-effective-context-engineering.md`
- Re-open this note when revisiting the source without the original web page.
- Update this note if the local summary or relevance judgment changes materially.

### Anthropic Effective Harnesses For Long-Running Agents
Source: `docs/artifacts/spec-coding-research-2026-03/web/anthropic-effective-harnesses.md`
- Re-open this note when revisiting the source without the original web page.
- Update this note if the local summary or relevance judgment changes materially.

### OpenAI Codex Exec Plans
Source: `docs/artifacts/spec-coding-research-2026-03/web/openai-codex-exec-plans.md`
- Re-open this note when revisiting the source without the original web page.
- Update this note if the local summary or relevance judgment changes materially.

### OpenAI Harness Engineering
Source: `docs/artifacts/spec-coding-research-2026-03/web/openai-harness-engineering.md`
- Re-open this note when revisiting the source without the original web page.
- Update this note if the local summary or relevance judgment changes materially.

### OpenAI Practical Guide To Building Agents
Source: `docs/artifacts/spec-coding-research-2026-03/web/openai-practical-guide-to-building-agents.md`
- Re-open this note when revisiting the source without the original PDF.
- Update this note if the local summary or relevance judgment changes materially.

### OpenSpec Home Summary
Source: `docs/artifacts/spec-coding-research-2026-03/web/openspec-home.md`
- Re-open this note when revisiting the source without the original web page.
- Update this note if the local summary or relevance judgment changes materially.

### Maintaining Reusable Items (可复用项维护)
Source: `docs/norms-maintaining-reusable-items.md`
- At the start of each iteration, check whether the project needs a new reusable-items catalog for an active domain (coding/design/writing/knowledge) and create/update it.
- When introducing or updating a reusable item (component/library/mechanism/token/style pattern/index; including API/behavior/ownership/deprecation), verify the relevant catalog entry is correct and update it in the same change.
- When SOP/frontmatter changes in these docs, regenerate `docs/must-sop.md` with `sh "$BAGAKIT_LIVING_DOCS_SKILL_DIR/scripts/bagakit_generate_sop.sh" .`.

### Continuous Learning (Default)
Source: `docs/notes-continuous-learning.md`
- At the end of a Bagakit Agent work session, capture a draft learning note into `docs/.bagakit/inbox/` (manual or via `sh "$BAGAKIT_LIVING_DOCS_SKILL_DIR/scripts/bagakit_learning.sh" extract --root . --last`). The default extractor upserts into a daily file to avoid fragmentation.
- Weekly (or before major releases), review `docs/.bagakit/inbox/` and promote durable items into `docs/.bagakit/memory/`.
- When promoting, keep entries short and source-linked; prefer `decision-*`/`preference-*`/`gotcha-*`/`howto-*` over long narratives. If the curated target already exists, merge instead of creating duplicates.

### Bagakit Feat Task Harness - Requirements
Source: `docs/notes-requirements.md`
- Read this doc before changing strict gates, manifests, or external integration helpers.
- Update this doc when adding/removing integration profiles (for example OpenSpec).
- After updates, run `./scripts_dev/test.sh`.

### Spec-Coding Lifecycle Research (2026-03)
Source: `docs/notes-spec-coding-lifecycle-research-2026-03.md`
- Read this doc before redesigning feat lifecycle, workspace defaults, discard flow, or stale-feat handling.
- Update this doc when the external research set or design recommendation changes materially.
- Regenerate must-sop.md after updating this doc.

### Spec-Coding Reference Bundle (2026-03)
Source: `docs/notes-spec-coding-reference-bundle-2026-03.md`
- Read this doc when you need the source set behind the lifecycle/design conclusions in `notes-spec-coding-lifecycle-research-2026-03.md`.
- Update this doc when the source bundle, local attachments, or source summaries change materially.
- Regenerate must-sop.md after updating this doc.

