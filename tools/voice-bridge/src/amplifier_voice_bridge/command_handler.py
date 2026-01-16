"""Command handler for voice bridge.

Ties together session discovery, command parsing, and response generation.
"""

from dataclasses import dataclass
from typing import Optional

from .session_discovery import (
    SessionDiscovery,
    SessionState,
    format_session_detail_for_voice,
    format_sessions_for_voice,
    format_todos_for_voice,
)
from .voice_commands import (
    CommandType,
    ParsedCommand,
    VoiceCommandParser,
    get_help_text,
)


@dataclass
class CommandResult:
    """Result of executing a voice command."""

    text: str
    session_id: Optional[str] = None
    success: bool = True
    needs_amplifier: bool = False  # True if this needs to be sent to Amplifier
    amplifier_prompt: Optional[str] = None


class CommandHandler:
    """Handles voice commands by coordinating discovery and parsing."""

    def __init__(self):
        self.parser = VoiceCommandParser()
        self.discovery = SessionDiscovery()

    def handle(self, text: str) -> CommandResult:
        """Handle a voice command and return a response."""
        command = self.parser.parse(text)

        handlers = {
            CommandType.LIST_SESSIONS: self._handle_list_sessions,
            CommandType.SESSION_STATUS: self._handle_session_status,
            CommandType.SESSION_TODOS: self._handle_session_todos,
            CommandType.WHAT_WORKING_ON: self._handle_what_working_on,
            CommandType.CREATE_SESSION: self._handle_create_session,
            CommandType.SEND_TO_SESSION: self._handle_send_to_session,
            CommandType.HELP: self._handle_help,
            CommandType.UNKNOWN: self._handle_unknown,
        }

        handler = handlers.get(command.command_type, self._handle_unknown)
        return handler(command)

    def _handle_list_sessions(self, command: ParsedCommand) -> CommandResult:
        """List all sessions."""
        sessions = self.discovery.discover_sessions()
        return CommandResult(
            text=format_sessions_for_voice(sessions),
            success=True,
        )

    def _handle_session_status(self, command: ParsedCommand) -> CommandResult:
        """Get status of a specific session."""
        if not command.target_session:
            return CommandResult(
                text="Which session would you like to know about?",
                success=False,
            )

        session = self.discovery.get_session_by_project(command.target_session)
        if not session:
            # Try to find similar sessions
            all_sessions = self.discovery.discover_sessions()
            if all_sessions:
                names = [s.project_name for s in all_sessions[:3]]
                return CommandResult(
                    text=f"I couldn't find a session matching '{command.target_session}'. "
                    f"Available sessions: {', '.join(names)}.",
                    success=False,
                )
            return CommandResult(
                text=f"No session found matching '{command.target_session}'.",
                success=False,
            )

        return CommandResult(
            text=format_session_detail_for_voice(session),
            session_id=session.session_id,
            success=True,
        )

    def _handle_session_todos(self, command: ParsedCommand) -> CommandResult:
        """Get todos for a specific session."""
        session: Optional[SessionState] = None

        if command.target_session:
            session = self.discovery.get_session_by_project(command.target_session)
        else:
            # Use most recently active running session
            running = self.discovery.get_running_sessions()
            if running:
                # Sort by last activity
                running.sort(
                    key=lambda s: s.last_activity or s.session_id,
                    reverse=True,
                )
                session = running[0]

        if not session:
            return CommandResult(
                text="I couldn't find that session. Try asking 'what sessions are running?' first.",
                success=False,
            )

        return CommandResult(
            text=format_todos_for_voice(session),
            session_id=session.session_id,
            success=True,
        )

    def _handle_what_working_on(self, command: ParsedCommand) -> CommandResult:
        """Get current work across all sessions."""
        running = self.discovery.get_running_sessions()

        if not running:
            return CommandResult(
                text="No Amplifier sessions are currently running.",
                success=True,
            )

        # Find sessions with active work
        active_work = []
        for session in running:
            in_progress = [t for t in session.todos if t.status == "in_progress"]
            if in_progress:
                active_work.append((session.project_name, in_progress[0].content))

        if not active_work:
            # Fall back to listing running sessions
            if len(running) == 1:
                return CommandResult(
                    text=f"One session running: {running[0].project_name}. No specific task in progress.",
                    success=True,
                )
            names = [s.project_name for s in running[:3]]
            return CommandResult(
                text=f"{len(running)} sessions running: {', '.join(names)}. No specific tasks in progress.",
                success=True,
            )

        if len(active_work) == 1:
            return CommandResult(
                text=f"{active_work[0][0]}: {active_work[0][1]}",
                success=True,
            )

        # Multiple active tasks
        parts = [f"{name}: {task}" for name, task in active_work[:2]]
        response = " Also, ".join(parts)
        if len(active_work) > 2:
            response += f". Plus {len(active_work) - 2} more sessions with active tasks."
        return CommandResult(text=response, success=True)

    def _handle_create_session(self, command: ParsedCommand) -> CommandResult:
        """Create a new session."""
        if not command.prompt:
            return CommandResult(
                text="What would you like the new session to work on?",
                success=False,
            )

        # This requires Amplifier integration
        return CommandResult(
            text=f"Creating a new session to: {command.prompt}. "
            "Note: Session creation requires full Amplifier integration, "
            "which isn't available in standalone mode.",
            success=True,
            needs_amplifier=True,
            amplifier_prompt=command.prompt,
        )

    def _handle_send_to_session(self, command: ParsedCommand) -> CommandResult:
        """Send a prompt to a specific session."""
        if not command.target_session:
            return CommandResult(
                text="Which session should I send this to?",
                success=False,
            )

        session = self.discovery.get_session_by_project(command.target_session)
        if not session:
            return CommandResult(
                text=f"I couldn't find a session matching '{command.target_session}'.",
                success=False,
            )

        if not session.is_running:
            return CommandResult(
                text=f"The {session.project_name} session isn't running. "
                "I can only send messages to active sessions.",
                success=False,
            )

        # This would require inter-process communication with the session
        return CommandResult(
            text=f"To send to {session.project_name}: '{command.prompt}'. "
            "Note: Sending to running sessions requires the full bridge, "
            "not standalone mode.",
            success=True,
            needs_amplifier=True,
            session_id=session.session_id,
            amplifier_prompt=command.prompt,
        )

    def _handle_help(self, command: ParsedCommand) -> CommandResult:
        """Show help."""
        return CommandResult(
            text=get_help_text(),
            success=True,
        )

    def _handle_unknown(self, command: ParsedCommand) -> CommandResult:
        """Handle unknown commands."""
        # For unknown commands, we could:
        # 1. Try to send to the most recently active session
        # 2. Ask for clarification
        # 3. Treat as a general Amplifier prompt

        running = self.discovery.get_running_sessions()
        if running:
            # Find most recently active
            running.sort(
                key=lambda s: s.last_activity or s.session_id,
                reverse=True,
            )
            session = running[0]

            return CommandResult(
                text=f"I'll send that to the {session.project_name} session.",
                session_id=session.session_id,
                success=True,
                needs_amplifier=True,
                amplifier_prompt=command.prompt or command.raw_input,
            )

        return CommandResult(
            text="I'm not sure what you're asking. "
            "Try 'help' to see what I can do, or 'what sessions are running?' "
            "to get started.",
            success=False,
        )
