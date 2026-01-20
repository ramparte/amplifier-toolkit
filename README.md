# Amplifier Toolkit

Personal collection of Amplifier bundles, recipes, scripts, and extensions.

## Quick Start

```bash
# Add the toolkit bundle (includes my-amplifier)
amplifier bundle add git+https://github.com/ramparte/amplifier-toolkit@main --name my-amplifier
amplifier bundle use my-amplifier
```

## Contents

### Bundles (`bundles/`)

| Bundle | Description |
|--------|-------------|
| `my-amplifier` | Personal amplifier with dev-memory, deliberate-development, looper, vibecoding, and user habits enforcement |
| `deliberate-development` | Decomposition-first workflow with planning/implementation phases |
| `looper` | Supervised work loop that keeps working until done |

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
| `code-field` | Environmental prompting for rigorous code generation - surfaces edge cases, makes assumptions visible |

### Tools (`tools/`)

| Tool | Description |
|------|-------------|
| [`voice-bridge`](tools/voice-bridge/) | Control Amplifier sessions via voice from iPhone using Siri Shortcuts |

## Usage

### Using the Main Bundle

```bash
# Install and activate
amplifier bundle add git+https://github.com/ramparte/amplifier-toolkit@main --name my-amplifier
amplifier bundle use my-amplifier

# Or run directly
amplifier run --bundle git+https://github.com/ramparte/amplifier-toolkit@main
```

### Using Individual Bundles

Reference sub-bundles in your own bundle's includes:

```yaml
includes:
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/deliberate-development
  - bundle: git+https://github.com/ramparte/amplifier-toolkit@main#subdirectory=bundles/looper
```

### Using Recipes

```bash
amplifier recipes execute git+https://github.com/ramparte/amplifier-toolkit@main:recipes/feature-workflow.yaml \
  --context '{"feature_name": "my-feature", "feature_description": "..."}'
```

## License

MIT
