"""
Project analysis and code mapping for Local Coding Agent.
"""

import ast
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from .config import get_config
from .llm import get_llm_client
from .state import get_state, save_state

console = Console()


class ProjectAnalyzer:
    """Analyzer for project structure and code mapping."""
    
    def __init__(self):
        self.config = get_config()
        self.llm_client = get_llm_client()
    
    def analyze_project(self, path: str = ".") -> Dict[str, Any]:
        """Analyze project structure and generate comprehensive report."""
        project_path = Path(path)
        
        if not project_path.exists():
            raise ValueError(f"Path {path} does not exist")
        
        console.print(f"[blue]Analyzing project at: {project_path.absolute()}[/blue]")
        
        # Collect project information
        project_info = {
            'path': str(project_path.absolute()),
            'scan_time': str(self.config.agent_log_dir),  # Using timestamp placeholder
            'files': [],
            'directories': [],
            'languages': {},
            'python_symbols': [],
            'file_sizes': {},
            'total_size': 0,
            'structure': {}
        }
        
        # Scan directory structure
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
            
            rel_root = Path(root).relative_to(project_path)
            
            # Add directories
            for dir_name in dirs:
                dir_path = rel_root / dir_name
                project_info['directories'].append(str(dir_path))
            
            # Process files
            for file_name in files:
                if file_name.startswith('.'):
                    continue
                
                file_path = rel_root / file_name
                full_path = project_path / file_path
                
                try:
                    file_size = full_path.stat().st_size
                    project_info['total_size'] += file_size
                    project_info['file_sizes'][str(file_path)] = file_size
                    
                    # Determine language
                    language = self._detect_language(file_name)
                    if language:
                        project_info['languages'][language] = project_info['languages'].get(language, 0) + 1
                    
                    # Analyze Python files
                    if language == 'Python':
                        symbols = self._analyze_python_file(full_path)
                        project_info['python_symbols'].extend(symbols)
                    
                    project_info['files'].append({
                        'path': str(file_path),
                        'size': file_size,
                        'language': language,
                        'symbols': len(symbols) if language == 'Python' else 0
                    })
                    
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not analyze {file_path}: {e}[/yellow]")
        
        # Generate structure tree
        project_info['structure'] = self._generate_structure_tree(project_path)
        
        # Update state
        state = get_state()
        state.update_project_info(project_info)
        save_state(state)
        
        return project_info
    
    def _detect_language(self, filename: str) -> Optional[str]:
        """Detect programming language from filename."""
        extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            '.ini': 'INI',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.zsh': 'Zsh',
            '.fish': 'Fish',
            '.ps1': 'PowerShell',
            '.bat': 'Batch',
            '.cmd': 'Batch',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.m': 'Objective-C',
            '.mm': 'Objective-C++',
            '.pl': 'Perl',
            '.lua': 'Lua',
            '.sql': 'SQL',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.elm': 'Elm',
            '.clj': 'Clojure',
            '.hs': 'Haskell',
            '.ml': 'OCaml',
            '.fs': 'F#',
            '.dart': 'Dart',
            '.nim': 'Nim',
            '.zig': 'Zig',
            '.v': 'V',
            '.cr': 'Crystal',
            '.ex': 'Elixir',
            '.exs': 'Elixir',
            '.erl': 'Erlang',
            '.hrl': 'Erlang',
            '.beam': 'Erlang',
            '.pyx': 'Cython',
            '.pxd': 'Cython',
            '.pyi': 'Python Stub',
            '.ipynb': 'Jupyter Notebook',
            '.rpy': 'Ren\'Py',
            '.gml': 'GameMaker',
            '.gd': 'GDScript',
            '.godot': 'Godot',
            '.unity': 'Unity',
            '.uproject': 'Unreal',
            '.uplugin': 'Unreal',
            '.cpp': 'C++',
            '.h': 'C/C++ Header',
            '.hpp': 'C++ Header',
            '.cxx': 'C++',
            '.cc': 'C++',
            '.hh': 'C++ Header',
            '.hxx': 'C++ Header',
            '.tcc': 'C++ Template',
            '.ipp': 'C++ Template',
            '.inl': 'C++ Inline',
            '.def': 'C++ Module',
            '.ixx': 'C++ Module',
            '.cppm': 'C++ Module',
            '.mpp': 'C++ Module',
            '.cpp20': 'C++20',
            '.cpp23': 'C++23',
            '.cpp2a': 'C++2a',
            '.cpp2b': 'C++2b',
            '.cpp2c': 'C++2c',
            '.cpp2d': 'C++2d',
            '.cpp2e': 'C++2e',
            '.cpp2f': 'C++2f',
            '.cpp2g': 'C++2g',
            '.cpp2h': 'C++2h',
            '.cpp2i': 'C++2i',
            '.cpp2j': 'C++2j',
            '.cpp2k': 'C++2k',
            '.cpp2l': 'C++2l',
            '.cpp2m': 'C++2m',
            '.cpp2n': 'C++2n',
            '.cpp2o': 'C++2o',
            '.cpp2p': 'C++2p',
            '.cpp2q': 'C++2q',
            '.cpp2r': 'C++2r',
            '.cpp2s': 'C++2s',
            '.cpp2t': 'C++2t',
            '.cpp2u': 'C++2u',
            '.cpp2v': 'C++2v',
            '.cpp2w': 'C++2w',
            '.cpp2x': 'C++2x',
            '.cpp2y': 'C++2y',
            '.cpp2z': 'C++2z',
        }
        
        suffix = Path(filename).suffix.lower()
        return extensions.get(suffix)
    
    def _analyze_python_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze Python file and extract symbols."""
        symbols = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    symbols.append({
                        'type': 'class',
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'file': str(file_path)
                    })
                elif isinstance(node, ast.FunctionDef):
                    symbols.append({
                        'type': 'function',
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'file': str(file_path)
                    })
                elif isinstance(node, ast.AsyncFunctionDef):
                    symbols.append({
                        'type': 'async_function',
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'file': str(file_path)
                    })
        
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse Python file {file_path}: {e}[/yellow]")
        
        return symbols
    
    def _generate_structure_tree(self, project_path: Path) -> Dict[str, Any]:
        """Generate a tree structure of the project."""
        def build_tree(path: Path, max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {'type': 'truncated', 'path': str(path)}
            
            tree = {
                'name': path.name,
                'path': str(path),
                'type': 'directory' if path.is_dir() else 'file',
                'children': []
            }
            
            if path.is_dir():
                try:
                    for item in sorted(path.iterdir()):
                        if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules', '.git']:
                            continue
                        tree['children'].append(build_tree(item, max_depth, current_depth + 1))
                except PermissionError:
                    tree['type'] = 'inaccessible'
            
            return tree
        
        return build_tree(project_path)
    
    def generate_codemap(self, project_info: Dict[str, Any]) -> str:
        """Generate CODEMAP.md content using LLM."""
        # Prepare context for LLM
        context = f"""
