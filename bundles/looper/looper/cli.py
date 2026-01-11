"""
CLI entry point for the supervised loop.

Usage:
    looper "Implement a REST API for user management"
    looper --max-iterations 20 "Fix all the type errors in src/"
    looper --input-file ./user_input.txt "Refactor the authentication module"
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from looper.orchestrator import LoopConfig, LoopResult, SupervisedLoop


@click.command()
@click.argument("task")
@click.option(
    "--max-iterations",
    "-m",
    default=10,
    help="Maximum number of work iterations (default: 10)",
)
@click.option(
    "--supervisor",
    "-s",
    default="looper:agents/supervisor",
    help="Supervisor agent to use for evaluation",
)
@click.option(
    "--bundle",
    "-b",
    default=None,
    help="Bundle for working agent (default: current session's bundle)",
)
@click.option(
    "--input-file",
    "-i",
    type=click.Path(path_type=Path),
    default=None,
    help="File to watch for user input injection",
)
@click.option(
    "--state-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory to persist loop state for resumption",
)
@click.option(
    "--min-confidence",
    default=0.8,
    help="Minimum supervisor confidence to mark complete (default: 0.8)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Print progress to stderr",
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Output result as JSON",
)
def main(
    task: str,
    max_iterations: int,
    supervisor: str,
    bundle: str | None,
    input_file: Path | None,
    state_dir: Path | None,
    min_confidence: float,
    verbose: bool,
    json_output: bool,
) -> None:
    """
    Run a supervised work loop on TASK.

    The working agent will work on the task until a supervisor confirms
    it's complete, or max iterations are reached.

    You can inject input during execution by:
    - Typing in the terminal (if interactive)
    - Writing to the --input-file

    Examples:

        looper "Implement a REST API for user management"

        looper -m 20 "Fix all type errors in the project"

        looper -i ./guidance.txt "Refactor the auth module"
    """
    config = LoopConfig(
        task=task,
        max_iterations=max_iterations,
        supervisor_agent=supervisor,
        working_bundle=bundle,
        input_file=input_file,
        state_dir=state_dir,
        min_confidence=min_confidence,
        verbose=verbose,
    )

    loop = SupervisedLoop(config)

    try:
        result = asyncio.run(loop.run())
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user", err=True)
        sys.exit(1)

    if json_output:
        import json

        output = {
            "complete": result.complete,
            "iterations": result.iterations,
            "reason": result.reason,
            "session_id": result.session_id,
            "final_output": result.final_output,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        _print_result(result)

    sys.exit(0 if result.complete else 1)


def _print_result(result: LoopResult) -> None:
    """Pretty-print the loop result."""
    click.echo()
    click.echo("=" * 60)
    click.echo(f"Status: {'COMPLETE' if result.complete else 'INCOMPLETE'}")
    click.echo(f"Iterations: {result.iterations}")
    click.echo(f"Reason: {result.reason}")
    if result.session_id:
        click.echo(f"Session ID: {result.session_id}")
    click.echo("=" * 60)
    click.echo()
    click.echo("Final Output:")
    click.echo("-" * 40)
    click.echo(result.final_output)


if __name__ == "__main__":
    main()
