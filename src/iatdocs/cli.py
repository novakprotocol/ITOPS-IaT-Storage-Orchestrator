# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from . import __product_name__, __version__
from .build import build_project
from .config import load_config
from .errors import IaTDocsError
from .initdoc import initialize_document
from .metrics import refresh_metrics
from .migrate import migrate_jekyll_project
from .serve import serve_project
from .util import git_metadata, load_json
from .validate import render_report, report_json, validate_project


def _root(value: str) -> Path:
    return Path(value).resolve()


def _json_print(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def _doctor(root: Path) -> dict[str, Any]:
    packages: dict[str, str] = {}
    for distribution in ("MarkupSafe", "Jinja2", "mistune"):
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = "missing"
    config_status: dict[str, Any]
    try:
        config = load_config(root)
        config_status = {
            "status": "valid",
            "output_dir": str(config.output_dir),
            "content_files": list(config.build.content_files),
            "theme_dir": str(config.theme_dir),
        }
    except Exception as exc:
        config_status = {"status": "invalid", "error": str(exc)}
    return {
        "product": __product_name__,
        "engine_version": __version__,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "platform": sys.platform,
        "root": str(root),
        "packages": packages,
        "tools": {
            "git": shutil.which("git") or "missing",
            "gh": shutil.which("gh") or "missing",
        },
        "git": git_metadata(root),
        "configuration": config_status,
    }


def _list_profiles(root: Path) -> dict[str, Any]:
    catalog = load_json(root / "ai" / "document-profiles.json")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("profiles"), list):
        raise IaTDocsError("ai/document-profiles.json is invalid")
    return {
        "count": len(catalog["profiles"]),
        "profiles": [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "document_type": item.get("document_type"),
                "default_mode": item.get("default_mode"),
                "purpose": item.get("purpose"),
            }
            for item in catalog["profiles"] if isinstance(item, dict)
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iatdocs",
        description=f"{__product_name__} {__version__} — Python-native controlled-document compiler",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--repo", default=".", help="Project repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Compile Markdown, data, and the controlled reader theme into a static site")
    build.add_argument("--strict", action="store_true")
    build.add_argument("--release", action="store_true", help="Apply release validation before and after the build")
    build.add_argument("--json", action="store_true")

    validate = sub.add_parser("validate", help="Validate project structure, policy, content, and generated HTML")
    validate.add_argument("--release", action="store_true")
    validate.add_argument("--built", action="store_true", help="Also inspect site/index.html when present")
    validate.add_argument("--json", action="store_true")

    serve = sub.add_parser("serve", help="Build, serve, watch, and live-reload the controlled site")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--open", action="store_true", dest="open_browser")

    doctor = sub.add_parser("doctor", help="Inspect the Python, dependency, Git, GHE CLI, and project environment")
    doctor.add_argument("--json", action="store_true")

    profiles = sub.add_parser("profiles", help="List available GS-2210 document profiles")
    profiles.add_argument("--json", action="store_true")

    metrics = sub.add_parser("metrics", help="Generate repository size, contribution, and Work Ledger evidence")
    metrics.add_argument("--apply", action="store_true")
    metrics.add_argument("--require-ghe", action="store_true")
    metrics.add_argument("--recent-limit", type=int, default=30)
    metrics.add_argument("--max-commits", type=int, default=5000)

    init = sub.add_parser("init", help="Generate a profile-driven controlled document in a derived repository")
    init.add_argument("--profile", required=True)
    init.add_argument("--mode", choices=("minimum", "recommended", "comprehensive"))
    init.add_argument("--document-id", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--source-repository", required=True)
    init.add_argument("--version", default="v0.01")
    init.add_argument("--subtitle")
    init.add_argument("--summary")
    init.add_argument("--creator-name")
    init.add_argument("--creator-account")
    init.add_argument("--creator-work-ledger-id")
    init.add_argument("--creator-position-number")
    init.add_argument("--owner")
    init.add_argument("--steward")
    init.add_argument("--created-at")
    init.add_argument("--review-date")
    init.add_argument("--ghe-host", default="enterprise.example.invalid")
    init.add_argument("--allow-canonical", action="store_true")
    init.add_argument("--apply", action="store_true")
    init.add_argument("--json", action="store_true")

    migrate = sub.add_parser("migrate", help="Migrate a v0.07 Jekyll-derived controlled document to 2210Docs")
    migrate.add_argument("--engine-source")
    migrate.add_argument("--apply", action="store_true")
    migrate.add_argument("--json", action="store_true")

    release = sub.add_parser("release", help="Refresh evidence, validate release gates, and build the publication site")
    release.add_argument("--skip-metrics", action="store_true")
    release.add_argument("--require-ghe", action="store_true")
    release.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = _root(args.repo)
    try:
        if args.command == "build":
            result = build_project(root, strict=args.strict, release=args.release)
            if args.json:
                _json_print(result)
            else:
                print(f"BUILT: {result['index']}")
                print(f"BUILD_ID: {result['build_id']}")
                print(f"SECTIONS: {result['heading_count']}")
                print(f"FILES: {result['output_file_count']}")
            return 0

        if args.command == "validate":
            config = load_config(root)
            built = config.output_dir / "index.html" if args.built else None
            report = validate_project(config, mode="release" if args.release else "template", built_html=built)
            print(report_json(report) if args.json else render_report(report), end="")
            return 0 if report.passed else 2

        if args.command == "serve":
            return serve_project(root, host=args.host, port=args.port, open_browser=args.open_browser)

        if args.command == "doctor":
            result = _doctor(root)
            if args.json:
                _json_print(result)
            else:
                print(f"{result['product']} {result['engine_version']}")
                print(f"Python: {result['python']} ({result['executable']})")
                print(f"MarkupSafe: {result['packages']['MarkupSafe']}")
                print(f"Jinja2: {result['packages']['Jinja2']}")
                print(f"Mistune: {result['packages']['mistune']}")
                print(f"Git: {result['tools']['git']}")
                print(f"gh: {result['tools']['gh']}")
                print(f"Configuration: {result['configuration']['status']}")
                if result['configuration']['status'] == 'invalid':
                    print(result['configuration']['error'])
            return 0 if result["configuration"]["status"] == "valid" else 2

        if args.command == "profiles":
            result = _list_profiles(root)
            if args.json:
                _json_print(result)
            else:
                print(f"PROFILES: {result['count']}")
                for item in result["profiles"]:
                    print(f"- {item['id']}: {item['name']} [{item['default_mode']}]")
            return 0

        if args.command == "metrics":
            return refresh_metrics(
                root,
                apply=args.apply,
                require_ghe=args.require_ghe,
                recent_limit=args.recent_limit,
                max_commits=args.max_commits,
            )

        if args.command == "init":
            result = initialize_document(
                root,
                profile_id=args.profile,
                mode=args.mode,
                document_id=args.document_id,
                title=args.title,
                source_repository=args.source_repository,
                version=args.version,
                subtitle=args.subtitle,
                summary=args.summary,
                creator_name=args.creator_name,
                creator_account=args.creator_account,
                creator_work_ledger_id=args.creator_work_ledger_id,
                creator_position_number=args.creator_position_number,
                owner=args.owner,
                steward=args.steward,
                created_at=args.created_at,
                review_date=args.review_date,
                ghe_host=args.ghe_host,
                allow_canonical=args.allow_canonical,
                apply=args.apply,
            )
            if args.json:
                _json_print(result)
            else:
                print(f"STATUS: {result['status']}")
                print(f"PROFILE: {result['profile']}")
                print(f"MODE: {result['mode']}")
                print(f"SECTIONS: {result['section_count']}")
                print(f"MODULES: {', '.join(str(item) for item in result['modules'])}")
                if not args.apply:
                    print("DRY RUN: add --apply after reviewing the plan.")
            return 0

        if args.command == "migrate":
            result = migrate_jekyll_project(
                root,
                engine_source=Path(args.engine_source).resolve() if args.engine_source else None,
                apply=args.apply,
            )
            if args.json:
                _json_print(result)
            else:
                print(f"STATUS: {result['status']}")
                print(f"TARGET: {result['target']}")
                print(f"MAPPINGS: {len(result['mappings'])}")
                if not args.apply:
                    print("DRY RUN: add --apply after reviewing the migration plan.")
            return 0

        if args.command == "release":
            if not args.skip_metrics:
                code = refresh_metrics(root, apply=True, require_ghe=args.require_ghe)
                if code:
                    return code
            result = build_project(root, strict=True, release=True)
            if args.json:
                _json_print(result)
            else:
                print(f"RELEASE BUILD: {result['index']}")
                print(f"BUILD_ID: {result['build_id']}")
            return 0

        parser.error(f"unknown command: {args.command}")
    except (IaTDocsError, OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0
