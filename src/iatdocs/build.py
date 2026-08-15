# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from dataclasses import asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from . import __product_name__, __version__
from .config import ProjectConfig, load_config
from .errors import BuildError, ValidationFailure
from .markdown import Heading, RenderedSource, render_markdown_files
from .util import (
    copy_tree_contents,
    deterministic_digest,
    git_metadata,
    iter_files,
    load_json,
    normalized_words,
    relative_posix,
    safe_clean_dir,
    sha256_file,
    utc_now,
    write_json,
)
from .validate import render_report, validate_project


class _SectionCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None
        self.capture_heading = False
        self.heading_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h2":
            if self.current:
                self.sections.append(self.current)
            self.current = {"anchor": str(values.get("id") or ""), "title": "", "parts": []}
            self.capture_heading = True
            self.heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self.capture_heading:
            if self.current is not None:
                self.current["title"] = " ".join(self.heading_parts).strip()
            self.capture_heading = False

    def handle_data(self, data: str) -> None:
        clean = data.strip()
        if not clean:
            return
        if self.capture_heading:
            self.heading_parts.append(clean)
        elif self.current is not None:
            self.current["parts"].append(clean)

    def close(self) -> None:
        super().close()
        if self.current:
            self.sections.append(self.current)
            self.current = None


def _content_paths(config: ProjectConfig) -> list[Path]:
    return [config.path(f"{config.paths.content_dir}/{item}", "content file") for item in config.build.content_files]


