from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TodoStatus = Literal["pending", "in_progress", "completed", "cancelled"]


class TodoItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    status: TodoStatus = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class AgentState(BaseModel):
    todos: List[TodoItem] = Field(default_factory=list)


def load_state(path: Path) -> AgentState:
    if not path.exists():
        return AgentState()
    data = json.loads(path.read_text() or "{}")
    todos = [TodoItem(**t) for t in data.get("todos", [])]
    return AgentState(todos=todos)


def save_state(path: Path, state: AgentState) -> None:
    data = state.model_dump()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def add_todo(path: Path, title: str, status: TodoStatus = "pending") -> TodoItem:
    state = load_state(path)
    item = TodoItem(title=title, status=status)
    state.todos.append(item)
    save_state(path, state)
    return item


def list_todos(path: Path) -> List[TodoItem]:
    state = load_state(path)
    return state.todos


def mark_todo_done(path: Path, todo_id_or_index: str) -> Optional[TodoItem]:
    state = load_state(path)
    target: Optional[TodoItem] = None
    if todo_id_or_index.isdigit():
        idx = int(todo_id_or_index)
        if 0 <= idx < len(state.todos):
            target = state.todos[idx]
    else:
        for t in state.todos:
            if t.id.startswith(todo_id_or_index):
                target = t
                break
    if not target:
        return None
    target.status = "completed"
    target.updated_at = datetime.now().isoformat()
    save_state(path, state)
    return target


def todos_markdown(todos: List[TodoItem]) -> str:
    if not todos:
        return "(no todos)"
    lines = ["| # | id | status | title |", "|---|---|---|---|"]
    for idx, t in enumerate(todos):
        lines.append(f"| {idx} | {t.id[:8]} | {t.status} | {t.title} |")
    return "\n".join(lines)
