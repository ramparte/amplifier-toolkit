# Looper

**Supervised work loop for Amplifier** - keeps working on a task until a supervisor confirms it's done, with support for user input injection.

## The Problem

Agentic systems often stop halfway through tasks, even when told to continue. You end up saying "keep going" over and over.

## The Solution

Looper implements a **supervised loop pattern**:

1. **Working agent** executes your task
2. **Supervisor agent** evaluates: is this actually done?
3. If not done, supervisor provides feedback and working agent continues
4. **You can inject input** at any time that gets noticed on the next iteration
5. Loop continues until supervisor says COMPLETE or max iterations reached

```
┌─────────────────────────────────────────────────────────┐
│                   Looper Orchestrator                   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ while not complete and iter < max:              │   │
│  │   1. Check for user input                       │   │
│  │   2. Working agent does work                    │   │
│  │   3. Supervisor evaluates                       │   │
│  │   4. If incomplete: inject feedback, continue   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  User Input ──────────────────────┐                    │
│  (file or stdin)                  ▼                    │
│                            [Injected on next           │
│                             iteration]                 │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
# From source
cd looper
pip install -e .

# With Amplifier integration
pip install -e ".[amplifier]"
```

## Usage

### Basic

```bash
looper "Implement a REST API for user management"
```

### With Options

```bash
# More iterations for complex tasks
looper --max-iterations 20 "Refactor the entire authentication module"

# Custom supervisor
looper --supervisor my-bundle:agents/strict-reviewer "Fix all type errors"

# Verbose output
looper -v "Build a CLI tool for data processing"
```

### User Input Injection

While looper is running, you can provide input that gets noticed on the next iteration:

**Via stdin (interactive):**
Just type and press Enter while looper is running.

**Via file:**
```bash
# Start looper watching a file
looper --input-file ./guidance.txt "Build a web scraper"

# In another terminal, inject guidance
echo "Focus on error handling next" > ./guidance.txt
```

### JSON Output

```bash
looper --json-output "Task description" | jq .
```

## How It Works

### The Loop

1. **First iteration**: Working agent receives the task and starts working
2. **Supervisor evaluation**: Supervisor reviews output and decides COMPLETE or INCOMPLETE
3. **Feedback injection**: If incomplete, supervisor's feedback goes to next iteration
4. **User input**: Any user input is also injected into the next prompt
5. **Repeat**: Until COMPLETE (with sufficient confidence) or max iterations

### Session Continuity

The working agent maintains **session continuity** - it remembers its previous work and builds on it rather than starting fresh each iteration.

### Supervisor Configuration

The supervisor runs with:
- Lower temperature (0.1) for consistent evaluation
- Faster model (claude-sonnet) for quick decisions
- No tools (evaluation only, no actions)
- Strict JSON output format

## Configuration

### LoopConfig Options

| Option | Default | Description |
|--------|---------|-------------|
| `task` | required | The task description |
| `max_iterations` | 10 | Maximum work iterations |
| `supervisor_agent` | `looper:agents/supervisor` | Agent for evaluation |
| `working_bundle` | current bundle | Bundle for working agent |
| `input_file` | None | File to watch for input |
| `state_dir` | None | Directory for state persistence |
| `min_confidence` | 0.8 | Min confidence to mark complete |
| `verbose` | False | Print progress to stderr |

### Custom Supervisor

Create your own supervisor agent:

```markdown
---
meta:
  name: my-supervisor
  description: Custom task evaluator

providers:
  - module: provider-anthropic
    config:
      default_model: claude-sonnet-4-5
      temperature: 0.2

tools: []
---

# My Supervisor

Your custom evaluation instructions here...

Response format:
{"status": "COMPLETE" or "INCOMPLETE", "confidence": 0.0-1.0, ...}
```

## Programmatic Usage

```python
import asyncio
from looper import SupervisedLoop, LoopConfig

async def main():
    config = LoopConfig(
        task="Implement user authentication",
        max_iterations=15,
        verbose=True,
    )
    
    loop = SupervisedLoop(config)
    
    # Optionally inject input programmatically
    # await loop.inject_input("Focus on JWT tokens")
    
    result = await loop.run()
    
    print(f"Complete: {result.complete}")
    print(f"Iterations: {result.iterations}")
    print(f"Final output: {result.final_output}")

asyncio.run(main())
```

## Why Not Recipes?

We consulted the Amplifier experts. Recipes don't support:
- **Conditional looping** ("until done") - only `foreach` over known lists
- **User input injection** - approval gates are binary approve/deny
- **Session continuity** - each step spawns a fresh agent

A Python orchestrator gives us full control over these requirements.

## Architecture

```
looper/
├── looper/
│   ├── __init__.py      # Package exports
│   ├── orchestrator.py  # SupervisedLoop class
│   └── cli.py           # CLI entry point
├── agents/
│   └── supervisor.md    # Default supervisor agent
├── pyproject.toml
└── README.md
```

## License

MIT
