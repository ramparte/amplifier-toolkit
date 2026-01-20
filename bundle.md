---
bundle:
  name: my-amplifier
  version: 1.2.0
  description: Personal Amplifier with amplifier-dev + dev-memory + deliberate development + looper + user habits enforcement

config:
  allowed_write_dirs:
    - ~/.amplifier/dev-memory

includes:
  # Amplifier-dev - stay current with Amplifier developments automatically
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=bundles/amplifier-dev.yaml
  
  # Dev-memory behavior - persistent local memory
  - bundle: git+https://github.com/ramparte/amplifier-collection-dev-memory@main#subdirectory=behaviors/dev-memory.yaml
  
  # Looper - supervised work loop (keeps working until done)
  - bundle: amplifier-toolkit:bundles/looper
  
  # Deliberate development - decomposition-first workflow
  - bundle: amplifier-toolkit:bundles/deliberate-development
---

# My Personal Amplifier

Personal amplifier bundle with dev-memory, deliberate development workflow, and user habits enforcement.

## What's Included

**From Amplifier-Dev:**
- All standard tools (filesystem, bash, web, search, task delegation)
- Session configuration and hooks
- Access to all foundation agents (zen-architect, modular-builder, explorer, etc.)
- Shadow environments for safe testing
- Automatic updates when foundation evolves

**From Dev-Memory:**
- Persistent memory at `~/.amplifier/dev-memory/`
- Natural language: "remember this:", "what do you remember about X?"
- Work tracking: "what was I working on?"
- Token-efficient architecture (reads delegated to sub-agent)

**From Looper:**
- Supervised work loop tool
- Keeps working until supervisor confirms completion
- User input injection via `./looper-input.txt`

**From Deliberate Development:**
- Decomposition-first planning (deliberate-planner agent)
- Specification-based implementation (deliberate-implementer agent)
- Recipes: deliberate-design, feature-development
- "4-5 planning turns, then one go-do-it turn" philosophy

**User Habits Enforcement:**
- Proactive prompting for exit criteria and reference materials
- Rejection of "blocked" as acceptable task closure
- Evidence requirements before accepting completion claims
- Dev-memory integration for tracking commitments
- Active pushback when setting up for failure

## Usage

```bash
amplifier bundle add git+https://github.com/ramparte/amplifier-toolkit@main --name my-amplifier
amplifier bundle use my-amplifier
```

---

@amplifier-toolkit:bundles/my-amplifier/context/user-habits.md

---

@foundation:context/shared/common-system-base.md
