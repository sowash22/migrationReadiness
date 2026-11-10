from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from migration_readiness.state import StateStore
from migration_readiness.types import MigrationState


@dataclass
class AgentResult:
    agent: str
    summary: str
    state: MigrationState
    details: dict[str, Any] = field(default_factory=dict)


class BaseAgent(Protocol):
    name: str

    def run(
        self,
        state: MigrationState,
        store: StateStore,
        **kwargs: Any,
    ) -> AgentResult: ...
