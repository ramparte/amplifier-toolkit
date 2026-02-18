---
bundle:
  name: task-iteration
  version: 1.0.0
  description: Recipe-based task iteration system with quality control - automated implementation and validation loops

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

agents:
  include:
    - task-builder
    - task-validator
---

# Task Iteration System

Recipe-based system for iterating through implementation tasks with quality control.

This bundle provides the task-iteration-loop recipe for automating task implementation with:
- Fresh context per task (no overflow)
- Antagonistic validation (finds problems)  
- Real tests required (no stubs)
- Type safety enforced
- Design adherence checked

## Usage

**Test run (3 tasks):**
```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=@task-iteration:recipes/task-iteration-loop.yaml \
  context='{"max_tasks": 3, "validation_strictness": "lenient"}'
```

**Production run (10 tasks):**
```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=@task-iteration:recipes/task-iteration-loop.yaml \
  context='{"task_file": "new-features-tasks.yaml", "max_tasks": 10}'
```

## Components

- **task-builder agent** - Implements tasks from design specs
- **task-validator agent** - Antagonistic code review
- **task-iteration-loop recipe** - Master coordinator

## Validation Strictness

- **strict**: Block on any issues (critical features)
- **moderate**: Block on critical issues only (default)
- **lenient**: Block on showstoppers only (rapid prototyping)

---

@foundation:context/shared/common-system-base.md
