# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigurationError
from .util import safe_relative


@dataclass(slots=True)
class EngineSettings:
    name: str = "2210Docs"
    version: str = "0.08.2"
    schema_version: int = 1


@dataclass(slots=True)
class SiteSettings:
    title: str = "2210 Controlled Document"
    description: str = "Controlled documentation rendered from repository source."
    language: str = "en"
    base_path: str = "/"


@dataclass(slots=True)
class PathSettings:
    content_dir: str = "content"
    data_dir: str = "data"
    theme_dir: str = "theme"
    output_dir: str = "site"
    attachments_dir: str = "content/attachments"
    document_data: str = "data/document.json"
    repository_data: str = "data/repository.json"
    revisions_data: str = "data/revisions.json"
    contributions_data: str = "data/contributions.json"
    source_register: str = "source-material-register.json"


@dataclass(slots=True)
class BuildSettings:
    mode: str = "single-manual"
    content_files: list[str] = field(default_factory=lambda: ["index.md"])
    clean_output: bool = True
    copy_attachments: bool = True
    emit_search_index: bool = True
    emit_source_map: bool = True
    emit_manifest: bool = True
    allow_raw_html: bool = True
    template: str = "manual.html"


@dataclass(slots=True)
class ReaderSettings:
    bookmark_limit: int = 20
    update_check_seconds: int = 60
    watermark_url: str = "https://software-itops-iat-storage-assets-images.pages.enterprise.example.invalid/brand/Controlled-Reader-WATERMARK.png"


@dataclass(slots=True)
class ValidationSettings:
    forbidden_visible_text: list[str] = field(default_factory=list)
    forbidden_reader_controls: list[str] = field(default_factory=lambda: ["Print", "Export", "Download document"])
    release_placeholders: list[str] = field(default_factory=lambda: [
        "CONFIGURE-", "Configure ", "YYYY-MM-DD", "OWNER/NEW-2210-DOCUMENT-REPOSITORY",
        "SELECT PROFILE", "Not effective", "Approval pending", "reviewer pending",
    ])
    required_data_files: list[str] = field(default_factory=lambda: [
        "document.json", "repository.json", "revisions.json", "contributions.json",
    ])
    require_h2_sections: bool = True


@dataclass(slots=True)
class ProjectConfig:
    root: Path
    engine: EngineSettings = field(default_factory=EngineSettings)
    site: SiteSettings = field(default_factory=SiteSettings)
    paths: PathSettings = field(default_factory=PathSettings)
    build: BuildSettings = field(default_factory=BuildSettings)
    reader: ReaderSettings = field(default_factory=ReaderSettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)

    def path(self, value: str, label: str) -> Path:
        try:
            return safe_relative(self.root, value, label)
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc

    @property
    def content_dir(self) -> Path:
        return self.path(self.paths.content_dir, "content_dir")

    @property
    def data_dir(self) -> Path:
        return self.path(self.paths.data_dir, "data_dir")

    @property
    def theme_dir(self) -> Path:
        return self.path(self.paths.theme_dir, "theme_dir")

    @property
    def output_dir(self) -> Path:
        return self.path(self.paths.output_dir, "output_dir")


def _as_dict(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"[{name}] must be a TOML table")
    return value


def _only_known(values: dict[str, Any], allowed: set[str], name: str) -> None:
    extras = sorted(set(values) - allowed)
    if extras:
        raise ConfigurationError(f"unknown key(s) in [{name}]: {', '.join(extras)}")


def _merge_dataclass(instance: Any, values: dict[str, Any], name: str) -> Any:
    allowed = set(instance.__dataclass_fields__)
    _only_known(values, allowed, name)
    for key, value in values.items():
        setattr(instance, key, value)
    return instance


def load_config(root: Path, config_name: str = "iatdocs.toml") -> ProjectConfig:
    root = root.resolve()
    path = root / config_name
    if not path.is_file():
        raise ConfigurationError(f"configuration file not found: {path}")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"invalid TOML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError(f"configuration root must be a TOML table: {path}")

    _only_known(raw, {"engine", "site", "paths", "build", "reader", "validation"}, "root")
    config = ProjectConfig(root=root)
    config.engine = _merge_dataclass(config.engine, _as_dict(raw.get("engine"), "engine"), "engine")
    config.site = _merge_dataclass(config.site, _as_dict(raw.get("site"), "site"), "site")
    config.paths = _merge_dataclass(config.paths, _as_dict(raw.get("paths"), "paths"), "paths")
    config.build = _merge_dataclass(config.build, _as_dict(raw.get("build"), "build"), "build")
    config.reader = _merge_dataclass(config.reader, _as_dict(raw.get("reader"), "reader"), "reader")
    config.validation = _merge_dataclass(config.validation, _as_dict(raw.get("validation"), "validation"), "validation")

    if config.build.mode != "single-manual":
        raise ConfigurationError("v0.08.2 supports build.mode = 'single-manual'")
    if not isinstance(config.build.content_files, list) or not all(isinstance(item, str) and item for item in config.build.content_files):
        raise ConfigurationError("build.content_files must be a non-empty array of relative Markdown paths")
    if not (1 <= int(config.reader.bookmark_limit) <= 100):
        raise ConfigurationError("reader.bookmark_limit must be between 1 and 100")
    if not (15 <= int(config.reader.update_check_seconds) <= 3600):
        raise ConfigurationError("reader.update_check_seconds must be between 15 and 3600 seconds")
    if not isinstance(config.reader.watermark_url, str) or not config.reader.watermark_url.strip():
        raise ConfigurationError("reader.watermark_url must be a non-empty URL or repository-relative asset path")

    # Force evaluation of all configured paths before any destructive build operation.
    for label, value in (
        ("content_dir", config.paths.content_dir), ("data_dir", config.paths.data_dir),
        ("theme_dir", config.paths.theme_dir), ("output_dir", config.paths.output_dir),
        ("attachments_dir", config.paths.attachments_dir), ("document_data", config.paths.document_data),
        ("repository_data", config.paths.repository_data), ("revisions_data", config.paths.revisions_data),
        ("contributions_data", config.paths.contributions_data), ("source_register", config.paths.source_register),
    ):
        config.path(value, label)
    return config
