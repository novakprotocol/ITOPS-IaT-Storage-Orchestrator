# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import mistune

from .errors import BuildError
from .util import collapse_whitespace, sha256_file, slugify

_FORBIDDEN_HTML = [
    (re.compile(r"<\s*script\b", re.I), "script elements are not allowed in document content"),
    (re.compile(r"<\s*(?:iframe|object|embed|applet|base|meta|link|style)\b", re.I), "active or document-level HTML elements are not allowed in content"),
    (re.compile(r"<\s*(?:form|input|button|textarea|select|option)\b", re.I), "interactive form controls are not allowed in document content"),
    (re.compile(r"\bon[a-z]+\s*=", re.I), "inline event handlers are not allowed in document content"),
    (re.compile(r"javascript\s*:", re.I), "javascript: URLs are not allowed in document content"),
    (re.compile(r"data\s*:\s*text/html", re.I), "data:text/html URLs are not allowed in document content"),
    (re.compile(r"\bsrcdoc\s*=", re.I), "srcdoc is not allowed in document content"),
]

_DIRECTIVE_START = re.compile(r"^:::\s*(control|warning|stop|evidence|note|template)(?:\s+(.+?))?\s*$", re.I)
_FRONT_MATTER = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)
_TAG = re.compile(r"<[^>]+>")


@dataclass(slots=True)
class Heading:
    level: int
    text: str
    anchor: str
    source: str


@dataclass(slots=True)
class RenderedSource:
    source: str
    html: str
    plain_text: str
    headings: list[Heading] = field(default_factory=list)
    sha256: str = ""


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return collapse_whitespace(" ".join(self.parts))


def strip_legacy_front_matter(text: str) -> str:
    return _FRONT_MATTER.sub("", text, count=1)


def scan_content_security(text: str, source: str) -> list[str]:
    problems: list[str] = []
    for pattern, message in _FORBIDDEN_HTML:
        if pattern.search(text):
            problems.append(f"{source}: {message}")
    return problems


def _plain_from_html(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return parser.text()


def _plain_heading(value: str) -> str:
    return collapse_whitespace(html.unescape(_TAG.sub("", value))) or "Section"


class ControlledRenderer(mistune.HTMLRenderer):
    def __init__(self, *, source: str, used_ids: set[str], headings: list[Heading], allow_raw_html: bool) -> None:
        super().__init__(escape=not allow_raw_html)
        self.source = source
        self.used_ids = used_ids
        self.headings = headings
        self.allow_raw_html = allow_raw_html

    def heading(self, text: str, level: int, **attrs: object) -> str:
        visible = _plain_heading(text)
        base = slugify(visible)
        anchor = base
        suffix = 2
        while anchor in self.used_ids:
            anchor = f"{base}-{suffix}"
            suffix += 1
        self.used_ids.add(anchor)
        self.headings.append(Heading(level=level, text=visible, anchor=anchor, source=self.source))
        return f'<h{level} id="{html.escape(anchor)}" class="document-heading level-{level}">{text}</h{level}>\n'

    def link(self, text: str, url: str, title: str | None = None) -> str:
        parsed = urlparse(url)
        attrs = ""
        if parsed.scheme in {"http", "https"}:
            attrs = ' rel="noopener noreferrer"'
        title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
        return f'<a href="{html.escape(url, quote=True)}"{title_attr}{attrs}>{text}</a>'

    def image(self, text: str, url: str, title: str | None = None) -> str:
        title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
        alt = _plain_heading(text)
        return f'<img src="{html.escape(url, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy"{title_attr}>'

    def block_html(self, value: str) -> str:
        if not self.allow_raw_html:
            return html.escape(value)
        return value

    def inline_html(self, value: str) -> str:
        if not self.allow_raw_html:
            return html.escape(value)
        return value


def _directive_inner_renderer() -> mistune.Markdown:
    return mistune.create_markdown(
        escape=False,
        renderer=mistune.HTMLRenderer(escape=False),
        plugins=["table", "strikethrough", "task_lists", "url"],
    )


def expand_directives(text: str) -> str:
    """Convert small semantic callout blocks into the reader theme's callout markup.

    Syntax::

        ::: warning Optional title
        Markdown body.
        :::
    """
    lines = text.splitlines()
    output: list[str] = []
    index = 0
    inner_markdown = _directive_inner_renderer()
    while index < len(lines):
        match = _DIRECTIVE_START.match(lines[index])
        if not match:
            output.append(lines[index])
            index += 1
            continue
        kind = match.group(1).lower()
        title = (match.group(2) or kind.title()).strip()
        body: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip() != ":::":
            body.append(lines[index])
            index += 1
        if index >= len(lines):
            raise BuildError(f"unterminated ::: {kind} directive")
        index += 1
        rendered = inner_markdown("\n".join(body).strip()) if body else ""
        output.append(f'<aside class="callout {html.escape(kind)}">')
        output.append(f'<strong>{html.escape(title)}</strong>')
        output.append(rendered)
        output.append("</aside>")
    return "\n".join(output)


def render_markdown_files(
    files: Iterable[Path],
    *,
    root: Path,
    allow_raw_html: bool,
) -> tuple[str, list[RenderedSource], list[Heading]]:
    used_ids: set[str] = set()
    all_headings: list[Heading] = []
    rendered_sources: list[RenderedSource] = []
    html_parts: list[str] = []

    for path in files:
        if not path.is_file():
            raise BuildError(f"content file not found: {path}")
        source = path.resolve().relative_to(root.resolve()).as_posix()
        raw = path.read_text(encoding="utf-8")
        body = strip_legacy_front_matter(raw)
        problems = scan_content_security(body, source)
        if problems:
            raise BuildError("unsafe document content:\n- " + "\n- ".join(problems))
        body = expand_directives(body)
        headings: list[Heading] = []
        renderer = ControlledRenderer(
            source=source,
            used_ids=used_ids,
            headings=headings,
            allow_raw_html=allow_raw_html,
        )
        markdown = mistune.create_markdown(
            escape=not allow_raw_html,
            renderer=renderer,
            plugins=["table", "strikethrough", "task_lists", "url"],
        )
        rendered_html = markdown(body)
        plain_text = _plain_from_html(rendered_html)
        rendered = RenderedSource(
            source=source,
            html=rendered_html,
            plain_text=plain_text,
            headings=headings,
            sha256=sha256_file(path),
        )
        rendered_sources.append(rendered)
        all_headings.extend(headings)
        html_parts.append(rendered_html)

    return "\n".join(html_parts), rendered_sources, all_headings
