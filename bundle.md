---
bundle:
  name: amplifier-toolkit
  version: 1.0.0
  description: Wrapper to load my-amplifier from subdirectory (workaround for amplifier-foundation#subdirectory bug)

includes:
  - bundle: amplifier-toolkit:bundles/my-amplifier
---

# Amplifier Toolkit

This is a thin wrapper that loads `bundles/my-amplifier`. 

Use directly: `amplifier bundle add git+https://github.com/ramparte/amplifier-toolkit@main`

See [bundles/my-amplifier/bundle.md](bundles/my-amplifier/bundle.md) for the actual bundle content.
