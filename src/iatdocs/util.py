# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

_SLUG_BAD = re.compile(r"[^a-z0-9]+")
_WS = re.compile(r"\s+")
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_'&./:-]*")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    value = value.strip().lower().replace("&", " and ")
    value = _SLUG_BAD.sub("-", value).strip("-")
    return value or "section"


def collapse_whitespace(value: str) -> str:
    return _WS.sub(" ", value).strip()


def normalized_words(value: str) -> list[str]:
    return [match.group(0).lower() for match in _WORD.finditer(value)]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path, *, required: bool = True, default: Any = None) -> Any:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def safe_relative(root: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be a project-relative path without '..': {value}")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"{label} escapes the project root: {value}")
    return resolved


def safe_clean_dir(path: Path, root: Path) -> None:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved == root_resolved or root_resolved not in resolved.parents:
        raise ValueError(f"refusing to clean unsafe output path: {path}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_tree_contents(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def iter_files(path: Path) -> Iterable[Path]:
    if not path.exists():
        return
    for item in sorted(path.rglob("*")):
        if item.is_file():
            yield item


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def run_command(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def run_git(root: Path, args: list[str]) -> str | None:
    try:
        completed = run_command(["git", *args], cwd=root, check=True)
    except (FileNotFoundError, RuntimeError):
        return None
    return completed.stdout.strip()


def git_metadata(root: Path) -> dict[str, Any]:
    commit = run_git(root, ["rev-parse", "HEAD"]) or "uncommitted"
    short = run_git(root, ["rev-parse", "--short=12", "HEAD"]) or commit[:12]
    branch = run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"
    status = run_git(root, ["status", "--porcelain"])
    return {"commit": commit, "short_commit": short, "branch": branch, "dirty": bool(status)}


def deterministic_digest(files: Iterable[Path], root: Path, *, extra: Iterable[str] = ()) -> str:
    digest = hashlib.sha256()
    for item in sorted(set(path.resolve() for path in files if path.is_file()), key=lambda p: p.as_posix()):
        rel = relative_posix(item, root)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    for value in extra:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def format_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(max(0, value))
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}
