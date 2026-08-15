# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .errors import IaTDocsError


def refresh_metrics(
    root: Path,
    *,
    apply: bool = False,
    require_ghe: bool = False,
    recent_limit: int = 30,
    max_commits: int = 5000,
) -> int:
    script = root / "tools" / "refresh_pages_intelligence.py"
    if not script.is_file():
        raise IaTDocsError(f"metrics tool is missing: {script}")
    command = [
        sys.executable,
        str(script),
        "--repo",
        str(root),
        "--recent-limit",
        str(recent_limit),
        "--max-commits",
        str(max_commits),
    ]
    if require_ghe:
        command.append("--require-ghe")
    if apply:
        command.append("--apply")
    completed = subprocess.run(command, cwd=root, text=True)
    return completed.returncode
