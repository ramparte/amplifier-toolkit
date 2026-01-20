# M365 Collaboration Tool

An Amplifier tool for agent-to-agent communication via Microsoft 365 SharePoint.

## Overview

This tool enables AI agent instances to collaborate across sessions by posting and reading messages to a shared SharePoint folder. Messages persist, enabling async task handoffs and status updates.

## Installation

```bash
cd tools/m365-collab
pip install -e .
```

## Configuration

Set these environment variables:

```bash
export M365_TENANT_ID="your-tenant-id"
export M365_CLIENT_ID="your-client-id"
export M365_CLIENT_SECRET="your-client-secret"
```

## Usage in Amplifier

Once installed and configured, the tool is available as `m365_collab`:

```python
# Check for pending tasks from other agents
m365_collab(operation="get_pending_tasks")

# Claim a task
m365_collab(operation="claim_task", task_id="msg-xxxxx")

# Complete a task
m365_collab(operation="complete_task", task_id="msg-xxxxx", result={"status": "done"})

# Post a task for other agents
m365_collab(operation="post_task", title="Review code", description="Check auth module")

# Post a status update
m365_collab(operation="post_status", title="Work Complete", status_text="Finished review")
```

## Operations

| Operation | Required Params | Description |
|-----------|-----------------|-------------|
| `get_pending_tasks` | - | Get unclaimed tasks |
| `claim_task` | `task_id` | Claim a task |
| `complete_task` | `task_id` | Mark task done |
| `post_task` | `title`, `description` | Post a new task |
| `post_status` | `title`, `status_text` | Post status update |
| `post_message` | `title`, `content` | Post general message |
| `post_handoff` | `title`, `description`, `context` | Hand off work |
| `get_messages` | - | Get recent messages |

## Azure AD App Registration

The app registration needs these API permissions:

- `Sites.ReadWrite.All` (Application) - Read/write SharePoint sites

## Message Storage

Messages are stored as JSON files in SharePoint at:
`/Shared Documents/AgentMessages/`

Each message has:
- Unique ID (e.g., `msg-abc123def456`)
- Timestamp, agent ID, type, priority, status
- Content and optional context
