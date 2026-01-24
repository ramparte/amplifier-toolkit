"""Command-line interface for Amplifier Swarm."""

import logging
import subprocess
import sys
import time
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .database import TaskDatabase
from .migrate import migrate_yaml_to_db, export_db_to_yaml

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def cli(verbose):
    """Amplifier Swarm - Parallel task execution system."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


@cli.command()
@click.argument("yaml_file", type=click.Path(exists=True, path_type=Path))
@click.option("--db", type=click.Path(path_type=Path), help="Database path (default: tasks.db)")
@click.option("--clear", is_flag=True, help="Clear existing tasks before import")
def import_tasks(yaml_file: Path, db: Path | None, clear: bool):
    """Import tasks from YAML file to database."""
    if db is None:
        db = Path.cwd() / "tasks.db"
    
    console.print(f"[blue]Importing tasks from {yaml_file} to {db}[/blue]")
    
    stats = migrate_yaml_to_db(yaml_file, db, clear_existing=clear)
    
    console.print(f"[green]✓[/green] Total tasks: {stats['total_tasks']}")
    console.print(f"[green]✓[/green] Imported: {stats['imported']}")
    console.print(f"[yellow]![/yellow] Updated: {stats['updated']}")
    console.print(f"[dim]◦[/dim] Skipped: {stats['skipped']}")


@cli.command()
@click.argument("db_file", type=click.Path(exists=True, path_type=Path))
@click.argument("yaml_file", type=click.Path(path_type=Path))
@click.option("--status", help="Export only tasks with this status")
def export_tasks(db_file: Path, yaml_file: Path, status: str | None):
    """Export tasks from database to YAML file."""
    console.print(f"[blue]Exporting tasks from {db_file} to {yaml_file}[/blue]")
    
    export_db_to_yaml(db_file, yaml_file, status_filter=status)
    
    console.print(f"[green]✓[/green] Tasks exported to {yaml_file}")


@cli.command()
@click.option("--db", type=click.Path(exists=True, path_type=Path), required=True, help="Database path")
@click.option("--project-root", type=click.Path(exists=True, path_type=Path), required=True, help="Project root")
@click.option("--builder-agent", required=True, help="Builder agent name")
@click.option("--validator-agent", required=True, help="Validator agent name")
@click.option("--workers", "-n", type=int, default=1, help="Number of workers (default: 1 for serial)")
@click.option("--no-validation", is_flag=True, help="Disable validation")
@click.option("--dashboard-port", type=int, default=8765, help="Dashboard port (default: 8765)")
@click.option("--no-dashboard", is_flag=True, help="Don't start dashboard")
def start(
    db: Path,
    project_root: Path,
    builder_agent: str,
    validator_agent: str,
    workers: int,
    no_validation: bool,
    dashboard_port: int,
    no_dashboard: bool,
):
    """Start the swarm orchestrator and dashboard."""
    console.print("[bold blue]🐝 Starting Amplifier Swarm[/bold blue]")
    console.print(f"[dim]Database: {db}[/dim]")
    console.print(f"[dim]Project: {project_root}[/dim]")
    console.print(f"[dim]Workers: {workers} ({'serial' if workers == 1 else 'parallel'})[/dim]")
    console.print(f"[dim]Validation: {'disabled' if no_validation else 'enabled'}[/dim]")
    
    # Start dashboard in background (if enabled)
    dashboard_proc = None
    if not no_dashboard:
        console.print(f"[blue]Starting dashboard on http://localhost:{dashboard_port}[/blue]")
        dashboard_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "amplifier_swarm.dashboard",
                "--db", str(db),
                "--port", str(dashboard_port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(2)  # Give dashboard time to start
        
        if dashboard_proc.poll() is not None:
            console.print("[red]✗ Dashboard failed to start[/red]")
            return
        
        console.print(f"[green]✓ Dashboard running at http://localhost:{dashboard_port}[/green]")
    
    # Start orchestrator (blocking)
    try:
        console.print("[blue]Starting orchestrator...[/blue]")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "amplifier_swarm.orchestrator",
                "--db", str(db),
                "--project-root", str(project_root),
                "--builder-agent", builder_agent,
                "--validator-agent", validator_agent,
                "--workers", str(workers),
            ] + (["--no-validation"] if no_validation else []),
            check=True,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Orchestrator failed with exit code {e.returncode}[/red]")
    finally:
        if dashboard_proc:
            console.print("[blue]Stopping dashboard...[/blue]")
            dashboard_proc.terminate()
            dashboard_proc.wait(timeout=5)


@cli.command()
@click.option("--db", type=click.Path(exists=True, path_type=Path), required=True, help="Database path")
def status(db: Path):
    """Show current swarm status."""
    db_obj = TaskDatabase(db)
    
    # Task summary
    summary = db_obj.get_tasks_summary()
    
    console.print("\n[bold]📊 Task Progress[/bold]")
    task_table = Table(show_header=True)
    task_table.add_column("Status")
    task_table.add_column("Count", justify="right")
    task_table.add_column("Hours", justify="right")
    
    for status_name, data in summary.items():
        if status_name == "total":
            continue
        task_table.add_row(
            status_name.replace("_", " ").title(),
            str(data["count"]),
            f"{data['hours']:.1f}h",
        )
    
    if "total" in summary:
        task_table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{summary['total']['count']}[/bold]",
            f"[bold]{summary['total']['hours']:.1f}h[/bold]",
            style="bold",
        )
    
    console.print(task_table)
    
    # Workers
    workers = db_obj.get_all_workers()
    
    if workers:
        console.print("\n[bold]👷 Workers[/bold]")
        worker_table = Table(show_header=True)
        worker_table.add_column("Worker ID")
        worker_table.add_column("Status")
        worker_table.add_column("PID", justify="right")
        worker_table.add_column("Completed", justify="right")
        worker_table.add_column("Failed", justify="right")
        worker_table.add_column("Current Task")
        
        for worker in workers:
            status_color = "green" if worker["status"] == "active" else "dim"
            worker_table.add_row(
                worker["worker_id"],
                f"[{status_color}]{worker['status']}[/{status_color}]",
                str(worker["pid"]),
                str(worker["tasks_completed"]),
                str(worker["tasks_failed"]),
                worker["current_task_id"] or "-",
            )
        
        console.print(worker_table)
    else:
        console.print("\n[dim]No active workers[/dim]")
    
    # Progress bar
    if "total" in summary and summary["total"]["count"] > 0:
        total = summary["total"]["count"]
        completed = summary.get("completed", {}).get("count", 0)
        failed = summary.get("failed", {}).get("count", 0)
        in_progress = summary.get("in_progress", {}).get("count", 0) + summary.get("claimed", {}).get("count", 0)
        
        console.print(f"\n[bold]Progress:[/bold] {completed + failed}/{total} tasks completed")
        
        pct = (completed + failed) / total * 100
        console.print(f"[green]{'█' * int(pct / 2)}[/green][dim]{'░' * (50 - int(pct / 2))}[/dim] {pct:.1f}%")


@cli.command()
@click.option("--db", type=click.Path(exists=True, path_type=Path), required=True, help="Database path")
@click.option("--status", help="Filter by status")
@click.option("--limit", type=int, default=20, help="Number of tasks to show")
def list_tasks(db: Path, status: str | None, limit: int):
    """List tasks."""
    db_obj = TaskDatabase(db)
    tasks = db_obj.get_all_tasks(status=status)
    
    if not tasks:
        console.print("[dim]No tasks found[/dim]")
        return
    
    table = Table(show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Phase", style="dim")
    table.add_column("Hours", justify="right")
    table.add_column("Worker", style="dim")
    
    for task in tasks[:limit]:
        status_color = {
            "completed": "green",
            "failed": "red",
            "in_progress": "yellow",
            "claimed": "blue",
            "not_started": "dim",
        }.get(task["status"], "white")
        
        table.add_row(
            task["id"],
            task["name"][:50],
            f"[{status_color}]{task['status']}[/{status_color}]",
            task["phase"] or "-",
            f"{task['estimated_hours']:.1f}h" if task["estimated_hours"] else "-",
            task["worker_id"] or "-",
        )
    
    console.print(table)
    
    if len(tasks) > limit:
        console.print(f"\n[dim]Showing {limit} of {len(tasks)} tasks. Use --limit to show more.[/dim]")


@cli.command()
@click.argument("task_id")
@click.option("--db", type=click.Path(exists=True, path_type=Path), required=True, help="Database path")
def task_info(task_id: str, db: Path):
    """Show detailed task information."""
    db_obj = TaskDatabase(db)
    task = db_obj.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return
    
    console.print(f"\n[bold]Task: {task['id']}[/bold]")
    console.print(f"[bold]Name:[/bold] {task['name']}")
    console.print(f"[bold]Status:[/bold] {task['status']}")
    console.print(f"[bold]Phase:[/bold] {task['phase']}")
    console.print(f"[bold]Estimated Hours:[/bold] {task['estimated_hours']}")
    
    if task['description']:
        console.print(f"\n[bold]Description:[/bold]\n{task['description']}")
    
    if task['worker_id']:
        console.print(f"\n[bold]Worker:[/bold] {task['worker_id']}")
        console.print(f"[bold]Claimed:[/bold] {task['claimed_at']}")
        if task['started_at']:
            console.print(f"[bold]Started:[/bold] {task['started_at']}")
        if task['completed_at']:
            console.print(f"[bold]Completed:[/bold] {task['completed_at']}")
    
    if task['retry_count'] > 0:
        console.print(f"\n[yellow]Retry Count:[/yellow] {task['retry_count']}/{task['max_retries']}")
    
    if task['last_error']:
        console.print(f"\n[red]Last Error:[/red] {task['last_error']}")
    
    # Show log
    log = db_obj.get_task_log(task_id)
    if log:
        console.print(f"\n[bold]Execution Log:[/bold]")
        log_table = Table(show_header=True)
        log_table.add_column("Time", style="dim")
        log_table.add_column("Event")
        log_table.add_column("Message")
        
        for entry in log[:10]:
            log_table.add_row(
                entry["timestamp"],
                entry["event_type"],
                entry["message"],
            )
        
        console.print(log_table)


@cli.command()
@click.argument("task_id")
@click.option("--db", type=click.Path(exists=True, path_type=Path), required=True, help="Database path")
def retry(task_id: str, db: Path):
    """Retry a failed or completed task."""
    db_obj = TaskDatabase(db)
    task = db_obj.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return
    
    if task["status"] not in ["failed", "completed"]:
        console.print(f"[red]Cannot retry task with status: {task['status']}[/red]")
        return
    
    with db_obj.connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = 'not_started',
                worker_id = NULL,
                claimed_at = NULL,
                started_at = NULL,
                completed_at = NULL,
                builder_session_id = NULL,
                validator_session_id = NULL,
                last_error = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (task_id,),
        )
        
        db_obj.log_event(
            conn,
            task_id=task_id,
            worker_id=None,
            event_type="manual_retry",
            message="Task manually reset for retry via CLI",
        )
    
    console.print(f"[green]✓ Task {task_id} reset for retry[/green]")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
