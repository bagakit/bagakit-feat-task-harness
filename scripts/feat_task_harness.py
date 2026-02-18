#!/usr/bin/env python3
"""Core implementation for bagakit-feat-task-harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

FEAT_ID_RE = re.compile(r"^f-\d{8}-[a-z0-9][a-z0-9-]*$")
TASK_ID_RE = re.compile(r"^T-\d{3}$")
FEAT_STATUS = {"proposal", "ready", "in_progress", "blocked", "done", "archived"}
TASK_STATUS = {"todo", "in_progress", "done", "blocked"}
GATE_STATUS = {"pass", "fail"}
UNRESOLVED_ENV_RE = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*")
REFERENCE_SKILLS_ENV = "BAGAKIT_REFERENCE_SKILLS_HOME"


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def run_shell(command: str, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=True,
        check=False,
    )


def ensure_git_repo(root: Path) -> None:
    cp = run_cmd(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"])
    if cp.returncode != 0 or cp.stdout.strip() != "true":
        raise SystemExit(f"error: not a git repository: {root}")


def command_exists(name: str) -> bool:
    cp = run_cmd(["bash", "-lc", f"command -v {shlex.quote(name)} >/dev/null 2>&1"])
    return cp.returncode == 0


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise SystemExit("error: slug became empty after normalization")
    return value


@dataclass
class HarnessPaths:
    root: Path

    @property
    def harness_dir(self) -> Path:
        return self.root / ".bagakit" / "ft-harness"

    @property
    def feats_dir(self) -> Path:
        return self.harness_dir / "feats"

    @property
    def feats_archived_dir(self) -> Path:
        return self.harness_dir / "feats-archived"

    @property
    def index_dir(self) -> Path:
        return self.harness_dir / "index"

    @property
    def artifacts_dir(self) -> Path:
        return self.harness_dir / "artifacts"

    @property
    def index_file(self) -> Path:
        return self.index_dir / "feats.json"

    @property
    def config_file(self) -> Path:
        return self.harness_dir / "config.json"

    @property
    def ref_report_json(self) -> Path:
        return self.artifacts_dir / "ref-read-report.json"

    @property
    def ref_report_md(self) -> Path:
        return self.artifacts_dir / "ref-read-report.md"

    def feat_dir(self, feat_id: str, *, status: str | None = None) -> Path:
        base = self.feats_archived_dir if status == "archived" else self.feats_dir
        return base / feat_id

    def feat_state(self, feat_id: str, *, status: str | None = None) -> Path:
        return self.feat_dir(feat_id, status=status) / "state.json"

    def feat_tasks(self, feat_id: str, *, status: str | None = None) -> Path:
        return self.feat_dir(feat_id, status=status) / "tasks.json"

    def feat_summary(self, feat_id: str, *, status: str | None = None) -> Path:
        return self.feat_dir(feat_id, status=status) / "summary.md"


def load_index(paths: HarnessPaths) -> dict[str, Any]:
    if not paths.index_file.exists():
        raise SystemExit(f"error: missing harness index: {paths.index_file}")
    data = load_json(paths.index_file)
    if not isinstance(data, dict) or "feats" not in data:
        raise SystemExit(f"error: invalid index schema: {paths.index_file}")
    return data


def save_index(paths: HarnessPaths, index_data: dict[str, Any]) -> None:
    index_data["updated_at"] = utc_now()
    save_json(paths.index_file, index_data)


def get_feat_index_entry(index_data: dict[str, Any], feat_id: str) -> dict[str, Any] | None:
    for item in index_data.get("feats", []):
        if item.get("feat_id") == feat_id:
            return item
    return None


def upsert_feat_index(paths: HarnessPaths, state: dict[str, Any]) -> None:
    index_data = load_index(paths)
    entries = index_data.setdefault("feats", [])
    payload = {
        "feat_id": state["feat_id"],
        "title": state.get("title", ""),
        "status": state.get("status", "proposal"),
        "branch": state.get("branch", ""),
        "worktree_name": state.get("worktree_name", ""),
        "updated_at": state.get("updated_at", utc_now()),
    }
    for i, item in enumerate(entries):
        if item.get("feat_id") == payload["feat_id"]:
            entries[i] = payload
            save_index(paths, index_data)
            return
    entries.append(payload)
    entries.sort(key=lambda x: str(x.get("feat_id", "")))
    save_index(paths, index_data)


def feat_index_status(paths: HarnessPaths, feat_id: str) -> str:
    index_data = load_index(paths)
    entry = get_feat_index_entry(index_data, feat_id)
    if entry is None:
        raise SystemExit(f"error: feat not indexed: {feat_id}")
    return str(entry.get("status") or "proposal")


def load_feat(paths: HarnessPaths, feat_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    status = feat_index_status(paths, feat_id)
    state_file = paths.feat_state(feat_id, status=status)
    tasks_file = paths.feat_tasks(feat_id, status=status)
    if not state_file.exists():
        raise SystemExit(f"error: missing feat state file: {state_file}")
    if not tasks_file.exists():
        raise SystemExit(f"error: missing feat tasks file: {tasks_file}")
    state = load_json(state_file)
    tasks = load_json(tasks_file)
    return state, tasks


def save_feat(paths: HarnessPaths, feat_id: str, state: dict[str, Any], tasks: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    tasks["updated_at"] = utc_now()
    status = str(state.get("status") or "")
    save_json(paths.feat_state(feat_id, status=status), state)
    save_json(paths.feat_tasks(feat_id, status=status), tasks)
    sync_tasks_markdown(paths, feat_id, tasks, status=status)
    upsert_feat_index(paths, state)


def sync_tasks_markdown(
    paths: HarnessPaths, feat_id: str, tasks: dict[str, Any], *, status: str | None = None
) -> None:
    target = paths.feat_dir(feat_id, status=status) / "tasks.md"
    rows: list[str] = [f"# Feat Tasks: {feat_id}", "", "JSON SSOT: `tasks.json`", "", "## Task Checklist"]
    for item in tasks.get("tasks", []):
        checked = "x" if item.get("status") == "done" else " "
        rows.append(f"- [{checked}] {item.get('id', '<id>')} {item.get('title', '')}")
    rows += ["", "## Status Legend", "- todo", "- in_progress", "- done", "- blocked", ""]
    write_text(target, "\n".join(rows))


def find_task(tasks: dict[str, Any], task_id: str) -> dict[str, Any]:
    for item in tasks.get("tasks", []):
        if item.get("id") == task_id:
            return item
    raise SystemExit(f"error: task not found: {task_id}")


def count_tasks(tasks: dict[str, Any], status: str) -> int:
    return sum(1 for t in tasks.get("tasks", []) if t.get("status") == status)


def ensure_harness_exists(paths: HarnessPaths) -> None:
    if not paths.harness_dir.exists():
        raise SystemExit(
            "error: harness not initialized. run feat_task_harness.sh initialize-harness first"
        )


def ensure_worktrees_ignored(root: Path) -> None:
    gitignore = root / ".gitignore"
    content = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    lines = [line.strip() for line in content.splitlines()]
    if ".worktrees" not in lines:
        with gitignore.open("a", encoding="utf-8") as f:
            if content and not content.endswith("\n"):
                f.write("\n")
            f.write(".worktrees\n")
        print(f"write: {gitignore} (+.worktrees)")


def load_template(skill_dir: Path, rel: str) -> str:
    path = skill_dir / "references" / rel
    if not path.exists():
        raise SystemExit(f"error: missing template: {path}")
    return read_text(path)


def copy_template_if_missing(skill_dir: Path, rel: str, dest: Path) -> None:
    if dest.exists():
        return
    write_text(dest, load_template(skill_dir, rel))
    print(f"write: {dest}")


def detect_living_docs(root: Path) -> bool:
    docs = root / "docs"
    return (
        (docs / "must-guidebook.md").exists()
        and (docs / "must-docs-taxonomy.md").exists()
        and (docs / ".bagakit" / "inbox").exists()
    )


def manifest_path(skill_dir: Path, path_override: str | None) -> Path:
    if path_override:
        return Path(path_override)
    return skill_dir / "references" / "required-reading-manifest.json"


def resolve_manifest_location(raw: str) -> tuple[str, str | None]:
    expanded = os.path.expanduser(os.path.expandvars(raw))
    if UNRESOLVED_ENV_RE.search(expanded):
        return expanded, "unresolved environment variable in location"
    return expanded, None


def default_reference_skills_home() -> Path | None:
    env_raw = os.environ.get(REFERENCE_SKILLS_ENV, "").strip()
    if env_raw:
        return Path(os.path.expanduser(os.path.expandvars(env_raw)))

    home = Path.home()
    candidates = [
        Path(os.path.expanduser(os.path.expandvars(os.environ.get("BAGAKIT_HOME", "")))) / "skills"
        if os.environ.get("BAGAKIT_HOME")
        else None,
        home / ".bagakit" / "skills",
    ]
    for c in candidates:
        if c and c.exists() and c.is_dir():
            return c
    return None


def ensure_reference_skills_home() -> Path | None:
    p = default_reference_skills_home()
    if p is None:
        return None
    os.environ.setdefault(REFERENCE_SKILLS_ENV, str(p))
    return p


def compute_manifest_hash(path: Path) -> str:
    return sha256_file(path)


def cmd_ref_read_gate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    skill_dir = Path(args.skill_dir).resolve()
    mpath = manifest_path(skill_dir, args.manifest)
    detected_ref_home = ensure_reference_skills_home()

    if not mpath.exists():
        eprint(f"error: manifest not found: {mpath}")
        return 1

    manifest_data = load_json(mpath)
    entries = manifest_data.get("entries", [])
    if not isinstance(entries, list):
        eprint("error: manifest 'entries' must be list")
        return 1

    result_entries: list[dict[str, Any]] = []
    ok = True

    for entry in entries:
        entry_id = str(entry.get("id", ""))
        entry_type = str(entry.get("type", ""))
        location = str(entry.get("location", ""))
        resolved_location = location
        required = bool(entry.get("required", True))
        exists = False
        digest = ""
        error = ""

        if not entry_id or entry_type not in {"file", "url"} or not location:
            ok = False
            error = "invalid manifest entry"
        elif entry_type == "file":
            resolved_location, resolve_error = resolve_manifest_location(location)
            if resolve_error:
                exists = False
                error = resolve_error
            else:
                p = Path(resolved_location)
                if p.exists() and p.is_file():
                    exists = True
                    digest = sha256_file(p)
                else:
                    exists = False
                    error = "file not found"
        elif entry_type == "url":
            try:
                with urllib.request.urlopen(location, timeout=20) as r:
                    data = r.read()
                exists = True
                digest = sha256_bytes(data)
            except (urllib.error.URLError, TimeoutError) as exc:
                exists = False
                error = f"url fetch failed: {exc}"

        if required and not exists:
            ok = False

        result_entries.append(
            {
                "id": entry_id,
                "type": entry_type,
                "location": location,
                "resolved_location": resolved_location,
                "required": required,
                "exists": exists,
                "sha256": digest,
                "error": error,
            }
        )

    status = "VALID" if ok else "INVALID"
    generated_at = utc_now()
    mhash = compute_manifest_hash(mpath)

    payload = {
        "status": status,
        "generated_at": generated_at,
        "project_root": str(root),
        "manifest_path": str(mpath),
        "manifest_sha256": mhash,
        "entries": result_entries,
    }

    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)
    save_json(paths.ref_report_json, payload)

    lines = [
        "# Reference Read Report",
        "",
        f"Status: {status}",
        f"Generated At (UTC): {generated_at}",
        f"Project Root: {root}",
        f"Manifest Path: {mpath}",
        f"Manifest SHA256: {mhash}",
        "",
        "## Entries",
        "",
        "| ID | Type | Required | Exists | SHA256 | Error |",
        "|---|---|---|---|---|---|",
    ]
    for item in result_entries:
        lines.append(
            "| {id} | {type} | {required} | {exists} | {sha256} | {error} |".format(
                id=item["id"],
                type=item["type"],
                required="yes" if item["required"] else "no",
                exists="yes" if item["exists"] else "no",
                sha256=item["sha256"] or "-",
                error=(item["error"] or "-").replace("|", "/"),
            )
        )

    lines += ["", "## Reading Notes", ""]
    for item in result_entries:
        lines += [
            f"### {item['id']}",
            "- Summary:",
            "- Key takeaways:",
            "",
        ]

    write_text(paths.ref_report_md, "\n".join(lines))

    print(f"write: {paths.ref_report_json}")
    print(f"write: {paths.ref_report_md}")
    if detected_ref_home is not None:
        print(f"info: {REFERENCE_SKILLS_ENV}={detected_ref_home}")
    else:
        eprint(
            "warn: BAGAKIT_REFERENCE_SKILLS_HOME not found automatically; "
            "file-based manifest entries may fail if required skills are missing"
        )
    if not ok:
        eprint("error: reference read gate failed (missing required entries)")
        return 1
    print("ok: reference read report generated")
    return 0


def check_ref_report(paths: HarnessPaths, skill_dir: Path, manifest_override: str | None = None) -> list[str]:
    ensure_reference_skills_home()
    issues: list[str] = []
    mpath = manifest_path(skill_dir, manifest_override)
    if not mpath.exists():
        issues.append(f"manifest missing: {mpath}")
        return issues

    if not paths.ref_report_json.exists():
        issues.append(
            "missing report: "
            f"{paths.ref_report_json} "
            f"(run feat_task_harness.sh check-reference-readiness --root {paths.root})"
        )
        return issues

    try:
        report = load_json(paths.ref_report_json)
    except Exception as exc:  # noqa: BLE001
        issues.append(f"failed to read report json: {exc}")
        return issues

    if report.get("status") != "VALID":
        issues.append("ref-read report status is not VALID")

    expected_hash = compute_manifest_hash(mpath)
    if report.get("manifest_sha256") != expected_hash:
        issues.append("manifest hash mismatch; regenerate report")

    entries = report.get("entries", [])
    if not isinstance(entries, list):
        issues.append("report entries malformed")
        return issues

    missing_required = [
        item.get("id")
        for item in entries
        if item.get("required", True) and not item.get("exists", False)
    ]
    if missing_required:
        issues.append(f"missing required references: {', '.join(str(i) for i in missing_required)}")
        issues.append(
            "hint: ensure required skills are installed and "
            "set BAGAKIT_REFERENCE_SKILLS_HOME to the correct skills directory "
            "(for one-shot shell calls, set it inline with the command)"
        )

    return issues


def cmd_check_ref_report(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    skill_dir = Path(args.skill_dir).resolve()
    paths = HarnessPaths(root)
    issues = check_ref_report(paths, skill_dir, args.manifest)
    if issues:
        for issue in issues:
            eprint(f"error: {issue}")
        return 1
    print("ok")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    skill_dir = Path(args.skill_dir).resolve()
    paths = HarnessPaths(root)

    if args.strict:
        issues = check_ref_report(paths, skill_dir, args.manifest)
        if issues:
            for issue in issues:
                eprint(f"error: {issue}")
            return 1

    paths.harness_dir.mkdir(parents=True, exist_ok=True)
    paths.feats_dir.mkdir(parents=True, exist_ok=True)
    paths.feats_archived_dir.mkdir(parents=True, exist_ok=True)
    paths.index_dir.mkdir(parents=True, exist_ok=True)
    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)

    copy_template_if_missing(skill_dir, "feats-index-template.json", paths.index_file)
    copy_template_if_missing(skill_dir, "harness-config-template.json", paths.config_file)

    if not (paths.harness_dir / "README.md").exists():
        runtime_rel = str(paths.harness_dir.relative_to(root))
        write_text(
            paths.harness_dir / "README.md",
            f"# {runtime_rel}\n\nJSON SSOT feat/task harness runtime data.\n",
        )
        print(f"write: {paths.harness_dir / 'README.md'}")

    if not (paths.harness_dir / ".gitignore").exists():
        write_text(paths.harness_dir / ".gitignore", "artifacts/*.log\n")
        print(f"write: {paths.harness_dir / '.gitignore'}")

    ensure_worktrees_ignored(root)
    print(f"ok: harness initialized at {paths.harness_dir}")
    return 0


def pick_base_branch(root: Path) -> str:
    for candidate in ("main", "master"):
        cp = run_cmd(["git", "-C", str(root), "show-ref", "--verify", f"refs/heads/{candidate}"])
        if cp.returncode == 0:
            return candidate
    cp = run_cmd(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"])
    branch = cp.stdout.strip() if cp.returncode == 0 else ""
    return branch or "HEAD"


def unique_feat_id(paths: HarnessPaths, slug: str) -> str:
    existing_ids = {str(item.get("feat_id", "")) for item in load_index(paths).get("feats", [])}

    def exists(feat_id: str) -> bool:
        return (
            feat_id in existing_ids
            or paths.feat_dir(feat_id).exists()
            or paths.feat_dir(feat_id, status="archived").exists()
        )

    base = f"f-{utc_day()}-{slug}"
    if not exists(base):
        return base
    i = 2
    while True:
        candidate = f"{base}-{i}"
        if not exists(candidate):
            return candidate
        i += 1


def cmd_feat_new(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    skill_dir = Path(args.skill_dir).resolve()
    ensure_git_repo(root)
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)

    if args.strict:
        issues = check_ref_report(paths, skill_dir, args.manifest)
        if issues:
            for issue in issues:
                eprint(f"error: {issue}")
            return 1

    title = args.title.strip()
    goal = args.goal.strip()
    slug = slugify(args.slug if args.slug else title)
    feat_id = unique_feat_id(paths, slug)
    if not FEAT_ID_RE.match(feat_id):
        eprint(f"error: generated invalid feat id: {feat_id}")
        return 1

    feat_dir = paths.feat_dir(feat_id)
    feat_dir.mkdir(parents=True, exist_ok=False)
    (feat_dir / "spec-deltas").mkdir(parents=True, exist_ok=True)
    (feat_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (feat_dir / "gate").mkdir(parents=True, exist_ok=True)

    branch = f"feat/{feat_id}"
    wt_name = f"wt-{feat_id}"
    wt_rel = Path(".worktrees") / wt_name
    wt_abs = root / wt_rel

    ensure_worktrees_ignored(root)
    (root / ".worktrees").mkdir(parents=True, exist_ok=True)
    base_ref = pick_base_branch(root)

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
        eprint(cp.stderr.strip() or cp.stdout.strip())
        eprint("error: failed to create worktree")
        return 1

    proposal = load_template(skill_dir, "feat-proposal-template.md")
    proposal = (
        proposal.replace("<feat-id>", feat_id)
        .replace("<goal>", goal)
    )
    write_text(feat_dir / "proposal.md", proposal)

    tasks_md = load_template(skill_dir, "feat-tasks-template.md").replace("<feat-id>", feat_id)
    write_text(feat_dir / "tasks.md", tasks_md)

    spec_delta = load_template(skill_dir, "feat-spec-delta-template.md").replace("<capability>", "core")
    write_text(feat_dir / "spec-deltas" / "core.md", spec_delta)

    state: dict[str, Any] = {
        "version": 1,
        "feat_id": feat_id,
        "title": title,
        "slug": slug,
        "goal": goal,
        "status": "proposal",
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
            {
                "at": utc_now(),
                "action": "feat_created",
                "detail": f"base_ref={base_ref}",
            }
        ],
    }

    tasks: dict[str, Any] = {
        "version": 1,
        "feat_id": feat_id,
        "updated_at": utc_now(),
        "tasks": [
            {
                "id": "T-001",
                "title": "Implement first scoped change for this feat",
                "status": "todo",
                "summary": "Replace this placeholder with actual task detail.",
                "gate_result": None,
                "last_gate_at": None,
                "last_gate_commands": [],
                "last_commit_hash": None,
                "started_at": None,
                "finished_at": None,
                "updated_at": utc_now(),
                "notes": [],
            }
        ],
    }

    save_feat(paths, feat_id, state, tasks)
    write_text(
        feat_dir / "gate" / "ui-verification.md",
        load_template(skill_dir, "ui-gate-template.md"),
    )

    print(f"write: {feat_dir / 'state.json'}")
    print(f"write: {feat_dir / 'tasks.json'}")
    print(f"worktree: {wt_abs}")
    print(f"branch: {branch}")
    print(f"feat_id: {feat_id}")
    return 0


def cmd_feat_status(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)
    index_data = load_index(paths)
    feats = index_data.get("feats", [])

    if args.feat:
        state, tasks = load_feat(paths, args.feat)
        payload = {
            "feat": state,
            "tasks": tasks,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        print(f"feat_id: {state['feat_id']}")
        print(f"title: {state.get('title', '')}")
        print(f"status: {state.get('status', '')}")
        print(f"branch: {state.get('branch', '')}")
        print(f"worktree: {state.get('worktree_path', '')}")
        print(f"current_task: {state.get('current_task_id')}")
        print(
            "tasks: "
            f"todo={count_tasks(tasks, 'todo')} "
            f"in_progress={count_tasks(tasks, 'in_progress')} "
            f"done={count_tasks(tasks, 'done')} "
            f"blocked={count_tasks(tasks, 'blocked')}"
        )
        return 0

    if args.json:
        print(json.dumps({"feats": feats}, ensure_ascii=False, indent=2))
        return 0

    if not feats:
        print("no feats")
        return 0

    print("feat_id\tstatus\ttitle\tbranch\tupdated_at")
    for item in feats:
        print(
            f"{item.get('feat_id','')}\t{item.get('status','')}\t"
            f"{item.get('title','')}\t{item.get('branch','')}\t{item.get('updated_at','')}"
        )
    return 0


def cmd_task_start(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)
    state, tasks = load_feat(paths, args.feat)

    task_id = args.task
    if not TASK_ID_RE.match(task_id):
        eprint(f"error: invalid task id: {task_id}")
        return 1

    for t in tasks.get("tasks", []):
        if t.get("status") == "in_progress" and t.get("id") != task_id:
            eprint(f"error: another task is already in_progress: {t.get('id')}")
            return 1

    target = find_task(tasks, task_id)
    if target.get("status") not in {"todo", "blocked"}:
        eprint(f"error: task {task_id} cannot be started from status={target.get('status')}")
        return 1

    target["status"] = "in_progress"
    target["started_at"] = target.get("started_at") or utc_now()
    target["updated_at"] = utc_now()
    state["status"] = "in_progress"
    state["current_task_id"] = task_id
    state.setdefault("history", []).append(
        {"at": utc_now(), "action": "task_started", "detail": task_id}
    )
    save_feat(paths, args.feat, state, tasks)
    print(f"ok: task started {args.feat}/{task_id}")
    return 0


def detect_project_type(root: Path, config: dict[str, Any]) -> str:
    gate_cfg = config.get("gate", {}) if isinstance(config, dict) else {}
    explicit = str(gate_cfg.get("project_type", "auto"))
    if explicit in {"ui", "non_ui"}:
        return explicit

    rules = gate_cfg.get("project_type_rules", {})
    if isinstance(rules, dict):
        ui_rules = rules.get("ui", {})
        non_ui_rules = rules.get("non_ui", {})
        default_type = str(rules.get("default", "non_ui"))
        if default_type not in {"ui", "non_ui"}:
            default_type = "non_ui"

        def matches(rule_set: Any) -> bool:
            if not isinstance(rule_set, dict):
                return False
            any_paths = rule_set.get("any_path_exists", [])
            if isinstance(any_paths, list) and any_paths:
                for rel in any_paths:
                    if (root / str(rel)).exists():
                        return True
            all_paths = rule_set.get("all_paths_exist", [])
            if isinstance(all_paths, list) and all_paths:
                if all((root / str(rel)).exists() for rel in all_paths):
                    return True
            return False

        if matches(ui_rules):
            return "ui"
        if matches(non_ui_rules):
            return "non_ui"
        return default_type

    # Legacy compatibility fallback when no rules are configured.
    return "non_ui"


def collect_non_ui_commands(root: Path, config: dict[str, Any]) -> list[str]:
    gate_cfg = config.get("gate", {}) if isinstance(config, dict) else {}
    custom = gate_cfg.get("non_ui_commands", [])
    if isinstance(custom, list) and custom:
        return [str(c) for c in custom]

    commands: list[str] = []
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists() or (root / "pytest.ini").exists():
        if command_exists("pytest"):
            commands.append("pytest -q")
    if (root / "go.mod").exists() and command_exists("go"):
        commands.append("go test ./...")
    if (root / "Cargo.toml").exists() and command_exists("cargo"):
        commands.append("cargo test -q")
    package_json = root / "package.json"
    if package_json.exists() and command_exists("npm"):
        try:
            data = load_json(package_json)
            scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
            if isinstance(scripts, dict) and "test" in scripts:
                commands.append("npm test --silent")
        except Exception:  # noqa: BLE001
            pass
    return commands


def validate_ui_evidence(evidence_file: Path) -> list[str]:
    errors: list[str] = []
    if not evidence_file.exists():
        return [f"missing UI verification file: {evidence_file}"]
    text = read_text(evidence_file)
    for heading in ("## Critical Paths", "## Screenshots", "## Console Errors"):
        if heading not in text:
            errors.append(f"missing heading in UI evidence: {heading}")
    if "console errors: none" not in text.lower():
        errors.append("UI evidence must declare 'Console Errors: none'")
    return errors


def cmd_task_gate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)

    state, tasks = load_feat(paths, args.feat)
    feat_dir = paths.feat_dir(args.feat, status=str(state.get("status") or ""))
    task = find_task(tasks, args.task)
    if task.get("status") != "in_progress":
        eprint(f"error: task {args.task} must be in_progress before gate")
        return 1
    if state.get("current_task_id") != args.task:
        eprint("error: feat current_task_id does not match requested task")
        return 1

    config = load_json(paths.config_file) if paths.config_file.exists() else {}
    project_type = detect_project_type(root, config)

    records: list[dict[str, Any]] = []
    failed = False
    fail_reasons: list[str] = []

    if project_type == "ui":
        evidence = feat_dir / "gate" / "ui-verification.md"
        ui_errors = validate_ui_evidence(evidence)
        if ui_errors:
            failed = True
            fail_reasons.extend(ui_errors)
        ui_cmds = config.get("gate", {}).get("ui_commands", []) if isinstance(config, dict) else []
        if isinstance(ui_cmds, list):
            for cmd in ui_cmds:
                cp = run_shell(str(cmd), cwd=root)
                rec = {
                    "command": str(cmd),
                    "exit_code": cp.returncode,
                    "status": "pass" if cp.returncode == 0 else "fail",
                }
                records.append(rec)
                if cp.returncode != 0:
                    failed = True
                    fail_reasons.append(f"ui command failed: {cmd}")
    else:
        commands = collect_non_ui_commands(root, config)
        if not commands:
            failed = True
            fail_reasons.append(
                f"no non-ui gate command available; set gate.non_ui_commands in {paths.config_file.relative_to(root)}"
            )
        else:
            for cmd in commands:
                cp = run_shell(cmd, cwd=root)
                rec = {
                    "command": cmd,
                    "exit_code": cp.returncode,
                    "status": "pass" if cp.returncode == 0 else "fail",
                }
                records.append(rec)
                if cp.returncode != 0:
                    failed = True
                    fail_reasons.append(f"command failed: {cmd}")

    gate_result = "fail" if failed else "pass"
    ts = utc_now()

    logs_dir = feat_dir / "artifacts"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"gate-{ts.replace(':', '').replace('-', '')}.log"
    lines = [f"gate_time={ts}", f"project_type={project_type}", f"result={gate_result}"]
    if fail_reasons:
        lines.append("reasons:")
        for r in fail_reasons:
            lines.append(f"- {r}")
    lines.append("commands:")
    for rec in records:
        lines.append(f"- {rec['command']} => {rec['status']} ({rec['exit_code']})")
    write_text(log_file, "\n".join(lines) + "\n")

    counters = state.setdefault("counters", {})
    counters["round_count"] = int(counters.get("round_count", 0)) + 1
    counters["no_progress_rounds"] = int(counters.get("no_progress_rounds", 0)) + 1
    if gate_result == "pass":
        counters["gate_fail_streak"] = 0
    else:
        counters["gate_fail_streak"] = int(counters.get("gate_fail_streak", 0)) + 1

    state["gate"] = {
        "last_result": gate_result,
        "last_task_id": args.task,
        "last_checked_at": ts,
        "last_check_commands": records,
        "last_log_path": str(log_file.relative_to(root)),
    }
    state.setdefault("history", []).append(
        {
            "at": ts,
            "action": "task_gate",
            "detail": f"{args.task} => {gate_result}",
        }
    )

    task["gate_result"] = gate_result
    task["last_gate_at"] = ts
    task["last_gate_commands"] = records
    task["updated_at"] = ts

    save_feat(paths, args.feat, state, tasks)

    if gate_result == "fail":
        eprint(f"error: gate failed for {args.feat}/{args.task}")
        for reason in fail_reasons:
            eprint(f"error: {reason}")
        print(f"gate_log: {log_file}")
        return 1

    print(f"ok: gate passed {args.feat}/{args.task}")
    print(f"gate_log: {log_file}")
    return 0


def build_commit_message(
    state: dict[str, Any],
    task: dict[str, Any],
    summary: str,
    task_status: str,
    gate_result: str,
) -> str:
    feat_id = state["feat_id"]
    task_id = task["id"]
    checks = task.get("last_gate_commands", [])
    check_lines = []
    if checks:
        for rec in checks:
            check_lines.append(
                f"- `{rec.get('command','')}` => {rec.get('status','unknown').upper()}"
            )
    else:
        check_lines.append("- No gate command records found")

    body = [
        f"feat({feat_id}): task({task_id}) {summary}",
        "",
        "Plan:",
        f"- Feat Goal: {state.get('goal','')}",
        f"- Task: {task.get('title','')}",
        "",
        "Check:",
        *check_lines,
        "",
        "Learn:",
        "- Add key learnings, risks, or follow-up notes here.",
        "",
        f"Feat-ID: {feat_id}",
        f"Task-ID: {task_id}",
        f"Gate-Result: {gate_result}",
        f"Task-Status: {task_status}",
        "",
    ]
    return "\n".join(body)


def parse_trailers(lines: list[str]) -> dict[str, str]:
    trailers: dict[str, str] = {}
    for line in lines:
        m = re.match(r"^([A-Za-z0-9-]+):\s*(.+)$", line.strip())
        if m:
            trailers[m.group(1)] = m.group(2)
    return trailers


def validate_commit_message(
    text: str,
    expected_feat: str,
    expected_task: str,
    expected_task_status: str,
    expected_gate_result: str,
) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines:
        return ["empty commit message"]

    subj = lines[0].strip()
    m = re.match(r"^feat\((f-\d{8}-[a-z0-9][a-z0-9-]*)\): task\((T-\d{3})\) .+$", subj)
    if not m:
        errors.append("invalid subject format")
    else:
        if m.group(1) != expected_feat:
            errors.append("subject feat-id mismatch")
        if m.group(2) != expected_task:
            errors.append("subject task-id mismatch")

    blob = "\n".join(lines)
    for marker in ("\nPlan:\n", "\nCheck:\n", "\nLearn:\n"):
        if marker not in f"\n{blob}\n":
            errors.append(f"missing section: {marker.strip()}")

    trailers = parse_trailers(lines)
    required = {
        "Feat-ID": expected_feat,
        "Task-ID": expected_task,
        "Gate-Result": expected_gate_result,
        "Task-Status": expected_task_status,
    }
    for k, v in required.items():
        if trailers.get(k) != v:
            errors.append(f"missing or invalid trailer {k}")

    if expected_task_status == "done" and expected_gate_result != "pass":
        errors.append("done status requires gate_result=pass")

    return errors


def cmd_task_commit(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)
    ensure_git_repo(root)

    state, tasks = load_feat(paths, args.feat)
    feat_dir = paths.feat_dir(args.feat, status=str(state.get("status") or ""))
    task = find_task(tasks, args.task)
    if task.get("status") != "in_progress":
        eprint(f"error: task must be in_progress before commit: {args.task}")
        return 1

    gate_result = str(task.get("gate_result") or "")
    if gate_result not in GATE_STATUS:
        eprint("error: task gate_result is missing; run feat_task_harness.sh run-task-gate first")
        return 1

    task_status = args.task_status
    if task_status == "done" and gate_result != "pass":
        eprint("error: Task-Status done requires Gate-Result pass")
        return 1

    msg = build_commit_message(state, task, args.summary.strip(), task_status, gate_result)
    msg_file = (
        Path(args.message_out).resolve()
        if args.message_out
        else feat_dir
        / "artifacts"
        / f"commit-{args.task}-{utc_now().replace(':', '').replace('-', '')}.msg"
    )
    write_text(msg_file, msg)

    errors = validate_commit_message(
        msg,
        expected_feat=args.feat,
        expected_task=args.task,
        expected_task_status=task_status,
        expected_gate_result=gate_result,
    )
    if errors:
        for err in errors:
            eprint(f"error: {err}")
        return 1

    print(f"message_file: {msg_file}")
    print(
        "next: git add -A && "
        f"git commit -F {shlex.quote(str(msg_file))}"
    )

    if args.execute:
        cp = run_cmd(["git", "-C", str(root), "commit", "-F", str(msg_file)])
        if cp.returncode != 0:
            eprint(cp.stderr.strip() or cp.stdout.strip() or "git commit failed")
            return 1
        head = run_cmd(["git", "-C", str(root), "rev-parse", "HEAD"])
        if head.returncode == 0:
            task["last_commit_hash"] = head.stdout.strip()
            task["updated_at"] = utc_now()
            save_feat(paths, args.feat, state, tasks)
            print(f"commit_hash: {task['last_commit_hash']}")

    return 0


def cmd_task_finish(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)

    state, tasks = load_feat(paths, args.feat)
    task = find_task(tasks, args.task)

    if task.get("status") != "in_progress":
        eprint(f"error: task is not in_progress: {args.task}")
        return 1
    if state.get("current_task_id") != args.task:
        eprint("error: state current_task_id mismatch")
        return 1

    result = args.result
    if result == "done" and task.get("gate_result") != "pass":
        eprint("error: cannot finish task as done without gate pass")
        return 1

    ts = utc_now()
    task["status"] = result
    task["finished_at"] = ts
    task["updated_at"] = ts

    state["current_task_id"] = None
    state.setdefault("counters", {})["no_progress_rounds"] = 0
    state.setdefault("history", []).append(
        {"at": ts, "action": "task_finished", "detail": f"{args.task} => {result}"}
    )

    if result == "blocked":
        state["status"] = "blocked"
    else:
        if count_tasks(tasks, "todo") == 0 and count_tasks(tasks, "in_progress") == 0:
            state["status"] = "done"
        else:
            state["status"] = "ready"

    save_feat(paths, args.feat, state, tasks)
    print(f"ok: task finished {args.feat}/{args.task} => {result}")
    print(f"feat_status: {state['status']}")
    return 0


def render_summary(state: dict[str, Any], tasks: dict[str, Any]) -> str:
    feat_id = state["feat_id"]
    todo = count_tasks(tasks, "todo")
    in_prog = count_tasks(tasks, "in_progress")
    done = count_tasks(tasks, "done")
    blocked = count_tasks(tasks, "blocked")
    counters = state.get("counters", {})
    cleanup = state.get("archived_cleanup", {}) if isinstance(state.get("archived_cleanup"), dict) else {}

    return "\n".join(
        [
            f"# Feat Summary: {feat_id}",
            "",
            f"- Title: {state.get('title', '')}",
            f"- Goal: {state.get('goal', '')}",
            f"- Final Status: {state.get('status', '')}",
            f"- Closed From Status: {state.get('closed_from_status', '')}",
            f"- Base Ref: {state.get('base_ref', '')}",
            f"- Branch: {state.get('branch', '')}",
            f"- Worktree: {state.get('worktree_path', '')}",
            f"- Archived At (UTC): {state.get('archived_at', '') or utc_now()}",
            "",
            "## Archive Cleanup",
            f"- Branch Merged: {cleanup.get('branch_merged', '')}",
            f"- Worktree Removed: {cleanup.get('worktree_removed', '')}",
            f"- Branch Deleted: {cleanup.get('branch_deleted', '')}",
            f"- Cleanup Note: {cleanup.get('note', '')}",
            "",
            "## Task Stats",
            f"- todo: {todo}",
            f"- in_progress: {in_prog}",
            f"- done: {done}",
            f"- blocked: {blocked}",
            "",
            "## Counters",
            f"- gate_fail_streak: {counters.get('gate_fail_streak', 0)}",
            f"- no_progress_rounds: {counters.get('no_progress_rounds', 0)}",
            f"- round_count: {counters.get('round_count', 0)}",
            "",
            "## Notes",
            "- Promote durable decisions and gotchas to living docs memory when applicable.",
            "",
        ]
    )


def apply_template(template: str, replacements: dict[str, str]) -> str:
    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def resolve_worktree_abs(root: Path, raw: str) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def git_local_branch_exists(root: Path, branch: str) -> bool:
    cp = run_cmd(["git", "-C", str(root), "show-ref", "--verify", f"refs/heads/{branch}"])
    return cp.returncode == 0


def git_branch_merged_into(root: Path, branch: str, base_ref: str) -> bool:
    cp = run_cmd(["git", "-C", str(root), "merge-base", "--is-ancestor", branch, base_ref])
    return cp.returncode == 0


def cmd_feat_archive(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    skill_dir = Path(args.skill_dir).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)
    ensure_git_repo(root)

    state, tasks = load_feat(paths, args.feat)
    current_status = str(state.get("status") or "")
    if current_status not in {"done", "blocked", "archived"}:
        eprint(
            "error: feat must be done/blocked before archive "
            f"(current={current_status})"
        )
        return 1

    branch = str(state.get("branch") or "")
    base_ref = str(state.get("base_ref") or pick_base_branch(root))
    worktree_path = str(state.get("worktree_path") or "")
    wt_abs = resolve_worktree_abs(root, worktree_path) if worktree_path else None

    branch_exists = bool(branch) and git_local_branch_exists(root, branch)
    branch_merged = bool(branch_exists and git_branch_merged_into(root, branch, base_ref))
    if current_status == "done" and not branch_merged:
        eprint(f"error: feat is done but branch is not merged into {base_ref}: {branch}")
        eprint(
            "hint: merge the feat branch into base (or mark the feat blocked) before archiving"
        )
        return 1

    # Safety: don't remove a dirty worktree.
    if wt_abs is not None and wt_abs.exists():
        cp = run_cmd(["git", "-C", str(wt_abs), "status", "--porcelain"])
        if cp.returncode != 0:
            eprint(cp.stderr.strip() or cp.stdout.strip() or "git status failed")
            return 1
        if cp.stdout.strip():
            eprint(f"error: worktree has uncommitted changes: {wt_abs}")
            eprint("hint: commit/stash/clean the worktree before archiving this feat")
            return 1

    # Remove worktree first (branch deletion is blocked while checked out).
    worktree_removed = False
    if wt_abs is not None and wt_abs.exists():
        cp = run_cmd(["git", "-C", str(root), "worktree", "remove", str(wt_abs)])
        if cp.returncode != 0:
            eprint(cp.stderr.strip() or cp.stdout.strip() or "git worktree remove failed")
            return 1
        worktree_removed = True
        print(f"ok: worktree removed {wt_abs}")

    branch_deleted = False
    if branch_exists and branch_merged:
        cp = run_cmd(["git", "-C", str(root), "branch", "-D", branch])
        if cp.returncode != 0:
            eprint(cp.stderr.strip() or cp.stdout.strip() or "git branch delete failed")
            return 1
        branch_deleted = True
        print(f"ok: branch deleted {branch}")

    if detect_living_docs(root):
        inbox_dir = root / "docs" / ".bagakit" / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        repl = {
            "<feat-id>": args.feat,
            "<created-at>": utc_now(),
        }
        decision = apply_template(load_template(skill_dir, "inbox-decision-template.md"), repl)
        write_text(inbox_dir / f"decision-{args.feat}.md", decision)
        print(f"write: {inbox_dir / f'decision-{args.feat}.md'}")

        howto = apply_template(load_template(skill_dir, "inbox-howto-template.md"), repl)
        write_text(inbox_dir / f"howto-{args.feat}-result.md", howto)
        print(f"write: {inbox_dir / f'howto-{args.feat}-result.md'}")

        counters = state.get("counters", {})
        if state.get("status") == "blocked" or int(counters.get("gate_fail_streak", 0)) > 0:
            gotcha = apply_template(load_template(skill_dir, "inbox-gotcha-template.md"), repl)
            write_text(inbox_dir / f"gotcha-{args.feat}.md", gotcha)
            print(f"write: {inbox_dir / f'gotcha-{args.feat}.md'}")

    if current_status != "archived":
        state["closed_from_status"] = current_status
    state["status"] = "archived"
    state["archived_at"] = state.get("archived_at") or utc_now()
    state["archived_cleanup"] = {
        "base_ref": base_ref,
        "branch_merged": branch_merged,
        "worktree_removed": worktree_removed,
        "branch_deleted": branch_deleted,
        "note": "worktree removed; branch deleted only when merged into base",
    }
    state.setdefault("history", []).append(
        {"at": utc_now(), "action": "feat_archived", "detail": "moved + cleaned"}
    )

    # Physical archive: move feat dir into feats-archived/.
    if current_status != "archived":
        src_dir = paths.feat_dir(args.feat, status=current_status)
        dst_dir = paths.feat_dir(args.feat, status="archived")
        if not src_dir.exists():
            eprint(f"error: missing feat directory: {src_dir}")
            return 1
        if dst_dir.exists():
            eprint(f"error: archived feat directory already exists: {dst_dir}")
            return 1
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            src_dir.rename(dst_dir)
        except OSError:
            shutil.move(str(src_dir), str(dst_dir))
        print(f"ok: feat dir moved {src_dir} -> {dst_dir}")

    # Write summary into the archived directory (source of truth after move).
    summary = render_summary(state, tasks)
    summary_file = paths.feat_summary(args.feat, status="archived")
    write_text(summary_file, summary)
    print(f"write: {summary_file}")

    save_feat(paths, args.feat, state, tasks)
    print(f"ok: feat archived {args.feat}")
    return 0


def validate_feat(paths: HarnessPaths, root: Path, feat_id: str) -> list[str]:
    errors: list[str] = []
    state, tasks = load_feat(paths, feat_id)

    if not FEAT_ID_RE.match(feat_id):
        errors.append(f"invalid feat id format: {feat_id}")

    status = state.get("status")
    if status not in FEAT_STATUS:
        errors.append(f"{feat_id}: invalid feat status: {status}")

    if state.get("feat_id") != feat_id:
        errors.append(f"{feat_id}: state feat_id mismatch")

    counters = state.get("counters", {})
    for key in ("gate_fail_streak", "no_progress_rounds", "round_count"):
        try:
            val = int(counters.get(key, 0))
            if val < 0:
                errors.append(f"{feat_id}: counter {key} must be >= 0")
        except Exception:  # noqa: BLE001
            errors.append(f"{feat_id}: counter {key} not integer")

    task_items = tasks.get("tasks")
    if not isinstance(task_items, list) or not task_items:
        errors.append(f"{feat_id}: tasks.json missing tasks array")
        return errors

    seen: set[str] = set()
    in_progress: list[str] = []
    for task in task_items:
        tid = str(task.get("id", ""))
        if not TASK_ID_RE.match(tid):
            errors.append(f"{feat_id}: invalid task id: {tid}")
        if tid in seen:
            errors.append(f"{feat_id}: duplicate task id: {tid}")
        seen.add(tid)

        tstatus = task.get("status")
        if tstatus not in TASK_STATUS:
            errors.append(f"{feat_id}/{tid}: invalid task status: {tstatus}")
        if tstatus == "in_progress":
            in_progress.append(tid)

    if len(in_progress) > 1:
        errors.append(f"{feat_id}: more than one in_progress task: {', '.join(in_progress)}")

    cur = state.get("current_task_id")
    if cur is not None and cur not in in_progress:
        errors.append(f"{feat_id}: current_task_id does not match in_progress task")

    # Validate tracked commit messages for tasks that have commit hash.
    for task in task_items:
        commit_hash = task.get("last_commit_hash")
        if not commit_hash:
            continue
        cp = run_cmd(["git", "-C", str(root), "show", "-s", "--format=%B", str(commit_hash)])
        if cp.returncode != 0:
            errors.append(f"{feat_id}/{task.get('id')}: commit hash not found: {commit_hash}")
            continue
        text = cp.stdout
        gate_result = str(task.get("gate_result") or "pass")
        task_status = str(task.get("status") or "done")
        msg_errors = validate_commit_message(
            text,
            expected_feat=feat_id,
            expected_task=str(task.get("id")),
            expected_task_status=task_status if task_status in {"done", "blocked"} else "done",
            expected_gate_result=gate_result if gate_result in GATE_STATUS else "pass",
        )
        if msg_errors:
            errors.append(
                f"{feat_id}/{task.get('id')}: commit message invalid ({'; '.join(msg_errors)})"
            )

    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)
    ensure_git_repo(root)

    errors: list[str] = []
    if not paths.index_file.exists():
        errors.append(f"missing index file: {paths.index_file}")

    feats: list[str] = []
    feat_status_by_id: dict[str, str] = {}
    if paths.index_file.exists():
        try:
            index_data = load_index(paths)
            for item in index_data.get("feats", []):
                feat_id = str(item.get("feat_id", ""))
                if not feat_id:
                    continue
                feats.append(feat_id)
                feat_status_by_id[feat_id] = str(item.get("status") or "")
        except SystemExit as exc:
            errors.append(str(exc))

    for feat_id in feats:
        errors.extend(validate_feat(paths, root, feat_id))

    # Validate physical archive layout.
    for feat_id, status in feat_status_by_id.items():
        active_dir = paths.feat_dir(feat_id)
        archived_dir = paths.feat_dir(feat_id, status="archived")
        if status == "archived":
            if active_dir.exists():
                errors.append(f"{feat_id}: archived feat dir must not exist in feats/: {active_dir}")
            if not archived_dir.exists():
                errors.append(f"{feat_id}: archived feat dir missing: {archived_dir}")
        else:
            if not active_dir.exists():
                errors.append(f"{feat_id}: feat dir missing: {active_dir}")
            if archived_dir.exists():
                errors.append(
                    f"{feat_id}: non-archived feat dir must not exist in feats-archived/: {archived_dir}"
                )

    # Detect feat directories missing from index (active + archived).
    if paths.feats_dir.exists():
        for child in sorted(paths.feats_dir.iterdir()):
            if child.is_dir() and child.name not in feats:
                errors.append(f"feat directory not indexed: {child.name}")
    if paths.feats_archived_dir.exists():
        for child in sorted(paths.feats_archived_dir.iterdir()):
            if child.is_dir() and child.name not in feats:
                errors.append(f"archived feat directory not indexed: {child.name}")

    if errors:
        for err in errors:
            eprint(f"error: {err}")
        eprint(f"failed: {len(errors)} validation error(s)")
        return 1

    print("ok: validation passed")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    paths = HarnessPaths(root)
    ensure_harness_exists(paths)

    val_code = cmd_validate(
        argparse.Namespace(
            root=str(root),
        )
    )
    if val_code != 0:
        eprint("doctor: validation failed first")
        return 1

    config = load_json(paths.config_file) if paths.config_file.exists() else {}
    thresholds = config.get("stop_thresholds", {}) if isinstance(config, dict) else {}
    gate_fail_limit = int(thresholds.get("gate_fail_streak", 3))
    no_progress_limit = int(thresholds.get("no_progress_rounds", 2))
    max_round = int(thresholds.get("max_round_count", 8))

    index_data = load_index(paths)
    warnings: list[str] = []

    for item in index_data.get("feats", []):
        feat_id = str(item.get("feat_id", ""))
        state, tasks = load_feat(paths, feat_id)
        counters = state.get("counters", {})
        fail_streak = int(counters.get("gate_fail_streak", 0))
        no_progress = int(counters.get("no_progress_rounds", 0))
        rounds = int(counters.get("round_count", 0))

        if fail_streak >= gate_fail_limit:
            warnings.append(
                f"{feat_id}: gate_fail_streak={fail_streak} reached threshold {gate_fail_limit}"
            )
        if no_progress >= no_progress_limit:
            warnings.append(
                f"{feat_id}: no_progress_rounds={no_progress} reached threshold {no_progress_limit}"
            )
        if rounds >= max_round:
            warnings.append(
                f"{feat_id}: round_count={rounds} reached threshold {max_round}"
            )

        if state.get("status") == "in_progress" and count_tasks(tasks, "in_progress") == 0:
            warnings.append(f"{feat_id}: feat status in_progress but no task in_progress")

        if state.get("status") == "archived":
            summary_file = paths.feat_summary(feat_id, status="archived")
            if not summary_file.exists():
                warnings.append(f"{feat_id}: archived feat missing summary.md")

    print("== doctor report ==")
    if warnings:
        for w in warnings:
            print(f"warn: {w}")
    else:
        print("no warnings")

    print("\nrecommended next steps:")
    print("1) Address threshold warnings before starting next task.")
    print("2) Run feat_task_harness.sh run-task-gate before every task commit.")
    print("3) Promote living-doc inbox items after feat archive when applicable.")
    return 0


def query_list(paths: HarnessPaths) -> list[dict[str, Any]]:
    index_data = load_index(paths)
    out: list[dict[str, Any]] = []
    for item in index_data.get("feats", []):
        feat_id = str(item.get("feat_id", ""))
        try:
            state, tasks = load_feat(paths, feat_id)
        except SystemExit:
            continue
        out.append(
            {
                "feat_id": feat_id,
                "title": state.get("title", ""),
                "status": state.get("status", ""),
                "branch": state.get("branch", ""),
                "worktree": state.get("worktree_path", ""),
                "updated_at": state.get("updated_at", ""),
                "task_stats": {
                    "todo": count_tasks(tasks, "todo"),
                    "in_progress": count_tasks(tasks, "in_progress"),
                    "done": count_tasks(tasks, "done"),
                    "blocked": count_tasks(tasks, "blocked"),
                },
            }
        )
    return out


def query_one(paths: HarnessPaths, feat_id: str) -> dict[str, Any]:
    state, tasks = load_feat(paths, feat_id)
    return {"state": state, "tasks": tasks}


def query_filter(
    paths: HarnessPaths,
    *,
    feat_status: str | None,
    task_status: str | None,
    contains: str | None,
) -> list[dict[str, Any]]:
    items = query_list(paths)
    out: list[dict[str, Any]] = []
    needle = contains.lower() if contains else None

    for item in items:
        if feat_status and item.get("status") != feat_status:
            continue
        if task_status and int(item.get("task_stats", {}).get(task_status, 0)) == 0:
            continue
        if needle:
            hay = f"{item.get('feat_id','')} {item.get('title','')} {item.get('branch','')}".lower()
            if needle not in hay:
                continue
        out.append(item)
    return out


def cmd_query_list(args: argparse.Namespace) -> int:
    paths = HarnessPaths(Path(args.root).resolve())
    ensure_harness_exists(paths)
    print(json.dumps({"feats": query_list(paths)}, ensure_ascii=False, indent=2))
    return 0


def cmd_query_get(args: argparse.Namespace) -> int:
    paths = HarnessPaths(Path(args.root).resolve())
    ensure_harness_exists(paths)
    print(json.dumps(query_one(paths, args.feat), ensure_ascii=False, indent=2))
    return 0


def cmd_query_filter(args: argparse.Namespace) -> int:
    paths = HarnessPaths(Path(args.root).resolve())
    ensure_harness_exists(paths)
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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="bagakit feat/task harness")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--root", default=".")
        sp.add_argument("--skill-dir", default=str(Path(__file__).resolve().parent.parent))

    sp = sub.add_parser("check-reference-readiness", help="generate reference read report")
    add_common(sp)
    sp.add_argument("--manifest", default=None)
    sp.set_defaults(func=cmd_ref_read_gate)

    sp = sub.add_parser("validate-reference-report", help="validate strict ref-read report")
    add_common(sp)
    sp.add_argument("--manifest", default=None)
    sp.set_defaults(func=cmd_check_ref_report)

    sp = sub.add_parser("initialize-harness", help="apply harness files into project")
    add_common(sp)
    sp.add_argument("--manifest", default=None)
    sp.add_argument("--strict", dest="strict", action="store_true")
    sp.add_argument("--no-strict", dest="strict", action="store_false")
    sp.set_defaults(strict=True, func=cmd_apply)

    sp = sub.add_parser("create-feat", help="create feat + worktree")
    add_common(sp)
    sp.add_argument("--manifest", default=None)
    sp.add_argument("--strict", dest="strict", action="store_true")
    sp.add_argument("--no-strict", dest="strict", action="store_false")
    sp.add_argument("--title", required=True)
    sp.add_argument("--slug", default="")
    sp.add_argument("--goal", required=True)
    sp.set_defaults(strict=True, func=cmd_feat_new)

    sp = sub.add_parser("show-feat-status", help="show feat status")
    add_common(sp)
    sp.add_argument("--feat", default=None)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_feat_status)

    sp = sub.add_parser("start-task", help="start a task")
    add_common(sp)
    sp.add_argument("--feat", required=True)
    sp.add_argument("--task", required=True)
    sp.set_defaults(func=cmd_task_start)

    sp = sub.add_parser("run-task-gate", help="execute gate checks")
    add_common(sp)
    sp.add_argument("--feat", required=True)
    sp.add_argument("--task", required=True)
    sp.set_defaults(func=cmd_task_gate)

    sp = sub.add_parser("prepare-task-commit", help="generate/validate structured commit message")
    add_common(sp)
    sp.add_argument("--feat", required=True)
    sp.add_argument("--task", required=True)
    sp.add_argument("--summary", required=True)
    sp.add_argument("--task-status", choices=["done", "blocked"], default="done")
    sp.add_argument("--message-out", default="")
    sp.add_argument("--execute", action="store_true")
    sp.set_defaults(func=cmd_task_commit)

    sp = sub.add_parser("finish-task", help="finish task with result")
    add_common(sp)
    sp.add_argument("--feat", required=True)
    sp.add_argument("--task", required=True)
    sp.add_argument("--result", choices=["done", "blocked"], required=True)
    sp.set_defaults(func=cmd_task_finish)

    sp = sub.add_parser("archive-feat", help="archive feat (move dir + cleanup worktree)")
    add_common(sp)
    sp.add_argument("--feat", required=True)
    sp.set_defaults(func=cmd_feat_archive)

    sp = sub.add_parser("validate-harness", help="validate harness consistency")
    add_common(sp)
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("diagnose-harness", help="run doctor checks")
    add_common(sp)
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("list-feats", help="query feats list")
    add_common(sp)
    sp.set_defaults(func=cmd_query_list)

    sp = sub.add_parser("get-feat", help="query one feat")
    add_common(sp)
    sp.add_argument("--feat", required=True)
    sp.set_defaults(func=cmd_query_get)

    sp = sub.add_parser("filter-feats", help="query feats with filters")
    add_common(sp)
    sp.add_argument("--status", default=None)
    sp.add_argument("--task-status", choices=["todo", "in_progress", "done", "blocked"], default=None)
    sp.add_argument("--contains", default=None)
    sp.set_defaults(func=cmd_query_filter)

    return p


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
