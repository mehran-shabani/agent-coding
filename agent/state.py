"""
State management for Local Coding Agent.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pydantic
from rich.console import Console

from .config import get_config

console = Console()


class TodoItem(pydantic.BaseModel):
    """TODO item model."""
    
    id: int
    title: str
    description: Optional[str] = None
    created_at: datetime = pydantic.Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    completed: bool = False
    
    def mark_completed(self) -> None:
        """Mark the TODO item as completed."""
        self.completed = True
        self.completed_at = datetime.now()


class AgentState(pydantic.BaseModel):
    """Agent state model."""
    
    todos: List[TodoItem] = pydantic.Field(default_factory=list)
    last_analysis: Optional[datetime] = None
    project_info: Optional[Dict[str, Any]] = None
    created_at: datetime = pydantic.Field(default_factory=datetime.now)
    updated_at: datetime = pydantic.Field(default_factory=datetime.now)
    
    def add_todo(self, title: str, description: Optional[str] = None) -> TodoItem:
        """Add a new TODO item."""
        todo_id = max([todo.id for todo in self.todos], default=0) + 1
        todo = TodoItem(id=todo_id, title=title, description=description)
        self.todos.append(todo)
        self.updated_at = datetime.now()
        return todo
    
    def get_todo(self, todo_id: int) -> Optional[TodoItem]:
        """Get a TODO item by ID."""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def complete_todo(self, todo_id: int) -> bool:
        """Complete a TODO item by ID."""
        todo = self.get_todo(todo_id)
        if todo and not todo.completed:
            todo.mark_completed()
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_pending_todos(self) -> List[TodoItem]:
        """Get all pending TODO items."""
        return [todo for todo in self.todos if not todo.completed]
    
    def get_completed_todos(self) -> List[TodoItem]:
        """Get all completed TODO items."""
        return [todo for todo in self.todos if todo.completed]
    
    def update_project_info(self, info: Dict[str, Any]) -> None:
        """Update project information."""
        self.project_info = info
        self.last_analysis = datetime.now()
        self.updated_at = datetime.now()


class StateManager:
    """Manager for agent state persistence."""
    
    def __init__(self):
        self.config = get_config()
        self.state_file = self.config.agent_state
        self._state: Optional[AgentState] = None
    
    def load_state(self) -> AgentState:
        """Load state from file."""
        if self._state is not None:
            return self._state
        
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._state = AgentState(**data)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load state file: {e}[/yellow]")
                self._state = AgentState()
        else:
            self._state = AgentState()
        
        return self._state
    
    def save_state(self) -> None:
        """Save state to file."""
        if self._state is None:
            return
        
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self._state.model_dump(), f, indent=2, default=str)
        except Exception as e:
            console.print(f"[red]Error saving state: {e}[/red]")
    
    def get_state(self) -> AgentState:
        """Get current state."""
        return self.load_state()
    
    def update_state(self, state: AgentState) -> None:
        """Update and save state."""
        self._state = state
        self.save_state()


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def get_state() -> AgentState:
    """Get current agent state."""
    return get_state_manager().get_state()


def save_state(state: AgentState) -> None:
    """Save agent state."""
    get_state_manager().update_state(state)