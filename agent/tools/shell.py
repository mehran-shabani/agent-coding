"""
Shell command execution for Local Coding Agent.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console
from rich.prompt import Confirm

from ..config import get_config

console = Console()


class ShellTool:
    """Tool for safe shell command execution."""
    
    def __init__(self):
        self.config = get_config()
    
    def run_command(
        self, 
        command: str, 
        cwd: Optional[str] = None,
        timeout: int = 300,
        confirm: bool = True
    ) -> Tuple[int, str, str]:
        """Run shell command safely."""
        
        # Use working directory from config if not specified
        if cwd is None:
            cwd = str(self.config.agent_workdir)
        
        # Safety check for dangerous commands
        dangerous_commands = [
            'rm -rf /', 'rm -rf /*', 'format', 'dd if=/dev/zero',
            'mkfs', 'fdisk', 'parted', 'chmod 777', 'chown root'
        ]
        
        command_lower = command.lower()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                console.print(f"[red]Warning: Potentially dangerous command detected: {dangerous}[/red]")
                if confirm:
                    if not Confirm.ask("Do you want to continue?"):
                        return 1, "", "Command cancelled by user"
        
        # Log the command
        log_file = self.config.get_log_file("commands")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"Command: {command}\n")
                f.write(f"Working Directory: {cwd}\n")
                f.write(f"Timestamp: {self.config.agent_log_dir}\n")
                f.write("-" * 50 + "\n")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not log command: {e}[/yellow]")
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Log output
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"Return Code: {result.returncode}\n")
                    f.write(f"STDOUT:\n{result.stdout}\n")
                    f.write(f"STDERR:\n{result.stderr}\n")
                    f.write("=" * 50 + "\n")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not log output: {e}[/yellow]")
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            console.print(f"[red]{error_msg}[/red]")
            return 1, "", error_msg
        except Exception as e:
            error_msg = f"Error executing command: {e}"
            console.print(f"[red]{error_msg}[/red]")
            return 1, "", error_msg
    
    def run_command_interactive(
        self, 
        command: str, 
        cwd: Optional[str] = None
    ) -> int:
        """Run shell command interactively (for commands that need user input)."""
        
        if cwd is None:
            cwd = str(self.config.agent_workdir)
        
        try:
            # Execute command interactively
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd
            )
            return result.returncode
        except Exception as e:
            console.print(f"[red]Error executing interactive command: {e}[/red]")
            return 1
    
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            result = subprocess.run(
                f"which {command}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_system_info(self) -> dict:
        """Get basic system information."""
        info = {}
        
        # OS information
        try:
            result = subprocess.run(
                "uname -a",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['os'] = result.stdout.strip()
        except Exception:
            pass
        
        # Python version
        info['python'] = sys.version
        
        # Working directory
        info['workdir'] = str(self.config.agent_workdir)
        
        # Available commands
        common_commands = ['git', 'python', 'pip', 'node', 'npm', 'docker']
        available_commands = []
        for cmd in common_commands:
            if self.check_command_exists(cmd):
                available_commands.append(cmd)
        info['available_commands'] = available_commands
        
        return info
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate if a command is safe to execute."""
        # Check for basic safety
        if not command.strip():
            return False, "Empty command"
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'rm -rf /',
            'rm -rf /*',
            'format',
            'dd if=/dev/zero',
            'mkfs',
            'fdisk',
            'parted',
            'chmod 777',
            'chown root',
            'sudo rm',
            'sudo format'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False, f"Dangerous pattern detected: {pattern}"
        
        return True, "Command appears safe"