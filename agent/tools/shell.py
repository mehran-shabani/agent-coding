"""Shell command execution for the Local Coding Agent."""

import json
import os
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console

console = Console()


class ShellResult:
    """Result of a shell command execution."""
    
    def __init__(self, command: str, returncode: int, stdout: str, stderr: str, 
                 execution_time: float, working_dir: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.working_dir = working_dir
        self.timestamp = datetime.now()
    
    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.returncode == 0
    
    @property
    def output(self) -> str:
        """Get combined output."""
        result = self.stdout
        if self.stderr:
            if result:
                result += "\n" + self.stderr
            else:
                result = self.stderr
        return result


def execute_command(
    command: str,
    working_dir: Optional[str] = None,
    timeout: Optional[float] = None,
    capture_output: bool = True
) -> ShellResult:
    """Execute a shell command safely."""
    
    if working_dir is None:
        working_dir = os.getcwd()
    
    working_path = Path(working_dir)
    if not working_path.exists():
        console.print(f"[red]Error:[/red] Working directory '{working_dir}' does not exist")
        return ShellResult(command, -1, "", f"Working directory does not exist: {working_dir}", 0.0, working_dir)
    
    # Parse command safely
    try:
        cmd_args = shlex.split(command)
    except ValueError as e:
        console.print(f"[red]Error:[/red] Invalid command syntax: {e}")
        return ShellResult(command, -1, "", str(e), 0.0, working_dir)
    
    console.print(f"[blue]Executing:[/blue] {command}")
    console.print(f"[dim]Working directory:[/dim] {working_path.absolute()}")
    
    start_time = time.time()
    
    try:
        # Execute command
        if capture_output:
            result = subprocess.run(
                cmd_args,
                shell=False,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            stdout = result.stdout
            stderr = result.stderr
            returncode = result.returncode
        else:
            # For interactive commands or when we want real-time output
            result = subprocess.run(
                cmd_args,
                shell=False,
                cwd=working_dir,
                timeout=timeout
            )
            stdout = ""
            stderr = ""
            returncode = result.returncode
        
        execution_time = time.time() - start_time
        
        # Create result object
        shell_result = ShellResult(command, returncode, stdout, stderr, execution_time, working_dir)
        
        # Display results
        if shell_result.success:
            console.print(f"[green]Command completed successfully[/green] (took {execution_time:.2f}s)")
            if stdout and capture_output:
                console.print("[dim]Output:[/dim]")
                console.print(stdout)
        else:
            console.print(f"[red]Command failed[/red] with exit code {returncode}")
            if stderr and capture_output:
                console.print("[dim]Error output:[/dim]")
                console.print(stderr)
            if stdout and capture_output:
                console.print("[dim]Standard output:[/dim]")
                console.print(stdout)
        
        return shell_result
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        console.print(f"[red]Command timed out[/red] after {execution_time:.2f}s")
        return ShellResult(command, -1, "", f"Command timed out after {execution_time:.2f}s", execution_time, working_dir)
    
    except Exception as e:
        execution_time = time.time() - start_time
        console.print(f"[red]Error executing command:[/red] {e}")
        return ShellResult(command, -1, "", str(e), execution_time, working_dir)


def log_command(result: ShellResult, log_dir: Path) -> None:
    """Log command execution to file in JSON format."""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"commands-{timestamp}.jsonl"
        
        # Prepare log entry
        log_entry = {
            "timestamp": result.timestamp.isoformat(),
            "command": result.command,
            "working_dir": result.working_dir,
            "exit_code": result.returncode,
            "execution_time": result.execution_time,
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        # Append to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')
        
        console.print(f"[dim]Command logged to: {log_file}[/dim]")
        
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to log command: {e}[/yellow]")


def get_command_history(log_dir: Path, limit: int = 10) -> List[Dict]:
    """Get recent command history from logs."""
    try:
        if not log_dir.exists():
            return []
        
        log_files = sorted(log_dir.glob("commands-*.jsonl"), reverse=True)
        history = []
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(history) >= limit:
                            break
                        try:
                            entry = json.loads(line.strip())
                            history.append(entry)
                        except json.JSONDecodeError:
                            continue  # Skip malformed entries
            except Exception:
                continue  # Skip files that can't be read
            
            if len(history) >= limit:
                break
        
        return history[:limit]
        
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to get command history: {e}[/yellow]")
        return []


def is_safe_command(command: str) -> Tuple[bool, str]:
    """Check if a command is considered safe to execute using whitelist approach."""
    
    # Whitelist of allowed commands
    ALLOWED_COMMANDS = {
        'ls', 'cat', 'grep', 'find', 'echo', 'pwd', 'cd', 'head', 'tail',
        'git', 'npm', 'pip', 'python', 'python3', 'node', 'make', 'cmake',
        'which', 'whoami', 'id', 'date', 'curl', 'wget', 'tree', 'less',
        'more', 'wc', 'sort', 'uniq', 'awk', 'sed', 'diff', 'patch',
        'tar', 'gzip', 'gunzip', 'zip', 'unzip', 'touch', 'mkdir', 'rm',
        'cp', 'mv', 'ln', 'chmod', 'chown', 'file', 'stat', 'du', 'df'
    }
    
    try:
        cmd_parts = shlex.split(command)
        if not cmd_parts:
            return False, "Empty command"
        
        base_command = cmd_parts[0].split('/')[-1]  # Get command name
        
        if base_command not in ALLOWED_COMMANDS:
            return False, f"Command '{base_command}' not in allowed list"
        
        # Check for command substitution
        if '$(' in command or '`' in command or '${' in command:
            return False, "Command substitution not allowed"
        
        # Check for dangerous redirections
        if any(redir in command for redir in [' > /dev/', ' >> /dev/', '> /dev/', '>> /dev/']):
            return False, "Redirection to device files not allowed"
        
        # Check for pipe to dangerous commands
        if '|' in command:
            pipe_parts = command.split('|')
            for part in pipe_parts[1:]:  # Check commands after pipes
                part = part.strip()
                if part:
                    try:
                        pipe_cmd = shlex.split(part)[0].split('/')[-1]
                        if pipe_cmd not in ALLOWED_COMMANDS:
                            return False, f"Piped command '{pipe_cmd}' not in allowed list"
                    except (IndexError, ValueError):
                        return False, "Invalid pipe syntax"
        
        # Special checks for rm command
        if base_command == 'rm':
            if '-rf' in command and ('*' in command or '/' in command):
                return False, "Dangerous rm command with recursive force and wildcards/root paths"
        
        # Check for absolute paths to critical directories
        critical_paths = ['/', '/dev', '/sys', '/proc', '/etc', '/usr', '/var']
        for arg in cmd_parts[1:]:
            if any(arg.startswith(path) for path in critical_paths):
                return False, f"Access to critical system path not allowed: {arg}"
        
        return True, "Command appears safe"
        
    except ValueError as e:
        return False, f"Invalid command syntax: {e}"