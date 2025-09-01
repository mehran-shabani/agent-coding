from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Tuple


def run_shell(command: str, workdir: str, log_dir: str) -> Tuple[int, str, str, str]:
    ts = time.strftime("%Y%m%d-%H%M%S")
    log_path = Path(log_dir) / f"commands-{ts}.log"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        command,
        cwd=workdir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = proc.communicate()
    code = proc.returncode
    log_path.write_text(f"$ {command}\n\nSTDOUT:\n{out}\n\nSTDERR:\n{err}\n", encoding="utf-8")
    return code, out, err, str(log_path)
