#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WIN_SCRIPT="$(wslpath -w "$SCRIPT_DIR/auto_freeze.py")"
PYTHON_EXE="/mnt/c/Users/conta/AppData/Local/Programs/Python/Python312/python.exe"

exec "$PYTHON_EXE" "$WIN_SCRIPT" "$@"
