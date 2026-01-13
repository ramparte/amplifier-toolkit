# Amplifier Session Manager

Save and restore running Amplifier sessions across reboots. Designed for VS Code + WSL workflows.

## What It Does

- **`amp-save-sessions`** - Scans for running Amplifier processes, captures their session IDs and working directories
- **`amp-restore-sessions`** - Opens a VS Code window for each saved session and automatically resumes them

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
Saved 2 session(s) to /home/user/.amplifier/saved-sessions.json

  /mnt/c/projects/app1 → abc123-session-id
  /mnt/c/projects/app2 → def456-session-id

To restore these sessions later, run: amp-restore-sessions
```

### Restore sessions after reboot

```bash
amp-restore-sessions
```

This opens a VS Code window for each saved session, with the terminal automatically running `amplifier session resume <id>`.

### Preview without restoring

```bash
amp-restore-sessions --dry-run
```

## How It Works

1. **Save**: Scans `/proc` for running Amplifier processes, extracts working directories and session IDs, saves to `~/.amplifier/saved-sessions.json`

2. **Restore**: For each saved session:
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
| `~/.amplifier/saved-sessions.json` | Saved session data |
| `/tmp/.amp-autorun` | Temporary trigger file (auto-deleted) |
| `~/.local/bin/amp-*` | The scripts |
