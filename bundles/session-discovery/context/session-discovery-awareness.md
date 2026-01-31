# Session Discovery System

You have access to session discovery capabilities for organizing and finding past Amplifier sessions.

## Available Capabilities

- **Automatic Indexing**: Sessions are automatically indexed when they complete with descriptive names
- **Session Index**: Searchable metadata at `~/.amplifier/session-index.json`
- **Session Namer Agent**: Generates descriptive 2-5 word names for sessions

## When to Use

**Delegate to `session-discovery:session-namer` when:**
- User wants to rename or organize their session history
- User asks "what should I call this session?"
- Bulk naming operations needed

**Check the session index for:**
- "What sessions do I have from last week?"
- "Find the session where I worked on authentication"
- "What are my current projects?"
- Quick metadata lookup before full session-analyst search

## Index Format

The index at `~/.amplifier/session-index.json` contains:
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

For deep session analysis, debugging, or rewinding, delegate to `foundation:session-analyst`.

The session-discovery system provides:
- ✅ Quick metadata lookup
- ✅ Human-readable session names
- ✅ Date/project filtering

The session-analyst provides:
- ✅ Deep transcript analysis
- ✅ Event log debugging
- ✅ Session repair/rewind
- ✅ Content search across conversations

## Common Queries

**"What was I working on last week?"**
```bash
# Quick filter by date from index
cat ~/.amplifier/session-index.json | jq '.[] | select(.created >= "2026-01-23")'
```

**"What are my current projects?"**
```bash
# List unique projects
cat ~/.amplifier/session-index.json | jq -r '.[].project' | sort -u
```

**"Find sessions about authentication"**
```bash
# Search by name keyword
cat ~/.amplifier/session-index.json | jq '.[] | select(.name | contains("auth"))'
```

For deeper content searches (searching within conversation transcripts), delegate to `foundation:session-analyst`.