def _load_data_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = load_json(path)
    except (FileNotFoundError, ValueError) as exc:
        raise BuildError(f"cannot load {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"{label} must be a JSON object: {path}")
    return value


def _derive_repository_url(doc: dict[str, Any]) -> str:
    configured = str(doc.get("repository_url") or "").strip().rstrip("/")
    if configured:
        return configured
    source = str(doc.get("source_repository") or "").strip().strip("/")
    host = str(doc.get("ghe_host") or "").strip().strip("/")
    if not source or not host or source.upper().startswith("OWNER/") or "CONFIGURE" in source.upper():
        return ""
    return f"https://{host}/{source}"


def _search_index(content_html: str, sources: list[RenderedSource], *, stop_words: set[str]) -> dict[str, Any]:
    collector = _SectionCollector()
    collector.feed(content_html)
    collector.close()
    sections: list[dict[str, Any]] = []
    vocabulary: Counter[str] = Counter()
    for index, section in enumerate(collector.sections, start=1):
        text = " ".join(section.pop("parts", []))
        words = [word for word in normalized_words(text) if len(word) > 1 and word not in stop_words]
        counts = Counter(words)
        vocabulary.update(counts)
        excerpt = text if len(text) <= 320 else text[:317].rsplit(" ", 1)[0] + "…"
        sections.append({
            "id": index,
            "title": section.get("title") or f"Section {index}",
            "anchor": section.get("anchor") or "",
            "url": f"index.html#{section.get('anchor') or ''}",
            "excerpt": excerpt,
            "terms": dict(counts.most_common(600)),
        })
    return {
        "schema_version": 1,
        "engine": "iatdocs",
        "engine_version": __version__,
        "source_files": [{"path": item.source, "sha256": item.sha256} for item in sources],
        "section_count": len(sections),
        "vocabulary_size": len(vocabulary),
        "sections": sections,
    }


def _render_404(doc: dict[str, Any]) -> str:
    title = str(doc.get("title") or "Controlled document")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Not found — {title}</title><meta http-equiv="refresh" content="3; url=./index.html">
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:760px;margin:10vh auto;padding:24px;line-height:1.5}}a{{color:#1686cf}}</style></head>
<body><h1>Page not found</h1><p>This controlled site uses a single authoritative manual entry point.</p><p><a href="./index.html">Open the controlled document</a></p></body></html>"""


def _build_source_files(config: ProjectConfig, content_files: list[Path]) -> list[Path]:
    """Return every controlled input that can affect the generated publication.

    The list intentionally includes the compiler source and contract catalogs, not only
    the subject Markdown. That makes the source digest and build manifest useful for
    reproducibility and release evidence even when a compiler change does not alter the
    document content.
    """
    files: list[Path] = [
        config.root / "iatdocs.toml",
        config.root / "pyproject.toml",
        config.root / "requirements.txt",
        config.root / "TEMPLATE_VERSION",
        *content_files,
    ]
    for configured in (
        config.paths.document_data,
        config.paths.repository_data,
        config.paths.revisions_data,
        config.paths.contributions_data,
        config.paths.source_register,
    ):
        path = config.path(configured, configured)
        if path.is_file():
            files.append(path)
    for directory in (
        config.theme_dir,
        config.path(config.paths.attachments_dir, "attachments_dir"),
        config.root / "src" / "iatdocs",
        config.root / "ai",
        config.root / "schemas",
        config.root / "section-library",
    ):
        files.extend(iter_files(directory))
    for tool in ("refresh_pages_intelligence.py", "add_revision.py"):
        path = config.root / "tools" / tool
        if path.is_file():
            files.append(path)
    return sorted({path.resolve() for path in files if path.is_file()})


def build_project(
    root: Path,
    *,
    strict: bool = False,
    release: bool = False,
    dev_reload: bool = False,
    config_name: str = "iatdocs.toml",
) -> dict[str, Any]:
    config = load_config(root, config_name=config_name)
    mode = "release" if release else "template"
    preflight = validate_project(config, mode=mode)
    if not preflight.passed:
        raise ValidationFailure(render_report(preflight))

    content_files = _content_paths(config)
    content_html, rendered_sources, headings = render_markdown_files(
        content_files,
        root=config.root,
        allow_raw_html=bool(config.build.allow_raw_html),
    )

    doc = _load_data_object(config.path(config.paths.document_data, "document_data"), "document data")
    repo = _load_data_object(config.path(config.paths.repository_data, "repository_data"), "repository data")
    revisions = _load_data_object(config.path(config.paths.revisions_data, "revisions_data"), "revision data")
    contributions = _load_data_object(config.path(config.paths.contributions_data, "contributions_data"), "contribution data")
    revision_entries = revisions.get("entries") if isinstance(revisions.get("entries"), list) else []
    contributors = contributions.get("contributors") if isinstance(contributions.get("contributors"), list) else []
    recent_edits = contributions.get("recent_edits") if isinstance(contributions.get("recent_edits"), list) else []
    mapped_contributors = int(contributions.get("mapped_work_ledger_contributors") or 0)

    source_files = _build_source_files(config, content_files)
    source_digest = deterministic_digest(source_files, config.root, extra=[__version__, config.build.mode])
    build_id = source_digest[:20]
    generated_at = utc_now()
    git = git_metadata(config.root)

    repository_url = _derive_repository_url(doc)
    branch = str(doc.get("source_branch") or "main")
    content_path = str(doc.get("content_path") or f"{config.paths.content_dir}/{config.build.content_files[0]}")
    edit_content_url = str(doc.get("edit_url") or "").strip()
    if not edit_content_url and repository_url:
        edit_content_url = f"{repository_url}/edit/{branch}/{content_path}"
    edit_control_url = f"{repository_url}/edit/{branch}/{config.paths.document_data}" if repository_url else ""
    edit_revisions_url = f"{repository_url}/edit/{branch}/{config.paths.revisions_data}" if repository_url else ""
    repo_tooltip = (
        f"Repository: {repo.get('repository', doc.get('source_repository', 'Not configured'))} · "
        f"Source: {repo.get('source', 'Not generated')} · Last measured: {repo.get('measured_at', 'Not generated')} · "
        f"Policy: {repo.get('policy', 'Not recorded')}"
    )

    output = config.output_dir
    if config.build.clean_output:
        safe_clean_dir(output, config.root)
    else:
        output.mkdir(parents=True, exist_ok=True)

    assets_source = config.theme_dir / "assets"
    copy_tree_contents(assets_source, output / "assets")
    rendered_css = output / "assets" / "css" / "manual.css"
    if rendered_css.is_file():
        css_text = rendered_css.read_text(encoding="utf-8")
        css_text = re.sub(
            r'background-image:\s*url\(["\'][^"\']*Controlled-Reader-WATERMARK\.png["\']\)',
            f'background-image: url("{config.reader.watermark_url}")',
            css_text,
            count=1,
        )
        rendered_css.write_text(css_text, encoding="utf-8", newline="\n")
    attachments_source = config.path(config.paths.attachments_dir, "attachments_dir")
    if config.build.copy_attachments and attachments_source.exists():
        copy_tree_contents(attachments_source, output / "attachments")

    environment = Environment(
        loader=FileSystemLoader(str(config.theme_dir / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template(config.build.template)
    context = {
        "site": asdict(config.site),
        "reader": asdict(config.reader),
        "doc": doc,
        "repo": repo,
        "revisions": revisions,
        "revision_entries": revision_entries,
        "contributions": contributions,
        "contributors": contributors,
        "recent_edits": recent_edits,
        "mapped_contributors": mapped_contributors,
        "content_html": content_html,
        "headings": headings,
        "engine_name": __product_name__,
        "engine_version": __version__,
        "build_id": build_id,
        "generated_at": generated_at,
        "git": git,
        "asset_prefix": "",
        "document_key": f"{doc.get('source_repository', '')}|{doc.get('document_id', '')}",
        "repository_url": repository_url,
        "edit_content_url": edit_content_url,
        "edit_control_url": edit_control_url,
        "edit_revisions_url": edit_revisions_url,
        "repo_tooltip": repo_tooltip,
        "paths": asdict(config.paths),
        "dev_reload": dev_reload,
    }
    html_output = template.render(**context)
    (output / "index.html").write_text(html_output, encoding="utf-8", newline="\n")
    (output / "404.html").write_text(_render_404(doc), encoding="utf-8", newline="\n")
    (output / ".nojekyll").write_text("", encoding="utf-8")

    if config.build.emit_search_index:
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or",
            "that", "the", "this", "to", "with",
        }
        write_json(output / "search-index.json", _search_index(content_html, rendered_sources, stop_words=stop_words))

    site_version = {
        "schema_version": 1,
        "engine": "iatdocs",
        "engine_version": __version__,
        "build_id": build_id,
        "document_id": doc.get("document_id"),
        "document_version": doc.get("version"),
        "source_commit": git["commit"],
        "branch": git["branch"],
        "generated_at": generated_at,
    }
    write_json(output / "site-version.json", site_version)

    if config.build.emit_source_map:
        source_map = {
            "schema_version": 1,
            "engine": "iatdocs",
            "engine_version": __version__,
            "build_id": build_id,
            "content": [
                {
                    "path": source.source,
                    "sha256": source.sha256,
                    "headings": [asdict(item) for item in source.headings],
                }
                for source in rendered_sources
            ],
        }
        write_json(output / "source-map.json", source_map)

    built_validation = validate_project(config, mode=mode, built_html=output / "index.html")
    if not built_validation.passed:
        raise ValidationFailure(render_report(built_validation))
    if strict and built_validation.warnings and release:
        raise ValidationFailure(render_report(built_validation))

    # Write the human receipt before the manifest so the manifest can hash it. The
    # manifest intentionally excludes itself to avoid a circular hash dependency.
    pre_receipt_files = [item for item in iter_files(output) if item.name not in {"build-manifest.json", "build-receipt.txt"}]
    final_file_count = len(pre_receipt_files) + 1 + (1 if config.build.emit_manifest else 0)
    receipt = [
        f"{__product_name__} {__version__}",
        f"BUILD_ID={build_id}",
        f"GENERATED_AT={generated_at}",
        f"DOCUMENT_ID={doc.get('document_id', '')}",
        f"DOCUMENT_VERSION={doc.get('version', '')}",
        f"SOURCE_COMMIT={git['commit']}",
        f"SOURCE_DIGEST_SHA256={source_digest}",
        f"OUTPUT_FILES={final_file_count}",
        f"VALIDATION_ERRORS={len(built_validation.errors)}",
        f"VALIDATION_WARNINGS={len(built_validation.warnings)}",
    ]
    (output / "build-receipt.txt").write_text("\n".join(receipt) + "\n", encoding="utf-8", newline="\n")

    output_files = [item for item in iter_files(output) if item.name != "build-manifest.json"]
    manifest = {
        "schema_version": 1,
        "product": __product_name__,
        "engine": "iatdocs",
        "engine_version": __version__,
        "build_id": build_id,
        "generated_at": generated_at,
        "document": {
            "document_id": doc.get("document_id"),
            "title": doc.get("title"),
            "version": doc.get("version"),
            "status": doc.get("status"),
        },
        "git": git,
        "source_digest": source_digest,
        "source_files": [
            {"path": relative_posix(path, config.root), "sha256": sha256_file(path)} for path in source_files
        ],
        "output_files": [
            {"path": relative_posix(path, output), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in output_files
        ],
        "validation": built_validation.as_dict(),
    }
    if config.build.emit_manifest:
        write_json(output / "build-manifest.json", manifest)

    return {
        "status": "built",
        "root": str(config.root),
        "output": str(output),
        "index": str(output / "index.html"),
        "build_id": build_id,
        "engine_version": __version__,
        "content_files": [relative_posix(path, config.root) for path in content_files],
        "heading_count": len(headings),
        "output_file_count": len(list(iter_files(output))),
        "validation": built_validation.as_dict(),
    }
