---
bundle:
  name: my-amplifier
  version: 1.2.0
  description: Personal Amplifier with amplifier-dev + dev-memory + vibecoding practices + user habits enforcement

config:
  allowed_write_dirs:
    - ~/.amplifier/dev-memory

includes:
  # Amplifier-dev - stay current with Amplifier developments automatically
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=bundles/amplifier-dev.yaml
  
  # Dev-memory behavior - persistent local memory
  - bundle: git+https://github.com/ramparte/amplifier-collection-dev-memory@main#subdirectory=behaviors/dev-memory.yaml
  
  # Looper - supervised work loop (keeps working until done)
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/looper
  
  # Deliberate development - decomposition-first workflow
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/deliberate-development
  
  # Vibecoding - practitioner community patterns (fresh-eyes, plan-persistence, etc.)
  - bundle: git+https://github.com/ramparte/vibecoding@main
---

# My Personal Amplifier

A thin bundle combining amplifier-dev with persistent dev-memory capabilities, community practices, and personal habit enforcement.

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

**From Vibecoding:**
- Community-sourced AI development patterns
- Behaviors: fresh-eyes, plan-persistence, clear-early, understanding-md, subagent-coordinator, question-bubbling
- Recipes: overnight-code-review, spec-iteration, token-burner, skill-testing, antagonistic-panel, wiggum-loop
- Chat analysis agent for extracting patterns from conversations

**User Habits Enforcement (NEW in 1.2.0):**
- Proactive prompting for exit criteria and reference materials
- Rejection of "blocked" as acceptable task closure
- Evidence requirements before accepting completion claims
- Dev-memory integration for tracking commitments
- Active pushback when setting up for failure

## Usage

```bash
# Add to your local bundle list
amplifier bundle add git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/my-amplifier

# Or run directly
amplifier run --bundle git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/my-amplifier

# Or set as default in ~/.amplifier/settings.yaml:
# bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/my-amplifier
```

---

@my-amplifier:context/user-habits.md

---

@foundation:context/shared/common-system-base.md
