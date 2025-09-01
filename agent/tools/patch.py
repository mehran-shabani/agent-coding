from __future__ import annotations

import difflib
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

from ..config import Config


console = Console()


def unified_diff(old_text: str, new_text: str, path: str) -> str:
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{path}", tofile=f"b/{path}")
    return "".join(diff)


def apply_single_file_patch(cfg: Config, rel_path: str, new_text: str, assume_yes: bool = False) -> None:
    abs_path = (cfg.workdir_path / rel_path).resolve()
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    old_text = abs_path.read_text() if abs_path.exists() else ""
    diff = unified_diff(old_text, new_text, rel_path)
    console.print("[cyan]Patch preview:[/cyan]\n" + diff)
    if assume_yes or Confirm.ask("Apply patch?", default=False):
        abs_path.write_text(new_text)
        console.print(f"[green]Patched[/green] {abs_path}")
    else:
        console.print("[red]Aborted[/red]")
