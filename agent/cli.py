from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from .config import load_settings
from .llm import LLMClient
from .state import StateStore, AgentState, TodoItem
from .tools.shell import run_shell
from .tools.fs import safe_write_file, safe_delete_path
from .tools.patch import apply_unified_diff
from .analyze import generate_codemap


console = Console()
app = typer.Typer(add_completion=False, help="Local Coding Agent (LCA)")


def require_api_key():
    if not (Path(".env").exists() or Path("/etc/environment").exists()):
        # still load settings to check
        pass
    settings = load_settings()
    if not settings.llm_api_key:
        console.print("[red]LLM_API_KEY is required. Set it in .env or env vars.[/red]")
        raise typer.Exit(code=1)
    return settings


@app.command()
def whoami():
    """Show configuration info."""
    settings = require_api_key()
    safe = {
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
        "agent_workdir": settings.agent_workdir,
        "agent_log_dir": settings.agent_log_dir,
        "agent_state": settings.agent_state,
    }
    console.print_json(data=safe)


@app.command()
def ask(q: str = typer.Argument(..., help="Question")):
    settings = require_api_key()
    llm = LLMClient(settings.llm_api_key, settings.llm_base_url, settings.llm_model)
    text = llm.ask([
        {"role": "system", "content": "تو یک ایجنت کدنویسی لوکال هستی"},
        {"role": "user", "content": q},
    ])
    console.print(text)


@app.command()
def analyze(path: str = typer.Argument(".", help="Path to scan")):
    out = generate_codemap(path)
    console.print(f"[green]Generated {out}[/green]")


@app.command()
def plan(goal: str = typer.Argument(..., help="High-level goal")):
    settings = require_api_key()
    store = StateStore(settings.agent_state)
    state = store.load()
    item = TodoItem(id=str(len(state.todos)+1), content=goal, status="pending")
    state.todos.append(item)
    store.save(state)
    console.print(f"[green]Added plan item:[/green] {goal}")


todo_app = typer.Typer(help="Manage TODOs")


@todo_app.command("add")
def todo_add(content: str = typer.Argument(...)):
    settings = require_api_key()
    store = StateStore(settings.agent_state)
    state = store.load()
    item = TodoItem(id=str(len(state.todos)+1), content=content, status="pending")
    state.todos.append(item)
    store.save(state)
    console.print(f"[green]Added:[/green] {content}")


@todo_app.command("list")
def todo_list():
    settings = require_api_key()
    store = StateStore(settings.agent_state)
    state = store.load()
    lines = ["# TODOs\n"]
    for t in state.todos:
        lines.append(f"- [{ 'x' if t.status=='completed' else ' '}] ({t.id}) {t.content} · {t.status}")
    console.print(Markdown("\n".join(lines)))


@todo_app.command("done")
def todo_done(todo_id: str = typer.Argument(...)):
    settings = require_api_key()
    store = StateStore(settings.agent_state)
    state = store.load()
    found = False
    for t in state.todos:
        if t.id == todo_id:
            t.status = "completed"
            found = True
            break
    store.save(state)
    if found:
        console.print(f"[green]Done:[/green] {todo_id}")
    else:
        console.print(f"[yellow]Not found:[/yellow] {todo_id}")


app.add_typer(todo_app, name="todo")


@app.command()
def run(cmd: str = typer.Argument(..., help="Shell command to run")):
    settings = require_api_key()
    code, out, err, log_path = run_shell(cmd, settings.agent_workdir, settings.agent_log_dir)
    console.print(f"[cyan]Log:[/cyan] {log_path}")
    if code == 0:
        console.print(out)
    else:
        console.print(f"[red]Exit {code}[/red]\n{err}")
        raise typer.Exit(code=code)


@app.command()
def write(path: str = typer.Option(..., "--path"), from_desc: str = typer.Option(..., "--from"), overwrite: bool = typer.Option(False, "--overwrite")):
    # For now, just write the description as file content placeholder
    try:
        written = safe_write_file(path, from_desc + "\n", overwrite=overwrite)
        console.print(f"[green]Wrote:[/green] {written}")
    except FileExistsError as e:
        console.print(f"[yellow]{e}[/yellow]")
        raise typer.Exit(code=1)


@app.command()
def edit(path: str = typer.Option(..., "--path"), inst: str = typer.Option(..., "--inst")):
    p = Path(path)
    before = p.read_text(encoding="utf-8") if p.exists() else ""
    # naive: append instruction as comment for demo
    after = before + f"\n# EDIT: {inst}\n"
    diff_text = apply_unified_diff(path, after, apply=False)
    console.print(Markdown(f"```diff\n{diff_text}\n```"))
    if typer.confirm("Apply this patch?", default=False):
        apply_unified_diff(path, after, apply=True)
        console.print("[green]Applied.[/green]")


@app.command()
def delete(path: str = typer.Option(..., "--path"), yes: bool = typer.Option(False, "--yes", help="Non-interactive")):
    p = Path(path)
    if not yes:
        if not typer.confirm(f"Delete {path}? This cannot be undone."):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()
    if p.exists():
        safe_delete_path(path)
        console.print("[green]Deleted.[/green]")
    else:
        console.print("[yellow]Path not found.[/yellow]")


@app.command()
def patch(from_desc: str = typer.Option(..., "--from"), apply: bool = typer.Option(False, "--apply", help="Apply without prompt")):
    # Minimal placeholder: create a README patch as demonstration
    target = "README.md"
    new_content = f"# README\n\n{from_desc}\n"
    diff_text = apply_unified_diff(target, new_content, apply=apply)
    console.print(Markdown(f"```diff\n{diff_text}\n```"))
    if not apply:
        if typer.confirm("Apply this patch?", default=False):
            apply_unified_diff(target, new_content, apply=True)
            console.print("[green]Applied.[/green]")


if __name__ == "__main__":
    app()
