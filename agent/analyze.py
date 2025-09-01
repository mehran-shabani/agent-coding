"""Code analysis module for project scanning and symbol extraction."""

import ast
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.progress import track


console = Console()


# Common programming language extensions
LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (JSX)",
    ".tsx": "TypeScript (TSX)",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".dart": "Dart",
    ".lua": "Lua",
    ".pl": "Perl",
    ".sh": "Shell",
    ".bash": "Bash",
    ".ps1": "PowerShell",
    ".md": "Markdown",
    ".json": "JSON",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
    ".txt": "Text",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
}


def get_file_stats(file_path: Path) -> Dict[str, any]:
    """Get statistics for a single file."""
    try:
        stat = file_path.stat()
        return {
            "path": str(file_path),
            "size": stat.st_size,
            "lines": count_lines(file_path),
            "language": LANGUAGE_EXTENSIONS.get(file_path.suffix.lower(), "Unknown"),
        }
    except Exception:
        return {
            "path": str(file_path),
            "size": 0,
            "lines": 0,
            "language": "Unknown",
        }


def count_lines(file_path: Path) -> int:
    """Count lines in a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def extract_python_symbols(file_path: Path) -> Dict[str, List[Dict]]:
    """Extract classes, functions, and docstrings from Python files."""
    symbols = {
        "classes": [],
        "functions": [],
        "methods": [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node),
                    "methods": []
                }
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "line": item.lineno,
                            "docstring": ast.get_docstring(item),
                            "is_async": isinstance(item, ast.AsyncFunctionDef),
                        }
                        class_info["methods"].append(method_info)
                        symbols["methods"].append({
                            **method_info,
                            "class": node.name,
                        })
                
                symbols["classes"].append(class_info)
            
            elif isinstance(node, ast.FunctionDef) and not any(
                isinstance(parent, ast.ClassDef) 
                for parent in ast.walk(tree) 
                if hasattr(parent, 'body') and node in getattr(parent, 'body', [])
            ):
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
                symbols["functions"].append(func_info)
    
    except Exception:
        # If parsing fails, return empty symbols
        pass
    
    return symbols


def analyze_directory(
    directory: Path,
    ignore_patterns: Optional[List[str]] = None
) -> Dict[str, any]:
    """Analyze a directory and extract project information."""
    
    if ignore_patterns is None:
        ignore_patterns = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "env",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
        ]
    
    stats = {
        "total_files": 0,
        "total_size": 0,
        "total_lines": 0,
        "languages": defaultdict(int),
        "files": [],
        "python_symbols": {},
    }
    
    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(directory):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in ignore_patterns)]
        
        for file in files:
            # Skip ignored files
            if any(pattern in file for pattern in ignore_patterns):
                continue
            
            file_path = Path(root) / file
            all_files.append(file_path)
    
    # Analyze files with progress bar
    for file_path in track(all_files, description="Analyzing files..."):
        file_stats = get_file_stats(file_path)
        
        stats["total_files"] += 1
        stats["total_size"] += file_stats["size"]
        stats["total_lines"] += file_stats["lines"]
        stats["languages"][file_stats["language"]] += 1
        stats["files"].append(file_stats)
        
        # Extract Python symbols
        if file_path.suffix == ".py":
            rel_path = file_path.relative_to(directory)
            symbols = extract_python_symbols(file_path)
            if any(symbols[key] for key in symbols):
                stats["python_symbols"][str(rel_path)] = symbols
    
    return stats


def generate_codemap(directory: Path, output_path: Path) -> bool:
    """Generate CODEMAP.md file with project analysis."""
    
    console.print(f"[cyan]Analyzing directory: {directory}[/cyan]")
    
    # Analyze the directory
    stats = analyze_directory(directory)
    
    # Generate markdown content
    content = [
        "# Code Map",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Directory:** {directory.absolute()}",
        "",
        "## Summary",
        f"- Total Files: {stats['total_files']}",
        f"- Total Size: {format_size(stats['total_size'])}",
        f"- Total Lines: {stats['total_lines']:,}",
        "",
        "## Languages",
    ]
    
    # Sort languages by file count
    for lang, count in sorted(stats["languages"].items(), key=lambda x: x[1], reverse=True):
        content.append(f"- {lang}: {count} files")
    
    content.extend(["", "## File Structure", ""])
    
    # Group files by directory
    files_by_dir = defaultdict(list)
    for file_stat in stats["files"]:
        file_path = Path(file_stat["path"])
        rel_path = file_path.relative_to(directory)
        dir_path = rel_path.parent
        files_by_dir[str(dir_path)].append(file_stat)
    
    # Sort directories
    for dir_name in sorted(files_by_dir.keys()):
        if dir_name == ".":
            content.append("### Root Directory")
        else:
            content.append(f"### {dir_name}")
        
        content.append("")
        
        # Sort files in directory
        for file_stat in sorted(files_by_dir[dir_name], key=lambda x: x["path"]):
            file_path = Path(file_stat["path"])
            size_str = format_size(file_stat["size"])
            content.append(f"- `{file_path.name}` - {file_stat['language']} ({size_str}, {file_stat['lines']} lines)")
        
        content.append("")
    
    # Add Python symbols if any
    if stats["python_symbols"]:
        content.extend(["## Python Symbols", ""])
        
        for file_path, symbols in sorted(stats["python_symbols"].items()):
            content.append(f"### {file_path}")
            content.append("")
            
            if symbols["classes"]:
                content.append("#### Classes")
                for cls in symbols["classes"]:
                    content.append(f"- `{cls['name']}` (line {cls['line']})")
                    if cls["docstring"]:
                        content.append(f"  - {cls['docstring'].split(chr(10))[0]}")
                    if cls["methods"]:
                        content.append("  - Methods:")
                        for method in cls["methods"]:
                            async_marker = " (async)" if method["is_async"] else ""
                            content.append(f"    - `{method['name']}`{async_marker} (line {method['line']})")
                content.append("")
            
            if symbols["functions"]:
                content.append("#### Functions")
                for func in symbols["functions"]:
                    async_marker = " (async)" if func["is_async"] else ""
                    content.append(f"- `{func['name']}`{async_marker} (line {func['line']})")
                    if func["docstring"]:
                        content.append(f"  - {func['docstring'].split(chr(10))[0]}")
                content.append("")
    
    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        console.print(f"[green]✅ Code map generated: {output_path}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Error writing code map: {e}[/red]")
        return False


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"