#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _check_requirements() -> None:
    if not _has_module("zstandard"):
        print("Missing Python package 'zstandard' (onefile compression disabled).", file=sys.stderr)
        print("Install with: uv add zstandard", file=sys.stderr)

    if sys.platform.startswith("linux") and shutil.which("patchelf") is None:
        print("Missing patchelf. Install with one of:", file=sys.stderr)
        print("  uv add patchelf", file=sys.stderr)
        print("  sudo apt-get install patchelf", file=sys.stderr)
        raise SystemExit(1)


def _select_compiler() -> str | None:
    if os.environ.get("CC"):
        return os.environ["CC"]

    for candidate in ("gcc", "clang"):
        path = shutil.which(candidate)
        if path:
            return candidate

    if sys.platform == "win32":
        # Let Nuitka/Scons discover MSVC if available.
        return None

    print("Missing C compiler (gcc/clang). Install build tools first.", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    _check_requirements()

    env = os.environ.copy()
    compiler = _select_compiler()
    if compiler:
        env["CC"] = compiler

    ccache = shutil.which("ccache")
    if ccache:
        env["NUITKA_CCACHE_BINARY"] = ccache
        if compiler:
            print(f"Using compiler: {compiler} (ccache: {ccache})")
        else:
            print(f"Using auto compiler detection (ccache: {ccache})")
    else:
        if compiler:
            print(f"Using compiler: {compiler}")
        else:
            print("Using auto compiler detection")

    project_root = Path(__file__).resolve().parents[1]
    entry = project_root / "mirava" / "cli.py"
    data_file = project_root / "mirava_full_json.json"

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        "--static-libpython=no",
        "--output-dir=dist",
        "--follow-imports",
        "--include-package=mirava",
        "--include-package=httpx",
        "--include-package=prompt_toolkit",
        f"--include-data-file={data_file}=mirava_full_json.json",
        str(entry),
        *sys.argv[1:],
    ]

    subprocess.run(cmd, check=True, cwd=project_root, env=env)


if __name__ == "__main__":
    main()
