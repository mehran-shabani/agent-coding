"""Main CLI interface for the Local Coding Agent."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel

from .config import load_config, AgentConfig
from .llm import LLMClient
from .state import AgentState
from .analyze import generate_codemap
from .tools.fs import safe_write_file, safe_read_file, safe_delete
from .tools.shell import execute_command, get_shell_info
from .tools.patch import apply_patch, display_patch, save_patch
from .prompts import ERROR_MESSAGES


app = typer.Typer(
    name="lca",
    help="Local Coding Agent - AI-powered coding assistant",
    add_completion=False,
)
console = Console()

# Global config and clients (initialized on first use)
_config: Optional[AgentConfig] = None
_llm_client: Optional[LLMClient] = None
_state: Optional[AgentState] = None


def get_config() -> AgentConfig:
    """Get or initialize configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_llm_client() -> LLMClient:
    """Get or initialize LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(get_config())
    return _llm_client


def get_state() -> AgentState:
    """Get or initialize state manager."""
    global _state
    if _state is None:
        _state = AgentState(get_config().agent_state)
    return _state


@app.command()
def whoami():
    """Display current configuration information."""
    config = get_config()
    
    table = Table(title="LCA Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("LLM API", config.llm_base_url)
    table.add_row("LLM Model", config.llm_model)
    table.add_row("Working Directory", str(config.agent_workdir))
    table.add_row("Log Directory", str(config.agent_log_dir))
    table.add_row("State File", str(config.agent_state))
    
    # Shell info
    shell_info = get_shell_info()
    table.add_row("Shell", shell_info["shell"])
    table.add_row("User", shell_info["user"])
    table.add_row("Current Directory", shell_info["pwd"])
    
    console.print(table)


@app.command()
def analyze(
    path: Optional[Path] = typer.Argument(None, help="Path to analyze (default: current directory)")
):
    """Analyze project structure and generate CODEMAP.md."""
    config = get_config()
    
    # Use provided path or current directory
    target_path = path or config.agent_workdir
    target_path = target_path.resolve()
    
    # Generate codemap
    output_path = target_path / "CODEMAP.md"
    success = generate_codemap(target_path, output_path)
    
    if not success:
        raise typer.Exit(1)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask the AI"),
    context: Optional[Path] = typer.Option(None, "--context", "-c", help="File to include as context"),
):
    """Ask a question to the AI assistant."""
    llm = get_llm_client()
    
    # Build the question with context if provided
    full_question = question
    if context and context.exists():
        success, content = safe_read_file(context, get_config().agent_workdir)
        if success:
            full_question = f"Context from {context}:\n```\n{content}\n```\n\nQuestion: {question}"
        else:
            console.print(f"[yellow]Warning: Could not read context file: {content}[/yellow]")
    
    # Get response
    with console.status("[cyan]Thinking...[/cyan]"):
        try:
            response = llm.ask(full_question)
            console.print(Panel(Markdown(response), title="AI Response", border_style="green"))
        except Exception as e:
            console.print(f"[red]{ERROR_MESSAGES['llm_error'].format(error=str(e))}[/red]")
            raise typer.Exit(1)


@app.command()
def plan(
    goal: str = typer.Argument(..., help="Goal to plan for"),
    add_todos: bool = typer.Option(True, "--add-todos/--no-todos", help="Add steps to TODO list"),
):
    """Generate a plan for achieving a goal."""
    llm = get_llm_client()
    state = get_state()
    
    # Get current context
    context = None
    codemap_path = get_config().agent_workdir / "CODEMAP.md"
    if codemap_path.exists():
        _, context = safe_read_file(codemap_path, get_config().agent_workdir)
    
    # Generate plan
    with console.status("[cyan]Planning...[/cyan]"):
        try:
            steps = llm.plan_task(goal, context)
            
            if not steps:
                console.print("[yellow]No steps generated[/yellow]")
                return
            
            # Display plan
            console.print(Panel(f"[bold cyan]Plan for:[/bold cyan] {goal}", expand=False))
            console.print()
            
            for i, step in enumerate(steps, 1):
                console.print(f"{i}. {step}")
                
                # Add to TODO if requested
                if add_todos:
                    todo = state.add_todo(step)
                    console.print(f"   [dim]→ Added as TODO #{todo.id}[/dim]")
            
            console.print()
            
        except Exception as e:
            console.print(f"[red]{ERROR_MESSAGES['llm_error'].format(error=str(e))}[/red]")
            raise typer.Exit(1)


# TODO subcommands
todo_app = typer.Typer(help="Manage TODO items")


@todo_app.command("add")
def todo_add(
    text: str = typer.Argument(..., help="TODO item text")
):
    """Add a new TODO item."""
    state = get_state()
    todo = state.add_todo(text)
    console.print(f"[green]✅ Added TODO item #{todo.id}[/green]")


@todo_app.command("list")
def todo_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (pending/done)"),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Output as markdown"),
):
    """List TODO items."""
    state = get_state()
    
    if markdown:
        console.print(Markdown(state.get_markdown_todos()))
    else:
        todos = state.list_todos(status)
        
        if not todos:
            console.print("[yellow]No TODO items found[/yellow]")
            return
        
        table = Table(title="TODO Items", show_header=True)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Status", width=10)
        table.add_column("Task")
        table.add_column("Created", style="dim")
        
        for todo in todos:
            status_style = "green" if todo.status == "done" else "yellow"
            status_icon = "✅" if todo.status == "done" else "⏳"
            
            table.add_row(
                str(todo.id),
                f"[{status_style}]{status_icon} {todo.status}[/{status_style}]",
                todo.text,
                todo.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)


@todo_app.command("done")
def todo_done(
    todo_id: int = typer.Argument(..., help="TODO item ID to mark as done")
):
    """Mark a TODO item as done."""
    state = get_state()
    
    if state.mark_todo_done(todo_id):
        console.print(f"[green]✅ Marked TODO #{todo_id} as done[/green]")
    else:
        console.print(f"[red]❌ TODO #{todo_id} not found or already done[/red]")
        raise typer.Exit(1)


app.add_typer(todo_app, name="todo")


@app.command()
def run(
    command: str = typer.Argument(..., help="Shell command to execute"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Command timeout in seconds"),
):
    """Execute a shell command in the working directory."""
    config = get_config()
    
    console.print(f"[cyan]Executing:[/cyan] {command}")
    console.print(f"[dim]Working directory:[/dim] {config.agent_workdir}")
    console.print()
    
    success, output, message = execute_command(
        command,
        config.agent_workdir,
        config.agent_log_dir,
        timeout
    )
    
    if output:
        console.print(Panel(output, title="Output", border_style="blue"))
    
    if success:
        console.print(f"[green]{message}[/green]")
    else:
        console.print(f"[red]{message}[/red]")
        if output:
            console.print(f"[red]Error output:[/red] {output}")
        raise typer.Exit(1)


@app.command()
def write(
    path: Path = typer.Option(..., "--path", "-p", help="Path to write file to"),
    from_desc: str = typer.Option(..., "--from", "-f", help="Description of file to generate"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """Generate and write a file based on description."""
    config = get_config()
    llm = get_llm_client()
    
    # Make path absolute if relative
    if not path.is_absolute():
        path = config.agent_workdir / path
    
    # Generate content
    with console.status("[cyan]Generating file content...[/cyan]"):
        try:
            file_type = path.suffix.lstrip('.') if path.suffix else None
            content = llm.generate_code(from_desc, file_type)
        except Exception as e:
            console.print(f"[red]{ERROR_MESSAGES['llm_error'].format(error=str(e))}[/red]")
            raise typer.Exit(1)
    
    # Write file
    success, message = safe_write_file(
        path,
        content,
        config.agent_workdir,
        overwrite=overwrite,
        force=yes
    )
    
    if success:
        console.print(f"[green]{message}[/green]")
    else:
        console.print(f"[red]{message}[/red]")
        raise typer.Exit(1)


@app.command()
def edit(
    path: Path = typer.Option(..., "--path", "-p", help="Path to file to edit"),
    inst: str = typer.Option(..., "--inst", "-i", help="Edit instruction"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """Edit an existing file using AI-generated patch."""
    config = get_config()
    llm = get_llm_client()
    
    # Make path absolute if relative
    if not path.is_absolute():
        path = config.agent_workdir / path
    
    # Read current file content
    success, content = safe_read_file(path, config.agent_workdir)
    if not success:
        console.print(f"[red]{content}[/red]")  # content contains error message
        raise typer.Exit(1)
    
    # Generate patch
    with console.status("[cyan]Generating patch...[/cyan]"):
        try:
            patch_content = llm.generate_patch(content, inst)
        except Exception as e:
            console.print(f"[red]{ERROR_MESSAGES['llm_error'].format(error=str(e))}[/red]")
            raise typer.Exit(1)
    
    # Display and apply patch
    if not yes:
        display_patch(patch_content)
    
    success, message = apply_patch(
        patch_content,
        config.agent_workdir,
        force=yes
    )
    
    if success:
        console.print(f"[green]{message}[/green]")
    else:
        # Save failed patch for debugging
        reports_dir = config.agent_state.parent / "reports"
        patch_path = save_patch(patch_content, reports_dir, "failed-edit")
        console.print(f"[red]{message}[/red]")
        console.print(f"[yellow]Patch saved to: {patch_path}[/yellow]")
        raise typer.Exit(1)


@app.command()
def delete(
    path: Path = typer.Option(..., "--path", "-p", help="Path to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a file or directory."""
    config = get_config()
    
    # Make path absolute if relative
    if not path.is_absolute():
        path = config.agent_workdir / path
    
    success, message = safe_delete(path, config.agent_workdir, force=yes)
    
    if success:
        console.print(f"[green]{message}[/green]")
    else:
        console.print(f"[red]{message}[/red]")
        raise typer.Exit(1)


