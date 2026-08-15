# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations

import json
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .build import build_project
from .config import load_config
from .util import iter_files


class _State:
    build_id = ""
    lock = threading.Lock()


class _Handler(SimpleHTTPRequestHandler):
    server_version = "IaTDocsDev/0.08"

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        if self.path.split("?", 1)[0] == "/__iatdocs_build_id":
            with _State.lock:
                payload = _State.build_id.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()


def _snapshot(root: Path, output: Path) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    ignored = {".git", ".template-backup", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for path in iter_files(root):
        if output == path or output in path.parents:
            continue
        if any(part in ignored for part in path.parts):
            continue
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        result[path.as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return result


def _watch(root: Path, stop: threading.Event) -> None:
    config = load_config(root)
    previous = _snapshot(root, config.output_dir)
    while not stop.wait(0.75):
        current = _snapshot(root, config.output_dir)
        if current == previous:
            continue
        previous = current
        try:
            result = build_project(root, strict=False, release=False, dev_reload=True)
            with _State.lock:
                _State.build_id = str(result["build_id"])
            print(f"[iatdocs] rebuilt {result['build_id']} ({result['heading_count']} sections)")
        except Exception as exc:  # keep the development server alive to show the last valid build
            print(f"[iatdocs] rebuild failed: {exc}")


def serve_project(root: Path, *, host: str = "127.0.0.1", port: int = 8000, open_browser: bool = False) -> int:
    root = root.resolve()
    result = build_project(root, strict=False, release=False, dev_reload=True)
    config = load_config(root)
    with _State.lock:
        _State.build_id = str(result["build_id"])

    handler = lambda *args, **kwargs: _Handler(*args, directory=str(config.output_dir), **kwargs)  # noqa: E731
    server = ThreadingHTTPServer((host, port), handler)
    stop = threading.Event()
    watcher = threading.Thread(target=_watch, args=(root, stop), daemon=True)
    watcher.start()
    url = f"http://{host}:{port}/"
    print(f"[iatdocs] serving {config.output_dir} at {url}")
    print("[iatdocs] source changes rebuild automatically; open pages reload when the build ID changes")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\n[iatdocs] stopping")
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        watcher.join(timeout=2)
    return 0
