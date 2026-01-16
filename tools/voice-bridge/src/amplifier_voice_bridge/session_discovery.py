"""Session discovery and state extraction for Amplifier sessions.

Discovers running Amplifier sessions and extracts their state from transcripts.
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class TodoItem:
    """A todo item from a session."""

    content: str
    status: str  # pending, in_progress, completed
    active_form: Optional[str] = None


@dataclass
class SessionState:
    """State of an Amplifier session."""

    session_id: str
    directory: str
    pid: int
    is_running: bool
    project_name: str
    todos: list[TodoItem] = field(default_factory=list)
    last_user_message: Optional[str] = None
    last_assistant_summary: Optional[str] = None
    last_activity: Optional[datetime] = None
    turn_count: int = 0
    transcript_path: Optional[Path] = None


class SessionDiscovery:
    """Discovers and extracts state from Amplifier sessions."""

    def __init__(self, amplifier_home: Optional[Path] = None):
        self.amplifier_home = amplifier_home or Path.home() / ".amplifier"
        self.saved_sessions_path = self.amplifier_home / "saved-sessions.json"
        self.projects_path = self.amplifier_home / "projects"

    def discover_sessions(self) -> list[SessionState]:
        """Discover all known Amplifier sessions and their state."""
        sessions = []

        # Load saved sessions
        saved = self._load_saved_sessions()
        if not saved:
            return sessions

        for entry in saved.get("sessions", []):
            session_id = entry.get("session_id")
            directory = entry.get("directory", "")
            pid = entry.get("pid", 0)

            if not session_id:
                continue

            # Check if process is running
            is_running = self._is_process_running(pid)

            # Get project name from directory
            project_name = self._extract_project_name(directory)

            # Find transcript path
            transcript_path = self._find_transcript(directory, session_id)

            state = SessionState(
                session_id=session_id,
                directory=directory,
                pid=pid,
                is_running=is_running,
                project_name=project_name,
                transcript_path=transcript_path,
            )

            # Parse transcript for state
            if transcript_path and transcript_path.exists():
                self._extract_state_from_transcript(state, transcript_path)

            sessions.append(state)

        return sessions

    def get_session_by_project(self, project_hint: str) -> Optional[SessionState]:
        """Find a session by project name hint (fuzzy match)."""
        sessions = self.discover_sessions()
        project_hint_lower = project_hint.lower()

        for session in sessions:
            if project_hint_lower in session.project_name.lower():
                return session
            if project_hint_lower in session.directory.lower():
                return session

        return None

    def get_running_sessions(self) -> list[SessionState]:
        """Get only currently running sessions."""
        return [s for s in self.discover_sessions() if s.is_running]

    def _load_saved_sessions(self) -> dict[str, Any]:
        """Load the saved sessions file."""
        if not self.saved_sessions_path.exists():
            return {}

        try:
            with open(self.saved_sessions_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running by PID."""
        if pid <= 0:
            return False

        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _extract_project_name(self, directory: str) -> str:
        """Extract a readable project name from a directory path."""
        if not directory:
            return "unknown"

        # Get the last component of the path
        path = Path(directory)
        name = path.name

        # Handle WSL paths like /mnt/c/ANext/carplay
        if name and name != "":
            return name

        # Fallback to last non-empty component
        parts = [p for p in path.parts if p and p != "/"]
        return parts[-1] if parts else "unknown"

    def _find_transcript(self, directory: str, session_id: str) -> Optional[Path]:
        """Find the transcript file for a session."""
        if not directory:
            return None

        # Convert directory to project path format
        # /mnt/c/ANext/carplay -> -mnt-c-ANext-carplay
        project_key = directory.replace("/", "-")
        if project_key.startswith("-"):
            project_key = project_key[1:]

        # Also try with leading dash
        for key in [project_key, f"-{project_key}"]:
            transcript_path = (
                self.projects_path / key / "sessions" / session_id / "transcript.jsonl"
            )
            if transcript_path.exists():
                return transcript_path

        # Try without the leading component variations
        for project_dir in self.projects_path.iterdir():
            if not project_dir.is_dir():
                continue
            transcript_path = (
                project_dir / "sessions" / session_id / "transcript.jsonl"
            )
            if transcript_path.exists():
                return transcript_path

        return None

    def _extract_state_from_transcript(
        self, state: SessionState, transcript_path: Path
    ) -> None:
        """Extract state information from a transcript file."""
        try:
            with open(transcript_path) as f:
                lines = f.readlines()
        except Exception:
            return

        state.turn_count = 0
        last_user_msg = None
        last_assistant_msg = None
        last_timestamp = None

        # Parse each line (message)
        for line in lines:
            try:
                msg = json.loads(line)
                role = msg.get("role")
                content = msg.get("content")
                timestamp_str = msg.get("timestamp")

                if timestamp_str:
                    try:
                        last_timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

                if role == "user":
                    state.turn_count += 1
                    if isinstance(content, str):
                        last_user_msg = content
                    elif isinstance(content, list):
                        # Extract text from content blocks
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                last_user_msg = block.get("text", "")
                                break

                elif role == "assistant":
                    if isinstance(content, str):
                        last_assistant_msg = content
                    elif isinstance(content, list):
                        # Extract text, look for tool calls with todo
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    last_assistant_msg = block.get("text", "")
                                elif block.get("type") == "tool_use":
                                    self._extract_todos_from_tool_call(state, block)

            except json.JSONDecodeError:
                continue

        # Store last messages (truncated for voice)
        if last_user_msg:
            state.last_user_message = last_user_msg[:200]

        if last_assistant_msg:
            state.last_assistant_summary = self._summarize_for_voice(last_assistant_msg)

        state.last_activity = last_timestamp

    def _extract_todos_from_tool_call(
        self, state: SessionState, tool_block: dict[str, Any]
    ) -> None:
        """Extract todos from a tool call block."""
        if tool_block.get("name") != "todo":
            return

        input_data = tool_block.get("input", {})
        todos_data = input_data.get("todos", [])

        if not todos_data:
            return

        # Replace todos with the latest set
        state.todos = []
        for todo in todos_data:
            if isinstance(todo, dict):
                state.todos.append(
                    TodoItem(
                        content=todo.get("content", ""),
                        status=todo.get("status", "pending"),
                        active_form=todo.get("activeForm"),
                    )
                )

    def _summarize_for_voice(self, text: str, max_length: int = 150) -> str:
        """Summarize text for voice output."""
        if not text:
            return ""

        # Remove markdown formatting
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"#+\s*", "", text)

        # Clean whitespace
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # Truncate
        if len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."

        return text


