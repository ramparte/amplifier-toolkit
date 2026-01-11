"""
Supervised work loop orchestrator.

Runs a working agent until a supervisor confirms the task is complete,
with support for user input injection between iterations.
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Amplifier imports - these will be available when run in Amplifier context
try:
    from amplifier_foundation import load_bundle  # type: ignore[import-not-found]

    AMPLIFIER_AVAILABLE = True
except ImportError:
    AMPLIFIER_AVAILABLE = False
    load_bundle = None  # type: ignore[assignment]


@dataclass
class LoopConfig:
    """Configuration for the supervised loop."""

    task: str
    """The task description for the working agent."""

    max_iterations: int = 10
    """Maximum number of work iterations before stopping."""

    supervisor_agent: str = "looper:agents/supervisor"
    """Agent to use for evaluation. Can be a path or agent reference."""

    working_bundle: str | None = None
    """Bundle for working agent. If None, uses current session's bundle."""

    input_file: Path | None = None
    """File to watch for user input injection. If None, uses stdin (if interactive)."""

    state_dir: Path | None = None
    """Directory to persist loop state. If None, no persistence."""

    min_confidence: float = 0.8
    """Minimum supervisor confidence to mark task complete."""

    verbose: bool = False
    """Print progress to stderr."""


@dataclass
class IterationResult:
    """Result of a single loop iteration."""

    iteration: int
    work_output: str
    supervisor_verdict: dict
    user_input: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class LoopResult:
    """Final result of the supervised loop."""

    complete: bool
    """Whether the task was completed successfully."""

    iterations: int
    """Number of iterations executed."""

    final_output: str
    """Final work output from the working agent."""

    history: list[IterationResult] = field(default_factory=list)
    """Full history of all iterations."""

    session_id: str | None = None
    """Session ID of the working agent (for potential resumption)."""

    reason: str = ""
    """Reason for completion or termination."""


