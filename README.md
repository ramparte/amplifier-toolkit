# Amplifier Toolkit

Personal collection of Amplifier recipes, bundles, and extensions.

## Contents

### Scripts (`scripts/`)

Utility scripts for Amplifier workflows.

| Script | Description |
|--------|-------------|
| [`session-manager`](scripts/session-manager/) | Save and restore running Amplifier sessions across reboots (VS Code + WSL) |

### Bundles (`bundles/`)

Custom bundle configurations and behaviors.

| Bundle | Description |
|--------|-------------|
| ~~`my-amplifier`~~ | ⚠️ **DEPRECATED** - Use the standalone repo: [ramparte/my-amplifier](https://github.com/ramparte/my-amplifier) |
| `deliberate-development` | Deliberate practice patterns for development |
| `looper` | Iterative refinement workflows |

### Recipes (`recipes/`)

Reusable multi-step workflows for common development tasks.

| Recipe | Description |
|--------|-------------|
| `feature-workflow.yaml` | Complete feature development lifecycle with design review gate |

### Skills (`skills/`)

Domain-specific knowledge and patterns.

| Skill | Description |
|-------|-------------|
| `code-field` | Environmental prompting for rigorous code generation - surfaces edge cases, makes assumptions visible |

**Usage:** Say "using code field principles, [task]" or "apply code field to this implementation"

### Tools (`tools/`)

Standalone tools and integrations for Amplifier.

| Tool | Description |
|------|-------------|
| [`voice-bridge`](tools/voice-bridge/) | Control Amplifier sessions via voice from iPhone using Siri Shortcuts - discovers sessions, parses natural language commands, returns voice-friendly responses |

## Usage

### Using Scripts

See individual script READMEs for installation and usage. Example:

```bash
# Save current Amplifier sessions before rebooting
amp-save-sessions

# Restore sessions after reboot
amp-restore-sessions
```

### Using Bundles

> **Note:** The `my-amplifier` bundle has moved to its own standalone repository for easier use.
> Use: `git+https://github.com/ramparte/my-amplifier`

For other bundles in this repo, reference them directly from GitHub:

```bash
amplifier run --bundle git+https://github.com/ramparte/amplifier-toolkit@main:bundles/deliberate-development/bundle.md
```

### Using Recipes

Reference recipes directly from GitHub:

```bash
amplifier recipes execute git+https://github.com/ramparte/amplifier-toolkit@main:recipes/feature-workflow.yaml \
  --context '{"feature_name": "my-feature", "feature_description": "...", "target_directory": "src/feature"}'
```

Or clone locally and reference by path.

## License

MIT
