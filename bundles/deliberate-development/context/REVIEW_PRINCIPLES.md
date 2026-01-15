# Review Principles

Principles for reviewing code, PRs, and architectural decisions. Derived from real PR review experiences where one approach was rejected in favor of a better one.

## Core Principle: Structural Prevention > Runtime Detection

When fixing behavior problems, prefer **structural prevention** (fix architecture so bad states can't happen) over **runtime detection** (monitor and warn after problems occur).

| Approach | Example | Problem |
|----------|---------|---------|
| **Runtime Detection** | Hook that warns after 30+ reads | Hours wasted before warning fires |
| **Structural Prevention** | Spec gate that stops immediately if incomplete | Fails fast, no wasted work |

**Key insight:** Runtime detection treats symptoms; structural prevention treats root causes.

### Questions to Ask

- "Does this fix prevent the problem, or just detect it?"
- "When does this solution act - before or after waste occurs?"
- "What's the failure mode - fail fast or fail slow?"

---

## Principle: Avoid Arbitrary Thresholds

Rules like "3-read rule" or "20-read checkpoint" are arbitrary and don't address **WHY** something is stuck.

**Bad pattern:**
```
If reads > 20 without writes:
    Warn user
```

**Better pattern:**
```
If specification incomplete:
    Stop immediately and ask for spec
```

### Questions to Ask

- "Why did I pick this number? Is there a principled reason?"
- "Does this threshold address root cause or just limit damage?"
- "Would fixing the actual problem eliminate the need for this threshold?"

---

## Principle: Clear Agent/Component Boundaries

Vague descriptions lead to bad delegation decisions. The coordinator/caller uses descriptions to decide what to invoke.

**Bad description:**
```
"Use PROACTIVELY for ALL implementation tasks"
```

**Good description:**
```
"Implementation-only agent. REQUIRES complete specification.

WHEN TO USE:
- Spec exists with file paths, interfaces, patterns
- Design decisions already made

WHEN NOT TO USE:
- Requirements unclear
- Design needed first
- Exploratory work"
```

### Key Guidelines

1. **First 3 lines matter most** - They survive truncation in logs/context
2. **Include WHEN NOT to use** - Prevents misuse
3. **State prerequisites upfront** - Caller knows what's needed
4. **Be specific about boundaries** - "Implementation-only" not "can do anything"

---

## Principle: Specification Gates

Require complete specifications upfront. If incomplete, STOP and ask immediately rather than guessing.

**Gate pattern:**
```
1. Check prerequisites (spec, file paths, interfaces)
2. If ANY missing → STOP immediately
3. Report what's missing clearly
4. Do NOT proceed with guesses
```

**Benefits:**
- Fails in seconds, not hours
- Clear feedback on what's needed
- No wasted work on wrong assumptions

### Specification Checklist

Before implementation, verify:
- [ ] File paths specified
- [ ] Interfaces/contracts defined
- [ ] Pattern or example provided
- [ ] Success criteria stated
- [ ] Scope boundaries clear

If any are missing, that's a STOP condition.

---

## Principle: Fix Root Causes

When reviewing a fix, ask: "Does this address why the problem happened, or just what happened?"

| Symptom | Band-aid Fix | Root Cause Fix |
|---------|--------------|----------------|
| Agent reads files forever | Add read counter + warning | Fix under-specified delegation |
| Tests fail randomly | Add retry logic | Fix the flaky condition |
| Users confused by errors | Add more error messages | Fix the confusing design |

### The "5 Whys" Test

For any proposed fix:
1. Why did this problem occur?
2. Why did THAT happen?
3. Why did THAT happen?
4. Why did THAT happen?
5. Why did THAT happen?

If your fix addresses something in the first 1-2 whys, you're treating symptoms.
If it addresses something in whys 4-5, you're treating root causes.

---

## Anti-Patterns to Flag in Review

### 1. Threshold-Based Fixes
```
"After X attempts, do Y"
"If count > N, warn"
"Limit to M iterations"
```
**Ask:** What's causing the need for limits? Fix that instead.

### 2. Detection Without Prevention
```
"Monitor for condition X and alert"
"Log when Y happens"
"Add metrics for Z"
```
**Ask:** Can we prevent X/Y/Z from happening at all?

### 3. Vague Boundaries
```
"Use this for most tasks"
"Generally applicable"
"Can handle various scenarios"
```
**Ask:** When should this NOT be used? Make it explicit.

### 4. Implicit Requirements
```
"Assumes the caller provides..."
"Works best when..."
"Expects that..."
```
**Ask:** Can we validate these upfront and fail fast if not met?

---

## Review Checklist

When reviewing code or PRs:

- [ ] **Root cause addressed?** - Not just symptoms
- [ ] **Fails fast?** - Catches issues early, not after waste
- [ ] **No arbitrary thresholds?** - Or thresholds are principled
- [ ] **Clear boundaries?** - WHEN TO USE and WHEN NOT TO USE
- [ ] **Prerequisites validated?** - Spec gates in place
- [ ] **Structural prevention?** - Bad states can't happen vs detected after

---

## Origin

These principles were extracted from the analysis of PR #28 vs PR #29 on amplifier-foundation, where a runtime-monitoring approach was rejected in favor of a structural-prevention approach. The key lesson: **it's better to make bad states impossible than to detect them after they occur.**