class SupervisedLoop:
    """
    Orchestrator that runs a working agent in a loop until a supervisor
    confirms the task is complete.

    The pattern:
    1. Working agent executes task (or continues from previous iteration)
    2. Supervisor evaluates: COMPLETE or INCOMPLETE?
    3. If INCOMPLETE and under max_iterations, inject feedback and continue
    4. Check for user input between iterations
    5. Repeat until COMPLETE or max_iterations reached

    User input can be injected via:
    - A watched file (set input_file in config)
    - Stdin if running interactively
    - Programmatic call to inject_input()
    """

    def __init__(self, config: LoopConfig):
        self.config = config
        self.iteration = 0
        self.history: list[IterationResult] = []
        self.working_session_id: str | None = None
        self._user_input_queue: asyncio.Queue[str] = asyncio.Queue()
        self._is_complete = False
        self._stop_requested = False

    async def run(self) -> LoopResult:
        """Execute the supervised loop."""
        if not AMPLIFIER_AVAILABLE:
            return await self._run_simulation()

        return await self._run_with_amplifier()

    async def _run_with_amplifier(self) -> LoopResult:
        """Run using actual Amplifier sessions."""
        if load_bundle is None:
            raise RuntimeError("Amplifier not available")

        # Load bundles
        if self.config.working_bundle:
            working_bundle = await load_bundle(self.config.working_bundle)
        else:
            # Use current bundle (will be passed in from CLI context)
            working_bundle = None

        supervisor_bundle = await load_bundle(self.config.supervisor_agent)

        # Prepare bundles
        working_prepared = await working_bundle.prepare() if working_bundle else None
        supervisor_prepared = await supervisor_bundle.prepare()

        # Start input listener if configured
        input_task = None
        if self.config.input_file or sys.stdin.isatty():
            input_task = asyncio.create_task(self._input_listener())

        try:
            while not self._is_complete and self.iteration < self.config.max_iterations:
                self.iteration += 1
                self._log(f"--- Iteration {self.iteration}/{self.config.max_iterations} ---")

                # Check for user input
                user_input = await self._drain_user_input()
                if user_input:
                    self._log(f"User input received: {user_input[:100]}...")

                # Build prompt for working agent
                prompt = self._build_working_prompt(user_input)

                # Execute working agent
                if working_prepared:
                    async with working_prepared.create_session(
                        session_id=self.working_session_id
                    ) as session:
                        work_output = await session.execute(prompt)
                        self.working_session_id = session.session_id
                else:
                    # Fallback: use task tool pattern (spawn sub-agent)
                    work_output = await self._execute_as_task(prompt)

                self._log(f"Work output: {work_output[:200]}...")

                # Supervisor evaluates
                verdict = await self._supervisor_evaluate(supervisor_prepared, work_output)
                self._log(f"Supervisor verdict: {verdict}")

                # Record iteration
                result = IterationResult(
                    iteration=self.iteration,
                    work_output=work_output,
                    supervisor_verdict=verdict,
                    user_input=user_input,
                )
                self.history.append(result)

                # Check completion
                if verdict.get("status") == "COMPLETE":
                    confidence = verdict.get("confidence", 1.0)
                    if confidence >= self.config.min_confidence:
                        self._is_complete = True
                        self._log(f"Task complete! Confidence: {confidence}")
                    else:
                        self._log(f"COMPLETE but low confidence ({confidence}), continuing...")

                # Persist state if configured
                if self.config.state_dir:
                    await self._save_state()

                if self._stop_requested:
                    break

        finally:
            if input_task:
                input_task.cancel()
                try:
                    await input_task
                except asyncio.CancelledError:
                    pass

        return LoopResult(
            complete=self._is_complete,
            iterations=self.iteration,
            final_output=self.history[-1].work_output if self.history else "",
            history=self.history,
            session_id=self.working_session_id,
            reason=self._determine_reason(),
        )

    async def _run_simulation(self) -> LoopResult:
        """
        Simulation mode when Amplifier is not available.
        Useful for testing the orchestration logic.
        """
        self._log("Running in simulation mode (Amplifier not available)")

        while not self._is_complete and self.iteration < self.config.max_iterations:
            self.iteration += 1
            self._log(f"--- Iteration {self.iteration} (simulated) ---")

            # Simulate work
            work_output = f"[Simulated work output for iteration {self.iteration}]"

            # Simulate evaluation - complete after 3 iterations
            if self.iteration >= 3:
                verdict = {
                    "status": "COMPLETE",
                    "confidence": 0.9,
                    "reasoning": "Simulated completion",
                }
                self._is_complete = True
            else:
                verdict = {
                    "status": "INCOMPLETE",
                    "confidence": 0.5,
                    "remaining_work": "More work needed",
                }

            self.history.append(
                IterationResult(
                    iteration=self.iteration,
                    work_output=work_output,
                    supervisor_verdict=verdict,
                )
            )

            await asyncio.sleep(0.1)  # Simulate processing time

        return LoopResult(
            complete=self._is_complete,
            iterations=self.iteration,
            final_output=self.history[-1].work_output if self.history else "",
            history=self.history,
            reason="Simulation complete",
        )

    def _build_working_prompt(self, user_input: str | None) -> str:
        """Build the prompt for the working agent."""
        if self.iteration == 1:
            prompt = f"""# Task

{self.config.task}

# Instructions

Work on this task thoroughly. When you reach a natural stopping point or complete
the task, summarize what you accomplished.

Do NOT ask for confirmation - make decisions and proceed. Be thorough and
continue making progress until the work is done."""
        else:
            last_result = self.history[-1] if self.history else None
            last_verdict = last_result.supervisor_verdict if last_result else {}
            remaining = last_verdict.get("remaining_work", "Continue making progress")

            prompt = f"""# Continue Task

{self.config.task}

# Supervisor Feedback

The supervisor reviewed your previous work and identified remaining work:

{remaining}

# Instructions

Continue from where you left off. Address the feedback and make further progress.
Do NOT repeat work already done - build on it."""

        # Inject user input if present
        if user_input:
            prompt += f"""

# User Message

The user has provided additional input:

{user_input}

Take this into account as you continue working."""

        return prompt

    async def _supervisor_evaluate(self, supervisor_prepared: Any, work_output: str) -> dict:
        """Have the supervisor evaluate the work output."""
        eval_prompt = f"""# Evaluate Task Completion

## Original Task

{self.config.task}

## Work Output (Iteration {self.iteration})

{work_output}

## Previous Iterations

{len(self.history)} iterations completed before this one.

## Your Evaluation

Evaluate whether the task is COMPLETE or INCOMPLETE.
Respond with the required JSON format only."""

        try:
            async with supervisor_prepared.create_session() as session:
                response = await session.execute(eval_prompt)

            # Parse JSON from response
            # Try to extract JSON from the response
            response_text = response.strip()

            # Handle markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            return json.loads(response_text)

        except json.JSONDecodeError:
            self._log(f"Warning: Could not parse supervisor response as JSON: {response[:100]}")
            # Fallback: try to determine status from text
            if "COMPLETE" in response.upper() and "INCOMPLETE" not in response.upper():
                return {
                    "status": "COMPLETE",
                    "confidence": 0.6,
                    "reasoning": "Inferred from response",
                }
            return {
                "status": "INCOMPLETE",
                "confidence": 0.5,
                "remaining_work": "Could not parse evaluation",
            }
        except Exception as e:
            self._log(f"Error in supervisor evaluation: {e}")
            return {"status": "INCOMPLETE", "confidence": 0.5, "remaining_work": str(e)}

    async def _execute_as_task(self, prompt: str) -> str:
        """Execute using task-tool pattern when no bundle is available."""
        # This would use the task tool to spawn a sub-agent
        # For now, return a placeholder
        return f"[Task execution not yet implemented: {prompt[:100]}...]"

    async def _drain_user_input(self) -> str | None:
        """Non-blocking drain of all queued user input."""
        messages = []
        while True:
            try:
                msg = self._user_input_queue.get_nowait()
                messages.append(msg)
            except asyncio.QueueEmpty:
                break
        return "\n".join(messages) if messages else None

    async def _input_listener(self) -> None:
        """Background task that listens for user input."""
        if self.config.input_file:
            await self._file_input_listener()
        else:
            await self._stdin_input_listener()

    async def _file_input_listener(self) -> None:
        """Watch a file for user input."""
        input_file = self.config.input_file
        if not input_file:
            return

        last_mtime = 0.0
        while not self._is_complete and not self._stop_requested:
            try:
                if input_file.exists():
                    mtime = input_file.stat().st_mtime
                    if mtime > last_mtime:
                        content = input_file.read_text().strip()
                        if content:
                            await self._user_input_queue.put(content)
                            self._log(f"Read input from file: {content[:50]}...")
                            # Clear the file after reading
                            input_file.write_text("")
                        last_mtime = mtime
            except Exception as e:
                self._log(f"Error reading input file: {e}")

            await asyncio.sleep(0.5)

    async def _stdin_input_listener(self) -> None:
        """Listen for stdin input (non-blocking)."""
        import select

        while not self._is_complete and not self._stop_requested:
            try:
                # Non-blocking stdin check (Unix only)
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline().strip()
                    if line:
                        await self._user_input_queue.put(line)
                        self._log(f"Read input from stdin: {line[:50]}...")
            except Exception:
                # select doesn't work on Windows or in some contexts
                pass

            await asyncio.sleep(0.1)

    async def inject_input(self, message: str) -> None:
        """Programmatically inject user input."""
        await self._user_input_queue.put(message)

    def request_stop(self) -> None:
        """Request the loop to stop after current iteration."""
        self._stop_requested = True

    async def _save_state(self) -> None:
        """Persist current state to disk."""
        if not self.config.state_dir:
            return

        self.config.state_dir.mkdir(parents=True, exist_ok=True)
        state_file = self.config.state_dir / f"loop_{self.working_session_id or 'default'}.json"

        state = {
            "task": self.config.task,
            "iteration": self.iteration,
            "working_session_id": self.working_session_id,
            "is_complete": self._is_complete,
            "history": [
                {
                    "iteration": r.iteration,
                    "work_output": r.work_output,
                    "supervisor_verdict": r.supervisor_verdict,
                    "user_input": r.user_input,
                    "timestamp": r.timestamp,
                }
                for r in self.history
            ],
        }

        state_file.write_text(json.dumps(state, indent=2))
        self._log(f"State saved to {state_file}")

    def _determine_reason(self) -> str:
        """Determine the reason for loop termination."""
        if self._is_complete:
            return "Task completed successfully"
        if self._stop_requested:
            return "Stop requested by user"
        if self.iteration >= self.config.max_iterations:
            return f"Maximum iterations ({self.config.max_iterations}) reached"
        return "Unknown"

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.config.verbose:
            print(f"[Looper] {message}", file=sys.stderr)
