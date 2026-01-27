"""Worker process that claims and executes tasks."""

import json
import logging
import os
import re
import signal
import socket
import subprocess
import time
from pathlib import Path

from .database import TaskDatabase

logger = logging.getLogger(__name__)


class SwarmWorker:
    """Worker that processes tasks from the queue."""

    def __init__(
        self,
        db_path: Path,
        worker_id: str,
        project_root: Path,
        builder_agent: str,
        validator_agent: str,
        validation_enabled: bool = True,
        heartbeat_interval: int = 30,
        orchestrator_pid: int | None = None,
    ):
        self.db_path = db_path
        self.worker_id = worker_id
        self.project_root = project_root
        self.builder_agent = builder_agent
        self.validator_agent = validator_agent
        self.validation_enabled = validation_enabled
        self.heartbeat_interval = heartbeat_interval
        self.orchestrator_pid = orchestrator_pid

        self.db = TaskDatabase(db_path)
        self.shutdown_requested = False
        self.current_task_id: str | None = None
        self.last_heartbeat = 0.0

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Worker {self.worker_id} received signal {signum}, shutting down gracefully")
        self.shutdown_requested = True

    def start(self):
        """Start the worker loop."""
        hostname = socket.gethostname()
        pid = os.getpid()

        logger.info(f"Worker {self.worker_id} starting (PID: {pid}, host: {hostname})")

        # Register worker
        self.db.register_worker(self.worker_id, pid, hostname, self.orchestrator_pid)

        try:
            self._work_loop()
        except Exception as e:
            logger.error(f"Worker {self.worker_id} crashed: {e}", exc_info=True)
            self.db.set_worker_status(self.worker_id, "crashed")
            raise
        finally:
            logger.info(f"Worker {self.worker_id} stopped")
            self.db.set_worker_status(self.worker_id, "stopped")

    def _work_loop(self):
        """Main work loop: claim task -> process -> repeat."""
        while not self.shutdown_requested:
            # Send heartbeat if needed
            self._maybe_heartbeat()

            # Try to claim a task
            task = self.db.claim_task(self.worker_id)

            if not task:
                # No tasks available, sleep and retry
                logger.debug(f"Worker {self.worker_id}: No tasks available, sleeping")
                time.sleep(5)
                continue

            # Process the task
            self.current_task_id = task["id"]
            logger.info(f"Worker {self.worker_id} processing task {task['id']}: {task['name']}")

            try:
                self._process_task(task)
            except Exception as e:
                logger.error(f"Worker {self.worker_id} failed to process task {task['id']}: {e}", exc_info=True)
                self.db.fail_task(
                    task["id"],
                    self.worker_id,
                    f"Worker exception: {str(e)}",
                )
                self.db.update_worker_stats(self.worker_id, failed=1)
            finally:
                self.current_task_id = None
                self._maybe_heartbeat()

        logger.info(f"Worker {self.worker_id} shutting down (shutdown requested)")

    def _process_task(self, task: dict):
        """Process a single task (builder + validator)."""
        # Mark task as in-progress
        self.db.start_task(task["id"], self.worker_id)
        self._maybe_heartbeat()

        # Step 1: Run builder session
        logger.info(f"Task {task['id']}: Spawning builder session")
        builder_result = self._run_builder_session(task)

        if builder_result["status"] == "failed":
            logger.warning(f"Task {task['id']}: Builder failed: {builder_result.get('blockers', 'Unknown error')}")
            self.db.fail_task(
                task["id"],
                self.worker_id,
                builder_result.get("blockers", "Builder failed"),
                builder_result=builder_result,
            )
            self.db.update_worker_stats(self.worker_id, failed=1)
            return

        # Step 2: Run validator session (if enabled and builder succeeded)
        validator_result = None
        if self.validation_enabled:
            logger.info(f"Task {task['id']}: Spawning validator session")
            self._maybe_heartbeat()

            validator_result = self._run_validator_session(task, builder_result)

            if validator_result["verdict"] == "FAIL":
                logger.warning(
                    f"Task {task['id']}: Validation failed: {validator_result.get('summary', 'Unknown issues')}"
                )
                self.db.fail_task(
                    task["id"],
                    self.worker_id,
                    f"Validation failed: {validator_result.get('summary', 'Unknown issues')}",
                    builder_result=builder_result,
                    validator_result=validator_result,
                )
                self.db.update_worker_stats(self.worker_id, failed=1)
                return

        # Success!
        logger.info(f"Task {task['id']}: Completed successfully")
        self.db.complete_task(task["id"], self.worker_id, builder_result, validator_result)
        self.db.update_worker_stats(self.worker_id, completed=1)

    def _run_builder_session(self, task: dict) -> dict:
        """Spawn a builder agent session via Amplifier task tool."""
        prompt = self._build_builder_prompt(task)

        try:
            # Use amplifier task tool to spawn the builder agent
            result = self._spawn_agent_session(
                agent=self.builder_agent,  # Pass agent name
                prompt=prompt,
                timeout=3600,  # 1 hour
            )

            # Store builder session_id
            if result.get("session_id"):
                self.db.update_task_sessions(
                    task_id=task["id"],
                    builder_session_id=result["session_id"],
                    validator_session_id=None,
                )
                logger.info(f"Stored builder session_id for task {task['id']}: {result['session_id']}")

            # Try to parse JSON from output
            try:
                return json.loads(result["output"])
            except json.JSONDecodeError:
                # If not valid JSON, return as text result
                logger.warning(f"Task {task['id']}: Builder did not return valid JSON")
                return {
                    "status": "failed" if result["returncode"] != 0 else "success",
                    "files_created": [],
                    "files_modified": [],
                    "tests_written": [],
                    "tests_passed": result["returncode"] == 0,
                    "implementation_notes": result["output"][:500],
                    "blockers": result["stderr"] if result["returncode"] != 0 else "",
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "files_created": [],
                "files_modified": [],
                "tests_written": [],
                "tests_passed": False,
                "implementation_notes": "",
                "blockers": "Builder session timed out (1 hour limit)",
            }
        except Exception as e:
            return {
                "status": "failed",
                "files_created": [],
                "files_modified": [],
                "tests_written": [],
                "tests_passed": False,
                "implementation_notes": "",
                "blockers": f"Builder session error: {str(e)}",
            }

    def _run_validator_session(self, task: dict, builder_result: dict) -> dict:
        """Spawn a validator agent session via Amplifier task tool."""
        prompt = self._build_validator_prompt(task, builder_result)

        try:
            result = self._spawn_agent_session(
                agent=self.validator_agent,  # Pass agent name
                prompt=prompt,
                timeout=1800,  # 30 minutes
            )

            # Store builder session_id
            if result.get("session_id"):
                self.db.update_task_sessions(
                    task_id=task["id"],
                    builder_session_id=result["session_id"],
                    validator_session_id=None,
                )
                logger.info(f"Stored builder session_id for task {task['id']}: {result['session_id']}")

            # Store validator session_id
            if result.get("session_id"):
                self.db.update_task_sessions(
                    task_id=task["id"],
                    builder_session_id=None,  # Keep existing
                    validator_session_id=result["session_id"],
                )
                logger.info(f"Stored validator session_id for task {task['id']}: {result['session_id']}")

            # Try to parse JSON from output
            try:
                return json.loads(result["output"])
            except json.JSONDecodeError:
                logger.warning(f"Task {task['id']}: Validator did not return valid JSON")
                return {
                    "verdict": "FAIL" if result["returncode"] != 0 else "PASS",
                    "confidence": 50,
                    "critical_issues": [],
                    "test_quality_score": 0,
                    "recommendations": "",
                    "summary": result["output"][:500],
                }

        except subprocess.TimeoutExpired:
            return {
                "verdict": "FAIL",
                "confidence": 0,
                "critical_issues": [{"file": "timeout", "issue": "Validator timed out", "severity": "critical"}],
                "test_quality_score": 0,
                "recommendations": "",
                "summary": "Validator session timed out (30 minute limit)",
            }
        except Exception as e:
            return {
                "verdict": "FAIL",
                "confidence": 0,
                "critical_issues": [{"file": "error", "issue": str(e), "severity": "critical"}],
                "test_quality_score": 0,
                "recommendations": "",
                "summary": f"Validator session error: {str(e)}",
            }

    def _spawn_agent_session(self, agent: str, prompt: str, timeout: int) -> dict:
        """Spawn an Amplifier agent session using the task tool.

        Args:
            agent: Agent name (e.g., "foundation:modular-builder")
            prompt: Task instruction for the agent
            timeout: Timeout in seconds

        Returns dict with: output (stdout), stderr, returncode, session_id
        """
        try:
            # Use amplifier tool invoke task to spawn agent
            cmd = [
                "amplifier",
                "tool",
                "invoke",
                "task",
                f"agent={agent}",
                f"instruction={prompt}",
            ]

            logger.debug(f"Spawning Amplifier task (agent: {agent}, prompt length: {len(prompt)} chars)")

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy(),
            )

            # Parse session_id from JSON response
            session_id = None
            try:
                # The task tool returns JSON with session_id
                output_data = json.loads(result.stdout)
                session_id = output_data.get("session_id")
                logger.info(f"Captured session_id: {session_id}")
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.warning(f"Could not parse session_id from output: {e}")
                # Try to extract from text output as fallback
                match = re.search(r'session[_-]id["\s:]+([a-f0-9-]+)', result.stdout, re.IGNORECASE)
                if match:
                    session_id = match.group(1)
                    logger.info(f"Extracted session_id from text: {session_id}")

            return {
                "output": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "session_id": session_id,
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Amplifier task timed out after {timeout}s")
            return {
                "output": "",
                "stderr": f"Timeout after {timeout}s",
                "returncode": 124,
                "session_id": None,
            }
        except Exception as e:
            logger.error(f"Failed to spawn task: {e}")
            return {
                "output": "",
                "stderr": str(e),
                "returncode": 1,
                "session_id": None,
            }

    def _build_builder_prompt(self, task: dict) -> str:
        """Build the prompt for the builder agent."""
        files = json.loads(task["files"]) if task["files"] else []
        files_section = "\n".join(f"  - {f}" for f in files) if files else "  (Not specified)"

        return f"""## Task: Implement {task["id"]} - {task["name"]}

**Working Directory:** {self.project_root}
**Task ID:** {task["id"]}
**Phase:** {task["phase"]}
**Estimated Hours:** {task["estimated_hours"]}

**Description:**
{task["description"]}

**Acceptance Criteria:**
{task["acceptance_criteria"]}

**Expected Files:**
{files_section}

**Your Mission:**
1. Implement the task according to the specification
2. Write comprehensive tests (NOT stubs)
3. Run tests locally and verify they pass
4. Ensure code quality (types, patterns, error handling)

**Output Required:**
Return JSON with:
```json
{{
  "status": "success" | "failed",
  "files_created": ["path/to/file"],
  "files_modified": ["path/to/file"],
  "tests_written": ["path/to/test"],
  "tests_passed": true/false,
  "implementation_notes": "summary of what was implemented",
  "blockers": "any issues encountered (empty if none)"
}}
```
"""

    def _build_validator_prompt(self, task: dict, builder_result: dict) -> str:
        """Build the prompt for the validator agent."""
        return f"""## Task: ANTAGONISTIC Validation of {task["id"]}

**Your Role:** Senior engineer reviewing code by a junior developer.
Your job is to find problems, not to approve.

**Working Directory:** {self.project_root}
**Task ID:** {task["id"]}

**Builder's Implementation:**
- Files created: {", ".join(builder_result.get("files_created", []))}
- Files modified: {", ".join(builder_result.get("files_modified", []))}
- Tests written: {", ".join(builder_result.get("tests_written", []))}
- Tests passed: {builder_result.get("tests_passed", False)}

**What to Validate:**
1. **Implementation Quality**: Types, patterns, edge cases
2. **Test Quality**: REAL tests (not stubs), meaningful assertions
3. **Design Adherence**: Does it meet the acceptance criteria?
4. **Integration**: Does it work with existing code?

**Task Description:**
{task["description"]}

**Acceptance Criteria:**
{task["acceptance_criteria"]}

**Output Required:**
Return JSON with:
```json
{{
  "verdict": "PASS" | "FAIL",
  "confidence": 0-100,
  "critical_issues": [
    {{
      "file": "path/to/file",
      "issue": "description",
      "severity": "critical | high | medium | low"
    }}
  ],
  "test_quality_score": 0-100,
  "recommendations": "improvements for next iteration",
  "summary": "2-3 sentence assessment"
}}
```

**Be honest.** If tests are stubs, say so. If code is incomplete, say so.
"""

    def _maybe_heartbeat(self):
        """Send heartbeat if interval has elapsed."""
        now = time.time()
        if now - self.last_heartbeat >= self.heartbeat_interval:
            self.db.heartbeat(self.worker_id, self.current_task_id)
            self.last_heartbeat = now


def main():
    """Entry point for running a worker directly."""
    import argparse

    parser = argparse.ArgumentParser(description="Amplifier Swarm Worker")
    parser.add_argument("--db", type=Path, required=True, help="Path to SQLite database")
    parser.add_argument("--worker-id", required=True, help="Worker ID")
    parser.add_argument("--project-root", type=Path, required=True, help="Project root directory")
    parser.add_argument("--builder-agent", required=True, help="Builder agent name")
    parser.add_argument("--validator-agent", required=True, help="Validator agent name")
    parser.add_argument(
        "--orchestrator-pid", type=int, default=None, help="Orchestrator process ID (for emergency stop)"
    )
    parser.add_argument("--no-validation", action="store_true", help="Disable validation")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    worker = SwarmWorker(
        db_path=args.db,
        worker_id=args.worker_id,
        project_root=args.project_root,
        builder_agent=args.builder_agent,  # Pass agent name
        validator_agent=args.validator_agent,  # Pass agent name
        validation_enabled=not args.no_validation,
        orchestrator_pid=args.orchestrator_pid,
    )

    worker.start()


if __name__ == "__main__":
    main()
