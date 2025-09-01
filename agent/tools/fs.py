from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.prompt import Confirm
from rich.console import Console

from ..config import Config


console = Console()


def safe_write_file(cfg: Config, path: Path, content: str, overwrite: bool = False, assume_yes: bool = False) -> None:
    path = path if path.is_absolute() else (cfg.workdir_path / path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        if assume_yes or Confirm.ask(f"[yellow]Overwrite[/yellow] existing file {path}?", default=False):
            pass
        else:
            console.print(f"[red]Aborted[/red]: not overwriting {path}")
            return
    path.write_text(content)
    console.print(f"[green]Wrote[/green] {path}")


def safe_delete_path(cfg: Config, path: Path, assume_yes: bool = False) -> bool:
    path = path if path.is_absolute() else (cfg.workdir_path / path)
    if not path.exists():
        console.print(f"[yellow]Not found[/yellow]: {path}")
        return False
    if assume_yes or Confirm.ask(f"[red]Delete[/red] {path}?", default=False):
        if path.is_dir():
            for p in sorted(path.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                else:
                    p.rmdir()
            path.rmdir()
        else:
            path.unlink()
        console.print(f"[green]Deleted[/green] {path}")
        return True
    console.print("[red]Aborted[/red]")
    return False
