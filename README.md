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
| `m365-collab` | Agent collaboration via M365 SharePoint | `git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/m365-collab` |
| `session-discovery` | Automatic session indexing and discovery - "what was I working on last week?" | `git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/session-discovery` |

**Example usage in your bundle.md:**
```yaml
includes:
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/looper
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/deliberate-development
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/m365-collab
```

### Examples (`examples/`)

Working demonstrations of Amplifier patterns:

| Example | Description |
|---------|-------------|
| [`continuous-code-review`](examples/continuous-code-review/) | Automated code review on every commit (inspired by roborev) |

### Recipes (`recipes/`)

| Recipe | Description |
|--------|-------------|
| `feature-workflow.yaml` | Complete feature development lifecycle with design review gate |
| `session-digest.yaml` | Generate shareable session summaries for collaboration and handoffs |

### Scripts (`scripts/`)

| Script | Description |
|--------|-------------|
| [`session-manager`](scripts/session-manager/) | Save and restore running Amplifier sessions across reboots (VS Code + WSL) |

### Skills (`skills/`)

| Skill | Description |
|-------|-------------|
| `code-field` | Environmental prompting for rigorous code generation |
| `project-mgmt` | AI-native project management with task tracking and team-aware assignment |

### Tools (`tools/`)

| Tool | Description |
|------|-------------|
| [`voice-bridge`](tools/voice-bridge/) | Control Amplifier sessions via voice from iPhone using Siri Shortcuts |
| [`m365-collab`](tools/m365-collab/) | Agent-to-agent collaboration via M365 SharePoint |

## License

MIT
