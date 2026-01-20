"""M365 Collaboration Tool implementation.

Provides agent-to-agent communication via SharePoint document storage.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import msal

from .config import M365Config

logger = logging.getLogger(__name__)


# === Authentication ===

class M365Auth:
    """MSAL-based authentication for Microsoft Graph API."""

    def __init__(self, config: M365Config):
        self.config = config
        self._app = msal.ConfidentialClientApplication(
            client_id=config.client_id,
            client_credential=config.client_secret,
            authority=f"https://login.microsoftonline.com/{config.tenant_id}",
        )
        self._token: Optional[str] = None

    def get_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        result = self._app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" in result:
            self._token = result["access_token"]
            return self._token
        raise RuntimeError(f"Failed to acquire token: {result.get('error_description', result)}")


# === Data Models ===

@dataclass
class AgentMessage:
    """A message in the agent collaboration system."""

    id: str
    timestamp: str
    agent_id: str
    message_type: str
    title: str
    content: str
    priority: str = "normal"
    status: str = "pending"
    context: dict = field(default_factory=dict)
    in_reply_to: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "message_type": self.message_type,
            "title": self.title,
            "content": self.content,
            "priority": self.priority,
            "status": self.status,
            "context": self.context,
            "in_reply_to": self.in_reply_to,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMessage":
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            agent_id=data["agent_id"],
            message_type=data["message_type"],
            title=data["title"],
            content=data["content"],
            priority=data.get("priority", "normal"),
            status=data.get("status", "pending"),
            context=data.get("context", {}),
            in_reply_to=data.get("in_reply_to"),
        )


# === Main Tool Class ===

class M365CollabTool:
    """
    M365 Collaboration Tool for Amplifier.
    
    Enables AI agents to communicate across sessions via SharePoint.
    """

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    FOLDER_NAME = "AgentMessages"

    def __init__(self, config: Optional[M365Config] = None, agent_id: Optional[str] = None):
        self.config = config or M365Config.from_env()
        self.auth = M365Auth(self.config)
        self.agent_id = agent_id or f"amplifier-{os.getpid()}"
        self._http = httpx.Client(timeout=30.0)
        self._drive_id: Optional[str] = None

    @property
    def drive_id(self) -> str:
        """Get the drive ID, fetching if needed."""
        if self._drive_id is None:
            response = self._request("GET", f"/sites/{self.config.site_path}/drive")
            if response.status_code == 200:
                self._drive_id = response.json()["id"]
            else:
                raise RuntimeError(f"Failed to get drive: {response.text}")
        return self._drive_id

    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
        content: Optional[bytes] = None,
    ) -> httpx.Response:
        """Make authenticated request to Graph API."""
        url = f"{self.GRAPH_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {self.auth.get_token()}",
            "Content-Type": "application/json",
        }

        if content is not None:
            return self._http.request(method, url, headers=headers, content=content)
        elif json_data is not None:
            return self._http.request(method, url, headers=headers, json=json_data)
        else:
            return self._http.request(method, url, headers=headers)

    def _ensure_folder(self) -> None:
        """Ensure the AgentMessages folder exists."""
        self._request(
            "POST",
            f"/drives/{self.drive_id}/root/children",
            json_data={
                "name": self.FOLDER_NAME,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail",
            },
        )

    # === Operations ===

    def post_message(
        self,
        title: str,
        content: str,
        message_type: str = "message",
        priority: str = "normal",
        context: Optional[dict] = None,
        in_reply_to: Optional[str] = None,
    ) -> AgentMessage:
        """Post a message to the collaboration space."""
        self._ensure_folder()

        msg = AgentMessage(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=self.agent_id,
            message_type=message_type,
            title=title,
            content=content,
            priority=priority,
            status="pending" if message_type == "task" else "completed",
            context=context or {},
            in_reply_to=in_reply_to,
        )

        filename = f"{msg.id}.json"
        file_content = json.dumps(msg.to_dict(), indent=2).encode()

        response = self._request(
            "PUT",
            f"/drives/{self.drive_id}/root:/{self.FOLDER_NAME}/{filename}:/content",
            content=file_content,
        )

        if response.status_code not in (200, 201):
            raise RuntimeError(f"Failed to post message: {response.text}")

        return msg

    def get_messages(
        self,
        message_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[AgentMessage]:
        """Get messages from the collaboration space."""
        response = self._request(
            "GET",
            f"/drives/{self.drive_id}/root:/{self.FOLDER_NAME}:/children"
            f"?$top={limit}&$orderby=lastModifiedDateTime desc",
        )

        if response.status_code != 200:
            return []

        messages = []
        for item in response.json().get("value", []):
            if not item["name"].endswith(".json"):
                continue

            download_url = item.get("@microsoft.graph.downloadUrl")
            if download_url:
                content_response = self._http.get(download_url)
                if content_response.status_code == 200:
                    try:
                        data = content_response.json()
                        msg = AgentMessage.from_dict(data)

                        if message_type and msg.message_type != message_type:
                            continue
                        if status and msg.status != status:
                            continue

                        messages.append(msg)
                    except (json.JSONDecodeError, KeyError):
                        pass

        return messages

    def get_message(self, message_id: str) -> Optional[AgentMessage]:
        """Get a specific message by ID."""
        filename = f"{message_id}.json" if not message_id.endswith(".json") else message_id

        response = self._request(
            "GET",
            f"/drives/{self.drive_id}/root:/{self.FOLDER_NAME}/{filename}:/content",
        )

        if response.status_code == 200:
            return AgentMessage.from_dict(response.json())
        return None

    def update_message_status(
        self, message_id: str, status: str, context_update: Optional[dict] = None
    ) -> Optional[AgentMessage]:
        """Update the status of a message."""
        msg = self.get_message(message_id)
        if not msg:
            return None

        msg.status = status
        msg.timestamp = datetime.now(timezone.utc).isoformat()
        if context_update:
            msg.context.update(context_update)

        filename = f"{message_id}.json" if not message_id.endswith(".json") else message_id
        file_content = json.dumps(msg.to_dict(), indent=2).encode()

        response = self._request(
            "PUT",
            f"/drives/{self.drive_id}/root:/{self.FOLDER_NAME}/{filename}:/content",
            content=file_content,
        )

        if response.status_code in (200, 201):
            return msg
        return None

    def post_task(self, title: str, description: str, priority: str = "normal", context: Optional[dict] = None) -> AgentMessage:
        """Post a task for other agents."""
        return self.post_message(title=title, content=description, message_type="task", priority=priority, context=context)

    def post_status(self, title: str, status_text: str, task_id: Optional[str] = None) -> AgentMessage:
        """Post a status update."""
        return self.post_message(title=title, content=status_text, message_type="status", in_reply_to=task_id)

    def post_handoff(self, title: str, description: str, context: dict, target_agent: Optional[str] = None) -> AgentMessage:
        """Post a work handoff."""
        ctx = context.copy()
        if target_agent:
            ctx["target_agent"] = target_agent
        return self.post_message(title=title, content=description, message_type="handoff", priority="high", context=ctx)

    def get_pending_tasks(self) -> list[AgentMessage]:
        """Get all pending tasks."""
        return self.get_messages(message_type="task", status="pending")

    def claim_task(self, task_id: str) -> Optional[AgentMessage]:
        """Claim a task."""
        return self.update_message_status(
            task_id, "in_progress",
            {"claimed_by": self.agent_id, "claimed_at": datetime.now(timezone.utc).isoformat()},
        )

    def complete_task(self, task_id: str, result: Optional[dict] = None) -> Optional[AgentMessage]:
        """Complete a task."""
        return self.update_message_status(
            task_id, "completed",
            {"completed_by": self.agent_id, "result": result or {}},
        )

    def close(self):
        """Close HTTP client."""
        self._http.close()

    # === Amplifier Tool Interface ===

    def execute(self, operation: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a tool operation."""
        try:
            if operation == "post_message":
                msg = self.post_message(**kwargs)
                return {"success": True, "message": msg.to_dict()}

            elif operation == "post_task":
                msg = self.post_task(**kwargs)
                return {"success": True, "task": msg.to_dict()}

            elif operation == "post_status":
                msg = self.post_status(**kwargs)
                return {"success": True, "status": msg.to_dict()}

            elif operation == "post_handoff":
                msg = self.post_handoff(**kwargs)
                return {"success": True, "handoff": msg.to_dict()}

            elif operation == "get_messages":
                messages = self.get_messages(**kwargs)
                return {"success": True, "messages": [m.to_dict() for m in messages], "count": len(messages)}

            elif operation == "get_pending_tasks":
                tasks = self.get_pending_tasks()
                return {"success": True, "tasks": [t.to_dict() for t in tasks], "count": len(tasks)}

            elif operation == "claim_task":
                task_id = kwargs.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id required"}
                msg = self.claim_task(task_id)
                if msg:
                    return {"success": True, "task": msg.to_dict()}
                return {"success": False, "error": "Task not found"}

            elif operation == "complete_task":
                task_id = kwargs.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id required"}
                msg = self.complete_task(task_id, kwargs.get("result"))
                if msg:
                    return {"success": True, "task": msg.to_dict()}
                return {"success": False, "error": "Task not found"}

            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.exception(f"Operation {operation} failed")
            return {"success": False, "error": str(e)}


