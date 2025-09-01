"""Shell command execution tools with logging."""

import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
from rich.console import Console

from ..prompts import SUCCESS_MESSAGES, ERROR_MESSAGES


console = Console()


def execute_command(
    command: str,
    workdir: Path,
    log_dir: Path,
    timeout: Optional[int] = None
) -> Tuple[bool, str, str]:
    """Execute a shell command and log the output."""
    
    # Create log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"commands-{timestamp}.log"
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Log command info
    log_content = [
        f"Command: {command}",
        f"Working Directory: {workdir}",
        f"Timestamp: {datetime.now().isoformat()}",
        "-" * 50,
        ""
    ]
    
    try:
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Log output
        log_content.extend([
            "STDOUT:",
            result.stdout or "(empty)",
            "",
            "STDERR:",
            result.stderr or "(empty)",
            "",
            f"Exit Code: {result.returncode}",
        ])
        
        # Write log
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_content))
        
        if result.returncode == 0:
            return True, result.stdout, SUCCESS_MESSAGES["command_executed"]
        else:
            return False, result.stderr, ERROR_MESSAGES["command_failed"].format(code=result.returncode)
    
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        log_content.append(f"ERROR: {error_msg}")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_content))
        
        return False, "", error_msg
    
    except Exception as e:
        error_msg = f"Error executing command: {e}"
        log_content.append(f"ERROR: {error_msg}")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_content))
        
        return False, "", error_msg


def validate_command(command: str) -> Tuple[bool, str]:
    """Basic validation of shell commands for safety."""
    # List of potentially dangerous commands/patterns
    dangerous_patterns = [
        "rm -rf /",
        "dd if=/dev/zero",
        "mkfs.",
        "> /dev/sda",
        "chmod -R 777 /",
    ]
    
    command_lower = command.lower().strip()
    
    for pattern in dangerous_patterns:
        if pattern.lower() in command_lower:
            return False, f"Potentially dangerous command pattern detected: {pattern}"
    
    return True, ""


def get_shell_info() -> dict:
    """Get information about the current shell environment."""
    return {
        "shell": os.environ.get("SHELL", "unknown"),
        "user": os.environ.get("USER", "unknown"),
        "pwd": os.getcwd(),
        "path": os.environ.get("PATH", "").split(":"),
    }