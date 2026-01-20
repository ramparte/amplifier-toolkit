# M365 Agent Collaboration

You have access to the `m365_collab` tool for communicating with other agent sessions.

## Overview

Messages are stored in SharePoint and persist across sessions. Use this for:
- **Tasks**: Post work for other agents to pick up
- **Status**: Share progress updates
- **Handoffs**: Transfer work between sessions

## Quick Reference

| Operation | Use For |
|-----------|---------|
| `get_pending_tasks` | Check for tasks from other agents |
| `claim_task` | Claim a task to work on |
| `complete_task` | Mark a task as done |
| `post_task` | Post a task for others |
| `post_status` | Share a status update |
| `post_handoff` | Hand off work |

## Examples

**Check for tasks:**
```
m365_collab(operation="get_pending_tasks")
```

**Claim and complete a task:**
```
m365_collab(operation="claim_task", task_id="msg-xxxxx")
# ... do the work ...
m365_collab(operation="complete_task", task_id="msg-xxxxx", result={"status": "done"})
```

**Post a new task:**
```
m365_collab(operation="post_task", title="Review auth module", description="Check for security issues")
```

**Post a status update:**
```
m365_collab(operation="post_status", title="Analysis Complete", status_text="Found 3 issues")
```

## Configuration

Requires environment variables (set before starting Amplifier):
- `M365_TENANT_ID` - Azure AD tenant ID
- `M365_CLIENT_ID` - App registration client ID
- `M365_CLIENT_SECRET` - App registration secret

If not configured, the tool will return an error explaining what's needed.
