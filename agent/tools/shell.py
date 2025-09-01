"""Shell command execution for the Local Coding Agent."""

import os
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
    
    console.print(f"[blue]Executing:[/blue] {command}")
    console.print(f"[dim]Working directory:[/dim] {working_path.absolute()}")
    
    start_time = time.time()
    
    try:
        # Execute command
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
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
                command,
                shell=True,
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
    """Log command execution to file."""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"commands-{timestamp}.log"
        
        # Prepare log entry
        log_entry = f"""
=== Command Execution Log ===
Timestamp: {result.timestamp.isoformat()}
Command: {result.command}
Working Directory: {result.working_dir}
Exit Code: {result.returncode}
Execution Time: {result.execution_time:.2f}s
Success: {result.success}

=== STDOUT ===
{result.stdout}

=== STDERR ===
{result.stderr}

=== END LOG ENTRY ===

"""
        
        # Append to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        console.print(f"[dim]Command logged to: {log_file}[/dim]")
        
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to log command: {e}[/yellow]")


def get_command_history(log_dir: Path, limit: int = 10) -> List[Dict]:
    """Get recent command history from logs."""
    try:
        if not log_dir.exists():
            return []
        
        log_files = sorted(log_dir.glob("commands-*.log"), reverse=True)
        history = []
        
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse log entries (simplified parsing)
                entries = content.split('=== Command Execution Log ===')[1:]
                for entry in entries:
                    lines = entry.strip().split('\n')
                    if len(lines) >= 6:
                        try:
                            timestamp = lines[0].replace('Timestamp: ', '')
                            command = lines[1].replace('Command: ', '')
                            working_dir = lines[2].replace('Working Directory: ', '')
                            exit_code = lines[3].replace('Exit Code: ', '')
                            exec_time = lines[4].replace('Execution Time: ', '')
                            success = lines[5].replace('Success: ', '') == 'True'
                            
                            history.append({
                                'timestamp': timestamp,
                                'command': command,
                                'working_dir': working_dir,
                                'exit_code': int(exit_code),
                                'execution_time': exec_time,
                                'success': success
                            })
                        except (ValueError, IndexError):
                            continue  # Skip malformed entries
            except Exception:
                continue  # Skip files that can't be read
        
        return history[:limit]
        
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to get command history: {e}[/yellow]")
        return []


def is_safe_command(command: str) -> Tuple[bool, str]:
    """Check if a command is considered safe to execute."""
    
    # List of potentially dangerous commands
    dangerous_patterns = [
        'rm -rf /',
        'rm -rf *',
        'dd if=',
        'mkfs.',
        'fdisk',
        'format',
        'shutdown',
        'reboot',
        'halt',
        'init 0',
        'init 6',
        'kill -9 -1',
        'killall -9',
        '> /dev/sda',
        '> /dev/sd',
        'chmod 777 /',
        'chown -R root:root /',
    ]
    
    command_lower = command.lower().strip()
    
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return False, f"Command contains potentially dangerous pattern: {pattern}"
    
    # Check for suspicious redirections
    if ' > /dev/' in command_lower or ' >> /dev/' in command_lower:
        return False, "Command attempts to write to device files"
    
    # Check for mass deletions
    if 'rm' in command_lower and ('*' in command or '-rf' in command_lower):
        return False, "Command attempts mass file deletion"
    
    return True, "Command appears safe"