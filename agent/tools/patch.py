"""
Patch management for Local Coding Agent.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console
from rich.prompt import Confirm

from ..config import get_config

console = Console()


class PatchTool:
    """Tool for managing unified diff patches."""
    
    def __init__(self):
        self.config = get_config()
    
    def parse_unified_diff(self, diff_content: str) -> List[dict]:
        """Parse unified diff content into structured format."""
        patches = []
        current_patch = None
        
        lines = diff_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for file header
            if line.startswith('--- ') or line.startswith('+++ '):
                if current_patch:
                    patches.append(current_patch)
                
                current_patch = {
                    'file_path': None,
                    'hunks': [],
                    'raw_content': []
                }
                
                # Extract file path
                if line.startswith('--- '):
                    file_path = line[4:].split('\t')[0]
                    if file_path.startswith('a/'):
                        file_path = file_path[2:]
                    current_patch['file_path'] = file_path
                
                current_patch['raw_content'].append(line)
            
            # Check for hunk header
            elif line.startswith('@@'):
                if current_patch:
                    hunk_info = self._parse_hunk_header(line)
                    current_hunk = {
                        'header': line,
                        'old_start': hunk_info['old_start'],
                        'old_count': hunk_info['old_count'],
                        'new_start': hunk_info['new_start'],
                        'new_count': hunk_info['new_count'],
                        'lines': []
                    }
                    current_patch['hunks'].append(current_hunk)
                    current_patch['raw_content'].append(line)
            
            # Add lines to current hunk
            elif current_patch and current_patch['hunks']:
                current_patch['hunks'][-1]['lines'].append(line)
                current_patch['raw_content'].append(line)
            
            i += 1
        
        # Add the last patch
        if current_patch:
            patches.append(current_patch)
        
        return patches
    
    def _parse_hunk_header(self, header: str) -> dict:
        """Parse hunk header line."""
        # Format: @@ -old_start,old_count +new_start,new_count @@
        pattern = r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
        match = re.match(pattern, header)
        
        if match:
            old_start = int(match.group(1))
            old_count = int(match.group(2)) if match.group(2) else 1
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) else 1
            
            return {
                'old_start': old_start,
                'old_count': old_count,
                'new_start': new_start,
                'new_count': new_count
            }
        
        return {'old_start': 0, 'old_count': 0, 'new_start': 0, 'new_count': 0}
    
    def validate_patch(self, diff_content: str) -> Tuple[bool, str]:
        """Validate if a patch is well-formed."""
        if not diff_content.strip():
            return False, "Empty patch content"
        
        try:
            patches = self.parse_unified_diff(diff_content)
            if not patches:
                return False, "No valid patches found"
            
            for patch in patches:
                if not patch['file_path']:
                    return False, "Missing file path in patch"
                
                if not patch['hunks']:
                    return False, f"No hunks found for file {patch['file_path']}"
            
            return True, "Patch appears valid"
        except Exception as e:
            return False, f"Error parsing patch: {e}"
    
    def apply_patch(
        self, 
        diff_content: str, 
        dry_run: bool = True,
        confirm: bool = True
    ) -> Tuple[bool, str]:
        """Apply a unified diff patch."""
        
        # Validate patch first
        is_valid, message = self.validate_patch(diff_content)
        if not is_valid:
            return False, message
        
        # Parse patches
        patches = self.parse_unified_diff(diff_content)
        
        # Show what will be changed
        console.print("[blue]Patch Summary:[/blue]")
        for patch in patches:
            console.print(f"  File: {patch['file_path']}")
            console.print(f"  Hunks: {len(patch['hunks'])}")
        
        if dry_run:
            console.print("[yellow]Dry run mode - no changes will be applied[/yellow]")
            return True, "Dry run completed"
        
        # Confirm application
        if confirm:
            if not Confirm.ask("Apply this patch?"):
                return False, "Patch application cancelled"
        
        # Apply patches
        success_count = 0
        error_messages = []
        
        for patch in patches:
            file_path = patch['file_path']
            
            if not self.config.agent_workdir.joinpath(file_path).exists():
                error_messages.append(f"File {file_path} does not exist")
                continue
            
            try:
                # Create temporary file with patch content
                with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as temp_file:
                    temp_file.write('\n'.join(patch['raw_content']))
                    temp_file_path = temp_file.name
                
                # Apply patch using patch command
                result = subprocess.run(
                    ['patch', '-p1', file_path, temp_file_path],
                    cwd=str(self.config.agent_workdir),
                    capture_output=True,
                    text=True
                )
                
                # Clean up temporary file
                Path(temp_file_path).unlink(missing_ok=True)
                
                if result.returncode == 0:
                    success_count += 1
                    console.print(f"[green]Applied patch to {file_path}[/green]")
                else:
                    error_messages.append(f"Failed to apply patch to {file_path}: {result.stderr}")
            
            except Exception as e:
                error_messages.append(f"Error applying patch to {file_path}: {e}")
        
        if success_count == len(patches):
            return True, f"Successfully applied {success_count} patches"
        else:
            error_summary = "; ".join(error_messages)
            return False, f"Applied {success_count}/{len(patches)} patches. Errors: {error_summary}"
    
    def create_patch_from_files(self, original_file: str, modified_file: str) -> Optional[str]:
        """Create a unified diff patch from two files."""
        try:
            result = subprocess.run(
                ['diff', '-u', original_file, modified_file],
                cwd=str(self.config.agent_workdir),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return ""  # No differences
            elif result.returncode == 1:
                return result.stdout  # Differences found
            else:
                console.print(f"[red]Error creating patch: {result.stderr}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Error creating patch: {e}[/red]")
            return None
    
    def save_patch(self, diff_content: str, filename: str) -> bool:
        """Save patch content to a file."""
        try:
            patch_file = Path(filename)
            patch_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(patch_file, 'w', encoding='utf-8') as f:
                f.write(diff_content)
            
            console.print(f"[green]Patch saved to {filename}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error saving patch: {e}[/red]")
            return False
    
    def load_patch(self, filename: str) -> Optional[str]:
        """Load patch content from a file."""
        try:
            patch_file = Path(filename)
            if not patch_file.exists():
                console.print(f"[red]Patch file {filename} does not exist[/red]")
                return None
            
            with open(patch_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            console.print(f"[red]Error loading patch: {e}[/red]")
            return None