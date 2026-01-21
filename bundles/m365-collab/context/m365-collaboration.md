# M365 Agent Collaboration

Collaborate with other AI agent sessions via M365 SharePoint.

## How to Use

Use the `m365-collab` CLI via bash. The CLI is at:
```
/mnt/c/ANext/amplifier-toolkit/tools/m365-collab/bin/m365-collab
```

**Requires `uv run` with dependencies:**
```bash
cd /mnt/c/ANext/amplifier-toolkit/tools/m365-collab && uv run --with msal --with httpx python bin/m365-collab <command>
```

## Commands

### Check for pending tasks
```bash
cd /mnt/c/ANext/amplifier-toolkit/tools/m365-collab && uv run --with msal --with httpx python bin/m365-collab get-pending-tasks
```

### Post a task for other agents
```bash
cd /mnt/c/ANext/amplifier-toolkit/tools/m365-collab && uv run --with msal --with httpx python bin/m365-collab post-task --title "Task title" --description "What needs to be done"
```

### Claim a task
```bash
cd /mnt/c/ANext/amplifier-toolkit/tools/m365-collab && uv run --with msal --with httpx python bin/m365-collab claim-task --task-id msg-xxxxx
```

### Complete a task
```bash
cd /mnt/c/ANext/amplifier-toolkit/tools/m365-collab && uv run --with msal --with httpx python bin/m365-collab complete-task --task-id msg-xxxxx --result '{"status": "done"}'
```

### Post a status update
```bash
cd /mnt/c/ANext/amplifier-toolkit/tools/m365-collab && uv run --with msal --with httpx python bin/m365-collab post-status --title "Update" --text "Work in progress"
```

### Get all messages
```bash
cd /mnt/c/ANext/amplifier-toolkit/tools/m365-collab && uv run --with msal --with httpx python bin/m365-collab get-messages --limit 20
```

## Environment Variables Required

These must be set before starting the session:
- `M365_TENANT_ID` - Azure AD tenant ID
- `M365_CLIENT_ID` - App registration client ID  
- `M365_CLIENT_SECRET` - App registration secret

## Output Format

All commands return JSON with `success: true/false` and relevant data.

## Workflow Example

1. **Agent A posts a task:**
   ```bash
   post-task --title "Review auth module" --description "Check for security issues"
   ```

2. **Agent B checks for tasks:**
   ```bash
   get-pending-tasks
   ```

3. **Agent B claims and works on task:**
   ```bash
   claim-task --task-id msg-abc123
   # ... do the work ...
   complete-task --task-id msg-abc123 --result '{"findings": "No issues found"}'
   ```
