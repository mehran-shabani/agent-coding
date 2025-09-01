from __future__ import annotations

import os
import sys
import json
import ast
from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console

from .config import Config


console = Console()


def _walk_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            files.append(p)
    return files


def _analyze_python_symbols(path: Path) -> Dict[str, List[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"classes": [], "functions": [], "docstrings": []}
    try:
        tree = ast.parse(text)
    except Exception:
        return {"classes": [], "functions": [], "docstrings": []}
    classes: List[str] = []
    functions: List[str] = []
    docstrings: List[str] = []
    module_doc = ast.get_docstring(tree)
    if module_doc:
        docstrings.append(module_doc)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
            ds = ast.get_docstring(node)
            if ds:
                docstrings.append(ds)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
            ds = ast.get_docstring(node)
            if ds:
                docstrings.append(ds)
    return {"classes": classes, "functions": functions, "docstrings": docstrings}


def generate_codemap(cfg: Config, target: Path) -> Path:
    root = target if target.is_absolute() else (cfg.workdir_path / target)
    files = _walk_files(root)
    sizes = {str(p.relative_to(cfg.workdir_path)): p.stat().st_size for p in files if p.exists()}
    exts = Counter([p.suffix.lower() for p in files])
    py_symbols: Dict[str, Dict[str, List[str]]] = {}
    for p in files:
        if p.suffix.lower() == ".py":
            rel = str(p.relative_to(cfg.workdir_path))
            py_symbols[rel] = _analyze_python_symbols(p)

    lines: List[str] = []
    lines.append(f"# CODEMAP\n")
    lines.append(f"Scanned time: {datetime.now().isoformat()}\n")
    lines.append(f"Scanned path: {str(root.resolve())}\n\n")
    lines.append("## Summary\n")
    lines.append(f"Total files: {len(files)}\n\n")
    lines.append("### Extensions\n")
    for ext, count in exts.most_common():
        lines.append(f"- {ext or '<none>'}: {count}\n")
    lines.append("\n### Largest files (top 20)\n")
    for rel, size in sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)[:20]:
        lines.append(f"- {rel}: {size} bytes\n")
    lines.append("\n### Python Symbols\n")
    for rel, symbols in py_symbols.items():
        lines.append(f"- {rel}\n")
        if symbols["classes"]:
            lines.append(f"  - classes: {', '.join(symbols['classes'])}\n")
        if symbols["functions"]:
            lines.append(f"  - functions: {', '.join(symbols['functions'])}\n")
        if symbols["docstrings"]:
            sample = symbols["docstrings"][0]
            sample = sample.replace("\n", " ")
            lines.append(f"  - doc: {sample[:120]}\n")

    out_path = cfg.workdir_path / "CODEMAP.md"
    out_path.write_text("".join(lines), encoding="utf-8")
    console.print(f"[green]Generated[/green] {out_path}")
    return out_path
