"""Amplifier execution bridge using subprocess.

Uses `amplifier run` CLI for execution - avoids Python environment issues
that occur when trying to load bundles programmatically.
"""

import asyncio
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from .session_discovery import SessionDiscovery, SessionState


@dataclass
class BridgeResponse:
    """Response from the Amplifier bridge."""

    text: str
    success: bool = True
    session_id: Optional[str] = None
    execution_time: float = 0.0
    error: Optional[str] = None


def is_amplifier_available() -> bool:
    """Check if the amplifier CLI is available."""
    return shutil.which("amplifier") is not None


class AmplifierBridge:
    """Bridge to Amplifier using subprocess execution.

    This approach avoids Python environment issues by using the CLI.
    """

    def __init__(self, bundle: Optional[str] = None, timeout: int = 120):
        """Initialize the bridge.

        Args:
            bundle: Bundle name or path (optional, uses default if not set)
            timeout: Execution timeout in seconds
        """
        self.bundle = bundle
        self.timeout = timeout
        self.discovery = SessionDiscovery()

    def execute(
        self,
        prompt: str,
        continue_session: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> BridgeResponse:
        """Execute a prompt via amplifier CLI.

        Args:
            prompt: The prompt to execute
            continue_session: Session hint to load context from
            working_directory: Directory to run in

        Returns:
            BridgeResponse with the result
        """
        start_time = time.time()

        if not is_amplifier_available():
            return BridgeResponse(
                text="Amplifier CLI not found. Install with: uv tool install amplifier",
                success=False,
                error="cli_not_found",
            )

        # Build the full prompt with context if continuing
        full_prompt = prompt
        if continue_session:
            context = self._build_context(continue_session)
            if context:
                full_prompt = f"{context}\n\nUser request: {prompt}"

        # Determine working directory
        cwd = working_directory
        if not cwd and continue_session:
            session = self._find_session(continue_session)
            if session and session.directory:
                cwd = session.directory

        # Build command
        cmd = ["amplifier", "run"]
        if self.bundle:
            cmd.extend(["--bundle", self.bundle])
        cmd.append(full_prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
            )

            elapsed = time.time() - start_time

            if result.returncode == 0:
                # Clean up the output (remove ANSI codes, etc.)
                output = self._clean_output(result.stdout)
                return BridgeResponse(
                    text=output,
                    success=True,
                    execution_time=elapsed,
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return BridgeResponse(
                    text=f"Execution failed: {error_msg[:200]}",
                    success=False,
                    error="execution_failed",
                    execution_time=elapsed,
                )

        except subprocess.TimeoutExpired:
            return BridgeResponse(
                text=f"Request timed out after {self.timeout} seconds",
                success=False,
                error="timeout",
                execution_time=self.timeout,
            )
        except Exception as e:
            return BridgeResponse(
                text=f"Error: {e}",
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    async def execute_async(
        self,
        prompt: str,
        continue_session: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> BridgeResponse:
        """Async version of execute."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute(prompt, continue_session, working_directory),
        )

    def _find_session(self, hint: str) -> Optional[SessionState]:
        """Find a session by ID or project name."""
        sessions = self.discovery.discover_sessions()

        # Try exact ID match
        for s in sessions:
            if s.session_id == hint or s.session_id.startswith(hint):
                return s

        # Try project name match
        hint_lower = hint.lower()
        for s in sessions:
            if hint_lower in s.project_name.lower():
                return s

        return None

    def _build_context(self, session_hint: str, max_messages: int = 5) -> Optional[str]:
        """Build conversation context from an existing session."""
        session = self._find_session(session_hint)
        if not session or not session.transcript_path:
            return None

        if not session.transcript_path.exists():
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
                            text = self._extract_text(content)
                            if text:
                                messages.append({"role": role, "content": text})
                    except json.JSONDecodeError:
                        continue

            if not messages:
                return None

            recent = messages[-max_messages:]
            lines = [
                f"[Context from session: {session.project_name}]",
                "[Recent conversation:]",
                "",
            ]
            for msg in recent:
                content = msg["content"]
                if len(content) > 300:
                    content = content[:300] + "..."
                lines.append(f"{msg['role'].capitalize()}: {content}")
                lines.append("")

            lines.append("[Now respond to the user's new request:]")
            return "\n".join(lines)

        except Exception:
            return None

    def _extract_text(self, content) -> str:
        """Extract text from message content."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "\n".join(parts)
        return ""

    def _clean_output(self, output: str) -> str:
        """Clean CLI output for voice response."""
        # Remove ANSI escape codes
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        output = ansi_pattern.sub("", output)

        # Remove common CLI prefixes/suffixes
        lines = output.strip().split("\n")

        # Filter out progress indicators, spinners, etc.
        filtered = []
        for line in lines:
            line = line.strip()
            # Skip empty lines and common noise
            if not line:
                continue
            if line.startswith("�") or line.startswith("✓") or line.startswith("→"):
                continue
            if "loading" in line.lower() or "initializing" in line.lower():
                continue
            filtered.append(line)

        return "\n".join(filtered) if filtered else output.strip()


class SyncBridge:
    """Synchronous wrapper for AmplifierBridge."""

    def __init__(self, bundle: Optional[str] = None, timeout: int = 120):
        self.bridge = AmplifierBridge(bundle, timeout)

    def execute(
        self,
        prompt: str,
        continue_session: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> BridgeResponse:
        """Execute a prompt synchronously."""
        return self.bridge.execute(prompt, continue_session, working_directory)
