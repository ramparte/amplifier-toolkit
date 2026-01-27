"""Migrate task files from YAML to SQLite database."""

import json
from pathlib import Path
from typing import Any

import yaml

from .database import TaskDatabase


def migrate_yaml_to_db(yaml_path: Path, db_path: Path, clear_existing: bool = False) -> dict:
    """Migrate tasks from YAML file to SQLite database.

    Args:
        yaml_path: Path to YAML task file
        db_path: Path to SQLite database (will be created if doesn't exist)
        clear_existing: If True, clear all existing tasks before import

    Returns:
        Dictionary with migration statistics
    """
    # Load YAML
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # Initialize database
    db = TaskDatabase(db_path)

    stats = {
        "total_tasks": 0,
        "imported": 0,
        "skipped": 0,
        "updated": 0,
    }

    # Clear existing if requested
    if clear_existing:
        with db.connection() as conn:
            conn.execute("DELETE FROM tasks")
            conn.execute("DELETE FROM execution_log")

    # Import tasks
    tasks = data.get("tasks", [])
    stats["total_tasks"] = len(tasks)

    with db.connection() as conn:
        for task in tasks:
            task_id = task.get("id")
            if not task_id:
                stats["skipped"] += 1
                continue

            # Check if task exists
            cursor = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
            exists = cursor.fetchone() is not None

            # Prepare task data
            task_data = {
                "id": task_id,
                "name": task.get("name", ""),
                "phase": task.get("phase"),
                "task_type": task.get("type"),
                "status": task.get("status", "not_started"),
                "priority": _priority_to_int(task.get("priority", "medium")),
                "estimated_hours": task.get("estimated_hours"),
                "description": task.get("description", ""),
                "acceptance_criteria": _format_acceptance_criteria(task.get("acceptance_criteria")),
                "files": json.dumps(task.get("files", [])),
                "design_docs": json.dumps(task.get("design_docs", [])),
                "dependencies": ",".join(task.get("dependencies", [])),
            }

            if exists:
                # Update existing (but preserve runtime fields)
                conn.execute(
                    """
                    UPDATE tasks SET
                        name = ?,
                        phase = ?,
                        task_type = ?,
                        priority = ?,
                        estimated_hours = ?,
                        description = ?,
                        acceptance_criteria = ?,
                        files = ?,
                        design_docs = ?,
                        dependencies = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status IN ('not_started', 'failed')
                    """,
                    (
                        task_data["name"],
                        task_data["phase"],
                        task_data["task_type"],
                        task_data["priority"],
                        task_data["estimated_hours"],
                        task_data["description"],
                        task_data["acceptance_criteria"],
                        task_data["files"],
                        task_data["design_docs"],
                        task_data["dependencies"],
                        task_id,
                    ),
                )
                if conn.total_changes > 0:
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                # Insert new
                conn.execute(
                    """
                    INSERT INTO tasks (
                        id, name, phase, task_type, status, priority,
                        estimated_hours, description, acceptance_criteria,
                        files, design_docs, dependencies
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_data["id"],
                        task_data["name"],
                        task_data["phase"],
                        task_data["task_type"],
                        task_data["status"],
                        task_data["priority"],
                        task_data["estimated_hours"],
                        task_data["description"],
                        task_data["acceptance_criteria"],
                        task_data["files"],
                        task_data["design_docs"],
                        task_data["dependencies"],
                    ),
                )
                stats["imported"] += 1

    return stats


def _priority_to_int(priority: str) -> int:
    """Convert priority string to integer for sorting."""
    mapping = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    return mapping.get(priority.lower(), 2)


def _format_acceptance_criteria(criteria: Any) -> str:
    """Format acceptance criteria as text."""
    if isinstance(criteria, list):
        return "\n".join(f"- {item}" for item in criteria)
    elif isinstance(criteria, str):
        return criteria
    else:
        return ""


def export_db_to_yaml(db_path: Path, yaml_path: Path, status_filter: str | None = None):
    """Export tasks from database back to YAML format.

    Args:
        db_path: Path to SQLite database
        yaml_path: Path to output YAML file
        status_filter: Optional status to filter by (e.g., 'completed')
    """
    db = TaskDatabase(db_path)

    # Get tasks
    tasks = db.get_all_tasks(status=status_filter)

    # Convert to YAML structure
    output = {
        "version": "2.0",
        "exported_at": str(Path(db_path).stat().st_mtime),
        "summary": db.get_tasks_summary(),
        "tasks": [],
    }

    for task in tasks:
        task_dict = {
            "id": task["id"],
            "name": task["name"],
            "phase": task["phase"],
            "type": task["task_type"],
            "status": task["status"],
            "priority": _int_to_priority(task["priority"]),
            "estimated_hours": task["estimated_hours"],
            "description": task["description"],
            "acceptance_criteria": task["acceptance_criteria"].split("\n") if task["acceptance_criteria"] else [],
            "files": json.loads(task["files"]) if task["files"] else [],
            "design_docs": json.loads(task["design_docs"]) if task["design_docs"] else [],
        }

        # Add dependencies if present
        if task["dependencies"]:
            task_dict["dependencies"] = [d.strip() for d in task["dependencies"].split(",") if d.strip()]

        # Add runtime info if present
        if task["completed_at"]:
            task_dict["completed_at"] = task["completed_at"]
        if task["retry_count"] > 0:
            task_dict["retry_count"] = task["retry_count"]
        if task["last_error"]:
            task_dict["last_error"] = task["last_error"]

        output["tasks"].append(task_dict)

    # Write YAML
    with open(yaml_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)


def _int_to_priority(priority_int: int) -> str:
    """Convert integer priority back to string."""
    mapping = {
        4: "critical",
        3: "high",
        2: "medium",
        1: "low",
    }
    return mapping.get(priority_int, "medium")
