"""Amplifier session bridge for voice commands.

This module creates and manages Amplifier sessions for executing voice commands.
It can either run fresh prompts or continue existing sessions by loading their
transcript as conversation context.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Try to import Amplifier - graceful fallback if not available
try:
    from amplifier_foundation import load_bundle

    AMPLIFIER_AVAILABLE = True
except ImportError:
    AMPLIFIER_AVAILABLE = False
    load_bundle = None

from .session_discovery import SessionDiscovery, SessionState


@dataclass
class BridgeResponse:
    """Response from the Amplifier bridge."""

    text: str
    success: bool = True
    session_id: Optional[str] = None
    execution_time: float = 0.0
    error: Optional[str] = None


class AmplifierBridge:
    """Bridge between voice commands and Amplifier sessions."""

    def __init__(self, bundle_path: Optional[str] = None):
        """Initialize the bridge.

        Args:
            bundle_path: Path to the bundle to use. If None, uses default.
        """
        self.bundle_path = bundle_path
        self.discovery = SessionDiscovery()
        self._session = None
        self._bundle = None
        self._prepared = None
        self._initialized = False
        self._loop = None

    async def initialize(self) -> bool:
        """Initialize the Amplifier session.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        if not AMPLIFIER_AVAILABLE or load_bundle is None:
            return False

        if self._initialized:
            return True

        try:
            # Load the bundle (load_bundle is guaranteed non-None here)
            if self.bundle_path:
                self._bundle = await load_bundle(self.bundle_path)
            else:
                # Use the default amplifier-dev bundle or foundation
                # Try to find an appropriate bundle
                home = Path.home()
                candidates = [
                    home / ".amplifier" / "cache" / "amplifier-foundation-*",
                    "/mnt/c/ANext/my-amplifier",
                ]
                for pattern in candidates:
                    matches = list(Path("/").glob(str(pattern).lstrip("/")))
                    if matches:
                        self._bundle = await load_bundle(str(matches[0]))
                        break

                if not self._bundle:
                    # Fallback: try loading foundation directly
                    self._bundle = await load_bundle("amplifier-foundation")

            if not self._bundle:
                return False

            # Prepare the bundle
            self._prepared = await self._bundle.prepare()
            self._initialized = True
            return True

        except Exception as e:
            print(f"Failed to initialize Amplifier: {e}")
            return False

    async def execute(
        self,
        prompt: str,
        continue_session: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> BridgeResponse:
        """Execute a prompt, optionally continuing an existing session.

        Args:
            prompt: The prompt to execute.
            continue_session: Session ID or project name to continue.
            working_directory: Working directory for the session.

        Returns:
            BridgeResponse with the result.
        """
        start_time = asyncio.get_event_loop().time()

        if not AMPLIFIER_AVAILABLE:
            return BridgeResponse(
                text="Amplifier is not available. Install amplifier-foundation.",
                success=False,
                error="amplifier_not_available",
            )

        if not self._initialized:
            if not await self.initialize():
                return BridgeResponse(
                    text="Failed to initialize Amplifier session.",
                    success=False,
                    error="initialization_failed",
                )

        try:
            # Build the full prompt with context if continuing a session
            full_prompt = prompt
            target_session = None

            if continue_session:
                target_session = self._find_session(continue_session)
                if target_session:
                    context = self._load_session_context(target_session)
                    if context:
                        full_prompt = f"{context}\n\nUser: {prompt}"

            # Create a session and execute
            if self._prepared is None:
                return BridgeResponse(
                    text="Bridge not properly initialized.",
                    success=False,
                    error="not_prepared",
                )
            session = await self._prepared.create_session()

            # Set working directory if specified
            if working_directory:
                os.chdir(working_directory)
            elif target_session and target_session.directory:
                os.chdir(target_session.directory)

            async with session:
                response = await session.execute(full_prompt)

            elapsed = asyncio.get_event_loop().time() - start_time

            return BridgeResponse(
                text=response,
                success=True,
                session_id=target_session.session_id if target_session else None,
                execution_time=elapsed,
            )

        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            return BridgeResponse(
                text=f"Error executing prompt: {e}",
                success=False,
                error=str(e),
                execution_time=elapsed,
            )

    def _find_session(self, hint: str) -> Optional[SessionState]:
        """Find a session by ID or project name hint."""
        sessions = self.discovery.discover_sessions()

        # Try exact session ID match first
        for s in sessions:
            if s.session_id == hint:
                return s

        # Try project name match
        hint_lower = hint.lower()
        for s in sessions:
            if hint_lower in s.project_name.lower():
                return s
            if hint_lower in s.directory.lower():
                return s

        return None

    def _load_session_context(
        self, session: SessionState, max_messages: int = 10
    ) -> Optional[str]:
        """Load conversation context from a session's transcript.

        Args:
            session: The session to load context from.
            max_messages: Maximum number of messages to include.

        Returns:
            Formatted context string, or None if unavailable.
        """
        if not session.transcript_path or not session.transcript_path.exists():
            return None

        try:
            messages = []
            with open(session.transcript_path) as f:
                for line in f:
                    try:
                        msg = json.loads(line)
                        role = msg.get("role")
                        content = msg.get("content")

                        if role and content:
                            # Extract text content
                            if isinstance(content, str):
                                text = content
                            elif isinstance(content, list):
                                # Find text blocks
                                text_parts = []
                                for block in content:
                                    if isinstance(block, dict):
                                        if block.get("type") == "text":
                                            text_parts.append(block.get("text", ""))
                                text = "\n".join(text_parts)
                            else:
                                continue

                            if text:
                                messages.append({"role": role, "content": text})
                    except json.JSONDecodeError:
                        continue

            if not messages:
                return None

            # Take last N messages
            recent = messages[-max_messages:]

            # Format as conversation context
            lines = [
                f"[Continuing session: {session.project_name}]",
                f"[Previous conversation ({len(recent)} messages):]",
                "",
            ]

            for msg in recent:
                role = msg["role"].capitalize()
                # Truncate very long messages
                content = msg["content"]
                if len(content) > 500:
                    content = content[:500] + "..."
                lines.append(f"{role}: {content}")
                lines.append("")

            lines.append("[Continue the conversation:]")

            return "\n".join(lines)

        except Exception as e:
            print(f"Error loading session context: {e}")
            return None


class SyncBridge:
    """Synchronous wrapper for AmplifierBridge.

    Use this in synchronous contexts (like the HTTP server).
    """

    def __init__(self, bundle_path: Optional[str] = None):
        self.bridge = AmplifierBridge(bundle_path)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def execute(
        self,
        prompt: str,
        continue_session: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> BridgeResponse:
        """Execute a prompt synchronously."""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.bridge.execute(prompt, continue_session, working_directory)
        )

    def initialize(self) -> bool:
        """Initialize the bridge synchronously."""
        loop = self._get_loop()
        return loop.run_until_complete(self.bridge.initialize())


def is_amplifier_available() -> bool:
    """Check if Amplifier is available."""
    return AMPLIFIER_AVAILABLE
