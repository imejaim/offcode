#!/usr/bin/env bash
# Dr. Oh v3.0 launcher (POSIX).
# Directory name `audrey_v3.0` contains a '.' so it cannot be a Python package;
# we run the inner `src` module with the project root on sys.path.
set -eu
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"
exec python -m src "$@"