@app.command()
def patch(
    from_desc: str = typer.Option(..., "--from", "-f", help="Description of changes to make"),
    apply: bool = typer.Option(False, "--apply", "-a", help="Apply the patch immediately"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """Generate and optionally apply a multi-file patch."""
    config = get_config()
    llm = get_llm_client()
    
    # Get project context
    context = ""
    codemap_path = config.agent_workdir / "CODEMAP.md"
    if codemap_path.exists():
        _, context = safe_read_file(codemap_path, config.agent_workdir)
    
    # Generate patch
    with console.status("[cyan]Generating patch...[/cyan]"):
        try:
            patch_content = llm.generate_multi_file_patch(context, from_desc)
        except Exception as e:
            console.print(f"[red]{ERROR_MESSAGES['llm_error'].format(error=str(e))}[/red]")
            raise typer.Exit(1)
    
    # Save patch
    reports_dir = config.agent_state.parent / "reports"
    patch_path = save_patch(patch_content, reports_dir, from_desc[:30])
    console.print(f"[green]Patch saved to: {patch_path}[/green]")
    
    # Display patch
    display_patch(patch_content)
    
    # Apply if requested
    if apply:
        success, message = apply_patch(
            patch_content,
            config.agent_workdir,
            force=yes
        )
        
        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[red]{message}[/red]")
            raise typer.Exit(1)


@app.callback()
def main_callback():
    """Initialize the application."""
    # Ensure .env is loaded
    from dotenv import load_dotenv
    load_dotenv()


def main():
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()