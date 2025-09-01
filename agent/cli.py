"""Main CLI module for the Local Coding Agent."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import AgentConfig, ensure_directories, load_config

app = typer.Typer(help="Local Coding Agent - A local coding assistant powered by LLM APIs")
console = Console()


def get_config() -> AgentConfig:
    """Get configuration and ensure directories exist."""
    try:
        config = load_config()
        ensure_directories(config)
        return config
    except ValueError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        sys.exit(1)


@app.command()
def whoami():
    """Display agent configuration information."""
    try:
        config = get_config()
        
        table = Table(title="Agent Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("LLM Base URL", config.llm_base_url)
        table.add_row("LLM Model", config.llm_model)
        table.add_row("API Key", f"{'*' * (len(config.llm_api_key) - 4)}{config.llm_api_key[-4:]}")
        table.add_row("Work Directory", str(config.agent_workdir.absolute()))
        table.add_row("Log Directory", str(config.agent_log_dir.absolute()))
        table.add_row("State File", str(config.agent_state.absolute()))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def analyze(path: Optional[str] = typer.Argument(None, help="Path to analyze (default: current directory)")):
    """Analyze project structure and generate CODEMAP.md."""
    try:
        config = get_config()
        
        # Import analyze tools
        from .analyze import analyze_project, generate_codemap, save_codemap
        
        # Determine target directory
        if path:
            if not Path(path).is_absolute():
                target_dir = config.agent_workdir / path
            else:
                target_dir = Path(path)
        else:
            target_dir = config.agent_workdir
        
        if not target_dir.exists():
            console.print(f"[red]Error:[/red] Directory '{target_dir}' does not exist")
            raise typer.Exit(1)
        
        if not target_dir.is_dir():
            console.print(f"[red]Error:[/red] '{target_dir}' is not a directory")
            raise typer.Exit(1)
        
        # Analyze project
        analysis = analyze_project(str(target_dir))
        
        # Generate CODEMAP content
        console.print("[blue]Generating CODEMAP.md...[/blue]")
        codemap_content = generate_codemap(analysis)
        
        # Save CODEMAP.md
        codemap_path = target_dir / "CODEMAP.md"
        success = save_codemap(codemap_content, str(codemap_path))
        
        if not success:
            raise typer.Exit(1)
        
        # Display summary
        console.print(f"\n[green]Analysis complete![/green]")
        console.print(f"- Analyzed {analysis.total_files:,} files")
        console.print(f"- Total {analysis.total_lines:,} lines of code")
        console.print(f"- {len(analysis.languages)} programming languages detected")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def ask(question: str = typer.Argument(..., help="Question to ask the LLM")):
    """Ask a free-form question to the LLM."""
    try:
        config = get_config()
        
        # Import LLM tools
        from .llm import create_llm_client
        
        # Create LLM client
        llm = create_llm_client(config)
        
        # Ask question
        console.print("[blue]Asking LLM...[/blue]")
        response = llm.ask_question(question)
        
        if response:
            console.print("\n[green]Response:[/green]")
            console.print(response)
        else:
            console.print("[red]Failed to get response from LLM[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def plan(goal: str = typer.Argument(..., help="Goal to create a plan for")):
    """Create a plan for achieving a goal and add to TODO."""
    try:
        config = get_config()
        
        # Import tools
        from .llm import create_llm_client
        from .state import create_state_manager, display_todos
        
        # Create LLM client and state manager
        llm = create_llm_client(config)
        state_manager = create_state_manager(config.agent_state)
        state = state_manager.get_state()
        
        # Generate plan
        console.print(f"[blue]Creating plan for:[/blue] {goal}")
        plan_steps = llm.create_plan(goal)
        
        if not plan_steps:
            console.print("[red]Failed to generate plan[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n[green]Generated plan with {len(plan_steps)} steps:[/green]")
        for i, step in enumerate(plan_steps, 1):
            console.print(f"  {i}. {step}")
        
        # Add to TODO list
        added_todos = state.add_plan_todos(plan_steps, goal)
        
        # Save state
        if not state_manager.save_state():
            console.print("[red]Failed to save state[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n[green]Added {len(added_todos)} TODO items[/green]")
        display_todos(added_todos, "New TODO Items")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def run(command: str = typer.Argument(..., help="Shell command to execute")):
    """Execute a shell command in the workspace."""
    try:
        config = get_config()
        
        # Import shell tools
        from .tools.shell import execute_command, log_command, is_safe_command
        
        # Check if command is safe
        safe, reason = is_safe_command(command)
        if not safe:
            console.print(f"[red]Unsafe command detected:[/red] {reason}")
            from rich.prompt import Confirm
            if not Confirm.ask("Do you want to execute this potentially dangerous command anyway?"):
                console.print("[blue]Command execution cancelled[/blue]")
                return
        
        # Execute command
        result = execute_command(command, str(config.agent_workdir))
        
        # Log the command
        log_command(result, config.agent_log_dir)
        
        # Exit with appropriate code
        if not result.success:
            raise typer.Exit(result.returncode)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def write(
    path: str = typer.Option(..., "--path", help="File path to write"),
    from_desc: str = typer.Option(..., "--from", help="Description of what to generate"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing file without confirmation")
):
    """Generate and write a file from description."""
    try:
        config = get_config()
        
        # Import tools
        from .llm import create_llm_client
        from .tools.fs import safe_write
        
        # Create LLM client
        llm = create_llm_client(config)
        
        # Generate content
        console.print("[blue]Generating file content...[/blue]")
        content = llm.generate_file_content(from_desc, path)
        
        if not content:
            console.print("[red]Failed to generate file content[/red]")
            raise typer.Exit(1)
        
        # Convert relative path to absolute if needed
        if not Path(path).is_absolute():
            full_path = config.agent_workdir / path
        else:
            full_path = Path(path)
        
        # Write file
        success = safe_write(str(full_path), content, overwrite)
        
        if not success:
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def edit(
    path: str = typer.Option(..., "--path", help="File path to edit"),
    instruction: str = typer.Option(..., "--inst", help="Edit instruction")
):
    """Edit a file using patch-based modifications."""
    try:
        config = get_config()
        
        # Import tools
        from .llm import create_llm_client
        from .tools.fs import read_file_safe
        from .tools.patch import validate_patch, display_patch, parse_unified_diff, apply_patch_to_file, create_backup
        from rich.prompt import Confirm
        
        # Convert relative path to absolute if needed
        if not Path(path).is_absolute():
            full_path = config.agent_workdir / path
        else:
            full_path = Path(path)
        
        # Read current file content
        current_content = read_file_safe(str(full_path))
        if current_content is None:
            raise typer.Exit(1)
        
        # Create LLM client
        llm = create_llm_client(config)
        
        # Generate edit patch
        console.print("[blue]Generating edit patch...[/blue]")
        patch_content = llm.generate_file_edit(current_content, str(full_path), instruction)
        
        if not patch_content:
            console.print("[red]Failed to generate edit patch[/red]")
            raise typer.Exit(1)
        
        # Validate patch
        validation = validate_patch(patch_content)
        if not validation.success:
            console.print(f"[red]Invalid patch: {validation.message}[/red]")
            raise typer.Exit(1)
        
        # Display patch
        display_patch(patch_content, str(full_path))
        
        # Ask for confirmation
        if not Confirm.ask("Apply this patch?"):
            console.print("[blue]Patch cancelled[/blue]")
            return
        
        # Create backup
        backup_dir = config.agent_state.parent / "backups"
        create_backup(str(full_path), backup_dir)
        
        # Parse and apply patch
        files_data = parse_unified_diff(patch_content)
        if files_data:
            result = apply_patch_to_file(str(full_path), files_data[0])
            if result.success:
                console.print(f"[green]Patch applied successfully[/green]")
            else:
                console.print(f"[red]Failed to apply patch: {result.message}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[red]No valid patch data found[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def delete(
    path: str = typer.Option(..., "--path", help="File or directory path to delete"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation")
):
    """Delete a file or directory."""
    try:
        config = get_config()
        
        # Import file system tools
        from .tools.fs import safe_delete
        
        # Convert relative path to absolute if needed
        if not Path(path).is_absolute():
            full_path = config.agent_workdir / path
        else:
            full_path = Path(path)
        
        # Execute deletion
        success = safe_delete(str(full_path), yes)
        
        if not success:
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def patch(
    from_desc: str = typer.Option(..., "--from", help="Description of changes to generate patch"),
    apply: bool = typer.Option(False, "--apply", help="Apply the patch immediately")
):
    """Generate and optionally apply a patch."""
    try:
        config = get_config()
        
        # Import tools
        from .llm import create_llm_client
        from .tools.patch import validate_patch, display_patch, save_patch, apply_patch_file
        from rich.prompt import Confirm
        
        # Create LLM client
        llm = create_llm_client(config)
        
        # Generate project context (simplified for now)
        project_context = f"Working directory: {config.agent_workdir}"
        
        # Generate patch
        console.print("[blue]Generating multi-file patch...[/blue]")
        patch_content = llm.generate_multi_file_patch(project_context, from_desc)
        
        if not patch_content:
            console.print("[red]Failed to generate patch[/red]")
            raise typer.Exit(1)
        
        # Validate patch
        validation = validate_patch(patch_content)
        if not validation.success:
            console.print(f"[red]Invalid patch: {validation.message}[/red]")
            # Save invalid patch for debugging
            reports_dir = config.agent_state.parent / "reports"
            save_patch(patch_content, reports_dir, "invalid-patch")
            raise typer.Exit(1)
        
        # Display patch
        display_patch(patch_content, "multi-file patch")
        
        # Save patch
        patch_dir = config.agent_state.parent / "patches"
        patch_file = save_patch(patch_content, patch_dir, from_desc)
        
        # Apply patch if requested
        if apply or Confirm.ask("Apply this patch?"):
            console.print("[blue]Applying patch...[/blue]")
            results = apply_patch_file(patch_file, config.agent_workdir)
            
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)
            
            if success_count == total_count:
                console.print(f"[green]Patch applied successfully to {success_count} file(s)[/green]")
            else:
                console.print(f"[yellow]Patch partially applied: {success_count}/{total_count} files[/yellow]")
                for result in results:
                    if not result.success:
                        console.print(f"[red]Failed: {result.message}[/red]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# TODO subcommands
todo_app = typer.Typer(help="Manage TODO items")
app.add_typer(todo_app, name="todo")


@todo_app.command("add")
def todo_add(item: str = typer.Argument(..., help="TODO item to add")):
    """Add a new TODO item."""
    try:
        config = get_config()
        
        # Import tools
        from .state import create_state_manager
        
        # Create state manager
        state_manager = create_state_manager(config.agent_state)
        state = state_manager.get_state()
        
        # Add TODO item
        todo = state.add_todo(item)
        
        # Save state
        if not state_manager.save_state():
            console.print("[red]Failed to save state[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]Added TODO item #{todo.id}:[/green] {todo.title}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@todo_app.command("list")
def todo_list():
    """List all TODO items."""
    try:
        config = get_config()
        
        # Import tools
        from .state import create_state_manager, display_todos, generate_todo_markdown
        
        # Create state manager
        state_manager = create_state_manager(config.agent_state)
        state = state_manager.get_state()
        
        # Display todos
        if not state.todos:
            console.print("[dim]No TODO items found[/dim]")
            return
        
        # Show active todos first
        active_todos = state.get_active_todos()
        if active_todos:
            display_todos(active_todos, "Active TODO Items")
        
        # Show completed todos
        completed_todos = state.get_completed_todos()
        if completed_todos:
            console.print()  # Add spacing
            display_todos(completed_todos[-5:], "Recent Completed Items (Last 5)")
        
        # Generate markdown output
        console.print(f"\n[dim]Total: {len(state.todos)} items ({len(active_todos)} active, {len(completed_todos)} completed)[/dim]")
        
        # Save markdown version
        markdown_content = generate_todo_markdown(state.todos)
        todo_md_path = config.agent_state.parent / "TODO.md"
        try:
            todo_md_path.write_text(markdown_content, encoding='utf-8')
            console.print(f"[dim]Markdown version saved to: {todo_md_path}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to save TODO.md: {e}[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@todo_app.command("done")
def todo_done(item_id: int = typer.Argument(..., help="TODO item ID to mark as done")):
    """Mark a TODO item as done."""
    try:
        config = get_config()
        
        # Import tools
        from .state import create_state_manager
        
        # Create state manager
        state_manager = create_state_manager(config.agent_state)
        state = state_manager.get_state()
        
        # Mark todo as done
        success = state.mark_todo_done(item_id)
        
        if not success:
            console.print(f"[red]TODO item #{item_id} not found[/red]")
            raise typer.Exit(1)
        
        # Save state
        if not state_manager.save_state():
            console.print("[red]Failed to save state[/red]")
            raise typer.Exit(1)
        
        todo = state.get_todo(item_id)
        console.print(f"[green]Marked TODO item #{item_id} as completed:[/green] {todo.title}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()