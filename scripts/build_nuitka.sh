#!/usr/bin/env bash
set -euo pipefail

UV_CACHE_DIR=${UV_CACHE_DIR:-/tmp/uv-cache}
uv run python scripts/build_nuitka.py "$@"
