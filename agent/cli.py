from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import Config, load_config, ensure_runtime_dirs, require_api_key
from .llm import ask as llm_ask
from .prompts import SYSTEM_PROMPT, plan_prompt, write_file_prompt, edit_file_prompt, multi_patch_prompt
from .state import add_todo, list_todos, mark_todo_done, todos_markdown
from .analyze import generate_codemap
from .tools.shell import run_shell
from .tools.fs import safe_write_file, safe_delete_path
from .tools.patch import apply_single_file_patch


app = typer.Typer(add_completion=False, help="Local Coding Agent (LCA)")
console = Console()


def _cfg() -> Config:
    cfg = load_config()
    ensure_runtime_dirs(cfg)
    return cfg


@app.command()
def whoami():
    """Show current configuration."""
    cfg = _cfg()
    table = Table(title="Configuration")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("LLM_BASE_URL", cfg.llm_base_url)
    table.add_row("LLM_MODEL", cfg.llm_model)
    table.add_row("LLM_API_KEY", cfg.mask_secret(cfg.llm_api_key))
    table.add_row("AGENT_WORKDIR", str(cfg.workdir_path))
    table.add_row("AGENT_LOG_DIR", str(cfg.log_dir_path))
    table.add_row("AGENT_STATE", str(cfg.state_file_path))
    console.print(table)


@app.command()
def analyze(path: Optional[str] = typer.Argument(None, help="Path to analyze", show_default=False)):
    cfg = _cfg()
    target = Path(path) if path else cfg.workdir_path
    generate_codemap(cfg, target)


@app.command()
def ask(prompt: str = typer.Argument(..., help="Question or instruction")):
    cfg = _cfg()
    require_api_key(cfg)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    text = llm_ask(cfg, messages)
    console.print(text)


@app.command()
def plan(goal: str = typer.Argument(..., help="Goal description")):
    cfg = _cfg()
    require_api_key(cfg)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": plan_prompt(goal)},
    ]
    text = llm_ask(cfg, messages)
    console.print(text)
    add_todo(cfg.state_file_path, f"Plan: {goal}")


todo_app = typer.Typer(help="Manage TODO list")


@todo_app.command("add")
def todo_add(title: str = typer.Argument(..., help="Todo title")):
    cfg = _cfg()
    item = add_todo(cfg.state_file_path, title)
    console.print(f"[green]Added[/green] {item.id[:8]}: {title}")


@todo_app.command("list")
def todo_list():
    cfg = _cfg()
    todos = list_todos(cfg.state_file_path)
    console.print(todos_markdown(todos))


@todo_app.command("done")
def todo_done(id_or_index: str = typer.Argument(..., help="Todo id (prefix) or index")):
    cfg = _cfg()
    done = mark_todo_done(cfg.state_file_path, id_or_index)
    if not done:
        console.print("[red]Not found[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Completed[/green] {done.id[:8]}: {done.title}")


app.add_typer(todo_app, name="todo")


@app.command()
def run(cmd: str = typer.Argument(..., help='Shell command, e.g. "echo test"')):
    cfg = _cfg()
    code = run_shell(cfg, cmd)
    raise typer.Exit(code)


@app.command()
def write(
    path: str = typer.Option(..., "--path", help="File path to write"),
    from_desc: str = typer.Option(..., "--from", help="Natural language description"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwrite without prompt"),
):
    cfg = _cfg()
    require_api_key(cfg)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": write_file_prompt(from_desc, path)},
    ]
    text = llm_ask(cfg, messages)
    safe_write_file(cfg, Path(path), text, overwrite=overwrite, assume_yes=overwrite)


@app.command()
def edit(
    path: str = typer.Option(..., "--path", help="File path to edit"),
    instruction: str = typer.Option(..., "--inst", help="Edit instruction"),
):
    cfg = _cfg()
    require_api_key(cfg)
    abs_path = (cfg.workdir_path / path).resolve()
    current_text = abs_path.read_text() if abs_path.exists() else ""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": edit_file_prompt(instruction, path, current_text)},
    ]
    new_text = llm_ask(cfg, messages)
    apply_single_file_patch(cfg, path, new_text)


@app.command()
def delete(path: str = typer.Option(..., "--path", help="Path to delete"), yes: bool = typer.Option(False, "--yes", help="Non-interactive")):
    cfg = _cfg()
    ok = safe_delete_path(cfg, Path(path), assume_yes=yes)
    raise typer.Exit(0 if ok else 1)


@app.command()
def patch(from_desc: str = typer.Option(..., "--from", help="Patch description"), apply: bool = typer.Option(False, "--apply", help="Apply without prompt")):
    cfg = _cfg()
    require_api_key(cfg)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": multi_patch_prompt(from_desc)},
    ]
    text = llm_ask(cfg, messages)
    console.print(text)
    # For now, single-file apply requires manual extraction; safer to require manual review
    if apply:
        console.print("[yellow]--apply for multi-file patches is not implemented for auto-apply. Review above diff and apply manually.[/yellow]")
        raise typer.Exit(2)

