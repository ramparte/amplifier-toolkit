---
bundle:
  name: my-amplifier
  version: 1.0.0
  description: Personal Amplifier with amplifier-dev + dev-memory

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
---

# My Personal Amplifier

A thin bundle combining amplifier-dev with persistent dev-memory capabilities.

## What's Included

**From Amplifier-Dev:**
- All standard tools (filesystem, bash, web, search, task delegation)
- Session configuration and hooks
- Access to all foundation agents (zen-architect, modular-builder, explorer, etc.)
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

@foundation:context/shared/common-system-base.md
