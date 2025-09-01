"""
File system operations for Local Coding Agent.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

from ..config import get_config

console = Console()


class FileSystemTool:
    """Tool for safe file system operations."""
    
    def __init__(self):
        self.config = get_config()
    
    def read_file(self, file_path: str) -> Optional[str]:
        """Read file content safely."""
        path = Path(file_path)
        
        if not path.exists():
            console.print(f"[red]Error: File {file_path} does not exist[/red]")
            return None
        
        if not path.is_file():
            console.print(f"[red]Error: {file_path} is not a file[/red]")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            console.print(f"[red]Error reading file {file_path}: {e}[/red]")
            return None
    
    def write_file(
        self, 
        file_path: str, 
        content: str, 
        overwrite: bool = False,
        confirm: bool = True
    ) -> bool:
        """Write file content safely."""
        path = Path(file_path)
        
        # Check if file exists and handle overwrite
        if path.exists() and not overwrite:
            if confirm:
                if not Confirm.ask(f"File {file_path} already exists. Overwrite?"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return False
            else:
                console.print(f"[red]Error: File {file_path} already exists. Use --overwrite to force.[/red]")
                return False
        
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            console.print(f"[green]File {file_path} written successfully[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error writing file {file_path}: {e}[/red]")
            return False
    
    def delete_file(
        self, 
        file_path: str, 
        recursive: bool = False,
        confirm: bool = True
    ) -> bool:
        """Delete file or directory safely."""
        path = Path(file_path)
        
        if not path.exists():
            console.print(f"[red]Error: {file_path} does not exist[/red]")
            return False
        
        # Safety checks
        if confirm:
            if path.is_file():
                if not Confirm.ask(f"Delete file {file_path}?"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return False
            elif path.is_dir():
                if not Confirm.ask(f"Delete directory {file_path} and all contents?"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return False
        
        try:
            if path.is_file():
                path.unlink()
                console.print(f"[green]File {file_path} deleted successfully[/green]")
            elif path.is_dir():
                if recursive:
                    shutil.rmtree(path)
                    console.print(f"[green]Directory {file_path} deleted successfully[/green]")
                else:
                    console.print(f"[red]Error: {file_path} is a directory. Use --recursive to delete.[/red]")
                    return False
            return True
        except Exception as e:
            console.print(f"[red]Error deleting {file_path}: {e}[/red]")
            return False
    
    def list_directory(self, dir_path: str = ".") -> list:
        """List directory contents."""
        path = Path(dir_path)
        
        if not path.exists():
            console.print(f"[red]Error: Directory {dir_path} does not exist[/red]")
            return []
        
        if not path.is_dir():
            console.print(f"[red]Error: {dir_path} is not a directory[/red]")
            return []
        
        try:
            items = []
            for item in path.iterdir():
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'is_file': item.is_file(),
                    'is_dir': item.is_dir(),
                    'size': item.stat().st_size if item.is_file() else None,
                }
                items.append(item_info)
            return items
        except Exception as e:
            console.print(f"[red]Error listing directory {dir_path}: {e}[/red]")
            return []
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get detailed file information."""
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        try:
            stat = path.stat()
            return {
                'name': path.name,
                'path': str(path),
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'permissions': oct(stat.st_mode)[-3:],
            }
        except Exception as e:
            console.print(f"[red]Error getting file info for {file_path}: {e}[/red]")
            return None
    
    def ensure_directory(self, dir_path: str) -> bool:
        """Ensure directory exists."""
        path = Path(dir_path)
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            console.print(f"[red]Error creating directory {dir_path}: {e}[/red]")
            return False
    
    def is_safe_path(self, path: str) -> bool:
        """Check if path is safe to operate on."""
        # Prevent operations outside working directory
        workdir = Path(self.config.agent_workdir).resolve()
        target_path = Path(path).resolve()
        
        try:
            # Check if target path is within working directory
            return workdir in target_path.parents or target_path == workdir
        except Exception:
            return False