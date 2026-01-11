"""
Looper tool for Amplifier.

Registers a `looper` tool that runs a supervised work loop until completion.
Can be invoked from inside an active Amplifier session.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from amplifier_core import Coordinator  # type: ignore[import-not-found]

# Default input file location (current directory for per-project input)
DEFAULT_INPUT_FILE = Path.cwd() / "looper-input.txt"


@dataclass
class LooperConfig:
    """Configuration extracted from tool parameters."""

    task: str
    max_iterations: int = 10
    min_confidence: float = 0.8
    checkpoint_every: int | None = None  # Pause for user input every N iterations
    input_file: Path = field(default_factory=lambda: DEFAULT_INPUT_FILE)
    verbose: bool = True


@dataclass
class LooperResult:
    """Result returned by the looper tool."""

    complete: bool
    iterations: int
    final_output: str
    reason: str
    history_summary: list[str]


async def looper_execute(
    task: str,
    max_iterations: int = 10,
    min_confidence: float = 0.8,
    checkpoint_every: int | None = None,
    coordinator: Coordinator | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Execute a supervised work loop on the given task.

    This tool keeps a working agent running on your task until a supervisor
    agent confirms it's complete. You can inject guidance by writing to:
    ~/.amplifier/looper-input.txt

    Args:
        task: The task description for the working agent
        max_iterations: Maximum work iterations before stopping (default: 10)
        min_confidence: Minimum supervisor confidence to mark complete (default: 0.8)
        checkpoint_every: Pause for user confirmation every N iterations (optional)
        coordinator: Injected by Amplifier - the session coordinator

    Returns:
        Dict with: complete, iterations, final_output, reason, history_summary
    """
    config = LooperConfig(
        task=task,
        max_iterations=max_iterations,
        min_confidence=min_confidence,
        checkpoint_every=checkpoint_every,
    )

    loop = LooperExecution(config, coordinator)
    result = await loop.run()

    return {
        "complete": result.complete,
        "iterations": result.iterations,
        "final_output": result.final_output,
        "reason": result.reason,
        "history_summary": result.history_summary,
    }


