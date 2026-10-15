#!/usr/bin/env python3
"""Fixed-slot isolated Git worktrees."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
from urllib.parse import urlparse


SLOT_COUNT = 6
DEFAULT_ROOT = Path(
    os.environ.get("AGENT_WORKTREE_ROOT", str(Path.home() / "worktrees"))
).expanduser()
DEFAULT_REMOTE = "origin"


class SlotError(RuntimeError):
    """User-facing failure."""


@dataclass
class WorktreeEntry:
    path: Path
    branch: Optional[str]


def run(
    command: list[str],
    *,
    cwd: Optional[Path] = None,
    capture: bool = False,
    dry_run: bool = False,
) -> str:
    if dry_run:
        print("$ " + " ".join(command), file=sys.stderr, flush=True)
        return ""
    # Keep stdout JSON-only; child chatter goes to stderr.
    options: dict[str, object] = {
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if cwd is not None:
        options["cwd"] = str(cwd)
    try:
        completed = subprocess.run(command, check=True, **options)
    except FileNotFoundError as error:
        raise SlotError(f"required command not found: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        raise SlotError(detail or f"command exited {error.returncode}") from error
    if not capture:
        if completed.stdout:
            print(completed.stdout, file=sys.stderr, end="", flush=True)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="", flush=True)
        return ""
    return str(completed.stdout).strip()


def git(
    repo: Path, *arguments: str, capture: bool = False, dry_run: bool = False
) -> str:
    return run(
        ["git", "-C", str(repo), *arguments],
        capture=capture,
        dry_run=dry_run,
    )


def repository_root(path: Path) -> Path:
    try:
        value = run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture=True,
        )
    except SlotError as error:
        raise SlotError(f"{path} is not a Git checkout") from error
    return Path(value).resolve()


def primary_worktree(repo: Path) -> Path:
    value = git(repo, "worktree", "list", "--porcelain", capture=True)
    first_line = value.splitlines()[0] if value else ""
    if not first_line.startswith("worktree "):
        raise SlotError(f"cannot determine the primary worktree for {repo}")
    return Path(first_line.removeprefix("worktree ")).resolve()


def parse_worktree_list(repo: Path) -> list[WorktreeEntry]:
    value = git(repo, "worktree", "list", "--porcelain", capture=True)
    entries: list[WorktreeEntry] = []
    path: Optional[Path] = None
    branch: Optional[str] = None
    for line in value.splitlines():
        if line.startswith("worktree "):
            if path is not None:
                entries.append(WorktreeEntry(path=path, branch=branch))
            path = Path(line.removeprefix("worktree ")).resolve()
            branch = None
        elif line.startswith("branch "):
            ref = line.removeprefix("branch ")
            branch = ref.removeprefix("refs/heads/")
        elif line == "detached":
            branch = None
    if path is not None:
        entries.append(WorktreeEntry(path=path, branch=branch))
    return entries


def local_branch_exists(repo: Path, branch: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
        ],
        check=False,
    )
    return result.returncode == 0


def remote_ref_exists(repo: Path, remote: str, branch: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/remotes/{remote}/{branch}",
        ],
        check=False,
    )
    return result.returncode == 0


def discover_pr_branch(repo: Path, pull_request: int) -> str:
    value = run(
        [
            "gh",
            "pr",
            "view",
            str(pull_request),
            "--json",
            "headRefName,isCrossRepository,headRepository,headRepositoryOwner",
        ],
        cwd=repo,
        capture=True,
    )
    try:
        metadata = json.loads(value)
    except json.JSONDecodeError as error:
        raise SlotError(f"could not resolve pull request #{pull_request}") from error
    branch = metadata.get("headRefName")
    if not branch:
        raise SlotError(f"could not resolve pull request #{pull_request}")
    if metadata.get("isCrossRepository"):
        owner = (metadata.get("headRepositoryOwner") or {}).get("login", "unknown")
        repository = (metadata.get("headRepository") or {}).get("name", "unknown")
        raise SlotError(
            f"pull request #{pull_request} comes from fork {owner}/{repository}; "
            "add that fork as a Git remote, fetch its head branch, then rerun with "
            f"--branch {branch}"
        )
    return str(branch)


def _slug_token(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._")
    return token or "repo"


def repo_storage_key(repo: Path, remote: str) -> str:
    """Prefer origin owner/repo so two clones with the same basename do not collide."""
    result = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", remote],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode == 0:
        url = result.stdout.strip()
        owner_repo = _owner_repo_from_remote(url)
        if owner_repo:
            return _slug_token(owner_repo)
    digest = hashlib.sha1(str(repo.resolve()).encode("utf-8")).hexdigest()[:8]
    return f"{_slug_token(repo.name)}-{digest}"


def _owner_repo_from_remote(url: str) -> Optional[str]:
    if url.startswith("git@"):
        match = re.match(r"git@[^:]+:(.+?)(?:\.git)?$", url)
        if match:
            return match.group(1).strip("/")
        return None
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https", "ssh", "git"} and parsed.path:
        path = parsed.path.strip("/").removesuffix(".git")
        return path or None
    return None


def spin_payload(
    *,
    repo: Path,
    storage_key: str,
    worktree: Path,
    branch: str,
    slot: Optional[int],
    reused: bool,
    dry_run: bool,
    kind: str,
) -> dict:
    return {
        "repo": str(repo),
        "storage_key": storage_key,
        "worktree": str(worktree),
        "branch": branch,
        "slot": slot,
        "kind": kind,
        "reused": reused,
        "dry_run": dry_run,
    }


def ensure_local_branch(repo: Path, branch: str, remote: str, *, dry_run: bool) -> None:
    try:
        git(repo, "fetch", remote, branch, dry_run=dry_run)
    except SlotError:
        # Local-only branches have nothing to fetch.
        if not local_branch_exists(repo, branch):
            raise
    if local_branch_exists(repo, branch):
        return
    if not remote_ref_exists(repo, remote, branch) and not dry_run:
        raise SlotError(
            f"branch {branch!r} not found locally or as {remote}/{branch}"
        )
    git(
        repo,
        "branch",
        "--track",
        branch,
        f"{remote}/{branch}",
        dry_run=dry_run,
    )


def slot_path(root: Path, storage_key: str, slot: int) -> Path:
    return (root / storage_key / f"slot-{slot}").resolve()


def paths_match(left: Path, right: Path) -> bool:
    left_r = left.resolve()
    right_r = right.resolve()
    if left_r == right_r:
        return True
    try:
        return left.exists() and right.exists() and left.samefile(right)
    except OSError:
        return False


def entry_by_path(
    entries: list[WorktreeEntry], path: Path
) -> Optional[WorktreeEntry]:
    for entry in entries:
        if paths_match(entry.path, path):
            return entry
    return None


def slot_state(
    path: Path, entries: list[WorktreeEntry]
) -> tuple[str, Optional[str]]:
    entry = entry_by_path(entries, path)
    if entry is not None:
        return "in-use", entry.branch
    if path.exists():
        return "orphan-dir", None
    return "missing", None


def find_branch_checkout(
    branch: str, entries: list[WorktreeEntry]
) -> Optional[WorktreeEntry]:
    for entry in entries:
        if entry.branch == branch:
            return entry
    return None


def find_slot_for_path(root: Path, storage_key: str, path: Path) -> Optional[int]:
    for slot in range(1, SLOT_COUNT + 1):
        if paths_match(slot_path(root, storage_key, slot), path):
            return slot
    return None


def is_dirty(worktree: Path) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(worktree),
            "status",
            "--porcelain",
            "--untracked-files=normal",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SlotError(
            (result.stderr or result.stdout or f"status failed in {worktree}").strip()
        )
    return bool(result.stdout.strip())


@contextmanager
def repo_lock(
    root: Path, storage_key: str, *, attempts: int = 10, delay_s: float = 0.05
) -> Iterator[None]:
    lock_dir = root / storage_key
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / ".slot-worktree.lock"
    try:
        handle = lock_file.open("a+", encoding="utf-8")
    except OSError as error:
        raise SlotError(f"cannot open lock {lock_file}: {error}") from error
    locked = False
    try:
        for attempt in range(attempts):
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                break
            except BlockingIOError:
                if attempt + 1 >= attempts:
                    raise SlotError(f"lock busy: {lock_file}") from None
                time.sleep(delay_s)
        yield
    finally:
        try:
            if locked:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def cmd_status(repo: Path, root: Path, storage_key: str) -> int:
    entries = parse_worktree_list(repo)
    slots = []
    for slot in range(1, SLOT_COUNT + 1):
        path = slot_path(root, storage_key, slot)
        state, branch = slot_state(path, entries)
        slots.append(
            {
                "slot": slot,
                "path": str(path),
                "state": state,
                "branch": branch,
            }
        )
    print(
        json.dumps(
            {
                "repo": str(repo),
                "storage_key": storage_key,
                "worktree_root": str(root),
                "slots": slots,
            },
            indent=2,
        )
    )
    return 0


def cmd_spin(
    repo: Path,
    root: Path,
    storage_key: str,
    *,
    branch: str,
    slot: Optional[int],
    remote: str,
    dry_run: bool,
) -> int:
    # Fetch outside the lock so concurrent spins are not blocked on the network.
    ensure_local_branch(repo, branch, remote, dry_run=dry_run)

    with repo_lock(root, storage_key):
        entries = parse_worktree_list(repo)

        existing = find_branch_checkout(branch, entries)
        if existing is not None:
            existing_slot = find_slot_for_path(root, storage_key, existing.path)
            if existing_slot is not None:
                print(
                    json.dumps(
                        spin_payload(
                            repo=repo,
                            storage_key=storage_key,
                            worktree=existing.path,
                            branch=branch,
                            slot=existing_slot,
                            reused=True,
                            dry_run=dry_run,
                            kind="slot",
                        ),
                        indent=2,
                    )
                )
                return 0
            kind = "control" if paths_match(existing.path, repo) else "other"
            print(
                json.dumps(
                    spin_payload(
                        repo=repo,
                        storage_key=storage_key,
                        worktree=existing.path,
                        branch=branch,
                        slot=None,
                        reused=True,
                        dry_run=dry_run,
                        kind=kind,
                    ),
                    indent=2,
                )
            )
            return 0

        chosen: Optional[int] = None
        if slot is not None:
            if slot < 1 or slot > SLOT_COUNT:
                raise SlotError(f"--slot must be 1..{SLOT_COUNT}")
            path = slot_path(root, storage_key, slot)
            state, _ = slot_state(path, entries)
            if state != "missing":
                raise SlotError(
                    f"slot-{slot} is not free (state={state}, path={path})"
                )
            chosen = slot
        else:
            for candidate in range(1, SLOT_COUNT + 1):
                path = slot_path(root, storage_key, candidate)
                state, _ = slot_state(path, entries)
                if state == "missing":
                    chosen = candidate
                    break
            if chosen is None:
                raise SlotError(
                    f"no free slots (1..{SLOT_COUNT}) under {root / storage_key}; "
                    "run status, then free a slot"
                )

        destination = slot_path(root, storage_key, chosen)
        destination.parent.mkdir(parents=True, exist_ok=True)
        git(repo, "worktree", "add", str(destination), branch, dry_run=dry_run)

    print(
        json.dumps(
            spin_payload(
                repo=repo,
                storage_key=storage_key,
                worktree=destination,
                branch=branch,
                slot=chosen,
                reused=False,
                dry_run=dry_run,
                kind="slot",
            ),
            indent=2,
        )
    )
    return 0


def cmd_free(
    repo: Path,
    root: Path,
    storage_key: str,
    *,
    slot: Optional[int],
    branch: Optional[str],
    force: bool,
    dry_run: bool,
) -> int:
    with repo_lock(root, storage_key):
        entries = parse_worktree_list(repo)

        target_slot: Optional[int] = slot
        target_path: Optional[Path] = None

        if branch is not None:
            existing = find_branch_checkout(branch, entries)
            if existing is None:
                raise SlotError(f"branch {branch!r} is not checked out in any worktree")
            target_path = existing.path
            target_slot = find_slot_for_path(root, storage_key, existing.path)
            if target_slot is None:
                raise SlotError(
                    f"branch {branch!r} is checked out at {existing.path}, "
                    "which is not a slot-* path under this skill"
                )
        elif slot is not None:
            if slot < 1 or slot > SLOT_COUNT:
                raise SlotError(f"--slot must be 1..{SLOT_COUNT}")
            target_slot = slot
            target_path = slot_path(root, storage_key, slot)
        else:
            raise SlotError("choose --slot or --branch")

        assert target_path is not None and target_slot is not None
        state, current_branch = slot_state(target_path, entries)

        if state == "missing":
            raise SlotError(f"slot-{target_slot} is already free ({target_path})")

        if state == "orphan-dir":
            if not force:
                raise SlotError(
                    f"slot-{target_slot} is an orphan directory (not in git worktree "
                    f"list): {target_path}; re-run with --force to delete"
                )
            if dry_run:
                print(f"$ rm -rf {target_path}", file=sys.stderr, flush=True)
            else:
                shutil.rmtree(target_path)
        else:
            if not force and is_dirty(target_path):
                raise SlotError(
                    f"slot-{target_slot} has uncommitted changes at {target_path}; "
                    "commit/stash, or re-run with --force"
                )
            remove = ["worktree", "remove", str(target_path)]
            if force:
                remove.append("--force")
            try:
                git(repo, *remove, dry_run=dry_run)
            except SlotError as error:
                if force:
                    raise
                raise SlotError(
                    f"{error}; if the directory still has ignored files, re-run "
                    "with --force"
                ) from error

    print(
        json.dumps(
            {
                "repo": str(repo),
                "storage_key": storage_key,
                "worktree": str(target_path),
                "branch": current_branch if state == "in-use" else branch,
                "slot": target_slot,
                "freed": True,
                "force": force,
                "dry_run": dry_run,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    spin = sub.add_parser("spin", help="allocate or reuse a slot worktree")
    spin.add_argument("--branch")
    spin.add_argument("--pr", type=int)
    spin.add_argument("--slot", type=int)
    spin.add_argument("--repo", default=".")
    spin.add_argument("--worktree-root", default=str(DEFAULT_ROOT))
    spin.add_argument("--remote", default=DEFAULT_REMOTE)
    spin.add_argument("--dry-run", action="store_true")

    status = sub.add_parser("status", help="list slot-1..6")
    status.add_argument("--repo", default=".")
    status.add_argument("--worktree-root", default=str(DEFAULT_ROOT))
    status.add_argument("--remote", default=DEFAULT_REMOTE)

    free = sub.add_parser("free", help="release a slot worktree")
    free.add_argument("--slot", type=int)
    free.add_argument("--branch")
    free.add_argument("--repo", default=".")
    free.add_argument("--worktree-root", default=str(DEFAULT_ROOT))
    free.add_argument("--remote", default=DEFAULT_REMOTE)
    free.add_argument("--force", action="store_true")
    free.add_argument("--dry-run", action="store_true")

    return parser


def resolve_repo(repo_arg: str) -> Path:
    supplied = repository_root(Path(repo_arg).expanduser())
    return primary_worktree(supplied)


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        repo = resolve_repo(args.repo)
        root = Path(args.worktree_root).expanduser().resolve()
        remote = getattr(args, "remote", DEFAULT_REMOTE)
        storage_key = repo_storage_key(repo, remote)

        if args.command == "status":
            return cmd_status(repo, root, storage_key)

        if args.command == "spin":
            if (args.branch is None) == (args.pr is None):
                parser.error("spin requires exactly one of --branch or --pr")
            branch = (
                args.branch
                if args.branch is not None
                else discover_pr_branch(repo, args.pr)
            )
            return cmd_spin(
                repo,
                root,
                storage_key,
                branch=branch,
                slot=args.slot,
                remote=args.remote,
                dry_run=args.dry_run,
            )

        if args.command == "free":
            if (args.slot is None) == (args.branch is None):
                parser.error("free requires exactly one of --slot or --branch")
            return cmd_free(
                repo,
                root,
                storage_key,
                slot=args.slot,
                branch=args.branch,
                force=args.force,
                dry_run=args.dry_run,
            )

        parser.error(f"unknown command {args.command}")
    except SlotError as error:
        print(f"slot-worktree: {error}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
