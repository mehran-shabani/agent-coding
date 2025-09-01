from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, List, Tuple


def _scan_directory(root: str) -> Tuple[int, List[Tuple[str, int]]]:
    files: List[Tuple[str, int]] = []
    total_size = 0
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            p = Path(dirpath) / fname
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            total_size += size
            files.append((str(p.relative_to(root)), size))
    files.sort(key=lambda x: x[0])
    return total_size, files


def _python_symbols(path: Path) -> List[str]:
    symbols: List[str] = []
    if not path.suffix == ".py":
        return symbols
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return symbols
    for line in src.splitlines():
        ls = line.lstrip()
        if ls.startswith("class ") or ls.startswith("def "):
            symbols.append(ls)
        if ls.startswith('"""') or ls.startswith("'''"):
            symbols.append("DOCSTRING: ...")
    return symbols


def generate_codemap(root: str, output: str = "CODEMAP.md") -> str:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    total_size, files = _scan_directory(root)
    by_lang: Dict[str, int] = {}
    lines: List[str] = []
    lines.append(f"# CODEMAP\n\nScanned: {root}\nDate: {ts}\n\n")
    lines.append(f"Total files: {len(files)} | Total size: {total_size} bytes\n\n")
    lines.append("## Files\n")
    for rel, size in files:
        ext = os.path.splitext(rel)[1].lower()
        by_lang[ext] = by_lang.get(ext, 0) + 1
        lines.append(f"- {rel} ({size} bytes)")
    lines.append("\n## Languages by extension\n")
    for ext, count in sorted(by_lang.items(), key=lambda x: x[0]):
        lines.append(f"- {ext or 'none'}: {count}")
    lines.append("\n## Python Symbols\n")
    for rel, _ in files:
        p = Path(root) / rel
        for sym in _python_symbols(p):
            lines.append(f"- {rel}: {sym}")
    Path(output).write_text("\n".join(lines), encoding="utf-8")
    return output
