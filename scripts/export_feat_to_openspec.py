#!/usr/bin/env python3
"""Export a feat into OpenSpec change structure."""

from __future__ import annotations

import argparse
from pathlib import Path

from feat_task_harness import HarnessPaths, load_feat, slugify, utc_now


def main() -> int:
    p = argparse.ArgumentParser(description="Export feat to OpenSpec change directory")
    p.add_argument("--root", default=".")
    p.add_argument("--feat", required=True)
    p.add_argument("--change-name", default="")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    if not paths.harness_dir.exists():
        raise SystemExit(
            "error: harness missing. run feat_task_harness.sh initialize-harness first"
        )

    state, tasks = load_feat(paths, args.feat)
    feat_dir = paths.feat_dir(args.feat, status=str(state.get("status") or ""))
    change_name = args.change_name.strip() or slugify(args.feat)
    change_dir = root / "openspec" / "changes" / change_name

    if change_dir.exists() and not args.overwrite:
        raise SystemExit(f"error: target change already exists: {change_dir} (use --overwrite)")

    (change_dir / "specs").mkdir(parents=True, exist_ok=True)

    # proposal
    proposal_src = feat_dir / "proposal.md"
    proposal_dst = change_dir / "proposal.md"
    if proposal_src.exists():
        proposal_dst.write_text(proposal_src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        proposal_dst.write_text(f"# Exported Proposal\n\nFrom feat {args.feat}\n", encoding="utf-8")

    # tasks
    lines = [f"# Implementation Tasks ({args.feat})", ""]
    for task in tasks.get("tasks", []):
        checked = "x" if task.get("status") == "done" else " "
        lines.append(f"- [{checked}] {task.get('title', task.get('id', 'task'))}")
    lines.append("")
    lines.append(f"<!-- Exported at {utc_now()} -->")
    (change_dir / "tasks.md").write_text("\n".join(lines), encoding="utf-8")

    # spec-deltas -> specs/<cap>/spec.md
    spec_delta_dir = feat_dir / "spec-deltas"
    if spec_delta_dir.exists():
        for src in spec_delta_dir.glob("*.md"):
            cap = slugify(src.stem)
            cap_dir = change_dir / "specs" / cap
            cap_dir.mkdir(parents=True, exist_ok=True)
            (cap_dir / "spec.md").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"ok: exported {args.feat} -> openspec/changes/{change_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