# === Module-level Interface ===

_tool_instance: Optional[M365CollabTool] = None


def _get_tool() -> M365CollabTool:
    """Get or create the tool instance."""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = M365CollabTool()
    return _tool_instance


def execute(operation: str, **kwargs: Any) -> dict[str, Any]:
    """Module-level execute for stateless invocation."""
    return _get_tool().execute(operation, **kwargs)


def get_tool_definition() -> dict[str, Any]:
    """Return the tool definition for Amplifier."""
    return {
        "name": "m365_collab",
        "description": """Collaborate with other AI agent sessions via M365 SharePoint.

Post tasks, status updates, and handoffs that persist across sessions.
Other agents can pick up tasks you post, and you can claim tasks from others.

Operations:
- get_pending_tasks: Check for tasks from other agents
- claim_task: Claim a task (task_id)
- complete_task: Mark a task done (task_id, result?)
- post_task: Post a task for others (title, description, priority?, context?)
- post_status: Post a status update (title, status_text, task_id?)
- post_handoff: Hand off work (title, description, context)
- get_messages: Get recent messages (message_type?, status?, limit?)
- post_message: Post a general message (title, content)

Example - check for tasks:
  m365_collab(operation="get_pending_tasks")

Example - post a task:
  m365_collab(operation="post_task", title="Review auth", description="Check for security issues")""",
        "parameters": {
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
                "priority": {"type": "string", "enum": ["high", "normal", "low"]},
                "message_type": {"type": "string", "enum": ["task", "status", "message", "handoff"]},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed"]},
                "context": {"type": "object", "description": "Additional context data"},
                "result": {"type": "object", "description": "Task completion result"},
                "limit": {"type": "integer", "description": "Max messages to return"},
            },
            "required": ["operation"],
        },
    }
