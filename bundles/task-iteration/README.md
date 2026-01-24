# WebWord Task Iteration System

This directory contains the recipe-based system for iterating through WebWord implementation tasks with quality control.

## Files

- **task-iteration-loop.yaml** - Master coordinator recipe
- **implement-task.yaml** - Single task implementation (legacy, replaced by task-iteration-loop)

## Agents

Located in `.amplifier/agents/`:
- **task-builder.md** - Implements tasks from design specs
- **task-validator.md** - Antagonistic code review

## Quick Start

### Test Run (3 tasks)
```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=.amplifier/recipes/task-iteration-loop.yaml \
  context='{"max_tasks": 3, "validation_strictness": "lenient"}'
```

### Production Run (10 tasks)
```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=.amplifier/recipes/task-iteration-loop.yaml \
  context='{"task_file": "new-features-tasks.yaml", "max_tasks": 10}'
```

### All Tasks Mode (unlimited)
```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=.amplifier/recipes/task-iteration-loop.yaml \
  context='{"task_file": "new-features-tasks.yaml", "max_tasks": -1}'
```

### Resume from Task ID
```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=.amplifier/recipes/task-iteration-loop.yaml \
  context='{"start_from_task": "2.6.1.5", "max_tasks": 10}'
```

## Configuration

All options via `context` parameter:

```json
{
  "task_file": "new-features-tasks.yaml",
  "task_filter": "phase-2.6.1",
  "max_tasks": 10,
  "start_from_task": "",
  "max_retries": 2,
  "validation_enabled": true,
  "validation_strictness": "moderate",
  "auto_commit": true
}
```

## How It Works

1. **Master Recipe** loads task list and iterates
2. **Builder Agent** (fresh session) implements each task
3. **Validator Agent** (fresh session) reviews with antagonistic lens
4. **Retry Logic** handles failures (up to max_retries)
5. **Webword-PM** tracks state and commits on success

## Quality Guarantees

- ✅ Fresh context per task (no overflow)
- ✅ Antagonistic validation (finds problems)
- ✅ Real tests required (no stubs)
- ✅ Type safety enforced
- ✅ Design adherence checked
- ✅ Integration validation

## Validation Strictness

- **strict**: Block on any issues (use for critical features)
- **moderate**: Block on critical issues only (default)
- **lenient**: Block on showstoppers only (use for rapid prototyping)

## Monitoring Progress

The recipe generates iteration reports in:
```
.amplifier/iteration-reports/report-<timestamp>.md
```

Check webword-pm for task status:
```bash
uvx --from ./tools/webword-pm webword-pm status
```

## Troubleshooting

### Recipe stops mid-batch
```bash
# Resume from last completed task
amplifier tool invoke recipes operation=resume session_id=<session-id>
```

### Tasks keep failing validation
- Review validator feedback in iteration report
- Adjust validation_strictness to "lenient" temporarily
- Review with manual code review

### Node/shadow environment issues
Shadow environment disabled by default (`use_shadow_env: false`). Enable when node config is fixed.

## Cost Estimates

- Builder: Claude Sonnet (~$1-2/task)
- Validator: Claude Opus (~$2-4/task)
- Total per task: $3-6
- 187 tasks: $561-1,122

## Next Steps

1. Test with 3 tasks
2. Review output quality
3. Adjust validation strictness
4. Run production batches (10 tasks at a time)
5. Review between phases