class LooperExecution:
    """
    Executes the supervised work loop.

    Pattern:
    1. Working agent executes task
    2. Supervisor evaluates: COMPLETE or INCOMPLETE?
    3. If INCOMPLETE, inject feedback and continue
    4. Check for user input between iterations
    5. Repeat until COMPLETE or max iterations
    """

    def __init__(self, config: LooperConfig, coordinator: Coordinator | None):
        self.config = config
        self.coordinator = coordinator
        self.iteration = 0
        self.history: list[dict[str, Any]] = []
        self._is_complete = False

    async def run(self) -> LooperResult:
        """Execute the supervised loop."""
        if not self.coordinator:
            return await self._run_standalone()

        return await self._run_with_coordinator()

    async def _run_with_coordinator(self) -> LooperResult:
        """Run using Amplifier coordinator for session spawning."""
        if not self.coordinator:
            return await self._run_standalone()

        # Get spawn capability from coordinator
        spawn_fn = self.coordinator.get_capability("session.spawn")
        if not spawn_fn:
            self._log("Warning: session.spawn capability not available, using standalone")
            return await self._run_standalone()

        # Ensure input file directory exists
        self.config.input_file.parent.mkdir(parents=True, exist_ok=True)

        while not self._is_complete and self.iteration < self.config.max_iterations:
            self.iteration += 1
            self._log(f"--- Iteration {self.iteration}/{self.config.max_iterations} ---")

            # Check for user input from file
            user_input = self._check_input_file()
            if user_input:
                self._log(f"User input: {user_input[:100]}...")

            # Build prompt for working agent
            working_prompt = self._build_working_prompt(user_input)

            # Execute working agent via spawn
            self._log("Working agent executing...")
            work_result = await spawn_fn(
                instruction=working_prompt,
                # Exclude looper tool to prevent recursion
                tool_filter={"exclude": ["looper"]},
            )
            work_output = work_result.get("output", str(work_result))
            self._log(f"Work output: {work_output[:200]}...")

            # Execute supervisor evaluation
            self._log("Supervisor evaluating...")
            eval_prompt = self._build_supervisor_prompt(work_output)
            eval_result = await spawn_fn(
                instruction=eval_prompt,
                # Supervisor has no tools - evaluation only
                tool_filter={"include": []},
            )
            verdict = self._parse_verdict(eval_result.get("output", str(eval_result)))
            self._log(f"Verdict: {verdict.get('status')} (confidence: {verdict.get('confidence')})")

            # Record iteration
            self.history.append(
                {
                    "iteration": self.iteration,
                    "work_output": work_output[:500],  # Truncate for summary
                    "verdict": verdict,
                    "user_input": user_input,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Check completion
            status = verdict.get("status", "").upper()
            confidence = verdict.get("confidence", 0.0)
            if status == "COMPLETE" and confidence >= self.config.min_confidence:
                self._is_complete = True
                self._log("Task marked complete!")

            # Checkpoint pause if configured
            if (
                self.config.checkpoint_every
                and self.iteration % self.config.checkpoint_every == 0
                and not self._is_complete
            ):
                await self._checkpoint_pause()

        return LooperResult(
            complete=self._is_complete,
            iterations=self.iteration,
            final_output=self.history[-1]["work_output"] if self.history else "",
            reason=self._determine_reason(),
            history_summary=[
                f"Iter {h['iteration']}: {h['verdict'].get('status', 'UNKNOWN')}"
                for h in self.history
            ],
        )

    async def _run_standalone(self) -> LooperResult:
        """Standalone mode without Amplifier (for testing)."""
        self._log("Running in standalone mode")

        while not self._is_complete and self.iteration < self.config.max_iterations:
            self.iteration += 1
            self._log(f"--- Iteration {self.iteration} (standalone) ---")

            # Simulate work
            work_output = f"[Simulated work for iteration {self.iteration}]"

            # Simulate evaluation - complete after 3 iterations
            if self.iteration >= 3:
                verdict = {"status": "COMPLETE", "confidence": 0.9}
                self._is_complete = True
            else:
                verdict = {"status": "INCOMPLETE", "confidence": 0.5}

            self.history.append(
                {
                    "iteration": self.iteration,
                    "work_output": work_output,
                    "verdict": verdict,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            await asyncio.sleep(0.1)

        return LooperResult(
            complete=self._is_complete,
            iterations=self.iteration,
            final_output=self.history[-1]["work_output"] if self.history else "",
            reason="Standalone simulation complete",
            history_summary=[
                f"Iter {h['iteration']}: {h['verdict'].get('status')}" for h in self.history
            ],
        )

    def _build_working_prompt(self, user_input: str | None) -> str:
        """Build the prompt for the working agent."""
        if self.iteration == 1:
            prompt = f"""# Task

{self.config.task}

# Instructions

Work on this task thoroughly. Make real progress - write code, create files, make changes.
When you reach a natural stopping point, summarize what you accomplished.

Do NOT ask for confirmation - make decisions and proceed autonomously.
Be thorough and continue until the work is done or you hit a blocking issue."""
        else:
            last = self.history[-1] if self.history else {}
            last_verdict = last.get("verdict", {})
            remaining = last_verdict.get("remaining_work", "Continue making progress")

            prompt = f"""# Continue Task

{self.config.task}

# Supervisor Feedback from Previous Iteration

{remaining}

# Instructions

Continue from where you left off. Address the feedback above.
Do NOT repeat work already done - build on your previous progress.
Make real, concrete progress toward completing the task."""

        if user_input:
            prompt += f"""

# User Guidance

The user has provided additional direction:

{user_input}

Incorporate this guidance as you continue."""

        return prompt

    def _build_supervisor_prompt(self, work_output: str) -> str:
        """Build the evaluation prompt for the supervisor."""
        return f"""# Task Completion Evaluation

You are evaluating whether a task has been completed.

## Original Task

{self.config.task}

## Work Output (Iteration {self.iteration})

{work_output}

## Evaluation Criteria

Rate as COMPLETE only if:
- The core objective has been achieved
- No critical steps are missing
- The work is at a reasonable stopping point

Rate as INCOMPLETE if:
- Core objectives not yet met
- Obvious important steps remain
- Work stopped prematurely
- Errors need fixing

## Required Response Format

Respond with ONLY this JSON (no other text):

{{
  "status": "COMPLETE" or "INCOMPLETE",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "remaining_work": "what still needs to be done if INCOMPLETE"
}}"""

    def _parse_verdict(self, response: str) -> dict[str, Any]:
        """Parse the supervisor's verdict from response."""
        try:
            # Try to extract JSON
            text = response.strip()
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()

            # Find JSON object
            if "{" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                text = text[start:end]

            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            # Fallback: infer from text
            upper = response.upper()
            if "COMPLETE" in upper and "INCOMPLETE" not in upper:
                return {"status": "COMPLETE", "confidence": 0.6, "reasoning": "Inferred"}
            return {"status": "INCOMPLETE", "confidence": 0.5, "remaining_work": "Could not parse"}

    def _check_input_file(self) -> str | None:
        """Check for and consume user input from file."""
        try:
            if self.config.input_file.exists():
                content = self.config.input_file.read_text().strip()
                if content:
                    # Clear the file after reading
                    self.config.input_file.write_text("")
                    return content
        except Exception as e:
            self._log(f"Error reading input file: {e}")
        return None

    async def _checkpoint_pause(self) -> None:
        """Pause for user checkpoint (placeholder for approval system integration)."""
        self._log(f"Checkpoint at iteration {self.iteration}")
        # In full integration, this would use coordinator.approval_system
        # For now, just log and continue
        pass

    def _determine_reason(self) -> str:
        """Determine the reason for loop termination."""
        if self._is_complete:
            return "Task completed successfully"
        if self.iteration >= self.config.max_iterations:
            return f"Maximum iterations ({self.config.max_iterations}) reached"
        return "Unknown"

    def _log(self, message: str) -> None:
        """Log progress (visible in Amplifier output)."""
        if self.config.verbose:
            print(f"[looper] {message}")


# Tool definition for Amplifier registration
TOOL_DEFINITION = {
    "name": "looper",
    "description": """Run a supervised work loop on a task until completion.

This tool keeps working on your task until a supervisor confirms it's done.
Use this when you want to ensure thorough completion of complex tasks.

The working agent will iterate, and a supervisor evaluates after each iteration.
The loop continues until the supervisor marks the task COMPLETE with sufficient confidence.

User can inject guidance by writing to: ~/.amplifier/looper-input.txt

Example:
    looper(task="Implement user authentication with JWT tokens", max_iterations=15)
""",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The task description for the working agent",
            },
            "max_iterations": {
                "type": "integer",
                "description": "Maximum work iterations (default: 10)",
                "default": 10,
            },
            "min_confidence": {
                "type": "number",
                "description": "Minimum supervisor confidence to mark complete (default: 0.8)",
                "default": 0.8,
            },
            "checkpoint_every": {
                "type": "integer",
                "description": "Pause for user confirmation every N iterations (optional)",
            },
        },
        "required": ["task"],
    },
    "execute": looper_execute,
}
