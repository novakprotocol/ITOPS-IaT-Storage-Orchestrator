# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

from .config import ProjectConfig
from .markdown import scan_content_security, strip_legacy_front_matter
from .util import load_json

Severity = Literal["error", "warning", "info"]


@dataclass(slots=True)
class Diagnostic:
    severity: Severity
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "code": self.code, "message": self.message, "path": self.path}


@dataclass(slots=True)
class ValidationReport:
    mode: Literal["template", "release"]
    errors: list[Diagnostic] = field(default_factory=list)
    warnings: list[Diagnostic] = field(default_factory=list)
    info: list[Diagnostic] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def add(self, severity: Severity, code: str, message: str, path: str | None = None) -> None:
        item = Diagnostic(severity=severity, code=code, message=message, path=path)
        if severity == "error":
            self.errors.append(item)
        elif severity == "warning":
            self.warnings.append(item)
        else:
            self.info.append(item)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "passed": self.passed,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "errors": [item.as_dict() for item in self.errors],
            "warnings": [item.as_dict() for item in self.warnings],
            "info": [item.as_dict() for item in self.info],
        }


class _HtmlAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.visible_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(str(values["id"]))
        if tag == "a" and values.get("href"):
            self.hrefs.append(str(values["href"]))

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.visible_parts.append(data)

    @property
    def visible_text(self) -> str:
        return " ".join(self.visible_parts)


def _is_placeholder(value: Any, patterns: list[str]) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    folded = text.casefold()
    return any(pattern.casefold() in folded for pattern in patterns)


