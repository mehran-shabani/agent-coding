"""File system tools for safe file operations."""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
from rich.prompt import Confirm

from ..prompts import SAFETY_WARNINGS, SUCCESS_MESSAGES, ERROR_MESSAGES


console = Console()


def ensure_in_workdir(path: Path, workdir: Path) -> bool:
    """Check if path is within the working directory."""
    try:
        path.resolve().relative_to(workdir.resolve())
        return True
    except ValueError:
        return False


def safe_write_file(
    path: Path, 
    content: str, 
    workdir: Path,
    overwrite: bool = False,
    force: bool = False
) -> Tuple[bool, str]:
    """Safely write content to a file with confirmation."""
    
    # Ensure path is within workdir
    if not ensure_in_workdir(path, workdir):
        return False, f"Path {path} is outside working directory"
    
    # Check if file exists
    if path.exists() and not overwrite:
        return False, f"File {path} already exists. Use --overwrite to replace it."
    
    # Confirm overwrite if needed
    if path.exists() and overwrite and not force:
        console.print(SAFETY_WARNINGS["overwrite"].format(path=path))
        if not Confirm.ask("Continue?"):
            return False, "Operation cancelled by user"
    
    try:
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, SUCCESS_MESSAGES["file_created"].format(path=path)
    except PermissionError:
        return False, ERROR_MESSAGES["permission_denied"].format(path=path)
    except Exception as e:
        return False, f"Error writing file: {e}"


def safe_read_file(path: Path, workdir: Path) -> Tuple[bool, str]:
    """Safely read content from a file."""
    
    # Ensure path is within workdir
    if not ensure_in_workdir(path, workdir):
        return False, f"Path {path} is outside working directory"
    
    if not path.exists():
        return False, ERROR_MESSAGES["file_not_found"].format(path=path)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return True, content
    except PermissionError:
        return False, ERROR_MESSAGES["permission_denied"].format(path=path)
    except Exception as e:
        return False, f"Error reading file: {e}"


def safe_delete(path: Path, workdir: Path, force: bool = False) -> Tuple[bool, str]:
    """Safely delete a file or directory with confirmation."""
    
    # Ensure path is within workdir
    if not ensure_in_workdir(path, workdir):
        return False, f"Path {path} is outside working directory"
    
    if not path.exists():
        return False, ERROR_MESSAGES["file_not_found"].format(path=path)
    
    # Confirm deletion
    if not force:
        console.print(SAFETY_WARNINGS["delete"].format(path=path))
        if not Confirm.ask("Continue?"):
            return False, "Operation cancelled by user"
    
    try:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        
        return True, SUCCESS_MESSAGES["file_deleted"].format(path=path)
    except PermissionError:
        return False, ERROR_MESSAGES["permission_denied"].format(path=path)
    except Exception as e:
        return False, f"Error deleting: {e}"


def list_files(directory: Path, pattern: str = "*") -> list[Path]:
    """List files in a directory matching a pattern."""
    if not directory.exists() or not directory.is_dir():
        return []
    
    return list(directory.glob(pattern))


def get_file_info(path: Path) -> dict:
    """Get information about a file."""
    if not path.exists():
        return {}
    
    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "modified": stat.st_mtime,
    }