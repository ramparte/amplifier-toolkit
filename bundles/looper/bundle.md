---
bundle:
  name: looper
  version: 0.1.0
  description: Supervised work loop - keeps working until a task is truly done

tools:
  - module: looper:looper.tool
    config: {}

agents:
  task-supervisor:
    bundle: looper:agents/supervisor.md
---

# Looper Bundle

This bundle provides the `looper` tool for supervised work loops.

## The Problem

Agentic systems often stop halfway through tasks, even when told to continue.
You end up saying "keep going" repeatedly.

## The Solution

The `looper` tool runs a **supervised work loop**:

1. Working agent executes your task
2. Supervisor evaluates: is this actually done?
3. If not done, supervisor provides feedback and working agent continues
4. Loop continues until supervisor says COMPLETE or max iterations reached

## Usage

From inside an Amplifier session, just ask to use looper:

```
"Implement user authentication using looper"
"Use looper to refactor the database module - max 15 iterations"
```

The agent will call the looper tool, which handles the loop internally.

## User Input Injection

While looper is running, you can inject guidance by writing to a file in the current project directory:

```
./looper-input.txt
```

From another terminal:
```bash
echo "Focus on error handling next" > looper-input.txt
```

This gets picked up on the next iteration.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| task | required | The task description |
| max_iterations | 10 | Maximum work iterations |
| min_confidence | 0.8 | Supervisor confidence threshold |
| checkpoint_every | None | Pause every N iterations (optional) |
