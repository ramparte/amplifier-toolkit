"""SQLite database operations for task queue management."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskDatabase:
    """SQLite database for managing task queue with atomic operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """Create tables if they don't exist."""
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phase TEXT,
                    task_type TEXT,  -- implementation, test, etc.
                    status TEXT NOT NULL DEFAULT 'not_started',
                    priority INTEGER DEFAULT 0,
                    estimated_hours REAL,
                    description TEXT,
                    acceptance_criteria TEXT,
                    files TEXT,  -- JSON array
                    design_docs TEXT,  -- JSON array

                    -- Worker tracking
                    worker_id TEXT,
                    claimed_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,

                    -- Session tracking
                    builder_session_id TEXT,
                    validator_session_id TEXT,

                    -- Retry handling
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 2,
                    last_error TEXT,

                    -- Dependencies
                    dependencies TEXT,  -- Comma-separated task IDs that must complete before this task

                    -- Results (JSON)
                    builder_result TEXT,
                    validator_result TEXT,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    pid INTEGER NOT NULL,
                    hostname TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'active',
                    tasks_completed INTEGER DEFAULT 0,
                    tasks_failed INTEGER DEFAULT 0,
                    current_task_id TEXT,
                    orchestrator_pid INTEGER,

                    FOREIGN KEY(current_task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    worker_id TEXT,
                    event_type TEXT NOT NULL,
                    message TEXT,
                    data TEXT,  -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_worker ON tasks(worker_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC, created_at ASC);
                CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status);
                CREATE INDEX IF NOT EXISTS idx_log_task ON execution_log(task_id);
                CREATE INDEX IF NOT EXISTS idx_log_timestamp ON execution_log(timestamp DESC);
                """
            )

    @contextmanager
    def connection(self):
        """Context manager for database connections with automatic commit."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level="IMMEDIATE",  # Immediate locking for writes
        )
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Task Operations
    # -------------------------------------------------------------------------

    def claim_task(self, worker_id: str) -> dict | None:
        """Claim next available task with no incomplete dependencies.

        Uses BEGIN IMMEDIATE to prevent race conditions under high load.

        Returns:
            Task dict if claimed, None if no tasks available
        """
        with self.connection() as conn:
            # Start exclusive transaction immediately
            conn.execute("BEGIN IMMEDIATE")

            try:
                # Find next available task
                cursor = conn.execute(
                    """
                    SELECT * FROM tasks
                    WHERE status = 'not_started'
                      AND retry_count < max_retries
                      AND (
                          -- No dependencies
                          dependencies IS NULL OR dependencies = ''
                          -- OR all dependencies are completed
                          OR NOT EXISTS (
                              SELECT 1 FROM tasks t2
                              WHERE (',' || tasks.dependencies || ',') LIKE ('%,' || t2.id || ',%')
                                AND t2.status != 'completed'
                          )
                      )
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    """,
                )

                task = cursor.fetchone()
                if not task:
                    conn.rollback()
                    return None

                # Atomically claim it
                cursor = conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'claimed',
                        worker_id = ?,
                        claimed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'not_started'
                    RETURNING *
                    """,
                    (worker_id, task["id"]),
                )

                claimed_task = cursor.fetchone()

                if claimed_task:
                    conn.commit()
                    self.log_event(
                        conn,
                        task_id=claimed_task["id"],
                        worker_id=worker_id,
                        event_type="claimed",
                        message=f"Task claimed by worker {worker_id}",
                    )
                    logger.info(f"Worker {worker_id} claimed task {claimed_task['id']}")
                    return dict(claimed_task)
                else:
                    # Task was claimed by another worker between SELECT and UPDATE
                    conn.rollback()
                    logger.debug(f"Task {task['id']} already claimed by another worker")
                    return None

            except Exception as e:
                conn.rollback()
                logger.error(f"Error claiming task: {e}")
                raise

    def start_task(self, task_id: str, worker_id: str):
        """Mark task as in_progress."""
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'in_progress',
                    started_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND worker_id = ?
                """,
                (task_id, worker_id),
            )
            self.log_event(
                conn,
                task_id=task_id,
                worker_id=worker_id,
                event_type="started",
                message="Task execution started",
            )

    def complete_task(
        self,
        task_id: str,
        worker_id: str,
        builder_result: dict,
        validator_result: dict | None = None,
    ):
        """Mark task as completed with results."""
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    builder_result = ?,
                    validator_result = ?
                WHERE id = ? AND worker_id = ?
                """,
                (
                    json.dumps(builder_result),
                    json.dumps(validator_result) if validator_result else None,
                    task_id,
                    worker_id,
                ),
            )
            self.log_event(
                conn,
                task_id=task_id,
                worker_id=worker_id,
                event_type="completed",
                message="Task completed successfully",
                data={"builder_result": builder_result, "validator_result": validator_result},
            )

    def fail_task(
        self,
        task_id: str,
        worker_id: str,
        error: str,
        builder_result: dict | None = None,
        validator_result: dict | None = None,
    ):
        """Mark task as failed."""
        with self.connection() as conn:
            # Check if we should retry or mark as failed
            cursor = conn.execute(
                "SELECT retry_count, max_retries FROM tasks WHERE id = ?",
                (task_id,),
            )
            row = cursor.fetchone()

            if row and row["retry_count"] < row["max_retries"]:
                # Retry available
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'not_started',
                        worker_id = NULL,
                        claimed_at = NULL,
                        started_at = NULL,
                        retry_count = retry_count + 1,
                        last_error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (error, task_id),
                )
                self.log_event(
                    conn,
                    task_id=task_id,
                    worker_id=worker_id,
                    event_type="retry",
                    message=f"Task failed, will retry (attempt {row['retry_count'] + 1}/{row['max_retries']})",
                    data={"error": error},
                )
            else:
                # Max retries reached, mark as failed
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'failed',
                        completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP,
                        last_error = ?,
                        builder_result = ?,
                        validator_result = ?
                    WHERE id = ?
                    """,
                    (
                        error,
                        json.dumps(builder_result) if builder_result else None,
                        json.dumps(validator_result) if validator_result else None,
                        task_id,
                    ),
                )
                self.log_event(
                    conn,
                    task_id=task_id,
                    worker_id=worker_id,
                    event_type="failed",
                    message=f"Task failed permanently: {error}",
                    data={"error": error},
                )

    def update_task_sessions(
        self,
        task_id: str,
        builder_session_id: str | None = None,
        validator_session_id: str | None = None,
    ):
        """Update session IDs for task."""
        with self.connection() as conn:
            updates = []
            params = []

            if builder_session_id:
                updates.append("builder_session_id = ?")
                params.append(builder_session_id)
            if validator_session_id:
                updates.append("validator_session_id = ?")
                params.append(validator_session_id)

            if updates:
                params.append(task_id)
                conn.execute(
                    f"UPDATE tasks SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    params,
                )

    def kill_task_sessions(self, task_id: str) -> dict:
        """Kill Amplifier sessions associated with a task.

        Returns:
            dict with builder_killed, validator_killed status
        """
        import subprocess

        task = self.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return {"builder_killed": False, "validator_killed": False}

        result = {"builder_killed": False, "validator_killed": False}

        # Kill builder session
        if task.get("builder_session_id"):
            try:
                # Use amplifier CLI to kill session
                subprocess.run(
                    ["amplifier", "session", "kill", task["builder_session_id"]],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                result["builder_killed"] = True
                logger.info(f"Killed builder session {task['builder_session_id']}")
            except Exception as e:
                logger.error(f"Failed to kill builder session: {e}")

        # Kill validator session
        if task.get("validator_session_id"):
            try:
                subprocess.run(
                    ["amplifier", "session", "kill", task["validator_session_id"]],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                result["validator_killed"] = True
                logger.info(f"Killed validator session {task['validator_session_id']}")
            except Exception as e:
                logger.error(f"Failed to kill validator session: {e}")

        return result

    def add_task_dependency(self, task_id: str, depends_on_task_id: str):
        """Mark that task_id depends on another task completing first.

        Args:
            task_id: The task that has a dependency
            depends_on_task_id: The task that must complete first
        """
        with self.connection() as conn:
            # Get current dependencies
            cursor = conn.execute("SELECT dependencies FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Task {task_id} not found, cannot add dependency")
                return

            deps = row["dependencies"] if row["dependencies"] else ""
            deps_list = [d.strip() for d in deps.split(",") if d.strip()]

            # Add new dependency if not already present
            if depends_on_task_id not in deps_list:
                deps_list.append(depends_on_task_id)

            new_deps = ",".join(deps_list)

            conn.execute("UPDATE tasks SET dependencies = ? WHERE id = ?", (new_deps, task_id))
            conn.commit()
            logger.info(f"Task {task_id} now depends on {depends_on_task_id}")

    def get_blocked_tasks(self) -> list[dict]:
        """Get tasks that are blocked by incomplete dependencies.

        Returns:
            List of tasks with their blocking dependencies
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    t1.id,
                    t1.name,
                    t1.dependencies,
                    t1.status,
                    GROUP_CONCAT(t2.id || ':' || t2.status) as blocking_tasks
                FROM tasks t1
                JOIN tasks t2 ON (',' || t1.dependencies || ',') LIKE ('%,' || t2.id || ',%')
                WHERE t1.status = 'not_started'
                  AND t1.dependencies IS NOT NULL
                  AND t1.dependencies != ''
                  AND t2.status != 'completed'
                GROUP BY t1.id
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_task(self, task_id: str) -> dict | None:
        """Get task by ID."""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_tasks_summary(self) -> dict:
        """Get summary of task statuses."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    status,
                    COUNT(*) as count,
                    SUM(estimated_hours) as total_hours
                FROM tasks
                GROUP BY status
                """
            )
            summary = {row["status"]: {"count": row["count"], "hours": row["total_hours"] or 0} for row in cursor}

            # Get total
            cursor = conn.execute("SELECT COUNT(*) as total, SUM(estimated_hours) as total_hours FROM tasks")
            row = cursor.fetchone()
            summary["total"] = {"count": row["total"], "hours": row["total_hours"] or 0}

            return summary

    def get_all_tasks(self, status: str | None = None) -> list[dict]:
        """Get all tasks, optionally filtered by status."""
        with self.connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, created_at ASC",
                    (status,),
                )
            else:
                cursor = conn.execute("SELECT * FROM tasks ORDER BY priority DESC, created_at ASC")
            return [dict(row) for row in cursor]

    # -------------------------------------------------------------------------
    # Worker Operations
    # -------------------------------------------------------------------------

    def register_worker(self, worker_id: str, pid: int, hostname: str, orchestrator_pid: int | None = None):
        """Register a new worker.

        Args:
            worker_id: Unique worker identifier
            pid: Worker process ID
            hostname: Machine hostname
            orchestrator_pid: PID of orchestrator process (for emergency stop)
        """
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO workers (worker_id, pid, hostname, orchestrator_pid, status)
                VALUES (?, ?, ?, ?, 'active')
                ON CONFLICT(worker_id) DO UPDATE SET
                    pid = excluded.pid,
                    hostname = excluded.hostname,
                    orchestrator_pid = excluded.orchestrator_pid,
                    started_at = CURRENT_TIMESTAMP,
                    last_heartbeat = CURRENT_TIMESTAMP,
                    status = 'active'
                """,
                (worker_id, pid, hostname, orchestrator_pid),
            )
            logger.info(f"Registered worker {worker_id} (PID {pid}, orchestrator PID {orchestrator_pid})")

    def heartbeat(self, worker_id: str, current_task_id: str | None = None):
        """Update worker heartbeat."""
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE workers
                SET last_heartbeat = CURRENT_TIMESTAMP,
                    current_task_id = ?
                WHERE worker_id = ?
                """,
                (current_task_id, worker_id),
            )

    def update_worker_stats(self, worker_id: str, completed: int = 0, failed: int = 0):
        """Update worker completion stats."""
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE workers
                SET tasks_completed = tasks_completed + ?,
                    tasks_failed = tasks_failed + ?
                WHERE worker_id = ?
                """,
                (completed, failed, worker_id),
            )

    def set_worker_status(self, worker_id: str, status: str):
        """Set worker status (active, stopping, stopped, crashed)."""
        with self.connection() as conn:
            conn.execute(
                "UPDATE workers SET status = ?, current_task_id = NULL WHERE worker_id = ?",
                (status, worker_id),
            )

    def get_worker(self, worker_id: str) -> dict | None:
        """Get worker by ID."""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM workers WHERE worker_id = ?", (worker_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_workers(self) -> list[dict]:
        """Get all workers."""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM workers ORDER BY started_at DESC")
            return [dict(row) for row in cursor]

    def find_dead_workers(self, timeout_seconds: int = 90) -> list[dict]:
        """Find workers that haven't sent heartbeat recently."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM workers
                WHERE status = 'active'
                  AND (julianday('now') - julianday(last_heartbeat)) * 86400 > ?
                """,
                (timeout_seconds,),
            )
            return [dict(row) for row in cursor]

    # -------------------------------------------------------------------------
    # Orphan Recovery
    # -------------------------------------------------------------------------

    def find_orphaned_tasks(self, timeout_minutes: int = 30) -> list[dict]:
        """Find tasks claimed but not progressing (worker crashed/stuck)."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM tasks
                WHERE status IN ('claimed', 'in_progress')
                  AND (julianday('now') - julianday(claimed_at)) * 1440 > ?
                """,
                (timeout_minutes,),
            )
            return [dict(row) for row in cursor]

    def reset_orphaned_tasks(self, timeout_minutes: int = 30):
        """Reset orphaned tasks to not_started (if retries available)."""
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'not_started',
                    worker_id = NULL,
                    claimed_at = NULL,
                    started_at = NULL,
                    retry_count = retry_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE status IN ('claimed', 'in_progress')
                  AND (julianday('now') - julianday(claimed_at)) * 1440 > ?
                  AND retry_count < max_retries
                """,
                (timeout_minutes,),
            )

            # Mark as failed if max retries reached
            conn.execute(
                """
                UPDATE tasks
                SET status = 'failed',
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    last_error = 'Task timed out (worker lost)'
                WHERE status IN ('claimed', 'in_progress')
                  AND (julianday('now') - julianday(claimed_at)) * 1440 > ?
                  AND retry_count >= max_retries
                """,
                (timeout_minutes,),
            )

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    def log_event(
        self,
        conn: sqlite3.Connection,
        task_id: str,
        worker_id: str | None,
        event_type: str,
        message: str,
        data: dict | None = None,
    ):
        """Log an event (called within existing transaction)."""
        conn.execute(
            """
            INSERT INTO execution_log (task_id, worker_id, event_type, message, data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, worker_id, event_type, message, json.dumps(data) if data else None),
        )

    def get_task_log(self, task_id: str) -> list[dict]:
        """Get execution log for a task."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM execution_log
                WHERE task_id = ?
                ORDER BY timestamp DESC
                """,
                (task_id,),
            )
            return [dict(row) for row in cursor]

    def get_recent_log(self, limit: int = 100) -> list[dict]:
        """Get recent log entries."""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM execution_log ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor]
