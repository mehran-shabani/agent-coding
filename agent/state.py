"""State management for the Local Coding Agent."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

console = Console()


class TodoItem(BaseModel):
    """A single TODO item."""
    
    id: int
    title: str
    description: str = ""
    created: datetime
    completed: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, cancelled
    
    @property
    def is_completed(self) -> bool:
        """Check if todo is completed."""
        return self.status == "completed"
    
    def mark_completed(self):
        """Mark todo as completed."""
        self.status = "completed"
        self.completed = datetime.now()
    
    def mark_in_progress(self):
        """Mark todo as in progress."""
        self.status = "in_progress"
    
    def cancel(self):
        """Cancel the todo."""
        self.status = "cancelled"


class AgentState(BaseModel):
    """Complete agent state."""
    
    version: str = "1.0"
    created: datetime
    last_updated: datetime
    todos: List[TodoItem] = []
    next_todo_id: int = 1
    metadata: Dict = {}
    
    def add_todo(self, title: str, description: str = "") -> TodoItem:
        """Add a new TODO item."""
        todo = TodoItem(
            id=self.next_todo_id,
            title=title,
            description=description,
            created=datetime.now()
        )
        
        self.todos.append(todo)
        self.next_todo_id += 1
        self.last_updated = datetime.now()
        
        return todo
    
    def get_todo(self, todo_id: int) -> Optional[TodoItem]:
        """Get a TODO item by ID."""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def get_pending_todos(self) -> List[TodoItem]:
        """Get all pending TODO items."""
        return [todo for todo in self.todos if todo.status == "pending"]
    
    def get_active_todos(self) -> List[TodoItem]:
        """Get all active (pending or in progress) TODO items."""
        return [todo for todo in self.todos if todo.status in ["pending", "in_progress"]]
    
    def get_completed_todos(self) -> List[TodoItem]:
        """Get all completed TODO items."""
        return [todo for todo in self.todos if todo.status == "completed"]
    
    def mark_todo_done(self, todo_id: int) -> bool:
        """Mark a TODO as completed."""
        todo = self.get_todo(todo_id)
        if todo:
            todo.mark_completed()
            self.last_updated = datetime.now()
            return True
        return False
    
    def add_plan_todos(self, plan: List[str], goal_description: str = "") -> List[TodoItem]:
        """Add multiple TODOs from a plan."""
        added_todos = []
        
        for i, step in enumerate(plan, 1):
            title = f"Step {i}: {step}" if len(plan) > 1 else step
            description = f"Part of plan: {goal_description}" if goal_description else ""
            
            todo = self.add_todo(title, description)
            added_todos.append(todo)
        
        return added_todos


class StateManager:
    """Manages agent state persistence."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._state: Optional[AgentState] = None
    
    def load_state(self) -> AgentState:
        """Load state from file or create new state."""
        if self._state:
            return self._state
        
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created' in data:
                    data['created'] = datetime.fromisoformat(data['created'])
                if 'last_updated' in data:
                    data['last_updated'] = datetime.fromisoformat(data['last_updated'])
                
                for todo_data in data.get('todos', []):
                    if 'created' in todo_data:
                        todo_data['created'] = datetime.fromisoformat(todo_data['created'])
                    if 'completed' in todo_data and todo_data['completed']:
                        todo_data['completed'] = datetime.fromisoformat(todo_data['completed'])
                
                self._state = AgentState(**data)
                console.print(f"[dim]Loaded state with {len(self._state.todos)} TODO items[/dim]")
                
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load state file: {e}[/yellow]")
                console.print("[yellow]Creating new state[/yellow]")
                self._state = AgentState(
                    created=datetime.now(),
                    last_updated=datetime.now()
                )
        else:
            self._state = AgentState(
                created=datetime.now(),
                last_updated=datetime.now()
            )
        
        return self._state
    
    def save_state(self) -> bool:
        """Save current state to file."""
        if not self._state:
            return True  # Nothing to save
        
        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict with ISO format dates
            data = self._state.model_dump()
            
            # Convert datetime objects to ISO strings
            data['created'] = self._state.created.isoformat()
            data['last_updated'] = self._state.last_updated.isoformat()
            
            for todo_data in data['todos']:
                if isinstance(todo_data['created'], datetime):
                    todo_data['created'] = todo_data['created'].isoformat()
                if todo_data.get('completed') and isinstance(todo_data['completed'], datetime):
                    todo_data['completed'] = todo_data['completed'].isoformat()
            
            # Write to file
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error saving state: {e}[/red]")
            return False
    
    def get_state(self) -> AgentState:
        """Get current state (load if not already loaded)."""
        return self.load_state()


def display_todos(todos: List[TodoItem], title: str = "TODO Items") -> None:
    """Display TODO items in a formatted table."""
    
    if not todos:
        console.print(f"[dim]No {title.lower()}[/dim]")
        return
    
    table = Table(title=title)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Status", style="yellow", width=12)
    table.add_column("Title", style="white")
    table.add_column("Created", style="dim", width=12)
    table.add_column("Completed", style="green", width=12)
    
    for todo in todos:
        status_color = {
            "pending": "[yellow]Pending[/yellow]",
            "in_progress": "[blue]In Progress[/blue]",
            "completed": "[green]Completed[/green]",
            "cancelled": "[red]Cancelled[/red]"
        }.get(todo.status, todo.status)
        
        created_str = todo.created.strftime("%m-%d %H:%M")
        completed_str = todo.completed.strftime("%m-%d %H:%M") if todo.completed else ""
        
        table.add_row(
            str(todo.id),
            status_color,
            todo.title,
            created_str,
            completed_str
        )
    
    console.print(table)


def generate_todo_markdown(todos: List[TodoItem]) -> str:
    """Generate Markdown representation of TODO items."""
    
    if not todos:
        return "No TODO items.\n"
    
    content = "# TODO List\n\n"
    
    # Group by status
    statuses = ["pending", "in_progress", "completed", "cancelled"]
    
    for status in statuses:
        status_todos = [todo for todo in todos if todo.status == status]
        if not status_todos:
            continue
        
        status_title = status.replace("_", " ").title()
        content += f"## {status_title}\n\n"
        
        for todo in status_todos:
            checkbox = "- [x]" if todo.status == "completed" else "- [ ]"
            content += f"{checkbox} **#{todo.id}** {todo.title}\n"
            
            if todo.description:
                content += f"  - {todo.description}\n"
            
            content += f"  - Created: {todo.created.strftime('%Y-%m-%d %H:%M')}\n"
            
            if todo.completed:
                content += f"  - Completed: {todo.completed.strftime('%Y-%m-%d %H:%M')}\n"
            
            content += "\n"
    
    return content


def create_state_manager(state_file: Path) -> StateManager:
    """Create and return a state manager."""
    return StateManager(state_file)