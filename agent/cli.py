"""
Command Line Interface for Local Coding Agent.
"""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .analyze import analyze_project
from .config import get_config
from .llm import get_llm_client
from .state import get_state, save_state
from .tools.fs import FileSystemTool
from .tools.patch import PatchTool
from .tools.shell import ShellTool

app = typer.Typer(
    name="lca",
    help="Local Coding Agent - A powerful local coding agent with CLI interface",
    add_completion=False,
    rich_markup_mode="rich"
)

console = Console()


@app.command()
def whoami():
    """Display agent configuration information."""
    try:
        config = get_config()
        
        # Create info table
        table = Table(title="Agent Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("LLM Base URL", config.llm_base_url)
        table.add_row("LLM Model", config.llm_model)
        table.add_row("Working Directory", str(config.agent_workdir))
        table.add_row("Log Directory", str(config.agent_log_dir))
        table.add_row("State File", str(config.agent_state))
        
        console.print(table)
        
        # System information
        shell_tool = ShellTool()
        sys_info = shell_tool.get_system_info()
        
        sys_table = Table(title="System Information")
        sys_table.add_column("Component", style="cyan")
        sys_table.add_column("Info", style="green")
        
        if 'os' in sys_info:
            sys_table.add_row("Operating System", sys_info['os'])
        sys_table.add_row("Python Version", sys_info['python'])
        sys_table.add_row("Working Directory", sys_info['workdir'])
        sys_table.add_row("Available Commands", ", ".join(sys_info['available_commands']))
        
        console.print(sys_table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def analyze(
    path: str = typer.Argument(".", help="Path to analyze")
):
    """Analyze project and generate CODEMAP.md."""
    try:
        project_info = analyze_project(path)
        console.print(f"[green]Analysis completed successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        sys.exit(1)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask the LLM")
):
    """Ask a question to the LLM."""
    try:
        llm_client = get_llm_client()
        
        console.print(f"[blue]Asking: {question}[/blue]")
        response = llm_client.ask(question)
        
        console.print(Panel(response, title="LLM Response", border_style="green"))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def plan(
    goal: str = typer.Argument(..., help="Goal to plan for")
):
    """Create a plan and add to TODO list."""
    try:
        llm_client = get_llm_client()
        
        console.print(f"[blue]Planning for: {goal}[/blue]")
        plan_response = llm_client.create_plan(goal)
        
        console.print(Panel(plan_response, title="Plan", border_style="blue"))
        
        # Add to TODO
        state = get_state()
        todo_item = state.add_todo(f"Plan: {goal}", plan_response)
        save_state(state)
        
        console.print(f"[green]Added to TODO with ID: {todo_item.id}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def todo(
    action: str = typer.Argument(..., help="Action: add, list, or done"),
    content: Optional[str] = typer.Argument(None, help="Content for add action or ID for done action")
):
    """Manage TODO items."""
    try:
        state = get_state()
        
        if action == "add":
            if not content:
                console.print("[red]Error: Content required for add action[/red]")
                sys.exit(1)
            
            todo_item = state.add_todo(content)
            save_state(state)
            console.print(f"[green]Added TODO with ID: {todo_item.id}[/green]")
            
        elif action == "list":
            pending_todos = state.get_pending_todos()
            completed_todos = state.get_completed_todos()
            
            if pending_todos:
                console.print("[bold blue]Pending TODOs:[/bold blue]")
                table = Table()
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Created", style="yellow")
                
                for todo in pending_todos:
                    table.add_row(
                        str(todo.id),
                        todo.title,
                        todo.created_at.strftime("%Y-%m-%d %H:%M")
                    )
                console.print(table)
            else:
                console.print("[yellow]No pending TODOs[/yellow]")
            
            if completed_todos:
                console.print("\n[bold blue]Completed TODOs:[/bold blue]")
                table = Table()
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Completed", style="yellow")
                
                for todo in completed_todos:
                    completed_time = todo.completed_at.strftime("%Y-%m-%d %H:%M") if todo.completed_at else "Unknown"
                    table.add_row(str(todo.id), todo.title, completed_time)
                console.print(table)
                
        elif action == "done":
            if not content:
                console.print("[red]Error: TODO ID required for done action[/red]")
                sys.exit(1)
            
            try:
                todo_id = int(content)
                if state.complete_todo(todo_id):
                    save_state(state)
                    console.print(f"[green]Marked TODO {todo_id} as completed[/green]")
                else:
                    console.print(f"[red]TODO {todo_id} not found or already completed[/red]")
                    sys.exit(1)
            except ValueError:
                console.print("[red]Error: Invalid TODO ID[/red]")
                sys.exit(1)
        else:
            console.print("[red]Error: Invalid action. Use 'add', 'list', or 'done'[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def run(
    command: str = typer.Argument(..., help="Shell command to execute"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Execute a shell command."""
    try:
        shell_tool = ShellTool()
        
        # Validate command
        is_safe, message = shell_tool.validate_command(command)
        if not is_safe:
            console.print(f"[red]Command validation failed: {message}[/red]")
            if not yes:
                sys.exit(1)
        
        console.print(f"[blue]Executing: {command}[/blue]")
        
        return_code, stdout, stderr = shell_tool.run_command(command, confirm=not yes)
        
        if return_code == 0:
            if stdout:
                console.print(Panel(stdout, title="Output", border_style="green"))
            console.print("[green]Command executed successfully[/green]")
        else:
            if stderr:
                console.print(Panel(stderr, title="Error", border_style="red"))
            console.print(f"[red]Command failed with return code: {return_code}[/red]")
            sys.exit(return_code)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def write(
    path: str = typer.Option(..., "--path", "-p", help="File path to write"),
    from_desc: str = typer.Option(..., "--from", "-f", help="Description of file content"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Generate and write a file from description."""
    try:
        llm_client = get_llm_client()
        fs_tool = FileSystemTool()
        
        console.print(f"[blue]Generating content for: {path}[/blue]")
        console.print(f"[blue]Description: {from_desc}[/blue]")
        
        # Generate file content
        content = llm_client.generate_file_content(from_desc)
        
        # Write file
        success = fs_tool.write_file(
            path, 
            content, 
            overwrite=overwrite,
            confirm=not yes
        )
        
        if success:
            console.print(f"[green]File {path} written successfully[/green]")
        else:
            console.print(f"[red]Failed to write file {path}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def edit(
    path: str = typer.Option(..., "--path", "-p", help="File path to edit"),
    inst: str = typer.Option(..., "--inst", "-i", help="Edit instruction"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Edit a file using LLM-generated unified diff."""
    try:
        llm_client = get_llm_client()
        fs_tool = FileSystemTool()
        patch_tool = PatchTool()
        
        # Read current file content
        current_content = fs_tool.read_file(path)
        if current_content is None:
            console.print(f"[red]Error: Could not read file {path}[/red]")
            sys.exit(1)
        
        console.print(f"[blue]Editing: {path}[/blue]")
        console.print(f"[blue]Instruction: {inst}[/blue]")
        
        # Generate unified diff
        diff_content = llm_client.edit_file(current_content, inst)
        
        if not diff_content.strip():
            console.print("[yellow]No changes generated[/yellow]")
            return
        
        # Show the diff
        console.print(Panel(diff_content, title="Generated Diff", border_style="blue"))
        
        # Apply the patch
        success, message = patch_tool.apply_patch(
            diff_content,
            dry_run=False,
            confirm=not yes
        )
        
        if success:
            console.print(f"[green]File {path} edited successfully[/green]")
        else:
            console.print(f"[red]Failed to edit file: {message}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def delete(
    path: str = typer.Option(..., "--path", "-p", help="Path to delete"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Delete directories recursively"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Delete a file or directory."""
    try:
        fs_tool = FileSystemTool()
        
        console.print(f"[blue]Deleting: {path}[/blue]")
        
        success = fs_tool.delete_file(
            path,
            recursive=recursive,
            confirm=not yes
        )
        
        if not success:
            console.print(f"[red]Failed to delete {path}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def patch(
    from_desc: str = typer.Option(..., "--from", "-f", help="Description of changes"),
    apply: bool = typer.Option(False, "--apply", help="Apply patch immediately"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Generate and optionally apply a unified diff patch."""
    try:
        llm_client = get_llm_client()
        patch_tool = PatchTool()
        
        console.print(f"[blue]Generating patch for: {from_desc}[/blue]")
        
        # Generate patch
        diff_content = llm_client.generate_patch(from_desc)
        
        if not diff_content.strip():
            console.print("[yellow]No patch generated[/yellow]")
            return
        
        # Show the patch
        console.print(Panel(diff_content, title="Generated Patch", border_style="blue"))
        
        if apply:
            # Apply the patch
            success, message = patch_tool.apply_patch(
                diff_content,
                dry_run=False,
                confirm=not yes
            )
            
            if success:
                console.print("[green]Patch applied successfully[/green]")
            else:
                console.print(f"[red]Failed to apply patch: {message}[/red]")
                sys.exit(1)
        else:
            # Save patch to file
            timestamp = llm_client.config.agent_log_dir  # Using placeholder
            patch_filename = f"patch-{timestamp}.diff"
            if patch_tool.save_patch(diff_content, patch_filename):
                console.print(f"[green]Patch saved to {patch_filename}[/green]")
            else:
                console.print("[red]Failed to save patch[/red]")
                sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        # Ensure configuration is loaded
        get_config()
        app()
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print("[yellow]Please check your .env file and ensure LLM_API_KEY is set.[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()