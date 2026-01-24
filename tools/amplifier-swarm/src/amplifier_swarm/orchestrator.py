"""Orchestrator that spawns and manages N worker processes."""

import logging
import multiprocessing as mp
import os
import signal
import socket
import sys
import time
from pathlib import Path
from typing import Optional

import psutil

from .database import TaskDatabase
from .worker import SwarmWorker

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """Manages a pool of worker processes."""

    def __init__(
        self,
        db_path: Path,
        project_root: Path,
        builder_agent: str,
        validator_agent: str,
        num_workers: int = 1,
        validation_enabled: bool = True,
        graceful_shutdown_timeout: int = 300,  # 5 minutes
    ):
        self.db_path = db_path
        self.project_root = project_root
        self.builder_agent = builder_agent
        self.validator_agent = validator_agent
        self.num_workers = num_workers
        self.validation_enabled = validation_enabled
        self.graceful_shutdown_timeout = graceful_shutdown_timeout

        self.db = TaskDatabase(db_path)
        self.workers: dict[str, mp.Process] = {}
        self.shutdown_requested = False
        self.hard_stop_requested = False

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._graceful_shutdown_handler)
        signal.signal(signal.SIGINT, self._graceful_shutdown_handler)
        signal.signal(signal.SIGUSR1, self._hard_stop_handler)  # Hard stop signal

    def _graceful_shutdown_handler(self, signum, frame):
        """Handle graceful shutdown (SIGTERM, SIGINT)."""
        if self.shutdown_requested:
            logger.warning("Already shutting down, send SIGUSR1 for hard stop")
            return

        logger.info(f"Orchestrator received signal {signum}, initiating graceful shutdown")
        self.shutdown_requested = True

    def _hard_stop_handler(self, signum, frame):
        """Handle hard stop (SIGUSR1) - immediate termination."""
        logger.warning("Hard stop requested, terminating all workers immediately")
        self.hard_stop_requested = True
        self.shutdown_requested = True

    def start(self):
        """Start the orchestrator and worker pool."""
        logger.info(
            f"Orchestrator starting with {self.num_workers} worker(s) (serial mode: {self.num_workers == 1})"
        )
        logger.info(f"Project: {self.project_root}")
        logger.info(f"Builder: {self.builder_agent}, Validator: {self.validator_agent}")
        logger.info(f"Validation: {'enabled' if self.validation_enabled else 'disabled'}")

        try:
            # Spawn workers
            self._spawn_workers()

            # Monitor loop
            self._monitor_loop()

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt, shutting down")
            self.shutdown_requested = True
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            self.shutdown_requested = True
            raise
        finally:
            self._shutdown()

    def _spawn_workers(self):
        """Spawn the worker processes."""
        for i in range(self.num_workers):
            worker_id = f"worker-{i+1}-{int(time.time())}"
            self._spawn_worker(worker_id)

    def _spawn_worker(self, worker_id: str):
        """Spawn a single worker process."""
        logger.info(f"Spawning worker: {worker_id}")

        # Use multiprocessing for proper isolation
        process = mp.Process(
            target=_worker_entry_point,
            args=(
                self.db_path,
                worker_id,
                self.project_root,
                self.builder_agent,
                self.validator_agent,
                self.validation_enabled,
            ),
            name=worker_id,
        )
        process.start()

        self.workers[worker_id] = process
        logger.info(f"Worker {worker_id} spawned with PID {process.pid}")

    def _monitor_loop(self):
        """Monitor workers and handle failures/orphans."""
        last_orphan_check = time.time()
        last_dead_worker_check = time.time()

        while not self.shutdown_requested:
            time.sleep(10)

            # Check for dead workers
            now = time.time()
            if now - last_dead_worker_check >= 60:
                self._check_dead_workers()
                last_dead_worker_check = now

            # Check for crashed workers and restart them
            self._check_crashed_workers()

            # Check for orphaned tasks
            if now - last_orphan_check >= 120:  # Every 2 minutes
                self._check_orphaned_tasks()
                last_orphan_check = now

            # Check if all workers are done and no tasks remain
            if self._all_workers_idle() and self._no_tasks_remaining():
                logger.info("All tasks completed, shutting down")
                self.shutdown_requested = True

    def _check_dead_workers(self):
        """Check database for workers that haven't sent heartbeat."""
        dead_workers = self.db.find_dead_workers(timeout_seconds=90)

        for worker_data in dead_workers:
            worker_id = worker_data["worker_id"]
            logger.warning(f"Worker {worker_id} appears dead (no heartbeat), marking as crashed")
            self.db.set_worker_status(worker_id, "crashed")

    def _check_crashed_workers(self):
        """Check for crashed worker processes and optionally restart."""
        for worker_id, process in list(self.workers.items()):
            if not process.is_alive():
                exitcode = process.exitcode
                logger.warning(f"Worker {worker_id} crashed (exit code: {exitcode})")

                # Mark as crashed in DB
                self.db.set_worker_status(worker_id, "crashed")

                # Remove from active workers
                del self.workers[worker_id]

                # Optionally restart if not shutting down
                if not self.shutdown_requested and self._should_restart_worker():
                    logger.info(f"Restarting crashed worker {worker_id}")
                    new_worker_id = f"{worker_id}-restarted"
                    self._spawn_worker(new_worker_id)

    def _should_restart_worker(self) -> bool:
        """Determine if we should restart a crashed worker."""
        # Only restart if we still have tasks to process
        summary = self.db.get_tasks_summary()
        not_started = summary.get("not_started", {}).get("count", 0)
        return not_started > 0

    def _check_orphaned_tasks(self):
        """Check for and reset orphaned tasks."""
        orphans = self.db.find_orphaned_tasks(timeout_minutes=30)

        if orphans:
            logger.warning(f"Found {len(orphans)} orphaned tasks, resetting them")
            self.db.reset_orphaned_tasks(timeout_minutes=30)

    def _all_workers_idle(self) -> bool:
        """Check if all workers are idle (no current task)."""
        workers = self.db.get_all_workers()
        active_workers = [w for w in workers if w["status"] == "active"]

        for worker in active_workers:
            if worker["current_task_id"]:
                return False

        return True

    def _no_tasks_remaining(self) -> bool:
        """Check if there are any tasks left to process."""
        summary = self.db.get_tasks_summary()
        not_started = summary.get("not_started", {}).get("count", 0)
        claimed = summary.get("claimed", {}).get("count", 0)
        in_progress = summary.get("in_progress", {}).get("count", 0)

        return (not_started + claimed + in_progress) == 0

    def _shutdown(self):
        """Shutdown all workers."""
        if not self.workers:
            logger.info("No workers to shut down")
            return

        if self.hard_stop_requested:
            logger.warning("Hard stop: Terminating all workers immediately")
            self._hard_stop()
        else:
            logger.info("Graceful shutdown: Waiting for workers to finish current tasks")
            self._graceful_shutdown()

    def _graceful_shutdown(self):
        """Gracefully shut down workers (let them finish current task)."""
        logger.info(f"Sending SIGTERM to {len(self.workers)} workers")

        # Send SIGTERM to all workers
        for worker_id, process in self.workers.items():
            if process.is_alive():
                logger.debug(f"Sending SIGTERM to {worker_id} (PID {process.pid})")
                try:
                    os.kill(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    logger.warning(f"Worker {worker_id} already terminated")

        # Wait for workers with timeout
        start_time = time.time()
        while self.workers and (time.time() - start_time) < self.graceful_shutdown_timeout:
            for worker_id, process in list(self.workers.items()):
                if not process.is_alive():
                    logger.info(f"Worker {worker_id} terminated gracefully")
                    del self.workers[worker_id]

            if self.workers:
                time.sleep(2)

        # Force kill any remaining workers
        if self.workers:
            logger.warning(
                f"Graceful shutdown timeout ({self.graceful_shutdown_timeout}s), "
                f"force killing {len(self.workers)} remaining workers"
            )
            self._hard_stop()

    def _hard_stop(self):
        """Immediately terminate all workers (SIGKILL)."""
        for worker_id, process in list(self.workers.items()):
            if process.is_alive():
                logger.warning(f"Force killing {worker_id} (PID {process.pid})")
                try:
                    process.kill()  # SIGKILL
                    process.join(timeout=5)
                except Exception as e:
                    logger.error(f"Error killing {worker_id}: {e}")

            del self.workers[worker_id]

        logger.info("All workers terminated")

    def get_status(self) -> dict:
        """Get current orchestrator status."""
        return {
            "num_workers": self.num_workers,
            "active_workers": len(self.workers),
            "workers": [
                {
                    "worker_id": worker_id,
                    "pid": process.pid,
                    "alive": process.is_alive(),
                }
                for worker_id, process in self.workers.items()
            ],
            "task_summary": self.db.get_tasks_summary(),
            "shutdown_requested": self.shutdown_requested,
        }


def _worker_entry_point(
    db_path: Path,
    worker_id: str,
    project_root: Path,
    builder_agent: str,
    validator_agent: str,
    validation_enabled: bool,
):
    """Entry point for worker process (called via multiprocessing)."""
    # Set up logging for worker process
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [{worker_id}] [%(levelname)s] %(message)s",
    )

    worker = SwarmWorker(
        db_path=db_path,
        worker_id=worker_id,
        project_root=project_root,
        builder_agent=builder_agent,
        validator_agent=validator_agent,
        validation_enabled=validation_enabled,
    )

    try:
        worker.start()
    except Exception as e:
        logger.error(f"Worker {worker_id} crashed: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Entry point for running orchestrator directly."""
    import argparse

    parser = argparse.ArgumentParser(description="Amplifier Swarm Orchestrator")
    parser.add_argument("--db", type=Path, required=True, help="Path to SQLite database")
    parser.add_argument("--project-root", type=Path, required=True, help="Project root directory")
    parser.add_argument("--builder-agent", required=True, help="Builder agent name")
    parser.add_argument("--validator-agent", required=True, help="Validator agent name")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers (default: 1 for serial)")
    parser.add_argument("--no-validation", action="store_true", help="Disable validation")
    parser.add_argument("--graceful-timeout", type=int, default=300, help="Graceful shutdown timeout (seconds)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [ORCHESTRATOR] [%(levelname)s] %(message)s",
    )

    orchestrator = SwarmOrchestrator(
        db_path=args.db,
        project_root=args.project_root,
        builder_agent=args.builder_agent,
        validator_agent=args.validator_agent,
        num_workers=args.workers,
        validation_enabled=not args.no_validation,
        graceful_shutdown_timeout=args.graceful_timeout,
    )

    orchestrator.start()


if __name__ == "__main__":
    main()
