# Amplifier Toolkit

A library of reusable Amplifier components: bundles, recipes, scripts, and tools.

> **Note:** This repo provides components to be *included* by other bundles. It is NOT itself a loadable bundle. For your main personal bundle, use [ramparte/my-amplifier](https://github.com/ramparte/my-amplifier).

## Contents

### Bundles (`bundles/`)

Include these in your own bundle via `#subdirectory=` syntax:

| Bundle | Description | Include As |
|--------|-------------|------------|
| `deliberate-development` | Decomposition-first workflow with planning/implementation phases | `git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/deliberate-development` |
| `looper` | Supervised work loop that keeps working until done | `git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/looper` |

**Example usage in your bundle.md:**
```yaml
includes:
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/looper
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/deliberate-development
```

### Recipes (`recipes/`)

| Recipe | Description |
|--------|-------------|
| `feature-workflow.yaml` | Complete feature development lifecycle with design review gate |

### Scripts (`scripts/`)

| Script | Description |
|--------|-------------|
| [`session-manager`](scripts/session-manager/) | Save and restore running Amplifier sessions across reboots (VS Code + WSL) |

### Skills (`skills/`)

| Skill | Description |
|-------|-------------|
| `code-field` | Environmental prompting for rigorous code generation |

### Tools (`tools/`)

| Tool | Description |
|------|-------------|
| [`voice-bridge`](tools/voice-bridge/) | Control Amplifier sessions via voice from iPhone using Siri Shortcuts |

## License

MIT
