---
title: Bagakit Feat Task Harness - Requirements
required: true
sop:
  - Read this doc before changing strict gates, manifests, or external integration helpers.
  - Update this doc when adding/removing integration profiles (for example OpenSpec).
  - After updates, run `./scripts_dev/test.sh`.
---

# Requirements

## Compatibility, Not Dependency

- Bagakit core must not hard-depend on external workflow systems (for example OpenSpec).
- External ecosystems are supported via explicit, opt-in adapters:
  - optional manifests (ref-read profiles)
  - optional import/export helpers

## Strict Ref-Read Gate Policy

- Default strict gate uses: `references/required-reading-manifest.json`
  - local ft-harness references only
  - no required external/prebuilt skills
  - no required URL entries
- OpenSpec workflows are opt-in via: `references/required-reading-manifest-openspec.json`
  - local-skill checks only (no required remote URL fetch)

## Enforced By

- `scripts_dev/test.sh` audits the default manifest and the optional OpenSpec manifest contract.
