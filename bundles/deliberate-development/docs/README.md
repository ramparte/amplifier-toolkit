# Deliberate Development Bundle

A mindful, decomposition-first approach to software engineering with AI assistance.

## Installation

```bash
# Add the bundle
amplifier bundle add ./deliberate-development

# Or reference directly
amplifier run --bundle ./deliberate-development
```

## Quick Start

### Use the Agents Directly

**For planning and design:**
```
"Use deliberate-planner to analyze this feature"
"Help me decompose this problem using deliberate-planner"
```

**For implementation:**
```
"Use deliberate-implementer to build this specification"
```

### Use the Recipes

**Quick design workflow:**
```
"Run the deliberate-design recipe for: [your feature]"
```

**Full feature lifecycle:**
```
"Run feature-development for: [feature] in [repo]"
```

## Core Philosophy

1. **Decompose before building** - 4-5 planning turns before implementation
2. **Ephemeral workspaces** - Fresh workspace per task
3. **Validation is implicit** - "Done" means "verified working"
4. **Leave room for insight** - Space between turns lets ideas emerge
5. **Generalize when patterns appear** - Look for "what else" opportunities

## Bundle Contents

```
deliberate-development/
├── bundle.md                    # Main bundle definition
├── agents/
│   ├── deliberate-planner.md    # Decomposition-first planning
│   └── deliberate-implementer.md # Specification-based implementation
├── behaviors/
│   └── planning-mode.yaml       # Planning mode restrictions
├── context/
│   ├── DELIBERATE_PHILOSOPHY.md # Core philosophy document
│   └── planning-mode-instructions.md
├── recipes/
│   ├── deliberate-design.yaml   # Design workflow recipe
│   └── feature-development.yaml # Full lifecycle recipe
└── docs/
    └── README.md                # This file
```

## Agents

### deliberate-planner

The planning agent that ensures thorough decomposition before implementation:

- Breaks problems into components
- Explores 2-3 alternative approaches
- Identifies generalization opportunities
- Creates clear specifications
- Hands off to implementer (does NOT code)

### deliberate-implementer

The implementation agent that builds from specifications:

- Requires clear specification to start
- Builds exactly what's specified
- Validates as it goes (not after)
- Reports complete only when verified
- Does NOT plan (requires specification input)

### deliberate-reviewer

The review agent that applies structural prevention principles:

- Reviews PRs, code changes, and architectural decisions
- Checks for anti-patterns (arbitrary thresholds, vague boundaries, etc.)
- Applies "5 Whys" analysis for root cause assessment
- Prefers structural prevention over runtime detection
- Generates actionable recommendations

## Recipes

### deliberate-design

5-step design workflow:
1. Decompose the problem
2. Explore 2-3 alternatives
3. Check for generalization
4. Create specification
5. Implement with validation

### deliberate-review

Systematic principled review:
1. Gather review context
2. Structural prevention analysis
3. Anti-pattern detection
4. Generate recommendations

### feature-development

8-step full lifecycle:
1. Setup workspace context
2. Decompose the feature
3. Explore solutions
4. Generalization check
5. Create specification
6. Implement
7. Validate integration
8. Summarize for handoff

## The Key Insight

The generalization step is what makes this "deliberate":

> Started with: "Add a plan mode with tool restrictions"
>
> Generalized to: "A modes system where any mode is: command + instruction + rules"
>
> Result: Instead of one feature, got a flexible framework

This only happens when you leave room for the "oooh, what else would be smart" moments.

## Integration

Works alongside foundation agents:
- **zen-architect** - Complex architecture
- **modular-builder** - Brick-style modules
- **bug-hunter** - Debug issues
- **explorer** - Codebase reconnaissance

## License

MIT
