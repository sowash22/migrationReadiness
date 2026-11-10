"""Vercel entry when the GitHub repo root is the project root."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "migration-readiness" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from migration_readiness.app import app  # noqa: E402

__all__ = ["app"]
