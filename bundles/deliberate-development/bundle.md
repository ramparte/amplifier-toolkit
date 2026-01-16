---
bundle:
  name: deliberate-development
  version: 1.0.0
  description: Deliberate development workflow - decomposition-first thinking, ephemeral workspaces, and validation-implicit implementation

includes:
  # Foundation provides core tools and agents
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  # Planning mode behavior
  - bundle: deliberate-development:behaviors/planning-mode

agents:
  include:
    - deliberate-development:deliberate-planner
    - deliberate-development:deliberate-implementer
    - deliberate-development:deliberate-reviewer
    - deliberate-development:deliberate-debugger
---

# Deliberate Development

A mindful, decomposition-first approach to software engineering with AI assistance.

@deliberate-development:context/DELIBERATE_PHILOSOPHY.md

---

## Core Principles

1. **Decompose before you build** - 4-5 planning turns, then one "go do it" turn
2. **Ephemeral workspaces** - Fresh workspace per task, destroy when done
3. **Validation is implicit** - "Done" means "verified working"
4. **Leave room for insight** - Space between turns lets ideas emerge
5. **Generalize when patterns appear** - Look for the "what else" opportunities

## Available Agents

### deliberate-planner

Use for decomposition and design:

```
"Use the deliberate-planner to analyze this feature request"
"Have the deliberate-planner explore solution alternatives"
"Ask deliberate-planner to look for generalization opportunities"
```

The planner:
- Decomposes problems into components
- Explores 2-3 alternative approaches
- Looks for generalization opportunities
- Creates clear specifications
- Does NOT implement (hands off to implementer)

### deliberate-implementer

Use for focused implementation:

```
"Use the deliberate-implementer to build this specification"
"Have deliberate-implementer implement and validate"
```

The implementer:
- Builds from specifications exactly
- Validates as it goes (not after)
- Reports complete only when verified
- Does NOT plan (requires specification input)

### deliberate-debugger

Use for issue investigation and resolution:

```
"Use deliberate-debugger to investigate this error"
"Have deliberate-debugger find the root cause of this bug"
```

The debugger:
- Investigates before taking action
- Finds exact root cause with file:line references
- Uses evidence-based testing (specific proof requirements)
- Follows the 6-phase workflow with two approval gates
- Does NOT guess - investigates until certain

## Available Recipes

### deliberate-design

Full design workflow: decompose -> explore -> generalize -> specify -> implement

```
"Run the deliberate-design recipe for: add a caching layer"
"Execute deliberate-design with feature_description='implement plan mode'"
```

Steps:
1. **decompose** - Break down the problem
2. **explore** - Consider 2-3 alternatives
3. **generalize** - Look for pattern opportunities
4. **specify** - Create implementation specification
5. **implement** - Build with validation implicit

### feature-development

Complete feature lifecycle: setup -> design -> implement -> validate -> cleanup

```
"Run the feature-development recipe for: new-feature in amplifier-app-cli"
"Execute feature-development with feature_name='plan-mode' repo='amplifier-app-cli'"
```

Steps:
1. **setup-context** - Gather relevant codebase context
2. **decompose** - Break down the feature
3. **explore-solutions** - Analyze alternatives
4. **generalization-check** - The key insight step
5. **create-spec** - Complete specification
6. **implement** - Build with validation
7. **validate** - Verify integration
8. **summarize** - Document for handoff

### issue-resolution

Systematic bug fixing: reconnaissance -> root cause -> fix -> shadow test -> push

```
"Run the issue-resolution recipe for: No providers mounted error"
"Execute issue-resolution with issue='tests failing after recent change'"
```

Stages (with approval gates):
1. **Investigation** (reconnaissance, root cause analysis)
2. **GATE 1** - User approves approach before implementation
3. **Implementation** (make fix, commit locally)
4. **Testing** (define evidence, shadow test)
5. **GATE 2** - User approves before push
6. **Finalization** (push, smoke test, document)

## The Deliberate Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. CREATE WORKSPACE                                        │
│     "I'm starting work on [feature]"                        │
├─────────────────────────────────────────────────────────────┤
│  2. DECOMPOSE (deliberate-planner)                          │
│     "Help me break down this problem"                       │
│     "What are the components here?"                         │
├─────────────────────────────────────────────────────────────┤
│  3. EXPLORE (deliberate-planner)                            │
│     "What are our options?"                                 │
│     "Compare these approaches"                              │
├─────────────────────────────────────────────────────────────┤
│  4. GENERALIZE (deliberate-planner)                         │
│     "Could this be more general?"                           │
│     "What else could benefit from this?"                    │
├─────────────────────────────────────────────────────────────┤
│  5. IMPLEMENT (deliberate-implementer)                      │
│     "Here's the spec, go build it"                          │
│     One turn, validation implicit                           │
├─────────────────────────────────────────────────────────────┤
│  6. CLEANUP                                                 │
│     Push to real repos, destroy workspace                   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Commands

**Start deliberate planning:**
```
"Use deliberate-planner to analyze: [your feature/problem]"
```

**Run full design workflow:**
```
"Run the deliberate-design recipe for: [your feature]"
```

**Run complete feature lifecycle:**
```
"Run feature-development for: [feature] in [repo]"
```

**Direct implementation (when spec exists):**
```
"Use deliberate-implementer to build: [specification]"
```

## Anti-Patterns This Bundle Prevents

| Anti-Pattern | Deliberate Alternative |
|--------------|----------------------|
| Jump to implementation | Decompose first (4-5 turns) |
| One mega-session | Ephemeral workspaces |
| "Test it later" | Validation is implicit |
| Single approach | Explore 2-3 alternatives |
| One-off solutions | Look for generalization |
| Returning to old sessions | Fresh start for new work |

## Integration with Foundation Agents

This bundle works alongside foundation agents:

- **zen-architect** - For complex architectural decisions
- **modular-builder** - For brick-style module implementation
- **bug-hunter** - When validation reveals issues
- **explorer** - For codebase reconnaissance
- **shadow-operator** - For isolated testing environments
- **shadow-smoke-test** - For independent validation
- **git-ops** - For commits and pushes with safety protocols

The deliberate agents provide the **workflow discipline**, while foundation agents provide **domain expertise**.

### Issue Handling Workflow

When bugs or errors arise, use the issue-resolution recipe or deliberate-debugger agent:

```
User reports error → deliberate-debugger investigates → GATE 1 approval
→ implement fix → shadow test → GATE 2 approval → push → smoke test
```

Key principles from @deliberate-development:context/ISSUE_HANDLING.md:
- **Investigation before action** - Never code until you understand completely
- **Evidence-based testing** - Define proof requirements BEFORE testing
- **User time is sacred** - Present complete solutions, not partial findings

## Philosophy Summary

> "The best implementation comes from thorough decomposition."
>
> "Leave room for insight - the 'oooh what else' moments."
>
> "4-5 planning turns is not overhead - it's investment."
>
> "Validation is implicit - 'done' means 'verified working'."
>
> "Fresh workspace, fresh context, clear scope."

---

@foundation:context/shared/common-system-base.md
