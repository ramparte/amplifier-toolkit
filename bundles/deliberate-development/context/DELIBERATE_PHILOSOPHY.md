# Deliberate Development Philosophy

This document captures the core philosophy of deliberate development - a mindful, decomposition-first approach to software engineering with AI assistance.

## Core Tenets

### 1. Decompose Before You Build

Never jump straight to implementation. Every task deserves analysis:

- **Break down the problem** into manageable pieces
- **Leave room for insight** - space between turns lets ideas emerge
- **Generalize when patterns appear** - "what else could benefit from this?"
- **4-5 planning turns, then one "go do it" turn**

The best solutions often come from the "oooh, you know what else would be smart" moments that only happen when you're not rushing.

### 2. Ephemeral Workspaces, Persistent Learning

**Workspaces are throwaway. Knowledge persists.**

- Create a fresh workspace for each focused task
- Initialize local git for safety (commits for rollback, never pushed)
- Keep notes in AGENTS.md as working memory
- Destroy the workspace when done - session history survives
- Never return to old sessions for improvements - start fresh

This prevents context pollution and forces clear scoping.

### 3. Scope Ruthlessly

A "task" is ambitious but focused:

- One feature, one workspace
- Can be "pretty decent sized" but has clear boundaries
- Completes in a single working session
- Small enough that Sonnet can handle it well

If you're thinking "I'll come back to this later" - you've scoped too big.

### 4. Validation is Implicit

Testing isn't a separate step - it's baked into expectation:

- "Go do it" means "implement AND validate"
- Kick the tires after publishing
- If it doesn't work, that's a bug - start a new session
- Don't batch validation at the end

### 5. Stay Current, Stay Fresh

- Pull updates frequently (amplifier update between sessions)
- When resuming after changes: pull latest, assess impact
- Exit and resume to get benefits of new updates
- Game-changer improvements happen regularly

### 6. Modes Over Monoliths

Instead of one-off features, think in generalizable modes:

- **Planning mode** - tool restrictions, context injection, visual indicators
- **Implementation mode** - full access, validation expected
- **Review mode** - analysis only, no changes

Each mode is: command + instruction + rules-for-tools + context injection

## The Deliberate Development Cycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. CREATE WORKSPACE                                        │
│     Fresh directory, local git, repos as submodules         │
├─────────────────────────────────────────────────────────────┤
│  2. DECOMPOSE THE PROBLEM                                   │
│     4-5 turns of analysis and design                        │
│     Look for generalization opportunities                   │
│     Create clear specifications                             │
├─────────────────────────────────────────────────────────────┤
│  3. IMPLEMENT                                               │
│     One "go do it" turn with validation implicit            │
│     Leverage existing patterns and tools                    │
├─────────────────────────────────────────────────────────────┤
│  4. VALIDATE                                                │
│     Kick the tires in real usage                            │
│     If issues found, that's a new task                      │
├─────────────────────────────────────────────────────────────┤
│  5. DESTROY WORKSPACE                                       │
│     Clean up, session history preserved                     │
│     Start fresh for any follow-up work                      │
└─────────────────────────────────────────────────────────────┘
```

## Anti-Patterns to Avoid

### The Marathon Session
- Working in one session for hours/days
- Context becomes polluted
- Decisions compound on stale assumptions

**Instead:** Focused sessions, throw away, start fresh.

### The Immediate Implementation
- User asks for feature → start coding
- No analysis of alternatives
- No consideration of generalization

**Instead:** Decompose first. "Let me analyze this problem and design the solution."

### The Eternal Session
- Returning to old sessions for improvements
- Building on top of accumulated cruft
- "Just one more thing" syndrome

**Instead:** New task = new session. Always.

### The Deferred Validation
- "I'll test it when I'm done"
- Batching validation at the end
- Hoping it works

**Instead:** Validation is implicit in "do it". Not a separate step.

## Practical Patterns

### The Working Memory Pattern

Use AGENTS.md as a scratchpad:
- Current task and context
- Key decisions made and why
- Things discovered during exploration
- What to preserve vs what to discard

### The Submodule Pattern

Keep reference repos accessible:
- Add as git submodules (not cloned copies)
- Read docs and code for context
- Don't modify - reference only
- Pull latest when needed

### The Exit-Update-Resume Pattern

Stay current without losing context:
1. Exit Amplifier session
2. Run `amplifier update`
3. Resume session with `amplifier resume`
4. Continue with benefits of updates

### The Desktop Notification Pattern

Leverage async workflows:
- Start task, give initial instruction
- Do something else while it works
- Desktop notification tells you it's ready
- Review and iterate

## Decision Framework

When faced with implementation choices:

1. **Is this the simplest approach?** - If not, simplify
2. **Could this be more general?** - Look for mode/pattern extraction
3. **Am I solving today's problem?** - Not hypothetical future problems
4. **Would a fresh session help?** - Context pollution check
5. **Have I decomposed enough?** - 4-5 turns of analysis?

## The Workspace Philosophy

**Why throwaway workspaces work:**

1. **Fresh context** - No accumulated assumptions
2. **Clear scope** - One task, one workspace
3. **Forced clarity** - Must define task upfront
4. **Easy cleanup** - Delete dir, done
5. **Preserved history** - Session logs survive in ~/.amplifier/projects

**The workspace contains:**
- Git repo (local only, for safety)
- Submodules for reference repos
- AGENTS.md for working memory
- .amplifier/settings.yaml for configuration

**The workspace does NOT contain:**
- Permanent artifacts (push to real repos)
- Long-term notes (use proper documentation)
- Reusable tools (extract to proper packages)

## Remember

> "It's easier to add complexity later than to remove it."
> 
> "Code you don't write has no bugs."
> 
> "The best design is often the simplest."

Deliberate development is about **intentional constraint**:
- Constrain scope to enable depth
- Constrain session length to force clarity  
- Constrain validation to be implicit
- Constrain workspaces to be ephemeral

These constraints paradoxically enable more ambitious, more capable, more reliable outcomes.
