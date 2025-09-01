"""Patch generation and application for the Local Coding Agent."""

import difflib
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax

console = Console()


class PatchResult:
    """Result of patch operations."""
    
    def __init__(self, success: bool, message: str, patch_content: Optional[str] = None):
        self.success = success
        self.message = message
        self.patch_content = patch_content
        self.timestamp = datetime.now()


def generate_unified_diff(original_content: str, modified_content: str, 
                         filename: str = "file") -> str:
    """Generate unified diff between two strings."""
    
    original_lines = original_content.splitlines(keepends=True)
    modified_lines = modified_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    )
    
    return ''.join(diff)


def generate_file_patch(file_path: str, new_content: str) -> PatchResult:
    """Generate a patch for a single file."""
    
    target_path = Path(file_path)
    
    # Read current content
    if target_path.exists():
        try:
            original_content = target_path.read_text(encoding='utf-8')
        except Exception as e:
            return PatchResult(False, f"Error reading file {file_path}: {e}")
    else:
        original_content = ""
    
    # Generate diff
    if original_content == new_content:
        return PatchResult(True, "No changes needed", "")
    
    patch_content = generate_unified_diff(original_content, new_content, file_path)
    
    if not patch_content:
        return PatchResult(False, "Failed to generate diff")
    
    return PatchResult(True, f"Patch generated for {file_path}", patch_content)


def parse_unified_diff(patch_content: str) -> List[Dict]:
    """Parse unified diff format into structured data."""
    
    files = []
    current_file = None
    
    lines = patch_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # File header
        if line.startswith('--- '):
            if current_file:
                files.append(current_file)
            
            current_file = {
                'original_file': line[4:].strip(),
                'modified_file': '',
                'hunks': []
            }
        
        elif line.startswith('+++ ') and current_file:
            current_file['modified_file'] = line[4:].strip()
        
        # Hunk header
        elif line.startswith('@@') and current_file:
            # Parse hunk header: @@ -start,count +start,count @@
            match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                hunk = {
                    'old_start': old_start,
                    'old_count': old_count,
                    'new_start': new_start,
                    'new_count': new_count,
                    'lines': []
                }
                
                # Read hunk content
                i += 1
                while i < len(lines) and not lines[i].startswith('@@') and not lines[i].startswith('---'):
                    hunk_line = lines[i]
                    if hunk_line.startswith(' ') or hunk_line.startswith('+') or hunk_line.startswith('-'):
                        hunk['lines'].append(hunk_line)
                    i += 1
                
                current_file['hunks'].append(hunk)
                continue
        
        i += 1
    
    if current_file:
        files.append(current_file)
    
    return files


def apply_patch_to_file(file_path: str, patch_data: Dict) -> PatchResult:
    """Apply patch data to a single file."""
    
    target_path = Path(file_path)
    
    # Read current content
    if target_path.exists():
        try:
            lines = target_path.read_text(encoding='utf-8').splitlines()
        except Exception as e:
            return PatchResult(False, f"Error reading file {file_path}: {e}")
    else:
        lines = []
    
    # Apply hunks in reverse order to maintain line numbers
    for hunk in reversed(patch_data['hunks']):
        try:
            # Apply hunk
            old_start = hunk['old_start'] - 1  # Convert to 0-based indexing
            
            # Remove old lines and add new ones
            new_lines = []
            hunk_lines = hunk['lines']
            
            for hunk_line in hunk_lines:
                if hunk_line.startswith('+'):
                    new_lines.append(hunk_line[1:])  # Add line (remove +)
                elif hunk_line.startswith(' '):
                    new_lines.append(hunk_line[1:])  # Context line (remove space)
                # Skip lines starting with '-' (deleted lines)
            
            # Replace the section
            end_line = old_start + hunk['old_count']
            lines[old_start:end_line] = new_lines
            
        except Exception as e:
            return PatchResult(False, f"Error applying hunk: {e}")
    
    # Write modified content
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return PatchResult(True, f"Patch applied successfully to {file_path}")
    except Exception as e:
        return PatchResult(False, f"Error writing file {file_path}: {e}")


