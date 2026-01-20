# Amplifier Session Manager

Save and restore running Amplifier sessions across reboots. Designed for VS Code + WSL workflows.

**Supports multiple sessions per directory** - if you have multiple terminals in the same VS Code window, they'll all be saved and restored.

## What It Does

- **`amp-save-sessions`** - Finds ALL running Amplifier processes, extracts their session IDs, and saves them to numbered history
- **`amp-restore-sessions`** - Opens VS Code windows with integrated WSL terminals running `amplifier resume`

## Installation

### 1. Install the scripts

```bash
mkdir -p ~/.local/bin

# Copy scripts to your PATH
cp amp-save-sessions ~/.local/bin/
cp amp-restore-sessions ~/.local/bin/

# Make executable
chmod +x ~/.local/bin/amp-save-sessions
chmod +x ~/.local/bin/amp-restore-sessions
```

### 2. Add the bashrc trigger (REQUIRED)

Add this to the **end** of your `~/.bashrc`:

```bash
# Amplifier session restore trigger
# Supports multiple sessions per directory (pops from array)
if [[ -f /tmp/.amp-restore-triggers.json ]]; then
    _amp_cmds=$(jq -r --arg pwd "$PWD" '.[$pwd] // empty' /tmp/.amp-restore-triggers.json 2>/dev/null)
    if [[ -n "$_amp_cmds" && "$_amp_cmds" != "null" ]]; then
        # Get the first command from the array
        _amp_cmd=$(echo "$_amp_cmds" | jq -r '.[0] // empty' 2>/dev/null)
        if [[ -n "$_amp_cmd" && "$_amp_cmd" != "null" ]]; then
            # Remove the first command from the array (shift)
            jq --arg pwd "$PWD" '.[$pwd] = .[$pwd][1:]' /tmp/.amp-restore-triggers.json > /tmp/.amp-restore-triggers.json.tmp
            mv /tmp/.amp-restore-triggers.json.tmp /tmp/.amp-restore-triggers.json
            # Run the command
            eval "$_amp_cmd"
        fi
    fi
    unset _amp_cmd _amp_cmds
fi
```

### 3. (Optional) VS Code settings

To prevent the welcome tab from opening in new windows:

```json
{
    "workbench.startupEditor": "none"
}
```

## Usage

### Save sessions before rebooting

```bash
amp-save-sessions
```

Output:
```
Scanning for running Amplifier sessions...
  ✓ /mnt/c/projects/app1
    Session: abc12345...
  ✓ /mnt/c/projects/app1
    Session: def67890...
  ✓ /mnt/c/projects/app2
    Session: 3f075...

Saved 3 session(s) as save #3

  /mnt/c/projects/app1: 2 session(s) ⚡
  /mnt/c/projects/app2: 1 session(s)

History now contains 3 save(s)
```

The ⚡ indicates multiple sessions in the same directory.

### Restore sessions after reboot

```bash
# Restore the most recent save
amp-restore-sessions

# List all saves and pick one
amp-restore-sessions --list

# Restore a specific save by ID
amp-restore-sessions --id 2
```

Each directory opens a VS Code window. If a directory had multiple sessions, multiple terminals open in that window.

### List mode

```bash
amp-restore-sessions --list
```

Output:
```
Saved Session Groups:

  #3 - 2026-01-15 10:30 (3 session(s) in 2 window(s))
      /mnt/c/projects/app1: 2 terminal(s)
      /mnt/c/projects/app2: 1 terminal(s)

  #2 - 2026-01-14 18:00 (2 session(s) in 2 window(s))
      /mnt/c/projects/app1: 1 terminal(s)
      /mnt/c/projects/app2: 1 terminal(s)

Enter save ID to restore (or 'q' to quit):
```

### Preview without restoring

```bash
amp-restore-sessions --dry-run
```

## How It Works

### Save

1. Finds all running `amplifier` processes (not just bash shells)
2. For each process, extracts the session ID from:
   - Command line arguments (if explicitly provided)
   - Timing correlation with session creation
   - Recent session modification times
3. Groups sessions by directory
4. Saves to `~/.amplifier/session-history.json`

### Restore

1. Creates trigger file with **array** of commands per directory
2. Opens VS Code windows (one per unique directory)
3. Opens integrated terminals (one per session in that directory)
4. Each terminal's bashrc pops the next command from the array and runs it

## Requirements

- WSL (Windows Subsystem for Linux)
- VS Code with Remote - WSL extension
- `jq` for JSON parsing (`apt install jq`)
- Amplifier CLI installed
- The bashrc trigger snippet (see Installation step 2)

## Files

| File | Purpose |
|------|---------|
| `~/.amp-session-history.json` | All saved session groups (outside ~/.amplifier to survive reset) |
| `/tmp/.amp-restore-triggers.json` | Temporary trigger file |
| `~/.local/bin/amp-*` | The scripts |

## Troubleshooting

### "No running Amplifier sessions found"

The script looks for actual `amplifier` processes, not just open terminals. Make sure you have amplifier sessions actively running.

### Some sessions show "UNKNOWN" 

The script couldn't determine the exact session ID. On restore, these will use `amplifier resume` (resumes most recent session for that directory).

### Terminals open but don't run the resume command

1. Ensure the bashrc snippet is installed
2. Check `jq` is installed: `which jq`
3. Verify trigger file: `cat /tmp/.amp-restore-triggers.json`

### Multiple terminals but same session resumes

If you had multiple `amplifier resume` (without explicit IDs) in the same directory, they were all resuming the same session. The save script can only detect what was actually running.

## Migration

Delete any old trigger snippets from `~/.bashrc` that reference `/tmp/.amp-autorun` - the new system uses `/tmp/.amp-restore-triggers.json` with a different format.
