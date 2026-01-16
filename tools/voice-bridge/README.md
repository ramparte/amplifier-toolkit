# Amplifier Voice Bridge

Control your Amplifier sessions via voice from your iPhone using Siri Shortcuts.

## Overview

The Voice Bridge lets you:
- **Query sessions**: "What sessions are running?", "What's the status of carplay?"
- **Check work**: "What's being worked on?", "What are the tasks for brian?"
- **Execute prompts**: Send commands to running sessions (requires Amplifier bridge)

## Architecture

```
iPhone (Siri Shortcut)
    │
    │ HTTP POST /chat
    ▼
Voice Bridge Server (Python)
    │
    ├── Session Discovery (reads ~/.amplifier/sessions/)
    ├── Voice Command Parser (NLP for voice queries)
    └── Amplifier Bridge (optional, for execution)
```

## Quick Start

### 1. Start the Server

```bash
cd tools/voice-bridge
python3 standalone_server.py --port 8765
```

### 2. Set Up Tailscale (for remote access)

The server runs on your local machine. To access it from your phone:

1. Install [Tailscale](https://tailscale.com/) on both your computer and iPhone
2. Get your Tailscale IP: `tailscale ip -4`
3. Use that IP in the iOS Shortcut

### 3. Create iOS Shortcut

Create a new Shortcut with these actions:

1. **Dictate Text** - Captures your voice
2. **Get Contents of URL**:
   - URL: `http://YOUR_TAILSCALE_IP:8765/chat`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Body (JSON):
     ```json
     {
       "prompt": "[Dictated Text]",
       "max_response_length": 500
     }
     ```
3. **Get Dictionary Value** - Key: `text`
4. **Speak Text** - Speaks the response

### 4. Add to CarPlay

In the Shortcuts app, enable "Show in CarPlay" for your shortcut.

## Voice Commands

| Command | Example | Response |
|---------|---------|----------|
| List sessions | "What sessions are running?" | "3 sessions: carplay, brian, ANext" |
| Session status | "What's the status of carplay?" | "carplay is running. Last request: ..." |
| Check todos | "What are the tasks for brian?" | Lists todo items |
| Current work | "What's being worked on?" | Shows in-progress tasks |
| Help | "Help" | Lists available commands |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check, shows running sessions |
| `/sessions` | GET | List all Amplifier sessions (JSON) |
| `/chat` | POST | Process voice command |

### POST /chat

```bash
curl -X POST http://localhost:8765/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What sessions are running?"}'
```

Response:
```json
{
  "text": "3 sessions running: carplay, brian, ANext.",
  "session_id": "default",
  "truncated": false,
  "execution_time": 0.05
}
```

## Full Amplifier Integration

By default, the server can only **read** session state. To enable **executing prompts**:

### Option 1: Run server from Amplifier session

```bash
amplifier run "Start the voice bridge server"
# Then in the session, run: python3 standalone_server.py
```

### Option 2: Install amplifier-foundation

```bash
pip install -e ~/.amplifier/cache/amplifier-foundation-*/
```

With the bridge enabled, you can:
- Continue existing sessions: "Tell carplay to check the test results"
- Execute new work: "Create a session to research async patterns"

## Files

| File | Purpose |
|------|---------|
| `standalone_server.py` | HTTP server (no Amplifier dependency) |
| `src/session_discovery.py` | Finds and reads Amplifier sessions |
| `src/voice_commands.py` | Natural language command parsing |
| `src/command_handler.py` | Routes commands to handlers |
| `src/amplifier_bridge.py` | Optional Amplifier execution |

## Requirements

- Python 3.10+
- Tailscale (for iPhone access)
- Running Amplifier sessions to query

## License

MIT
