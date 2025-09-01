"""State management for TODO items and agent state."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class TodoItem(BaseModel):
    """Model for a TODO item."""
    id: int
    text: str
    status: str = "pending"  # pending, done
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def mark_done(self):
        """Mark this TODO item as done."""
        self.status = "done"
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "id": self.id,
            "text": self.text,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoItem":
        """Create TodoItem from dictionary."""
        # Parse datetime strings
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


class AgentState:
    """Manages agent state including TODO items."""
    
    def __init__(self, state_file: Path):
        """Initialize state manager."""
        self.state_file = state_file
        self.todos: List[TodoItem] = []
        self.next_todo_id = 1
        self.load()
    
    def load(self):
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.todos = [TodoItem.from_dict(item) for item in data.get("todos", [])]
                    self.next_todo_id = data.get("next_todo_id", 1)
            except Exception:
                # If loading fails, start fresh
                self.todos = []
                self.next_todo_id = 1
    
    def save(self):
        """Save state to file."""
        data = {
            "todos": [todo.to_dict() for todo in self.todos],
            "next_todo_id": self.next_todo_id,
            "last_updated": datetime.now().isoformat()
        }
        
        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_todo(self, text: str) -> TodoItem:
        """Add a new TODO item."""
        todo = TodoItem(id=self.next_todo_id, text=text)
        self.todos.append(todo)
        self.next_todo_id += 1
        self.save()
        return todo
    
    def get_todo(self, todo_id: int) -> Optional[TodoItem]:
        """Get a TODO item by ID."""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def mark_todo_done(self, todo_id: int) -> bool:
        """Mark a TODO item as done."""
        todo = self.get_todo(todo_id)
        if todo and todo.status == "pending":
            todo.mark_done()
            self.save()
            return True
        return False
    
    def list_todos(self, status: Optional[str] = None) -> List[TodoItem]:
        """List TODO items, optionally filtered by status."""
        if status:
            return [todo for todo in self.todos if todo.status == status]
        return self.todos
    
    def get_markdown_todos(self) -> str:
        """Get TODO list as markdown."""
        if not self.todos:
            return "No TODO items."
        
        lines = ["# TODO List\n"]
        
        # Pending items
        pending = [t for t in self.todos if t.status == "pending"]
        if pending:
            lines.append("## 📋 Pending\n")
            for todo in pending:
                lines.append(f"- [ ] #{todo.id}: {todo.text}")
            lines.append("")
        
        # Completed items
        done = [t for t in self.todos if t.status == "done"]
        if done:
            lines.append("## ✅ Completed\n")
            for todo in done:
                completed_date = todo.completed_at.strftime("%Y-%m-%d %H:%M") if todo.completed_at else ""
                lines.append(f"- [x] #{todo.id}: {todo.text} ({completed_date})")
        
        return "\n".join(lines)