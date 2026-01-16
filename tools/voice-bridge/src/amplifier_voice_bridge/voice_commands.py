"""Natural language command parsing for voice queries.

Parses voice input into structured commands for the voice bridge.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CommandType(Enum):
    """Types of voice commands."""

    LIST_SESSIONS = "list_sessions"
    SESSION_STATUS = "session_status"
    SESSION_TODOS = "session_todos"
    WHAT_WORKING_ON = "what_working_on"
    CREATE_SESSION = "create_session"
    SEND_TO_SESSION = "send_to_session"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """A parsed voice command."""

    command_type: CommandType
    target_session: Optional[str] = None  # Session name/hint
    prompt: Optional[str] = None  # For create/send commands
    raw_input: str = ""


class VoiceCommandParser:
    """Parses natural language voice commands."""

    # Patterns for each command type
    LIST_PATTERNS = [
        r"(?:what|which|list|show)(?: all)? sessions?(?: are)?(?: running)?",
        r"(?:what|which) (?:are )?(?:the )?(?:running |active )?sessions?",
        r"(?:how many|any) sessions?(?: running)?",
        r"(?:what's|what is) running",
        r"sessions? status",
        r"list (?:all )?(?:running )?sessions?",
        r"(?:show|display) (?:me )?(?:the )?(?:running |active )?sessions?",
        r"running sessions",
        r"active sessions",
    ]

    STATUS_PATTERNS = [
        r"(?:what's|what is) (?:the )?(?:status|state) (?:of |on )?(.+)",
        r"(?:how's|how is) (.+?)(?: doing| going)?",
        r"(?:status|state) (?:of |on )?(.+)",
        r"(?:tell me about|describe) (?:the )?(.+?) session",
        r"(.+?) session (?:status|state)",
    ]

    TODOS_PATTERNS = [
        r"(?:what are the |what's the |show |list )?tasks? (?:for |on |in )?(.+)",
        r"(?:what are the |what's the |show |list )?todos? (?:for |on |in )?(.+)",
        r"(.+?) (?:task|todo) list",
        r"(?:what's|what is) (?:being worked on|in progress)(?: (?:for|on|in) (.+))?",
    ]

    WORKING_ON_PATTERNS = [
        r"what(?:'s| is| are)(?: you| we)? (?:working on|doing)",
        r"(?:current|active) (?:work|tasks?|todos?)",
        r"what(?:'s| is) in progress",
        r"(?:what's|what is) happening",
    ]

    CREATE_PATTERNS = [
        r"(?:create|start|make|new|begin)(?: a)?(?: new)? session (?:to |for |that )?(.+)",
        r"(?:can you |please )?(?:start|create|make)(?: a)?(?: new)? (.+?) session",
        r"new session[:\s]+(.+)",
    ]

    SEND_PATTERNS = [
        r"(?:tell|ask|send to|message) (.+?) (?:to |that )?(.+)",
        r"(?:in |on |to )(.+?)[,:\s]+(.+)",
    ]

    HELP_PATTERNS = [
        r"(?:help|what can you do|commands|options)",
        r"(?:how do I|how to) (?:use|talk to) (?:you|this|amplifier)",
    ]

    def parse(self, text: str) -> ParsedCommand:
        """Parse a voice command from text."""
        text = text.strip()
        text_lower = text.lower()

        # Try each pattern type in order of specificity
        
        # Help
        for pattern in self.HELP_PATTERNS:
            if re.search(pattern, text_lower):
                return ParsedCommand(
                    command_type=CommandType.HELP,
                    raw_input=text,
                )

        # List sessions
        for pattern in self.LIST_PATTERNS:
            if re.search(pattern, text_lower):
                return ParsedCommand(
                    command_type=CommandType.LIST_SESSIONS,
                    raw_input=text,
                )

        # What's being worked on (general)
        for pattern in self.WORKING_ON_PATTERNS:
            if re.search(pattern, text_lower):
                return ParsedCommand(
                    command_type=CommandType.WHAT_WORKING_ON,
                    raw_input=text,
                )

        # Session status
        for pattern in self.STATUS_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                target = match.group(1).strip()
                # Clean up common words
                target = self._clean_session_name(target)
                return ParsedCommand(
                    command_type=CommandType.SESSION_STATUS,
                    target_session=target,
                    raw_input=text,
                )

        # Todos/tasks for a session
        for pattern in self.TODOS_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                target = match.group(1).strip() if match.group(1) else None
                if target:
                    target = self._clean_session_name(target)
                return ParsedCommand(
                    command_type=CommandType.SESSION_TODOS,
                    target_session=target,
                    raw_input=text,
                )

        # Create session
        for pattern in self.CREATE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                prompt = match.group(1).strip()
                return ParsedCommand(
                    command_type=CommandType.CREATE_SESSION,
                    prompt=prompt,
                    raw_input=text,
                )

        # Send to specific session
        for pattern in self.SEND_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                target = self._clean_session_name(match.group(1).strip())
                prompt = match.group(2).strip()
                return ParsedCommand(
                    command_type=CommandType.SEND_TO_SESSION,
                    target_session=target,
                    prompt=prompt,
                    raw_input=text,
                )

        # Default: treat as a prompt to send to default/active session
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            prompt=text,
            raw_input=text,
        )

    def _clean_session_name(self, name: str) -> str:
        """Clean up a session name from voice input."""
        # Remove common filler words
        fillers = [
            "the", "a", "an", "my", "our", "that", "this",
            "session", "project", "please", "can you",
        ]
        words = name.split()
        cleaned = [w for w in words if w.lower() not in fillers]
        return " ".join(cleaned) if cleaned else name


def get_help_text() -> str:
    """Get help text for voice commands."""
    return """I can help you with your Amplifier sessions. Try saying:

"What sessions are running?" - List all active sessions.

"What's the status of carplay?" - Get details about a specific session.

"What are the tasks for carplay?" - See the todo list for a session.

"What's being worked on?" - See current work across all sessions.

"Create a session to research Python async patterns" - Start a new session.

Or just tell me what you want and I'll try to help!"""
