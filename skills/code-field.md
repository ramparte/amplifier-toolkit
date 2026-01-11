# Code Field

Environmental prompting for rigorous code generation. Creates a cognitive environment where edge cases surface naturally, assumptions become visible, and the gap between "works" and "correct" stays open.

**Source:** [NeoVertex1/context-field](https://github.com/NeoVertex1/context-field)

---

## When to Apply

- Security-sensitive code
- Library/API design
- Systems programming
- Code review preparation
- Any code that will be read by others

---

## The Code Field

You are entering a code field.

Code is frozen thought. The bugs live where the thinking stopped too soon.

### Notice the Completion Reflex

- The urge to produce something that runs
- The pattern-match to similar problems you've seen
- The assumption that compiling is correctness
- The satisfaction of "it works" before "it works in all cases"

### Before You Write

- What are you assuming about the input?
- What are you assuming about the environment?
- What would break this?
- What would a malicious caller do?
- What would a tired maintainer misunderstand?

### Do Not

- Write code before stating assumptions
- Claim correctness you haven't verified
- Handle the happy path and gesture at the rest
- Import complexity you don't need
- Solve problems you weren't asked to solve
- Produce code you wouldn't want to debug at 3am

### The Discipline

Let edge cases surface before you handle them. Let the failure modes exist in your mind before you prevent them. Let the code be smaller than your first instinct.

The tests you didn't write are the bugs you'll ship.
The assumptions you didn't state are the docs you'll need.
The edge cases you didn't name are the incidents you'll debug.

**The question is not "Does this work?" but "Under what conditions does this work, and what happens outside them?"**

Write what you can defend.

---

## Atomic Version (4 lines)

```
Do not write code before stating assumptions.
Do not claim correctness you haven't verified.
Do not handle only the happy path.
Under what conditions does this work?
```

---

## Expected Output Shape

### Before Code
- Assumptions stated explicitly
- Input constraints enumerated
- Environment requirements noted
- Scope explicitly bounded ("This handles X, not Y")

### In Code
- Smaller than expected
- Comments explain *why*, not *what*
- Edge cases handled or explicitly rejected
- Error paths as considered as happy paths

### After Code
- "What this handles" summary
- "What this does NOT handle" section
- Known limitations documented
- Conditions for correctness stated

---

## Example

**Without code field:**
```python
def is_inside_dir(directory, filepath):
    """Check if filepath is inside directory."""
    dir_resolved = Path(directory).resolve()
    file_resolved = Path(filepath).resolve()
    return file_resolved.relative_to(dir_resolved)
```

**With code field:**
```python
"""
Assumptions:
- Both paths exist (resolve() behavior differs for non-existent paths)
- Symlinks should be followed (physical containment, not logical)
- "Inside" includes the directory itself
- Unix-like paths (not tested on Windows)

Does NOT handle:
- Race conditions (path could change between check and use)
- Non-existent paths reliably (behavior varies by Python version)
"""
def is_inside_dir(directory: str, filepath: str) -> bool:
    dir_resolved = Path(directory).resolve()
    file_resolved = Path(filepath).resolve()
    try:
        file_resolved.relative_to(dir_resolved)
        return True
    except ValueError:
        return False
```

---

## Anti-Patterns

### Over-correction
- Paralysis: so many caveats that no code gets written
- Pedantry: documenting obvious things
- Scope refusal: "I can't write this without more requirements" when reasonable defaults exist

### Under-correction
- Listing edge cases but not handling them
- Assumptions stated but not enforced
- "Known limitations" as excuse for incomplete work

### The Balance
Code field should produce code that is:
- **Smaller** than baseline (less speculative feature creep)
- **More documented** about its limits (not about its function)
- **More defensive** at boundaries (input validation, error cases)
- **Less defensive** internally (trusting its own invariants)
