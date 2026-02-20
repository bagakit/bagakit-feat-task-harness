#!/usr/bin/env python3
"""Import an OpenSpec change into .bagakit/ft-harness feat format."""

from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

HARNESS_PATH = Path(__file__).resolve().with_name("feat-task-harness.py")


def load_harness_runtime():
    spec = importlib.util.spec_from_file_location("feat_task_harness_runtime", HARNESS_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"error: cannot load harness runtime: {HARNESS_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load_harness_runtime()
FEAT_ID_RE = runtime.FEAT_ID_RE
HarnessPaths = runtime.HarnessPaths
ensure_git_repo = runtime.ensure_git_repo
ensure_worktrees_ignored = runtime.ensure_worktrees_ignored
pick_base_branch = runtime.pick_base_branch
run_cmd = runtime.run_cmd
save_feat = runtime.save_feat
slugify = runtime.slugify
utc_day = runtime.utc_day
utc_now = runtime.utc_now

TASK_LINE_RE = re.compile(r"^- \[( |x)\]\s*(.+)$")


def parse_tasks_md(path: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    idx = 1
    for line in path.read_text(encoding="utf-8").splitlines():
        m = TASK_LINE_RE.match(line.strip())
        if not m:
            continue
        checked, text = m.groups()
        tid = f"T-{idx:03d}"
        status = "done" if checked == "x" else "todo"
        items.append(
            {
                "id": tid,
                "title": text,
                "status": status,
                "summary": text,
                "gate_result": "pass" if status == "done" else None,
                "last_gate_at": None,
                "last_gate_commands": [],
                "last_commit_hash": None,
                "started_at": None,
                "finished_at": None,
                "updated_at": utc_now(),
                "notes": [],
            }
        )
        idx += 1
    if not items:
        items.append(
            {
                "id": "T-001",
                "title": "Imported placeholder task",
                "status": "todo",
                "summary": "No task checkbox detected in OpenSpec tasks.md",
                "gate_result": None,
                "last_gate_at": None,
                "last_gate_commands": [],
                "last_commit_hash": None,
                "started_at": None,
                "finished_at": None,
                "updated_at": utc_now(),
                "notes": [],
            }
        )
    return items


def main() -> int:
    p = argparse.ArgumentParser(description="Import OpenSpec change to feat/task harness")
    p.add_argument("--root", default=".")
    p.add_argument("--change", required=True)
    p.add_argument("--feat-id", default="")
    args = p.parse_args()

    root = Path(args.root).resolve()
    paths = HarnessPaths(root)

    change_dir = root / "openspec" / "changes" / args.change
    if not change_dir.exists():
        raise SystemExit(f"error: change not found: {change_dir}")
    ensure_git_repo(root)
    if not paths.harness_dir.exists():
        raise SystemExit(
            "error: harness missing. run feat-task-harness.sh initialize-harness first"
        )

    if args.feat_id:
        feat_id = args.feat_id
    else:
        feat_id = f"f-{utc_day()}-{slugify(args.change)}"
    if not FEAT_ID_RE.match(feat_id):
        raise SystemExit(f"error: invalid feat-id: {feat_id}")

    feat_dir = paths.feat_dir(feat_id)
    if feat_dir.exists() or paths.feat_dir(feat_id, status="archived").exists():
        raise SystemExit(f"error: feat already exists: {feat_id}")

    branch = f"feat/{feat_id}"
    wt_name = f"wt-{feat_id}"
    wt_rel = Path(".worktrees") / wt_name
    wt_abs = root / wt_rel
    base_ref = pick_base_branch(root)

    ensure_worktrees_ignored(root)
    (root / ".worktrees").mkdir(parents=True, exist_ok=True)
    cp = run_cmd(
        [
            "git",
            "-C",
            str(root),
            "worktree",
            "add",
            str(wt_abs),
            "-b",
            branch,
            base_ref,
        ]
    )
    if cp.returncode != 0:
        raise SystemExit(cp.stderr.strip() or cp.stdout.strip() or "error: failed to create worktree")

    feat_dir.mkdir(parents=True, exist_ok=False)
    (feat_dir / "spec-deltas").mkdir(parents=True, exist_ok=True)
    (feat_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (feat_dir / "gate").mkdir(parents=True, exist_ok=True)

    proposal_src = change_dir / "proposal.md"
    tasks_src = change_dir / "tasks.md"

    proposal_text = proposal_src.read_text(encoding="utf-8") if proposal_src.exists() else f"# Imported Proposal: {args.change}\n"
    tasks_text = tasks_src.read_text(encoding="utf-8") if tasks_src.exists() else "# Imported Tasks\n- [ ] T-001 Imported task\n"

    (feat_dir / "proposal.md").write_text(proposal_text, encoding="utf-8")
    (feat_dir / "tasks.md").write_text(tasks_text, encoding="utf-8")

    spec_src_dir = change_dir / "specs"
    if spec_src_dir.exists():
        for cap in spec_src_dir.iterdir():
            if not cap.is_dir():
                continue
            src = cap / "spec.md"
            if src.exists():
                dst = feat_dir / "spec-deltas" / f"{cap.name}.md"
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    state = {
        "version": 1,
        "feat_id": feat_id,
        "title": f"Imported: {args.change}",
        "slug": slugify(args.change),
        "goal": f"Imported from openspec/changes/{args.change}",
        "status": "ready",
        "base_ref": base_ref,
        "branch": branch,
        "worktree_name": wt_name,
        "worktree_path": str(wt_rel),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "current_task_id": None,
        "counters": {
            "gate_fail_streak": 0,
            "no_progress_rounds": 0,
            "round_count": 0,
        },
        "gate": {
            "last_result": None,
            "last_task_id": None,
            "last_checked_at": None,
            "last_check_commands": [],
            "last_log_path": None,
        },
        "history": [
            {"at": utc_now(), "action": "import_openspec", "detail": args.change}
        ],
    }
    tasks = {
        "version": 1,
        "feat_id": feat_id,
        "updated_at": utc_now(),
        "tasks": parse_tasks_md(feat_dir / "tasks.md"),
    }

    save_feat(paths, feat_id, state, tasks)
    print(f"ok: imported {args.change} -> {feat_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
