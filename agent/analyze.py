"""Project analysis module for the Local Coding Agent."""

import ast
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console

console = Console()


class FileAnalysis:
    """Analysis data for a single file."""
    
    def __init__(self, path: str):
        self.path = path
        self.size = 0
        self.lines = 0
        self.language = "unknown"
        self.classes = []
        self.functions = []
        self.imports = []
        self.docstrings = []
        self.error = None


class ProjectAnalysis:
    """Complete project analysis data."""
    
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.timestamp = datetime.now()
        self.files = []
        self.total_files = 0
        self.total_size = 0
        self.total_lines = 0
        self.languages = {}
        self.summary = {}


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    
    extension_map = {
        '.py': 'Python',
        '.js': 'JavaScript', 
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.sql': 'SQL',
        '.sh': 'Shell Script',
        '.bash': 'Bash Script',
        '.zsh': 'Zsh Script',
        '.ps1': 'PowerShell',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.xml': 'XML',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.cfg': 'Config',
        '.conf': 'Config',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.txt': 'Text',
        '.log': 'Log File',
        '.dockerfile': 'Dockerfile',
        '.gitignore': 'Git Ignore',
        '.env': 'Environment',
    }
    
    path = Path(file_path)
    
    # Special cases
    if path.name.lower() in ['dockerfile', 'makefile', 'rakefile', 'gemfile']:
        return path.name.title()
    
    if path.name.lower().startswith('.'):
        if path.name.lower() in ['.gitignore', '.dockerignore', '.env']:
            return extension_map.get(path.name.lower(), 'Config')
    
    # Check extension
    extension = path.suffix.lower()
    return extension_map.get(extension, 'Unknown')


