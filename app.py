"""Vercel Flask entrypoint (repo root)."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "migration-readiness" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from migration_readiness.app import app

__all__ = ["app"]
