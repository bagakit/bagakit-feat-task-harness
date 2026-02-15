#!/usr/bin/env python3
"""Query interface for bagakit-feat-task-harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ft_core import HarnessPaths, ensure_harness_exists, query_filter, query_list, query_one


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Query feat/task harness state")
    p.add_argument("--root", default=".")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list", help="list all feats")
    sp.set_defaults(action="list")

    sp = sub.add_parser("query", help="get one feat")
    sp.add_argument("--feat", required=True)
    sp.set_defaults(action="query")

    sp = sub.add_parser("filter", help="filter feats")
    sp.add_argument("--status", default=None)
    sp.add_argument("--task-status", choices=["todo", "in_progress", "done", "blocked"], default=None)
    sp.add_argument("--contains", default=None)
    sp.set_defaults(action="filter")

    return p


def main() -> int:
    args = build_parser().parse_args()
    paths = HarnessPaths(Path(args.root).resolve())
    ensure_harness_exists(paths)

    if args.action == "list":
        print(json.dumps({"feats": query_list(paths)}, ensure_ascii=False, indent=2))
        return 0
    if args.action == "query":
        print(json.dumps(query_one(paths, args.feat), ensure_ascii=False, indent=2))
        return 0

    print(
        json.dumps(
            {
                "feats": query_filter(
                    paths,
                    feat_status=args.status,
                    task_status=args.task_status,
                    contains=args.contains,
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
