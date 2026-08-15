# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import copy
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .errors import IaTDocsError
from .markdown import strip_legacy_front_matter
from .util import load_json, write_json


def _engine_root() -> Path:
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "theme" / "templates" / "manual.html").is_file():
        return candidate
    raise IaTDocsError("cannot locate the 2210Docs source checkout; pass --engine-source")


def migrate_jekyll_project(
    target: Path,
    *,
    engine_source: Path | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    target = target.resolve()
    engine = (engine_source or _engine_root()).resolve()
    required_old = [
        target / "docs" / "index.md",
        target / "docs" / "_data" / "document.json",
        target / "docs" / "_data" / "revisions.json",
        target / "docs" / "assets" / "css" / "manual.css",
        target / "docs" / "assets" / "js" / "manual.js",
    ]
    missing = [str(path) for path in required_old if not path.is_file()]
    if missing:
        raise IaTDocsError("target is not a complete v0.07-style Jekyll document repository:\n" + "\n".join(missing))
    for required in (engine / "iatdocs.toml", engine / "theme" / "templates" / "manual.html"):
        if not required.is_file():
            raise IaTDocsError(f"engine source is incomplete: {required}")

    mappings = [
        (target / "docs" / "index.md", target / "content" / "index.md"),
        (target / "docs" / "_data" / "document.json", target / "data" / "document.json"),
        (target / "docs" / "_data" / "repository.json", target / "data" / "repository.json"),
        (target / "docs" / "_data" / "revisions.json", target / "data" / "revisions.json"),
        (target / "docs" / "_data" / "contributions.json", target / "data" / "contributions.json"),
        (target / "docs" / "_data" / "contribution-config.json", target / "data" / "contribution-config.json"),
    ]
    plan = {
        "status": "planned" if not apply else "applied",
        "target": str(target),
        "engine_source": str(engine),
        "mappings": [{"from": str(source), "to": str(destination)} for source, destination in mappings],
        "preserves_legacy_docs": True,
    }
    if not apply:
        return plan

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = target / ".template-backup" / f"iatdocs-migrate-{stamp}"
    for source, _ in mappings:
        if source.exists():
            destination = backup / source.relative_to(target)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    if (target / "theme").exists():
        shutil.copytree(target / "theme", backup / "theme", dirs_exist_ok=True)
    if (target / "iatdocs.toml").exists():
        shutil.copy2(target / "iatdocs.toml", backup / "iatdocs.toml")

    for source, destination in mappings:
        if not source.is_file():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.name == "index.md":
            destination.write_text(strip_legacy_front_matter(source.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        else:
            shutil.copy2(source, destination)

    old_attachments = target / "docs" / "attachments"
    if old_attachments.exists():
        shutil.copytree(old_attachments, target / "content" / "attachments", dirs_exist_ok=True)
    else:
        (target / "content" / "attachments").mkdir(parents=True, exist_ok=True)

    shutil.copytree(engine / "theme", target / "theme", dirs_exist_ok=True)
    shutil.copy2(engine / "iatdocs.toml", target / "iatdocs.toml")
    for tool_name in ("refresh_pages_intelligence.py", "add_revision.py"):
        source = engine / "tools" / tool_name
        if source.is_file():
            (target / "tools").mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target / "tools" / tool_name)

    document_path = target / "data" / "document.json"
    document = load_json(document_path)
    if not isinstance(document, dict):
        raise IaTDocsError("migrated document data is not a JSON object")
    document = copy.deepcopy(document)
    document["content_path"] = "content/index.md"
    document["template_version"] = f"v{__version__}"
    document["engine_version"] = __version__
    document["contribution_paths"] = [
        "content/index.md", "data/document.json", "data/revisions.json", "content/attachments",
    ]
    write_json(document_path, document)

    contributions_path = target / "data" / "contributions.json"
    if contributions_path.is_file():
        contributions = load_json(contributions_path)
        if isinstance(contributions, dict):
            contributions["tracked_paths"] = list(document["contribution_paths"])
            contributions["source"] = "Run python -m iatdocs metrics --apply after migration"
            contributions["status"] = "migration-refresh-required"
            write_json(contributions_path, contributions)

    register = target / "source-material-register.json"
    if not register.exists():
        write_json(register, {
            "schema_version": 1,
            "document_id": document.get("document_id", ""),
            "items": [],
            "rules": {
                "attachment_is_not_automatically_authoritative": True,
                "attachment_is_not_automatically_an_example": True,
                "unverified_items_cannot_supply_release_authority": True,
            },
        })

    note = target / "LEGACY-JEKYLL-MIGRATION.md"
    note.write_text(
        "# Legacy Jekyll Source Retained\n\n"
        f"2210Docs {__version__} migrated the controlled source into `content/`, `data/`, and `theme/`. "
        "The prior `docs/` tree was preserved for comparison and must not remain the active Pages publication source after cutover.\n",
        encoding="utf-8",
        newline="\n",
    )
    plan["backup"] = str(backup)
    return plan
