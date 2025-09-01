from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console

from ..config import Config, log_event


console = Console()


def run_shell(cfg: Config, command: str) -> int:
    workdir = cfg.workdir_path
    proc = subprocess.Popen(
        command,
        cwd=str(workdir),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdout is not None
    output_lines = []
    for line in proc.stdout:
        output_lines.append(line)
        console.print(line.rstrip())
    proc.wait()
    full = "".join(output_lines)
    log_event(cfg, "commands", f"$ {command}\n\n{full}")
    return proc.returncode or 0
