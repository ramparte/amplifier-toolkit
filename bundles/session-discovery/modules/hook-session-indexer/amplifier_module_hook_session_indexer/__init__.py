"""Session indexing hook - auto-names and indexes sessions on completion."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier_core import HookResult  # type: ignore[import-not-found]


class SessionIndexer:
    """
    Hook that indexes sessions when they complete.

    Observes session:end events and generates quick heuristic names.
    Maintains a searchable index at ~/.amplifier/session-index.json.
    """

    def __init__(self):
        self.index_path = Path.home() / ".amplifier" / "session-index.json"
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    async def on_session_end(self, event: str, data: dict[str, Any]) -> HookResult:
        """Index session when it completes."""
        session_id = data.get("session_id")
        parent_id = data.get("parent_id")

        # Only index root sessions (not sub-sessions spawned by agents)
        if parent_id:
            return HookResult(action="continue")

        # Get session directory path from event data
        session_dir = data.get("session_dir")
        if not session_dir or not session_id:
            return HookResult(action="continue")

        # Spawn indexing as background task (don't block session completion)
        asyncio.create_task(self._index_session_async(session_id, session_dir))

        return HookResult(action="continue")

    async def _index_session_async(self, session_id: str, session_dir: str):
        """Background task to index a session."""
        try:
            session_path = Path(session_dir)

            # Read metadata
            metadata_path = session_path / "metadata.json"
            if not metadata_path.exists():
                return

            with open(metadata_path) as f:
                metadata = json.load(f)

            # Quick heuristic: Generate name from first user message
            name = await self._generate_quick_name(session_path)

            # Extract project from path
            # Path format: ~/.amplifier/projects/PROJECT/sessions/SESSION_ID
            parts = session_path.parts
            project = parts[-3] if len(parts) >= 3 else "unknown"

            # Create index entry
            entry = {
                "session_id": session_id,
                "name": name,
                "project": project,
                "created": metadata.get("created"),
                "bundle": metadata.get("bundle"),
                "model": metadata.get("model"),
                "turn_count": metadata.get("turn_count", 0),
                "path": str(session_path),
                "indexed_at": datetime.now().isoformat(),
            }

            # Update index file
            await self._update_index(entry)

        except Exception as e:
            # Log but don't crash - indexing is best-effort
            print(f"Warning: Session indexing failed for {session_id}: {e}")

    async def _generate_quick_name(self, session_path: Path) -> str:
        """Generate quick name from first user message."""
        transcript_path = session_path / "transcript.jsonl"
        if not transcript_path.exists():
            return "Untitled Session"

        try:
            # Read first few lines to find first user message
            with open(transcript_path) as f:
                for line in f:
                    msg = json.loads(line)
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        # Take first 50 chars, clean up
                        name = content[:50].strip()
                        if len(content) > 50:
                            name += "..."
                        return name or "Untitled Session"
        except Exception:
            pass

        return "Untitled Session"

    async def _update_index(self, entry: dict[str, Any]):
        """Add entry to index file."""
        # Read existing index
        index = []
        if self.index_path.exists():
            try:
                with open(self.index_path) as f:
                    index = json.load(f)
            except Exception:
                index = []

        # Remove old entry for this session if exists
        index = [e for e in index if e.get("session_id") != entry["session_id"]]

        # Add new entry
        index.append(entry)

        # Write back (sorted by created date, newest first)
        index.sort(key=lambda e: e.get("created", ""), reverse=True)
        with open(self.index_path, "w") as f:
            json.dump(index, f, indent=2)


def mount():
    """Entry point - returns hook instances for coordinator to register."""
    indexer = SessionIndexer()

    return {
        "hooks": [
            {
                "event": "session:end",
                "handler": indexer.on_session_end,
            }
        ]
    }
