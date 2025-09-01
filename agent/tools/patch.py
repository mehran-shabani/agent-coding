"""Patch generation and application tools."""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.prompt import Confirm

from ..prompts import SAFETY_WARNINGS, SUCCESS_MESSAGES, ERROR_MESSAGES


console = Console()


def validate_patch(patch_content: str) -> Tuple[bool, str]:
    """Validate that the patch content is in unified diff format."""
    lines = patch_content.strip().split('\n')
    
    if not lines:
        return False, "Empty patch content"
    
    # Basic validation - check for diff headers
    has_diff_header = False
    for line in lines:
        if line.startswith('---') or line.startswith('+++'):
            has_diff_header = True
            break
    
    if not has_diff_header:
        return False, "Invalid patch format: missing diff headers"
    
    return True, ""


def display_patch(patch_content: str):
    """Display patch content with syntax highlighting."""
    console.print("\n[bold cyan]Patch Preview:[/bold cyan]")
    syntax = Syntax(patch_content, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()


def extract_affected_files(patch_content: str) -> List[str]:
    """Extract list of files affected by the patch."""
    files = []
    lines = patch_content.split('\n')
    
    for line in lines:
        if line.startswith('+++') and not line.startswith('+++ /dev/null'):
            # Extract filename from +++ line
            parts = line.split()
            if len(parts) >= 2:
                filename = parts[1]
                # Remove 'b/' prefix if present
                if filename.startswith('b/'):
                    filename = filename[2:]
                files.append(filename)
    
    return files


def apply_patch(
    patch_content: str,
    workdir: Path,
    force: bool = False,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """Apply a patch to the working directory."""
    
    # Validate patch
    valid, error = validate_patch(patch_content)
    if not valid:
        return False, f"{ERROR_MESSAGES['invalid_patch']}: {error}"
    
    # Extract affected files
    affected_files = extract_affected_files(patch_content)
    
    # Show confirmation if not forced
    if not force and not dry_run:
        files_str = ", ".join(affected_files) if affected_files else "unknown files"
        console.print(SAFETY_WARNINGS["patch"].format(files=files_str))
        
        # Display the patch
        display_patch(patch_content)
        
        if not Confirm.ask("Apply this patch?"):
            return False, "Operation cancelled by user"
    
    # Save patch to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(patch_content)
        patch_file = f.name
    
    try:
        # Prepare patch command
        cmd = ['patch', '-p1']
        if dry_run:
            cmd.append('--dry-run')
        
        # Apply patch
        result = subprocess.run(
            cmd,
            input=patch_content,
            text=True,
            capture_output=True,
            cwd=str(workdir)
        )
        
        if result.returncode == 0:
            if dry_run:
                return True, "Dry run successful - patch can be applied cleanly"
            else:
                return True, SUCCESS_MESSAGES["patch_applied"]
        else:
            error_details = result.stderr or result.stdout
            return False, f"Patch failed: {error_details}"
    
    except FileNotFoundError:
        return False, "patch command not found. Please install patch utility."
    except Exception as e:
        return False, f"Error applying patch: {e}"
    finally:
        # Clean up temp file
        Path(patch_file).unlink(missing_ok=True)


def save_patch(patch_content: str, reports_dir: Path, description: str = "") -> Path:
    """Save a patch to the reports directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sanitize description for filename
    safe_desc = ""
    if description:
        safe_desc = "-" + "".join(c if c.isalnum() or c in "-_" else "_" for c in description)[:50]
    
    filename = f"patch-{timestamp}{safe_desc}.diff"
    patch_path = reports_dir / filename
    
    # Ensure directory exists
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Save patch
    with open(patch_path, 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    return patch_path


def create_file_patch(original_content: str, new_content: str, filename: str) -> str:
    """Create a unified diff patch between two file contents."""
    import difflib
    
    # Split content into lines
    original_lines = original_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    # Generate unified diff
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=''
    )
    
    return ''.join(diff)