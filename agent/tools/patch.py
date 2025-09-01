from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import List


@dataclass
class FilePatch:
    path: str
    diff: str


def generate_unified_diff(path: str, new_content: str) -> str:
    p = Path(path)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    diff_lines = unified_diff(
        old.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
    )
    return "".join(diff_lines)


def apply_unified_diff(path: str, new_content: str, apply: bool) -> str:
    diff_text = generate_unified_diff(path, new_content)
    if apply:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new_content, encoding="utf-8")
    return diff_text
