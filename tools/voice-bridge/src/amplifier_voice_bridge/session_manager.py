"""Session manager for Amplifier voice bridge.

Manages AmplifierSession instances, routing prompts to sessions,
and capturing output via the hook system.
"""

import asyncio
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from amplifier_core.hooks import HookResult
from amplifier_core.session import AmplifierSession


@dataclass
class ManagedSession:
    """A managed Amplifier session with metadata."""

    id: str
    session: AmplifierSession
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turn_count: int = 0
    status: str = "active"  # active, idle, executing, expired
    working_directory: Optional[str] = None
    bundle: Optional[str] = None
    _output_buffer: list[str] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class SessionManager:
    """Manages multiple Amplifier sessions for the voice bridge."""

    def __init__(
        self,
        default_bundle: Optional[str] = None,
        idle_timeout: int = 3600,
        max_concurrent: int = 5,
    ):
        self.default_bundle = default_bundle
        self.idle_timeout = idle_timeout
        self.max_concurrent = max_concurrent
        self._sessions: dict[str, ManagedSession] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_session(
        self,
        session_id: str = "default",
        bundle: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> ManagedSession:
        """Get an existing session or create a new one."""
        async with self._lock:
            if session_id in self._sessions:
                managed = self._sessions[session_id]
                managed.last_activity = datetime.now(timezone.utc)
                return managed

            # Create new session
            if len(self._sessions) >= self.max_concurrent:
                # Evict oldest idle session
                await self._evict_oldest_idle()

            managed = await self._create_session(
                session_id=session_id,
                bundle=bundle or self.default_bundle,
                working_directory=working_directory,
            )
            self._sessions[session_id] = managed
            return managed

    async def _create_session(
        self,
        session_id: str,
        bundle: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> ManagedSession:
        """Create a new AmplifierSession with output capture hook."""
        # Import here to avoid circular imports and allow graceful degradation
        try:
            from amplifier_foundation.bundle import load_bundle
            from amplifier_foundation.session import create_session_from_bundle

            if bundle:
                bundle_config = load_bundle(bundle)
                session = await create_session_from_bundle(bundle_config)
            else:
                # Create minimal session without bundle
                session = AmplifierSession(session_id=session_id)
                await session.initialize()
        except ImportError:
            # Fallback: create basic session without foundation
            session = AmplifierSession(session_id=session_id)
            await session.initialize()

        managed = ManagedSession(
            id=session_id,
            session=session,
            working_directory=working_directory,
            bundle=bundle,
        )

        # Register hook to capture output
        await self._register_output_hook(managed)

        return managed

    async def _register_output_hook(self, managed: ManagedSession) -> None:
        """Register a hook to capture session output."""

        async def output_capture_hook(event: str, data: dict[str, Any]) -> HookResult:
            """Capture text output from the session."""
            # Capture content block deltas (streaming text)
            if event == "content_block:delta":
                delta = data.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        managed._output_buffer.append(text)

            # Capture final content blocks
            elif event == "content_block:end":
                content = data.get("content_block", {})
                if content.get("type") == "text":
                    # Already captured via deltas, but backup
                    pass

            return HookResult(action="continue")

        # Register the hook
        try:
            managed.session.coordinator.hooks.register(
                pattern="content_block:*",
                hook=output_capture_hook,
                priority=100,  # Low priority, just observe
                name=f"voice-bridge-output-{managed.id}",
            )
        except Exception:
            # Hook registration may fail if session not fully initialized
            pass

    async def execute_prompt(
        self,
        session_id: str,
        prompt: str,
        timeout: int = 120,
        max_response_length: int = 500,
    ) -> dict[str, Any]:
        """Execute a prompt on a session and return the response."""
        managed = await self.get_or_create_session(session_id)

        async with managed._lock:
            managed.status = "executing"
            managed._output_buffer.clear()
            managed.turn_count += 1
            turn_id = str(uuid.uuid4())[:8]
            start_time = time.time()

            try:
                # Execute with timeout
                response = await asyncio.wait_for(
                    managed.session.execute(prompt),
                    timeout=timeout,
                )
                execution_time = time.time() - start_time

                # Get the response text
                if response:
                    text = str(response)
                elif managed._output_buffer:
                    text = "".join(managed._output_buffer)
                else:
                    text = "I processed your request but have no response to share."

                # Format for voice
                text = self._format_for_voice(text)

                # Truncate if needed
                truncated = False
                if len(text) > max_response_length:
                    text = text[:max_response_length].rsplit(" ", 1)[0]
                    text += "... Response truncated for voice."
                    truncated = True

                managed.status = "active"
                managed.last_activity = datetime.now(timezone.utc)

                return {
                    "text": text,
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "truncated": truncated,
                    "execution_time": execution_time,
                }

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                managed.status = "active"

                # Return partial response if available
                partial = "".join(managed._output_buffer) if managed._output_buffer else None
                if partial:
                    partial = self._format_for_voice(partial)
                    if len(partial) > max_response_length:
                        partial = partial[:max_response_length]

                return {
                    "error": "Request timed out",
                    "partial_text": partial,
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "execution_time": execution_time,
                }

            except Exception as e:
                execution_time = time.time() - start_time
                managed.status = "active"

                return {
                    "error": f"Execution error: {str(e)}",
                    "partial_text": None,
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "execution_time": execution_time,
                }

    def _format_for_voice(self, text: str) -> str:
        """Format text for voice output."""
        # Remove markdown formatting
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Bold
        text = re.sub(r"\*(.+?)\*", r"\1", text)  # Italic
        text = re.sub(r"`(.+?)`", r"\1", text)  # Inline code
        text = re.sub(r"```[\s\S]*?```", "[code block omitted]", text)  # Code blocks
        text = re.sub(r"#+\s*", "", text)  # Headers

        # Remove URLs (speak domain only)
        text = re.sub(
            r"https?://([^/\s]+)[^\s]*",
            r"link to \1",
            text,
        )

        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"  +", " ", text)
        text = text.strip()

        return text

    async def list_sessions(self) -> list[dict[str, Any]]:
        """List all managed sessions."""
        sessions = []
        for managed in self._sessions.values():
            sessions.append({
                "id": managed.id,
                "status": managed.status,
                "turn_count": managed.turn_count,
                "created_at": managed.created_at,
                "last_activity": managed.last_activity,
                "working_directory": managed.working_directory,
                "bundle": managed.bundle,
            })
        return sessions

    async def get_session_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get information about a specific session."""
        managed = self._sessions.get(session_id)
        if not managed:
            return None

        return {
            "id": managed.id,
            "status": managed.status,
            "turn_count": managed.turn_count,
            "created_at": managed.created_at,
            "last_activity": managed.last_activity,
            "working_directory": managed.working_directory,
            "bundle": managed.bundle,
        }

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        async with self._lock:
            if session_id in self._sessions:
                managed = self._sessions.pop(session_id)
                managed.status = "expired"
                # Cleanup session resources if needed
                return True
            return False

    async def _evict_oldest_idle(self) -> None:
        """Evict the oldest idle session to make room for new ones."""
        oldest_idle = None
        oldest_time = None

        for managed in self._sessions.values():
            if managed.status in ("active", "idle"):
                if oldest_time is None or managed.last_activity < oldest_time:
                    oldest_time = managed.last_activity
                    oldest_idle = managed.id

        if oldest_idle:
            self._sessions.pop(oldest_idle, None)

    async def cleanup_expired(self) -> int:
        """Clean up expired sessions. Returns count of cleaned sessions."""
        now = datetime.now(timezone.utc)
        expired = []

        for session_id, managed in self._sessions.items():
            idle_seconds = (now - managed.last_activity).total_seconds()
            if idle_seconds > self.idle_timeout:
                expired.append(session_id)

        async with self._lock:
            for session_id in expired:
                self._sessions.pop(session_id, None)

        return len(expired)