def _date_ok(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except (ValueError, TypeError):
        return False
    return True


def _load_object(report: ValidationReport, path: Path, code: str) -> dict[str, Any]:
    try:
        value = load_json(path)
    except (FileNotFoundError, ValueError) as exc:
        report.add("error", code, str(exc), path.as_posix())
        return {}
    if not isinstance(value, dict):
        report.add("error", code, "expected a JSON object", path.as_posix())
        return {}
    return value


def validate_project(config: ProjectConfig, *, mode: Literal["template", "release"] = "template", built_html: Path | None = None) -> ValidationReport:
    report = ValidationReport(mode=mode)
    root = config.root

    structural = {
        "configuration": root / "iatdocs.toml",
        "document data": config.path(config.paths.document_data, "document_data"),
        "repository data": config.path(config.paths.repository_data, "repository_data"),
        "revision data": config.path(config.paths.revisions_data, "revisions_data"),
        "contribution data": config.path(config.paths.contributions_data, "contributions_data"),
        "theme template": config.theme_dir / "templates" / config.build.template,
        "theme CSS": config.theme_dir / "assets" / "css" / "manual.css",
        "theme JavaScript": config.theme_dir / "assets" / "js" / "manual.js",
        "AI contract": root / "AGENTS.md",
        "machine contract": root / "ai" / "template-contract.json",
    }
    for label, path in structural.items():
        if not path.is_file():
            report.add("error", "STRUCTURE_MISSING", f"required {label} is missing", path.as_posix())

    content_files: list[Path] = []
    for item in config.build.content_files:
        try:
            path = config.path(f"{config.paths.content_dir}/{item}", "content file")
        except Exception as exc:
            report.add("error", "CONTENT_PATH", str(exc), item)
            continue
        content_files.append(path)
        if not path.is_file():
            report.add("error", "CONTENT_MISSING", "configured Markdown source is missing", path.as_posix())
            continue
        text = strip_legacy_front_matter(path.read_text(encoding="utf-8"))
        for problem in scan_content_security(text, path.relative_to(root).as_posix()):
            report.add("error", "CONTENT_SECURITY", problem, path.as_posix())
        if config.validation.require_h2_sections and not re.search(r"(?m)^##\s+\S", text):
            report.add("error", "CONTENT_SECTIONS", "document source must contain at least one level-two section", path.as_posix())
        for forbidden in config.validation.forbidden_visible_text:
            if forbidden.casefold() in text.casefold():
                report.add("error", "FORBIDDEN_SUBJECT", f"subject-specific text is forbidden in the canonical template: {forbidden}", path.as_posix())

    doc = _load_object(report, config.path(config.paths.document_data, "document_data"), "DOCUMENT_JSON")
    repo = _load_object(report, config.path(config.paths.repository_data, "repository_data"), "REPOSITORY_JSON")
    revisions = _load_object(report, config.path(config.paths.revisions_data, "revisions_data"), "REVISIONS_JSON")
    contributions = _load_object(report, config.path(config.paths.contributions_data, "contributions_data"), "CONTRIBUTIONS_JSON")

    required_doc = [
        "document_id", "document_type", "title", "subtitle", "summary", "version", "status", "visibility",
        "owner", "steward", "effective_date", "review_date", "source_repository", "source_branch", "content_path",
        "template_version", "creator",
    ]
    for key in required_doc:
        if key not in doc:
            report.add("error", "DOCUMENT_FIELD", f"missing required document field: {key}", config.paths.document_data)
    creator = doc.get("creator") if isinstance(doc.get("creator"), dict) else {}
    if not creator:
        report.add("error", "CREATOR_FIELD", "creator must be a JSON object", config.paths.document_data)
    for key in ("name", "account", "work_ledger_id", "position_number", "created_at"):
        if key not in creator:
            report.add("error", "CREATOR_FIELD", f"missing required creator field: {key}", config.paths.document_data)

    visible_doc = " ".join(str(doc.get(key, "")) for key in ("document_type", "title", "subtitle", "summary"))
    for forbidden in config.validation.forbidden_visible_text:
        if forbidden.casefold() in visible_doc.casefold():
            report.add("error", "FORBIDDEN_SUBJECT", f"subject-specific text is forbidden in canonical document metadata: {forbidden}", config.paths.document_data)

    entries = revisions.get("entries") if isinstance(revisions.get("entries"), list) else []
    if not entries:
        report.add("error", "REVISION_EMPTY", "at least one controlled revision entry is required", config.paths.revisions_data)
    current_version = str(doc.get("version", ""))
    if current_version and not any(isinstance(item, dict) and str(item.get("version", "")) == current_version for item in entries):
        report.add("error", "REVISION_CURRENT", f"revision history does not contain current version {current_version}", config.paths.revisions_data)

    for date_key in ("created_at",):
        value = creator.get(date_key)
        if value and not _date_ok(str(value)):
            report.add("warning" if mode == "template" else "error", "DATE_FORMAT", f"{date_key} must use YYYY-MM-DD", config.paths.document_data)
    for date_key in ("effective_date", "last_review_date", "review_date"):
        value = doc.get(date_key)
        if value and value != "Not effective" and not _date_ok(str(value)):
            report.add("warning" if mode == "template" else "error", "DATE_FORMAT", f"{date_key} must use YYYY-MM-DD", config.paths.document_data)

    css_path = config.theme_dir / "assets" / "css" / "manual.css"
    if css_path.is_file():
        css = css_path.read_text(encoding="utf-8")
        required_watermark = f'background-image: url("{config.reader.watermark_url}")'
        if required_watermark not in css:
            report.add("error", "WATERMARK_URL", "theme CSS must use the governed central watermark URL", css_path.as_posix())
        body_rule = re.search(r"body::before\s*\{(.*?)\}", css, flags=re.S)
        if not body_rule:
            report.add("error", "WATERMARK_RULE", "body::before watermark rule is missing", css_path.as_posix())
        else:
            block = body_rule.group(1)
            if "top: calc(64px + 2.2vh)" not in block or "right: 2.2vw" not in block:
                report.add("error", "WATERMARK_POSITION", "watermark must be fixed in the upper-right below the header", css_path.as_posix())
            if re.search(r"\bbottom\s*:", block):
                report.add("error", "WATERMARK_POSITION", "watermark rule may not use bottom positioning", css_path.as_posix())

    js_path = config.theme_dir / "assets" / "js" / "manual.js"
    if js_path.is_file():
        js = js_path.read_text(encoding="utf-8")
        for marker in ("MAX_MANUAL_BOOKMARKS", "Update available — refresh your browser", "returnMarker", "bookmarkReference"):
            if marker not in js:
                report.add("error", "READER_FEATURE", f"required reader feature marker is missing: {marker}", js_path.as_posix())

    register_path = config.path(config.paths.source_register, "source_register")
    if register_path.exists():
        register = _load_object(report, register_path, "SOURCE_REGISTER_JSON")
        items = register.get("items", [])
        if not isinstance(items, list):
            report.add("error", "SOURCE_REGISTER_FORMAT", "source-material-register items must be an array", register_path.as_posix())
        elif mode == "release":
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    report.add("error", "SOURCE_REGISTER_ITEM", f"source register item {index + 1} must be an object", register_path.as_posix())
                    continue
                if str(item.get("classification", "unverified")).casefold() == "unverified":
                    report.add("error", "SOURCE_UNVERIFIED", f"source register item {index + 1} remains unverified", register_path.as_posix())
    else:
        report.add("warning" if mode == "template" else "error", "SOURCE_REGISTER_MISSING", "source-material-register.json is missing", register_path.as_posix())

    placeholders: list[tuple[str, str]] = []
    for key, value in doc.items():
        if key == "related_documents" or isinstance(value, (dict, list)):
            continue
        if _is_placeholder(value, config.validation.release_placeholders):
            placeholders.append((f"document.{key}", str(value)))
    for key, value in creator.items():
        if _is_placeholder(value, config.validation.release_placeholders):
            placeholders.append((f"document.creator.{key}", str(value)))
    for path in content_files:
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for pattern in config.validation.release_placeholders:
                if pattern.casefold() in text.casefold():
                    placeholders.append((path.relative_to(root).as_posix(), pattern))
                    break

    if placeholders:
        severity: Severity = "warning" if mode == "template" else "error"
        for location, value in placeholders[:40]:
            report.add(severity, "PLACEHOLDER", f"placeholder remains: {value}", location)
        if len(placeholders) > 40:
            report.add(severity, "PLACEHOLDER", f"{len(placeholders) - 40} additional placeholders omitted from report")

    if mode == "release":
        if str(doc.get("status", "")).casefold() in {"draft", "template", "in review", "review"}:
            report.add("error", "RELEASE_STATUS", "release validation requires an approved/effective status", config.paths.document_data)
        if str(doc.get("effective_date", "")).casefold() == "not effective":
            report.add("error", "RELEASE_EFFECTIVE_DATE", "release validation requires an effective date", config.paths.document_data)
        for item in entries:
            if not isinstance(item, dict) or str(item.get("version", "")) != current_version:
                continue
            for key in ("reviewer", "approver"):
                if _is_placeholder(item.get(key), config.validation.release_placeholders):
                    report.add("error", "RELEASE_APPROVAL", f"current revision {key} is incomplete", config.paths.revisions_data)
        if str(repo.get("size_status", "")).casefold() != "generated":
            report.add("error", "REPOSITORY_SIZE", "GHE repository size has not been synchronized", config.paths.repository_data)
        if str(contributions.get("status", "")).casefold() != "generated":
            report.add("error", "CONTRIBUTIONS", "contribution and Work Ledger evidence has not been generated", config.paths.contributions_data)

    if built_html and built_html.is_file():
        text = built_html.read_text(encoding="utf-8")
        audit = _HtmlAudit()
        audit.feed(text)
        duplicates = sorted({value for value in audit.ids if audit.ids.count(value) > 1})
        for value in duplicates:
            report.add("error", "HTML_DUPLICATE_ID", f"duplicate generated HTML id: {value}", built_html.as_posix())
        ids = set(audit.ids)
        for href in audit.hrefs:
            if href.startswith("#") and len(href) > 1 and href[1:] not in ids:
                report.add("error", "HTML_BROKEN_FRAGMENT", f"internal fragment has no target: {href}", built_html.as_posix())
        for forbidden in config.validation.forbidden_visible_text:
            if forbidden.casefold() in audit.visible_text.casefold():
                report.add("error", "HTML_FORBIDDEN_SUBJECT", f"generated reader contains forbidden subject text: {forbidden}", built_html.as_posix())
        for control in config.validation.forbidden_reader_controls:
            if re.search(rf">\s*{re.escape(control)}\s*<", text, flags=re.I):
                report.add("error", "HTML_FORBIDDEN_CONTROL", f"generated reader contains prohibited control: {control}", built_html.as_posix())
        if "{%" in text or "{{" in text:
            report.add("error", "HTML_TEMPLATE_RESIDUE", "unrendered template syntax remains in generated HTML", built_html.as_posix())

    report.add("info", "VALIDATION_SUMMARY", f"validated {len(content_files)} content file(s) in {mode} mode")
    return report


def render_report(report: ValidationReport) -> str:
    lines = [
        f"IaT Docs validation mode: {report.mode}",
        f"Result: {'PASS' if report.passed else 'FAIL'}",
        f"Errors: {len(report.errors)}",
        f"Warnings: {len(report.warnings)}",
        f"Info: {len(report.info)}",
    ]
    for heading, items in (("ERRORS", report.errors), ("WARNINGS", report.warnings), ("INFO", report.info)):
        if not items:
            continue
        lines.append("")
        lines.append(heading)
        for item in items:
            location = f" [{item.path}]" if item.path else ""
            lines.append(f"- {item.code}{location}: {item.message}")
    return "\n".join(lines) + "\n"


def report_json(report: ValidationReport) -> str:
    return json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n"
