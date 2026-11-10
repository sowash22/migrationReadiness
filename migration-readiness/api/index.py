"""Vercel serverless entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from migration_readiness.app import app  # noqa: E402

# Vercel looks for a module-level WSGI/ASGI callable named `app`.
__all__ = ["app"]
