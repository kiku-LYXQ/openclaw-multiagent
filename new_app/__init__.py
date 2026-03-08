from __future__ import annotations

from pathlib import Path

__all__ = []

# Extend the package search path to include the repository root so that
# modules located at the project root (server.py, run.py, etc.) can be
# accessed via the `new_app` package namespace.
__path__.append(str(Path(__file__).resolve().parents[1]))