Project Analysis Results:
- Path: {project_info['path']}
- Total Files: {len(project_info['files'])}
- Total Size: {project_info['total_size']} bytes
- Languages: {dict(project_info['languages'])}
- Python Symbols: {len(project_info['python_symbols'])}

Files by Language:
"""
        
        for lang, count in project_info['languages'].items():
            context += f"- {lang}: {count} files\n"
        
        context += "\nPython Symbols:\n"
        for symbol in project_info['python_symbols'][:50]:  # Limit to first 50
            context += f"- {symbol['type']}: {symbol['name']} (line {symbol['line']})\n"
        
        if len(project_info['python_symbols']) > 50:
            context += f"- ... and {len(project_info['python_symbols']) - 50} more symbols\n"
        
        # Generate codemap using LLM
        codemap_content = self.llm_client.analyze_project(context)
        
        # Add header
        header = f"""# 📋 CODEMAP.md

Generated on: {project_info['scan_time']}
Project Path: {project_info['path']}

## 📊 Project Overview

- **Total Files**: {len(project_info['files'])}
- **Total Size**: {project_info['total_size']:,} bytes
- **Languages**: {', '.join(project_info['languages'].keys())}
- **Python Symbols**: {len(project_info['python_symbols'])}

## 🗂️ File Structure

"""
        
        return header + codemap_content
    
    def display_summary(self, project_info: Dict[str, Any]) -> None:
        """Display project analysis summary."""
        console.print("\n[bold blue]Project Analysis Summary[/bold blue]")
        
        # Create summary table
        table = Table(title="Project Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Files", str(len(project_info['files'])))
        table.add_row("Total Size", f"{project_info['total_size']:,} bytes")
        table.add_row("Languages", str(len(project_info['languages'])))
        table.add_row("Python Symbols", str(len(project_info['python_symbols'])))
        
        console.print(table)
        
        # Language breakdown
        if project_info['languages']:
            console.print("\n[bold blue]Languages[/bold blue]")
            lang_table = Table()
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Files", style="green")
            
            for lang, count in sorted(project_info['languages'].items(), key=lambda x: x[1], reverse=True):
                lang_table.add_row(lang, str(count))
            
            console.print(lang_table)
        
        # Python symbols summary
        if project_info['python_symbols']:
            console.print("\n[bold blue]Python Symbols[/bold blue]")
            symbol_table = Table()
            symbol_table.add_column("Type", style="cyan")
            symbol_table.add_column("Count", style="green")
            
            symbol_types = {}
            for symbol in project_info['python_symbols']:
                symbol_types[symbol['type']] = symbol_types.get(symbol['type'], 0) + 1
            
            for symbol_type, count in sorted(symbol_types.items()):
                symbol_table.add_row(symbol_type, str(count))
            
            console.print(symbol_table)


def analyze_project(path: str = ".") -> Dict[str, Any]:
    """Convenience function to analyze a project."""
    analyzer = ProjectAnalyzer()
    project_info = analyzer.analyze_project(path)
    
    # Generate and save CODEMAP.md
    codemap_content = analyzer.generate_codemap(project_info)
    codemap_path = Path("CODEMAP.md")
    
    try:
        with open(codemap_path, 'w', encoding='utf-8') as f:
            f.write(codemap_content)
        console.print(f"[green]CODEMAP.md generated successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error writing CODEMAP.md: {e}[/red]")
    
    # Display summary
    analyzer.display_summary(project_info)
    
    return project_info