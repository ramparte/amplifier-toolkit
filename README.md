# Amplifier Toolkit

Personal collection of Amplifier recipes, bundles, and extensions.

## Contents

### Recipes (`recipes/`)

Reusable multi-step workflows for common development tasks.

| Recipe | Description |
|--------|-------------|
| `feature-workflow.yaml` | Complete feature development lifecycle with design review gate |

### Bundles (`bundles/`)

Custom bundle configurations and behaviors.

### Skills (`skills/`)

Domain-specific knowledge and patterns.

## Usage

### Using Recipes

Reference recipes directly from GitHub:

```bash
amplifier recipes execute git+https://github.com/ramparte/amplifier-toolkit@main:recipes/feature-workflow.yaml \
  --context '{"feature_name": "my-feature", "feature_description": "...", "target_directory": "src/feature"}'
```

Or clone locally and reference by path.

## License

MIT
