from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from migration_readiness.types import MigrationState, STAGE_ORDER


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StateStore:
    """Durable JSON-backed case store (Python stand-in for host.kv)."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(".migration-state")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, case_id: str) -> Path:
        return self.root / f"{case_id.upper()}.json"

    def load(self, case_id: str) -> MigrationState | None:
        path = self._path(case_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return MigrationState.from_dict(data)

    def save(self, state: MigrationState) -> MigrationState:
        state.updated_at = utc_now()
        path = self._path(state.case_id)
        path.write_text(
            json.dumps(state.to_dict(), indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        return state

    def create(self, case_id: str) -> MigrationState:
        now = utc_now()
        state = MigrationState(
            case_id=case_id.upper(),
            stage="intake",
            created_at=now,
            updated_at=now,
        )
        return self.save(state)

    def require(self, case_id: str) -> MigrationState:
        state = self.load(case_id)
        if state is None:
            raise ValueError(
                f'Unknown migration case "{case_id}". Run intake first.'
            )
        return state


def stage_index(stage: str) -> int:
    return STAGE_ORDER.index(stage)  # type: ignore[arg-type]
