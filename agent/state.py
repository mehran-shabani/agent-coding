from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict


@dataclass
class TodoItem:
    id: str
    content: str
    status: str = "pending"  # pending | in_progress | completed | cancelled


@dataclass
class AgentState:
    todos: List[TodoItem] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"todos": [item.__dict__ for item in self.todos]}

    @staticmethod
    def from_dict(data: Dict) -> "AgentState":
        todos = [TodoItem(**t) for t in data.get("todos", [])]
        return AgentState(todos=todos)


class StateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AgentState:
        if not self.path.exists():
            return AgentState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return AgentState.from_dict(data)

    def save(self, state: AgentState) -> None:
        self.path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
