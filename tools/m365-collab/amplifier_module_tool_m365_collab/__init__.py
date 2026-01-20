"""Amplifier tool module for M365 agent collaboration.

This module provides the `m365_collab` tool that agents can use to
communicate across sessions via SharePoint.
"""

from typing import Any

from amplifier_core import ToolResult

from .tool import M365CollabTool as _M365CollabTool


class M365CollabAgentTool:
    """Tool for M365 agent collaboration via SharePoint."""

    def __init__(self):
        self._client: _M365CollabTool | None = None

    def _get_client(self) -> _M365CollabTool:
        """Lazy-initialize the M365 client."""
        if self._client is None:
            self._client = _M365CollabTool()
        return self._client

    @property
    def name(self) -> str:
        return "m365_collab"

    @property
    def description(self) -> str:
        return """Collaborate with other AI agent sessions via M365 SharePoint.

Post tasks, status updates, and handoffs that persist across sessions.
Other agents can pick up tasks you post, and you can claim tasks from others.

Operations:
- get_pending_tasks: Check for tasks from other agents
- claim_task: Claim a task (requires task_id)
- complete_task: Mark a task done (requires task_id, optional result)
- post_task: Post a task for others (requires title, description)
- post_status: Post a status update (requires title, status_text)
- post_handoff: Hand off work (requires title, description, context)
- get_messages: Get recent messages (optional message_type, status, limit)
- post_message: Post a general message (requires title, content)

Examples:
- Check for tasks: {"operation": "get_pending_tasks"}
- Post a task: {"operation": "post_task", "title": "Review auth", "description": "Check for issues"}
- Claim a task: {"operation": "claim_task", "task_id": "msg-xxxxx"}
- Complete: {"operation": "complete_task", "task_id": "msg-xxxxx", "result": {"status": "done"}}"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": ["post_message", "post_task", "post_status", "post_handoff",
                             "get_messages", "get_pending_tasks", "claim_task", "complete_task"],
                },
                "title": {"type": "string", "description": "Message/task title"},
                "content": {"type": "string", "description": "Message content"},
                "description": {"type": "string", "description": "Task description"},
                "status_text": {"type": "string", "description": "Status update text"},
                "task_id": {"type": "string", "description": "Task ID for claim/complete"},
                "priority": {"type": "string", "enum": ["high", "normal", "low"], "default": "normal"},
                "message_type": {"type": "string", "enum": ["task", "status", "message", "handoff"]},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed"]},
                "context": {"type": "object", "description": "Additional context data"},
                "result": {"type": "object", "description": "Task completion result"},
                "limit": {"type": "integer", "description": "Max messages to return", "default": 50},
            },
            "required": ["operation"],
        }

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the M365 collaboration tool."""
        try:
            client = self._get_client()
            operation = input_data.get("operation")
            kwargs = {k: v for k, v in input_data.items() if k != "operation"}
            result = client.execute(operation, **kwargs)
            return ToolResult(
                success=result.get("success", False),
                output=result
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output={"error": str(e), "success": False}
            )


async def mount(coordinator: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mount the m365_collab tool into the coordinator."""
    tool = M365CollabAgentTool()
    await coordinator.mount("tools", tool, name=tool.name)
    return {
        "name": "tool-m365-collab",
        "version": "0.1.0",
        "provides": ["m365_collab"],
    }


__all__ = ["M365CollabAgentTool", "mount"]
__version__ = "0.1.0"
