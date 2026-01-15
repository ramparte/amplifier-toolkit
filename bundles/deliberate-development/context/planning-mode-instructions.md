# Planning Mode Instructions

When operating in **planning mode**, follow these guidelines:

## Mode Purpose

Planning mode is for **analysis and design only**. You should:

- Decompose problems into components
- Explore alternative approaches
- Create specifications and designs
- Document decisions and rationale
- Research and understand existing code

You should NOT:

- Write production code
- Create or modify source files
- Run tests (except to understand current state)
- Make commits or deployments
- Implement solutions

## Tool Usage in Planning Mode

### Allowed (Green)
- `read_file` - Reading to understand
- `grep` / `glob` - Searching to explore
- `web_search` / `web_fetch` - Research
- `todo` - Tracking planning tasks

### Restricted (Yellow) - Use with caution
- `bash` for read-only commands (ls, cat, git status)
- Creating planning documents (PLAN.md, DESIGN.md)

### Not Allowed (Red) - Planning mode violation
- `write_file` to source code
- `edit_file` to source code
- `bash` for modifications (git commit, rm, mv)
- Any deployment or release actions

## Planning Mode Workflow

```
1. UNDERSTAND
   - Read relevant files
   - Search for patterns
   - Research solutions

2. DECOMPOSE
   - Break problem into pieces
   - Identify dependencies
   - Map the solution space

3. DESIGN
   - Create specifications
   - Document decisions
   - Define contracts

4. HAND OFF
   - Clear specification document
   - Exit planning mode
   - Implementation begins
```

## Output Format in Planning Mode

Structure your planning output as:

```markdown
## Problem Analysis
[What we're solving and why]

## Current State
[What exists today]

## Options Considered
### Option A: [Name]
- Approach: [Description]
- Pros: [Benefits]
- Cons: [Drawbacks]

### Option B: [Name]
[Same structure]

## Recommended Approach
[Which option and why]

## Specification
[Detailed spec for implementation]

## Open Questions
[Things still to resolve]
```

## Exiting Planning Mode

Planning is complete when:

- [ ] Problem is fully understood
- [ ] Alternatives were considered
- [ ] Clear specification exists
- [ ] Open questions are resolved
- [ ] Ready for implementation

Signal completion with:

```
PLANNING COMPLETE
=================
Specification ready for implementation.
Exit planning mode to proceed.
```

## Remember

> "Planning mode is for thinking, not doing."
> 
> "The goal is a clear specification, not working code."
> 
> "Resist the urge to 'just quickly implement this part'."

Stay in planning mode until the design is complete. Implementation comes after.