def display_patch(patch_content: str, filename: str = "patch") -> None:
    """Display patch content with syntax highlighting."""
    
    if not patch_content.strip():
        console.print("[yellow]No changes to display[/yellow]")
        return
    
    console.print(Panel(
        Syntax(patch_content, "diff", theme="monokai", line_numbers=True),
        title=f"Patch Preview: {filename}",
        border_style="blue"
    ))


def save_patch(patch_content: str, patch_dir: Path, description: str = "patch") -> Path:
    """Save patch content to a file."""
    
    patch_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_desc = re.sub(r'[^\w\-_]', '_', description.lower())[:20]
    filename = f"{safe_desc}-{timestamp}.patch"
    
    patch_file = patch_dir / filename
    
    try:
        patch_file.write_text(patch_content, encoding='utf-8')
        console.print(f"[green]Patch saved to:[/green] {patch_file}")
        return patch_file
    except Exception as e:
        console.print(f"[red]Error saving patch:[/red] {e}")
        raise


def apply_patch_file(patch_file: Path, base_dir: Path, dry_run: bool = False) -> List[PatchResult]:
    """Apply a patch file to the specified base directory."""
    
    if not patch_file.exists():
        return [PatchResult(False, f"Patch file not found: {patch_file}")]
    
    try:
        patch_content = patch_file.read_text(encoding='utf-8')
    except Exception as e:
        return [PatchResult(False, f"Error reading patch file: {e}")]
    
    # Parse patch
    files_data = parse_unified_diff(patch_content)
    
    if not files_data:
        return [PatchResult(False, "No valid patch data found")]
    
    results = []
    
    for file_data in files_data:
        # Resolve file path relative to base directory
        file_path = file_data['modified_file']
        if file_path.startswith('b/'):
            file_path = file_path[2:]  # Remove 'b/' prefix
        
        full_path = base_dir / file_path
        
        # Validate path is within base_dir
        try:
            full_path = full_path.resolve()
            base_dir_resolved = base_dir.resolve()
            if not str(full_path).startswith(str(base_dir_resolved)):
                results.append(PatchResult(False, f"Path outside base directory: {file_path}"))
                continue
        except Exception as e:
            results.append(PatchResult(False, f"Invalid path: {file_path}"))
            continue
        
        if dry_run:
            results.append(PatchResult(True, f"Would apply patch to: {full_path}"))
        else:
            result = apply_patch_to_file(str(full_path), file_data)
            results.append(result)
    
    return results


def validate_patch(patch_content: str) -> PatchResult:
    """Validate patch format and content."""
    
    if not patch_content.strip():
        return PatchResult(False, "Empty patch content")
    
    try:
        files_data = parse_unified_diff(patch_content)
        
        if not files_data:
            return PatchResult(False, "No valid file changes found in patch")
        
        for file_data in files_data:
            if not file_data.get('hunks'):
                return PatchResult(False, f"No hunks found for file: {file_data.get('modified_file', 'unknown')}")
        
        return PatchResult(True, f"Valid patch with {len(files_data)} file(s)")
        
    except Exception as e:
        return PatchResult(False, f"Invalid patch format: {e}")


def create_backup(file_path: str, backup_dir: Path) -> Optional[Path]:
    """Create a backup of a file before applying patch."""
    
    source_path = Path(file_path)
    
    if not source_path.exists():
        return None
    
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.name}.backup.{timestamp}"
        backup_path = backup_dir / backup_name
        
        # Copy file
        shutil.copy2(source_path, backup_path)
        
        console.print(f"[dim]Backup created: {backup_path}[/dim]")
        return backup_path
        
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to create backup: {e}[/yellow]")
        return None