def analyze_python_file(file_path: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Analyze Python file for classes, functions, imports, and docstrings."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        classes = []
        functions = []
        imports = []
        docstrings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
                # Get class docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    docstrings.append(f"Class {node.name}: {node.body[0].value.value[:100]}...")
            
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                # Get function docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    docstrings.append(f"Function {node.name}: {node.body[0].value.value[:100]}...")
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")
                else:
                    for alias in node.names:
                        imports.append(alias.name)
        
        return classes, functions, imports, docstrings
        
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to analyze Python file {file_path}: {e}[/yellow]")
        return [], [], [], []


def analyze_javascript_file(file_path: str) -> Tuple[List[str], List[str], List[str]]:
    """Analyze JavaScript/TypeScript file for functions, classes, and imports."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        classes = []
        functions = []
        imports = []
        
        # Simple regex patterns for JS/TS analysis
        class_pattern = r'class\s+(\w+)'
        function_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|(\w+)\s*:\s*(?:async\s+)?function)'
        import_pattern = r'import\s+(?:{[^}]+}|\w+|[^from]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        
        # Find classes
        for match in re.finditer(class_pattern, content):
            classes.append(match.group(1))
        
        # Find functions
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                functions.append(func_name)
        
        # Find imports
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))
        
        return classes, functions, imports
        
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to analyze JS/TS file {file_path}: {e}[/yellow]")
        return [], [], []


def analyze_file(file_path: str) -> FileAnalysis:
    """Analyze a single file."""
    
    analysis = FileAnalysis(file_path)
    path = Path(file_path)
    
    try:
        # Basic file info
        stat = path.stat()
        analysis.size = stat.st_size
        analysis.language = detect_language(file_path)
        
        # Count lines
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                analysis.lines = sum(1 for _ in f)
        except UnicodeDecodeError:
            # Binary file
            analysis.lines = 0
        
        # Language-specific analysis
        if analysis.language == 'Python':
            classes, functions, imports, docstrings = analyze_python_file(file_path)
            analysis.classes = classes
            analysis.functions = functions
            analysis.imports = imports
            analysis.docstrings = docstrings
        
        elif analysis.language in ['JavaScript', 'TypeScript', 'React JSX', 'React TSX']:
            classes, functions, imports = analyze_javascript_file(file_path)
            analysis.classes = classes
            analysis.functions = functions
            analysis.imports = imports
        
    except Exception as e:
        analysis.error = str(e)
        console.print(f"[yellow]Warning: Failed to analyze {file_path}: {e}[/yellow]")
    
    return analysis


def scan_directory(directory: str, ignore_patterns: List[str] = None) -> List[str]:
    """Scan directory for files, respecting ignore patterns."""
    
    if ignore_patterns is None:
        ignore_patterns = [
            '.git', '.svn', '.hg',
            '__pycache__', '.pytest_cache', '.mypy_cache',
            'node_modules', '.npm', '.yarn',
            '.venv', 'venv', '.env',
            'dist', 'build', '.build',
            '.DS_Store', 'Thumbs.db',
            '*.pyc', '*.pyo', '*.pyd',
            '*.so', '*.dll', '*.dylib',
            '*.exe', '*.bin',
            '.agent'
        ]
    
    files = []
    root_path = Path(directory)
    
    for item in root_path.rglob('*'):
        if item.is_file():
            # Check ignore patterns
            relative_path = item.relative_to(root_path)
            should_ignore = False
            
            for pattern in ignore_patterns:
                if pattern.startswith('*'):
                    # Wildcard pattern
                    if str(relative_path).endswith(pattern[1:]):
                        should_ignore = True
                        break
                elif pattern in str(relative_path):
                    should_ignore = True
                    break
            
            if not should_ignore:
                files.append(str(item))
    
    return sorted(files)


def analyze_project(directory: str) -> ProjectAnalysis:
    """Analyze entire project directory."""
    
    console.print(f"[blue]Analyzing project directory:[/blue] {directory}")
    
    analysis = ProjectAnalysis(directory)
    
    # Scan for files
    files = scan_directory(directory)
    analysis.total_files = len(files)
    
    console.print(f"[dim]Found {len(files)} files to analyze[/dim]")
    
    # Analyze each file
    for i, file_path in enumerate(files, 1):
        if i % 10 == 0 or i == len(files):
            console.print(f"[dim]Analyzing file {i}/{len(files)}[/dim]")
        
        file_analysis = analyze_file(file_path)
        analysis.files.append(file_analysis)
        
        # Update totals
        analysis.total_size += file_analysis.size
        analysis.total_lines += file_analysis.lines
        
        # Update language stats
        lang = file_analysis.language
        if lang not in analysis.languages:
            analysis.languages[lang] = {'files': 0, 'lines': 0, 'size': 0}
        
        analysis.languages[lang]['files'] += 1
        analysis.languages[lang]['lines'] += file_analysis.lines
        analysis.languages[lang]['size'] += file_analysis.size
    
    # Generate summary
    analysis.summary = {
        'top_languages': sorted(analysis.languages.items(), 
                               key=lambda x: x[1]['lines'], reverse=True)[:5],
        'largest_files': sorted(analysis.files, key=lambda x: x.size, reverse=True)[:10],
        'most_complex_files': sorted([f for f in analysis.files if f.functions or f.classes], 
                                   key=lambda x: len(x.functions) + len(x.classes), reverse=True)[:10]
    }
    
    return analysis


def generate_codemap(analysis: ProjectAnalysis) -> str:
    """Generate CODEMAP.md content from project analysis."""
    
    content = f"""# Code Map

Generated on: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
Directory: `{analysis.root_path}`

## Project Overview

- **Total Files**: {analysis.total_files:,}
- **Total Lines**: {analysis.total_lines:,}
- **Total Size**: {format_size(analysis.total_size)}

## Languages Used

"""
    
    for lang, stats in analysis.summary['top_languages']:
        percentage = (stats['lines'] / analysis.total_lines * 100) if analysis.total_lines > 0 else 0
        content += f"- **{lang}**: {stats['files']} files, {stats['lines']:,} lines ({percentage:.1f}%)\n"
    
    content += "\n## File Structure\n\n"
    
    # Group files by directory
    dirs = {}
    for file_analysis in analysis.files:
        dir_path = str(Path(file_analysis.path).parent.relative_to(analysis.root_path))
        if dir_path == '.':
            dir_path = 'root'
        
        if dir_path not in dirs:
            dirs[dir_path] = []
        dirs[dir_path].append(file_analysis)
    
    for dir_name, files in sorted(dirs.items()):
        content += f"### {dir_name}\n\n"
        for file_analysis in sorted(files, key=lambda x: Path(x.path).name):
            file_name = Path(file_analysis.path).name
            content += f"- `{file_name}` ({file_analysis.language}, {file_analysis.lines} lines, {format_size(file_analysis.size)})\n"
            
            if file_analysis.classes:
                content += f"  - Classes: {', '.join(file_analysis.classes)}\n"
            if file_analysis.functions:
                content += f"  - Functions: {', '.join(file_analysis.functions[:10])}{'...' if len(file_analysis.functions) > 10 else ''}\n"
        
        content += "\n"
    
    # Add complexity analysis
    if analysis.summary['most_complex_files']:
        content += "## Most Complex Files\n\n"
        for file_analysis in analysis.summary['most_complex_files'][:5]:
            rel_path = str(Path(file_analysis.path).relative_to(analysis.root_path))
            complexity = len(file_analysis.functions) + len(file_analysis.classes)
            content += f"- `{rel_path}`: {complexity} symbols ({len(file_analysis.classes)} classes, {len(file_analysis.functions)} functions)\n"
        
        content += "\n"
    
    # Add imports analysis for Python files
    python_files = [f for f in analysis.files if f.language == 'Python' and f.imports]
    if python_files:
        content += "## Key Dependencies (Python)\n\n"
        all_imports = {}
        for file_analysis in python_files:
            for imp in file_analysis.imports:
                # Get root module name
                root_module = imp.split('.')[0]
                if root_module not in all_imports:
                    all_imports[root_module] = 0
                all_imports[root_module] += 1
        
        # Show top imports
        top_imports = sorted(all_imports.items(), key=lambda x: x[1], reverse=True)[:10]
        for module, count in top_imports:
            content += f"- `{module}`: used in {count} file(s)\n"
        
        content += "\n"
    
    # Add docstrings if available
    all_docstrings = []
    for file_analysis in analysis.files:
        all_docstrings.extend(file_analysis.docstrings)
    
    if all_docstrings:
        content += "## Documentation\n\n"
        content += f"Found {len(all_docstrings)} documented symbols.\n\n"
        
        # Show first few docstrings as examples
        for docstring in all_docstrings[:5]:
            content += f"- {docstring}\n"
        
        if len(all_docstrings) > 5:
            content += f"- ... and {len(all_docstrings) - 5} more\n"
        
        content += "\n"
    
    content += "---\n*Generated by Local Coding Agent*\n"
    
    return content


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def save_codemap(content: str, output_path: str) -> bool:
    """Save CODEMAP.md to file."""
    
    try:
        Path(output_path).write_text(content, encoding='utf-8')
        console.print(f"[green]CODEMAP.md saved to:[/green] {output_path}")
        return True
    except Exception as e:
        console.print(f"[red]Error saving CODEMAP.md:[/red] {e}")
        return False