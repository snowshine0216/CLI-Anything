"""Session state with undo/redo support."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


MAX_HISTORY = 100


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SessionState:
    source_path: str = ""
    project_path: str = ""
    custom_pipelines: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    modified: bool = False
    updated_at: str = field(default_factory=_now_iso)


class Session:
    """Mutable session object with snapshot-based undo/redo."""

    def __init__(self) -> None:
        self.state = SessionState()
        self._undo_stack: list[SessionState] = []
        self._redo_stack: list[SessionState] = []

    def snapshot(self) -> None:
        self._undo_stack.append(deepcopy(self.state))
        if len(self._undo_stack) > MAX_HISTORY:
            self._undo_stack = self._undo_stack[-MAX_HISTORY:]
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(deepcopy(self.state))
        self.state = self._undo_stack.pop()
        self.state.modified = True
        self.state.updated_at = _now_iso()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(deepcopy(self.state))
        self.state = self._redo_stack.pop()
        self.state.modified = True
        self.state.updated_at = _now_iso()
        return True

    def set_source_path(self, value: str) -> None:
        self.snapshot()
        self.state.source_path = value
        self.state.modified = True
        self.state.updated_at = _now_iso()

    def set_project_path(self, value: str) -> None:
        self.snapshot()
        self.state.project_path = value
        self.state.modified = True
        self.state.updated_at = _now_iso()

    def set_pipeline(self, name: str, steps: list[dict[str, Any]]) -> None:
        self.snapshot()
        self.state.custom_pipelines[name] = steps
        self.state.modified = True
        self.state.updated_at = _now_iso()

    def remove_pipeline(self, name: str) -> bool:
        if name not in self.state.custom_pipelines:
            return False
        self.snapshot()
        del self.state.custom_pipelines[name]
        self.state.modified = True
        self.state.updated_at = _now_iso()
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.state.source_path,
            "project_path": self.state.project_path,
            "custom_pipelines": self.state.custom_pipelines,
            "modified": self.state.modified,
            "updated_at": self.state.updated_at,
            "undo_depth": len(self._undo_stack),
            "redo_depth": len(self._redo_stack),
        }

    def save(self, session_file: str) -> str:
        path = Path(session_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "state": self.to_dict(),
            "undo": [self._state_to_dict(s) for s in self._undo_stack],
            "redo": [self._state_to_dict(s) for s in self._redo_stack],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.state.modified = False
        return str(path)

    def load(self, session_file: str) -> bool:
        path = Path(session_file)
        if not path.exists():
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        state = payload.get("state", {})
        self.state = self._state_from_dict(state)
        self._undo_stack = [self._state_from_dict(x) for x in payload.get("undo", [])]
        self._redo_stack = [self._state_from_dict(x) for x in payload.get("redo", [])]
        return True

    @staticmethod
    def _state_to_dict(state: SessionState) -> dict[str, Any]:
        return {
            "source_path": state.source_path,
            "project_path": state.project_path,
            "custom_pipelines": state.custom_pipelines,
            "modified": state.modified,
            "updated_at": state.updated_at,
        }

    @staticmethod
    def _state_from_dict(data: dict[str, Any]) -> SessionState:
        return SessionState(
            source_path=data.get("source_path", ""),
            project_path=data.get("project_path", ""),
            custom_pipelines=data.get("custom_pipelines", {}),
            modified=bool(data.get("modified", False)),
            updated_at=data.get("updated_at", _now_iso()),
        )
