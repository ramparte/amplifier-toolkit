# Amplifier Toolkit

Personal collection of Amplifier recipes, bundles, and extensions.

## Contents

### Bundles (`bundles/`)

Custom bundle configurations and behaviors.

| Bundle | Description |
|--------|-------------|
| `my-amplifier` | Thin bundle combining foundation + dev-memory for staying current while having persistent local memory |

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

## Usage

### Using Bundles

Use the my-amplifier bundle directly from GitHub:

```bash
amplifier run --bundle git+https://github.com/ramparte/amplifier-toolkit@main:bundles/my-amplifier/bundle.md
```

Or set as default in `~/.amplifier/settings.yaml`:

```yaml
bundle: git+https://github.com/ramparte/amplifier-toolkit@main:bundles/my-amplifier/bundle.md
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
