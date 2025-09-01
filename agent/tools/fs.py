from __future__ import annotations

from pathlib import Path
from typing import Optional


def safe_write_file(path: str, content: str, overwrite: bool = False) -> str:
    target = Path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return str(target)


def safe_delete_path(path: str) -> None:
    p = Path(path)
    if p.is_file():
        p.unlink()
    elif p.is_dir():
        for child in sorted(p.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        p.rmdir()
