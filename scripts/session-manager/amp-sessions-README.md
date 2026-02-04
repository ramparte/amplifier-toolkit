# Amplifier Session Save/Restore Tools

Tools to save and restore running Amplifier sessions across multiple VS Code windows and terminals.

## Quick Start

### Save Sessions
```bash
amp-save-sessions
```

Scans for all running Amplifier processes and saves their session IDs and directories.

### Restore Sessions
```bash
amp-restore-sessions          # Restore most recent save
amp-restore-sessions --list   # Choose from history
amp-restore-sessions --id 5   # Restore specific save
```

## Setup (Required for Auto-Run)

For terminals to automatically run `amplifier resume` when opened, add this to your `~/.bashrc`:

```bash
# Amplifier session restore - auto-run commands in new terminals
if [[ -f /tmp/.amp-restore-triggers.json ]] && [[ -n "$VSCODE_INJECTION" ]]; then
    trigger_file="/tmp/.amp-restore-triggers.json"
    cwd="$(pwd)"
    
    # Check if there's a command for this directory
    cmd=$(jq -r --arg dir "$cwd" 'if .[$dir] and (.[$dir] | length) > 0 then .[$dir][0] else "" end' "$trigger_file" 2>/dev/null)
    
    if [[ -n "$cmd" ]]; then
        # Remove the command from the queue (consume it)
        jq --arg dir "$cwd" 'if .[$dir] and (.[$dir] | length) > 0 then .[$dir] = .[$dir][1:] else . end' "$trigger_file" > "$trigger_file.tmp" && mv "$trigger_file.tmp" "$trigger_file"
        
        # Execute the command
        eval "$cmd"
    fi
fi
```

### To add this automatically:

```bash
# Backup your bashrc first
cp ~/.bashrc ~/.bashrc.backup

# Add the snippet
cat >> ~/.bashrc << 'BASHRC_EOF'

# Amplifier session restore - auto-run commands in new terminals
if [[ -f /tmp/.amp-restore-triggers.json ]] && [[ -n "$VSCODE_INJECTION" ]]; then
    trigger_file="/tmp/.amp-restore-triggers.json"
    cwd="$(pwd)"
    
    # Check if there's a command for this directory
    cmd=$(jq -r --arg dir "$cwd" 'if .[$dir] and (.[$dir] | length) > 0 then .[$dir][0] else "" end' "$trigger_file" 2>/dev/null)
    
    if [[ -n "$cmd" ]]; then
        # Remove the command from the queue (consume it)
        jq --arg dir "$cwd" 'if .[$dir] and (.[$dir] | length) > 0 then .[$dir] = .[$dir][1:] else . end' "$trigger_file" > "$trigger_file.tmp" && mv "$trigger_file.tmp" "$trigger_file"
        
        # Execute the command
        eval "$cmd"
    fi
fi
BASHRC_EOF

# Reload bashrc in current shell
source ~/.bashrc
```

## How It Works

### Save Process
1. Scans for all `amplifier` processes
2. Extracts session IDs from:
   - Command line arguments
   - Process/session timing correlation
   - Recent file modifications
   - `amplifier session list` (last resort)
3. Saves to `~/.amp-session-history.json`

### Restore Process
1. Reads saved session info from history
2. Creates a trigger file with commands for each directory
3. Opens VS Code windows (one per directory)
4. Opens terminals (one per session in that directory)
5. Bashrc snippet auto-runs `amplifier resume <session_id>` in each terminal

## Features

- **Multiple sessions per directory**: If you have 4 terminals in one VS Code window, all 4 restore in the same window
- **Session ID detection**: Tries multiple methods to identify session IDs
- **Unknown session handling**: If ID can't be determined, uses `amplifier resume` (most recent session)
- **History tracking**: All saves are preserved in `~/.amp-session-history.json`
- **Dry run**: Test with `--dry-run` to see what would happen

## Examples

### Save current work
```bash
$ amp-save-sessions
Scanning for running Amplifier sessions...
  ✓ /home/user/dev/project1
    Session: c0a98cca...
  ✓ /home/user/dev/project2
    Session: 7117442d...
  ? /home/user/dev/project3
    Session: unknown (will use most recent on restore)

Saved 3 session(s) as save #10

  /home/user/dev/project1: 1 session(s)
  /home/user/dev/project2: 1 session(s)
  /home/user/dev/project3: 1 session(s)
```

### View history
```bash
$ amp-restore-sessions --list
Saved Session Groups:

  #10 - 2026-02-04 14:36 (3 session(s) in 3 window(s))
      /home/user/dev/project1: 1 terminal(s)
        • c0a98cca...
      /home/user/dev/project2: 1 terminal(s)
        • 7117442d...
      /home/user/dev/project3: 1 terminal(s)
        • unknown (will use most recent)

  #9 - 2026-02-03 16:20 (5 session(s) in 2 window(s))
      /home/user/dev/project1: 3 terminal(s) ⚡
        • a1b2c3d4...
        • e5f6g7h8...
        • i9j0k1l2...
      /home/user/dev/project2: 2 terminal(s) ⚡
        • m3n4o5p6...
        • q7r8s9t0...
```

### Restore specific save
```bash
$ amp-restore-sessions --id 9
Restoring save #9 from 2026-02-03T16:20:00-08:00
(5 session(s) in 2 VS Code window(s))

  → /home/user/dev/project1 (3 terminal(s))
      Session: a1b2c3d4-...
      Session: e5f6g7h8-...
      Session: i9j0k1l2-...
  → /home/user/dev/project2 (2 terminal(s))
      Session: m3n4o5p6-...
      Session: q7r8s9t0-...

VS Code windows opened with terminals!
```

## Troubleshooting

### Terminals open but don't auto-run
**Problem**: VS Code terminals open but stay at bash prompt instead of running `amplifier resume`

**Solution**: Add the bashrc snippet (see Setup section above). The snippet must be in `~/.bashrc` to work.

### Session IDs show as "unknown"
**Problem**: Some sessions show as `unknown` during save

**Reasons**:
- Session was resumed without explicit ID (used `amplifier continue`)
- Process started before session files were created
- Session files are very old (>5 minutes since modification)

**Solution**: The tool will use `amplifier resume` (most recent session) for these. If you want specific IDs, note them manually or ensure you use `amplifier resume <session_id>` when starting sessions.

### No sessions found
**Problem**: `amp-save-sessions` reports "No running Amplifier sessions found"

**Checks**:
- Run `pgrep -f amplifier` to see if processes exist
- Make sure you're running Amplifier interactively (not one-off commands)
- Try running from a directory with an active Amplifier session

### VS Code windows don't open
**Problem**: Restore command runs but no VS Code windows appear

**Checks**:
- Verify `code` command works: `code --version`
- Check WSL integration: `wsl.exe -l -v`
- Ensure VS Code WSL extension is installed

## Files

- `~/.amp-session-history.json` - Persistent save history
- `/tmp/.amp-restore-triggers.json` - Temporary file for terminal auto-run (created during restore)

## Tips

- **Save often**: Run `amp-save-sessions` before shutting down or switching contexts
- **Name your sessions**: Use descriptive prompts when starting sessions to make them easier to identify in history
- **Clean up old saves**: The history file grows over time; you can manually edit `~/.amp-session-history.json` to remove old entries
