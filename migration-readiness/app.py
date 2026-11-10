"""Vercel Flask entrypoint when Root Directory is migration-readiness."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from migration_readiness.app import app

__all__ = ["app"]
