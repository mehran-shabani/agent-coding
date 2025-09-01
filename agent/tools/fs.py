"""File system operations for the Local Coding Agent."""

import os
import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm

console = Console()


def safe_delete(path: str, yes: bool = False) -> bool:
    """Safely delete a file or directory with confirmation."""
    target_path = Path(path)
    
    if not target_path.exists():
        console.print(f"[red]Error:[/red] Path '{path}' does not exist")
        return False
    
    # Show what will be deleted
    if target_path.is_file():
        console.print(f"[yellow]File to delete:[/yellow] {target_path.absolute()}")
    else:
        console.print(f"[yellow]Directory to delete:[/yellow] {target_path.absolute()}")
        # Show directory contents
        try:
            contents = list(target_path.iterdir())
            if contents:
                console.print(f"[yellow]Contains {len(contents)} items[/yellow]")
        except PermissionError:
            console.print("[red]Permission denied to read directory contents[/red]")
    
    # Confirm deletion unless --yes flag is used
    if not yes:
        if not Confirm.ask(f"Are you sure you want to delete '{path}'?"):
            console.print("[blue]Deletion cancelled[/blue]")
            return False
    
    try:
        if target_path.is_file():
            target_path.unlink()
            console.print(f"[green]File deleted:[/green] {path}")
        else:
            shutil.rmtree(target_path)
            console.print(f"[green]Directory deleted:[/green] {path}")
        return True
    except PermissionError:
        console.print(f"[red]Permission denied:[/red] Cannot delete '{path}'")
        return False
    except Exception as e:
        console.print(f"[red]Error deleting '{path}':[/red] {e}")
        return False


def safe_write(file_path: str, content: str, overwrite: bool = False) -> bool:
    """Safely write content to a file with confirmation for overwrite."""
    target_path = Path(file_path)
    
    # Check if file exists and handle overwrite
    if target_path.exists() and not overwrite:
        console.print(f"[yellow]File exists:[/yellow] {file_path}")
        if not Confirm.ask("Overwrite existing file?"):
            console.print("[blue]Write cancelled[/blue]")
            return False
    
    try:
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        target_path.write_text(content, encoding='utf-8')
        console.print(f"[green]File written:[/green] {file_path}")
        return True
    except PermissionError:
        console.print(f"[red]Permission denied:[/red] Cannot write to '{file_path}'")
        return False
    except Exception as e:
        console.print(f"[red]Error writing file:[/red] {e}")
        return False


def read_file_safe(file_path: str) -> Optional[str]:
    """Safely read a file and return its contents."""
    target_path = Path(file_path)
    
    if not target_path.exists():
        console.print(f"[red]Error:[/red] File '{file_path}' does not exist")
        return None
    
    if not target_path.is_file():
        console.print(f"[red]Error:[/red] '{file_path}' is not a file")
        return None
    
    try:
        content = target_path.read_text(encoding='utf-8')
        return content
    except PermissionError:
        console.print(f"[red]Permission denied:[/red] Cannot read '{file_path}'")
        return None
    except UnicodeDecodeError:
        console.print(f"[red]Error:[/red] Cannot decode '{file_path}' as UTF-8")
        return None
    except Exception as e:
        console.print(f"[red]Error reading file:[/red] {e}")
        return None


def get_file_info(file_path: str) -> dict:
    """Get information about a file or directory."""
    target_path = Path(file_path)
    
    if not target_path.exists():
        return {"exists": False}
    
    info = {
        "exists": True,
        "path": str(target_path.absolute()),
        "is_file": target_path.is_file(),
        "is_dir": target_path.is_dir(),
    }
    
    try:
        stat = target_path.stat()
        info.update({
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
        })
    except Exception as e:
        info["error"] = str(e)
    
    return info


def list_directory(dir_path: str, show_hidden: bool = False) -> list:
    """List contents of a directory."""
    target_path = Path(dir_path)
    
    if not target_path.exists():
        console.print(f"[red]Error:[/red] Directory '{dir_path}' does not exist")
        return []
    
    if not target_path.is_dir():
        console.print(f"[red]Error:[/red] '{dir_path}' is not a directory")
        return []
    
    try:
        contents = []
        for item in target_path.iterdir():
            if not show_hidden and item.name.startswith('.'):
                continue
            
            info = {
                "name": item.name,
                "path": str(item),
                "is_file": item.is_file(),
                "is_dir": item.is_dir(),
            }
            
            if item.is_file():
                try:
                    info["size"] = item.stat().st_size
                except:
                    info["size"] = 0
            
            contents.append(info)
        
        return sorted(contents, key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    except PermissionError:
        console.print(f"[red]Permission denied:[/red] Cannot read directory '{dir_path}'")
        return []
    except Exception as e:
        console.print(f"[red]Error reading directory:[/red] {e}")
        return []