def format_sessions_for_voice(sessions: list[SessionState]) -> str:
    """Format session list for voice output."""
    if not sessions:
        return "No Amplifier sessions found."

    running = [s for s in sessions if s.is_running]
    if not running:
        return f"Found {len(sessions)} sessions but none are currently running."

    if len(running) == 1:
        s = running[0]
        response = f"One session running: {s.project_name}."
        if s.todos:
            in_progress = [t for t in s.todos if t.status == "in_progress"]
            if in_progress:
                response += f" Currently: {in_progress[0].content}."
        return response

    # Multiple sessions
    response = f"{len(running)} sessions running: "
    names = [s.project_name for s in running[:3]]
    response += ", ".join(names)
    if len(running) > 3:
        response += f", and {len(running) - 3} more"
    response += "."

    return response


def format_session_detail_for_voice(session: SessionState) -> str:
    """Format detailed session info for voice output."""
    if not session:
        return "Session not found."

    status = "running" if session.is_running else "stopped"
    response = f"{session.project_name} is {status}."

    if session.todos:
        in_progress = [t for t in session.todos if t.status == "in_progress"]
        pending = [t for t in session.todos if t.status == "pending"]
        completed = [t for t in session.todos if t.status == "completed"]

        if in_progress:
            response += f" Currently working on: {in_progress[0].content}."
        if pending:
            response += f" {len(pending)} tasks pending."
        if completed:
            response += f" {len(completed)} tasks completed."
    else:
        if session.last_user_message:
            response += f" Last request: {session.last_user_message[:100]}."

    return response


def format_todos_for_voice(session: SessionState) -> str:
    """Format todo list for voice output."""
    if not session:
        return "Session not found."

    if not session.todos:
        return f"No task list for {session.project_name}."

    in_progress = [t for t in session.todos if t.status == "in_progress"]
    pending = [t for t in session.todos if t.status == "pending"]
    completed = [t for t in session.todos if t.status == "completed"]

    parts = []

    if in_progress:
        parts.append(f"In progress: {in_progress[0].content}")

    if pending:
        if len(pending) == 1:
            parts.append(f"Pending: {pending[0].content}")
        else:
            parts.append(f"{len(pending)} pending: {pending[0].content}, and {len(pending)-1} more")

    if completed:
        parts.append(f"{len(completed)} completed")

    return f"{session.project_name} tasks. " + ". ".join(parts) + "."
