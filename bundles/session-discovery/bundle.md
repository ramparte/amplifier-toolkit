---
bundle:
  name: session-discovery
  version: 1.0.0
  description: Session discovery and organization for Amplifier - auto-naming, indexing, and search

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: session-discovery:behaviors/session-discovery
---

# Session Discovery

Automatically index, name, and search your Amplifier sessions.

## What It Provides

**Automatic Session Indexing:**
- Sessions are indexed when they complete
- Quick heuristic names from first user message
- Metadata stored at `~/.amplifier/session-index.json`

**Session Namer Agent:**
- Generates descriptive 2-5 word session names
- Analyzes conversation transcripts for themes
- Available for manual naming or bulk operations

**Quick Discovery:**
- "What was I working on last week?"
- "What are my current projects?"
- "Find sessions about authentication"

## How It Works

When a session completes:
1. **Hook observes** `session:end` event
2. **Quick naming** extracts first user message (fast, good enough)
3. **Index updated** at `~/.amplifier/session-index.json` with metadata

For better names, use the `session-namer` agent manually.

## Usage

**Natural queries work automatically:**
```
"What was I working on last week?"
"What are my current projects?"
"Find sessions about authentication"
```

The system will check the index first for quick metadata filtering, then delegate to `session-analyst` for deeper content search if needed.

**Manual naming:**
```
"Use session-namer to name this session"
"Use session-namer to generate better names for my last 5 sessions"
```

## Index Structure

Sessions are indexed at `~/.amplifier/session-index.json`:

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

## Integration with session-analyst

This bundle **complements** the existing `session-analyst` agent:

| Task | System | Why |
|------|--------|-----|
| Quick lookup by name/date/project | **session-discovery** (index) | Fast metadata filter |
| Deep conversation analysis | **session-analyst** (grep) | Full content search |
| Session debugging/repair | **session-analyst** (exclusive) | Event log expertise |
| Auto-naming on completion | **session-discovery** (hook) | Lifecycle automation |

## Components

- **hook-session-indexer** - Observes session:end events, maintains index
- **session-namer agent** - Generates descriptive names from transcripts
- **session-discovery behavior** - Composes hook + agent + awareness context

## Installation

**Via amplifier-toolkit:**
```yaml
includes:
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/session-discovery
```

**Standalone:**
```yaml
includes:
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/session-discovery
```

---

@session-discovery:context/session-discovery-awareness.md

---

@foundation:context/shared/common-system-base.md
