# Session Discovery Bundle

Automatic session indexing, naming, and discovery for Amplifier - inspired by [Freshell](https://github.com/danshapiro/freshell)'s session browsing capabilities.

## Features

- **Automatic Indexing** - Sessions indexed when they complete with descriptive names
- **Quick Discovery** - "What was I working on last week?" just works
- **Project Organization** - "What are my current projects?" returns immediate answers
- **Session Namer Agent** - Generate better names for sessions on demand
- **Complements session-analyst** - Fast metadata filtering + deep content search

## Quick Start

Include in your bundle:

```yaml
includes:
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/session-discovery
```

Then just use naturally:
```
"What was I working on last week?"
"What are my current projects?"
"Find sessions about authentication"
```

## How It Works

### Automatic Indexing

When a session completes:
1. Hook observes `session:end` event
2. Extracts first user message as quick name
3. Updates index at `~/.amplifier/session-index.json`

### Manual Naming

For better names:
```
"Use session-namer to name this session"
"Generate better names for my last 5 sessions"
```

## Components

```
session-discovery/
├── agents/
│   └── session-namer.md           # AI-powered session naming
├── behaviors/
│   └── session-discovery.yaml     # Behavior composition
├── context/
│   └── session-discovery-awareness.md  # Thin pointer
├── modules/
│   └── hook-session-indexer/      # Hook module for auto-indexing
└── bundle.md                      # Root bundle
```

## Integration with session-analyst

| Task | System | Why |
|------|--------|-----|
| Quick lookup by name/date/project | **session-discovery** | Fast metadata filter |
| Deep conversation analysis | **session-analyst** | Full content search |
| Session debugging/repair | **session-analyst** | Event log expertise |

## Index Format

`~/.amplifier/session-index.json`:

```json
[
  {
    "session_id": "abc123...",
    "name": "API Authentication Implementation",
    "project": "myapp",
    "created": "2026-01-30T10:00:00",
    "bundle": "foundation",
    "model": "claude-sonnet-4-5",
    "turn_count": 25,
    "path": "/home/user/.amplifier/projects/myapp/sessions/abc123...",
    "indexed_at": "2026-01-30T10:30:00"
  }
]
```

## Philosophy

This bundle follows Amplifier's thin bundle pattern:

- ✅ **Context sink** - Heavy naming logic in agent, thin pointer in behavior
- ✅ **Hook-based automation** - Non-blocking session lifecycle observation
- ✅ **Composable** - Include the behavior, get the capability
- ✅ **Complements existing** - Works with session-analyst, doesn't replace it

## Inspiration

Inspired by [Freshell](https://github.com/danshapiro/freshell)'s "speak with the dead" feature - making past sessions discoverable and searchable.

## License

MIT
