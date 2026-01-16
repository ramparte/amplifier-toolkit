# Amplifier Session Manager

Save and restore running Amplifier sessions across reboots. Designed for VS Code + WSL workflows.

## What It Does

- **`amp-save-sessions`** - Scans for running Amplifier processes, captures their session IDs and working directories, appends to a numbered history
- **`amp-restore-sessions`** - Restores sessions from history; defaults to most recent, or lets you pick from past saves

## Installation

### 1. Install the scripts

```bash
# Clone this repo (or just download the scripts)
mkdir -p ~/.local/bin

# Copy scripts to your PATH
cp amp-save-sessions ~/.local/bin/
cp amp-restore-sessions ~/.local/bin/

# Make executable
chmod +x ~/.local/bin/amp-save-sessions
chmod +x ~/.local/bin/amp-restore-sessions
```

### 2. Add auto-run trigger to your shell

Add this to the **end** of your `~/.bashrc`:

```bash
# Auto-run amplifier commands from trigger file
if [[ -f /tmp/.amp-autorun ]]; then
    cmd=$(cat /tmp/.amp-autorun)
    rm /tmp/.amp-autorun
    eval "$cmd"
fi
```

### 3. (Optional) VS Code settings

To prevent the explorer pane from opening in new windows, add to your VS Code settings (Ctrl+Shift+P → "Preferences: Open User Settings (JSON)"):

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
Saved 2 session(s) as save #3

  /mnt/c/projects/app1 → abc123-session-id
  /mnt/c/projects/app2 → def456-session-id

History now contains 3 save(s)
To restore, run: amp-restore-sessions (latest) or amp-restore-sessions --list (pick one)
```

Each save is numbered and preserved in history. You can save multiple times without losing previous saves.

### Restore sessions after reboot

```bash
# Restore the most recent save (default)
amp-restore-sessions

# List all saves and pick one
amp-restore-sessions --list

# Restore a specific save by ID
amp-restore-sessions --id 2
```

### List mode

```bash
amp-restore-sessions --list
```

Output:
```
Saved Session Groups:

  #3 - 2026-01-15 10:30 (2 session(s))
      /mnt/c/projects/app1
      /mnt/c/projects/app2

  #2 - 2026-01-14 18:00 (3 session(s))
      /mnt/c/projects/app1
      /mnt/c/projects/app2
      /mnt/c/projects/app3

  #1 - 2026-01-13 09:15 (1 session(s))
      /mnt/c/projects/app1

Enter save ID to restore (or 'q' to quit):
```

### Preview without restoring

```bash
amp-restore-sessions --dry-run
amp-restore-sessions --list --dry-run
```

## How It Works

1. **Save**: Scans `/proc` for running Amplifier processes, extracts working directories and session IDs, appends a numbered entry to `~/.amplifier/session-history.json`

2. **Restore**: For each session in the selected save:
   - Writes the resume command to `/tmp/.amp-autorun`
   - Opens VS Code with `code --new-window --remote wsl+<distro> <directory>`
   - VS Code opens a terminal, which sources `~/.bashrc`
   - The bashrc trigger reads and executes the command, then deletes the trigger file

## Requirements

- WSL (Windows Subsystem for Linux)
- VS Code with Remote - WSL extension
- `jq` for JSON parsing (install via `apt install jq`)
- Amplifier CLI installed

## Files

| File | Purpose |
|------|---------|
| `~/.amplifier/session-history.json` | All saved session groups (numbered) |
| `/tmp/.amp-autorun` | Temporary trigger file (auto-deleted) |
| `~/.local/bin/amp-*` | The scripts |

## Migration from Old Format

If you have an existing `~/.amplifier/saved-sessions.json` from the old single-save format, you can safely delete it. The new scripts use `session-history.json` with a different structure that supports multiple saves.
