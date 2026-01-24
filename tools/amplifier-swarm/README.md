# Amplifier Swarm 🐝

Parallel task execution system for Amplifier with web dashboard monitoring and control.

## Overview

Amplifier Swarm enables you to execute large task lists in parallel using multiple Amplifier worker processes. It provides:

- **SQLite-based task queue** with atomic claim/release operations
- **Parallel or serial execution** (N workers configurable)
- **Real-time web dashboard** for monitoring and control
- **Robust error handling** with automatic retries and orphan detection
- **Graceful and emergency shutdown** options
- **Session isolation** - workers run in separate processes with no shared state

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard                             │
│              http://localhost:8765                           │
│         (Monitor, control, retry, kill tasks)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                              │
│            (Spawns and manages N workers)                    │
│          • Heartbeat monitoring                              │
│          • Orphan task recovery                              │
│          • Graceful/emergency shutdown                       │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
           ┌─────────┐  ┌─────────┐  ┌─────────┐
           │Worker 1 │  │Worker 2 │  │Worker N │
           └─────────┘  └─────────┘  └─────────┘
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                   ┌───────────────────────┐
                   │   SQLite Database     │
                   │   (Task queue)        │
                   │   • Atomic claims     │
                   │   • State tracking    │
                   │   • Execution logs    │
                   └───────────────────────┘
```

## Installation

```bash
cd tools/amplifier-swarm
uv pip install -e .
```

## Quick Start

### 1. Import Your Tasks

Convert your YAML task file to SQLite:

```bash
amplifier-swarm import-tasks /path/to/tasks.yaml --db tasks.db
```

### 2. Start the Swarm

**Serial Mode (N=1):**
```bash
amplifier-swarm start \
  --db tasks.db \
  --project-root /path/to/project \
  --builder-agent foundation:modular-builder \
  --validator-agent recipes:result-validator \
  --workers 1
```

**Parallel Mode (N=3):**
```bash
amplifier-swarm start \
  --db tasks.db \
  --project-root /path/to/project \
  --builder-agent foundation:modular-builder \
  --validator-agent recipes:result-validator \
  --workers 3
```

### 3. Monitor via Dashboard

Open http://localhost:8765 in your browser to:
- View real-time task progress
- Monitor worker status
- Retry failed tasks
- Kill stuck tasks
- Trigger graceful or emergency shutdown

### 4. Check Status via CLI

```bash
# Overall status
amplifier-swarm status --db tasks.db

# List tasks
amplifier-swarm list-tasks --db tasks.db --status in_progress

# Task details
amplifier-swarm task-info 2.6.1.a --db tasks.db

# Retry a task
amplifier-swarm retry 2.6.1.a --db tasks.db
```

## Features

### Atomic Task Queue

- **SQLite with IMMEDIATE isolation** ensures only one worker claims each task
- **No race conditions** - database handles concurrency
- **Retry support** - failed tasks automatically retried (configurable max retries)
- **Orphan detection** - tasks stuck >30 minutes are automatically reset

### Worker Process Model

- **Multiprocessing isolation** - each worker is a separate process
- **Heartbeat monitoring** - workers send heartbeat every 30 seconds
- **Graceful shutdown** - workers finish current task before stopping (5 min timeout)
- **Emergency stop** - immediate termination of all workers (SIGUSR1)
- **Automatic restart** - crashed workers are restarted if tasks remain

### Session Management

Each task spawns TWO Amplifier sessions:
1. **Builder session** - implements the task
2. **Validator session** - antagonistic validation (optional with `--no-validation`)

Sessions are spawned as subprocesses via `amplifier task <agent>`, ensuring:
- Full process isolation
- Independent failure domains
- Clean resource cleanup

### Dashboard Features

- **Real-time WebSocket updates** - no manual refresh needed
- **Task filtering** - by status (not_started, in_progress, completed, failed)
- **Worker monitoring** - see PID, heartbeat, current task
- **Time estimates** - remaining hours, progress percentage
- **Task controls** - retry failed tasks, kill stuck tasks
- **System controls** - graceful shutdown, emergency stop

### Error Handling

- **Automatic retries** - tasks retry up to 2 times by default (configurable)
- **Timeout detection** - tasks stuck >30 minutes marked as failed or retried
- **Worker crash recovery** - crashed workers logged, tasks reset for retry
- **Graceful degradation** - one worker crashing doesn't affect others

## Usage Patterns

### Serial Mode (N=1)

Use when:
- Testing the system
- You have a single powerful machine
- Tasks are memory-intensive
- You want predictable ordering

```bash
amplifier-swarm start --workers 1 --db tasks.db ...
```

### Parallel Mode (N=3+)

Use when:
- You have multiple cores available
- Tasks are I/O bound (waiting on Amplifier sessions)
- You want maximum throughput
- Order doesn't matter

```bash
amplifier-swarm start --workers 3 --db tasks.db ...
```

**Performance note:** Each worker spawns Amplifier sessions, which use LLMs. With N=3, you might have 3-6 concurrent LLM sessions (builder + validator).

### Validation Control

**With validation (default):**
```bash
amplifier-swarm start --db tasks.db ...
```

**Without validation (faster, less thorough):**
```bash
amplifier-swarm start --no-validation --db tasks.db ...
```

## Configuration

### Task Database Schema

The SQLite database tracks:
- **Task metadata** - id, name, phase, status, estimated hours
- **Worker assignment** - which worker is processing which task
- **Session tracking** - builder and validator session IDs
- **Retry handling** - retry count, max retries, last error
- **Execution log** - timestamped event history

### Agent Configuration

**Builder agent** receives:
- Task description and acceptance criteria
- Expected file paths
- Working directory context
- Must return JSON with: status, files_created, files_modified, tests_passed

**Validator agent** receives:
- Builder's implementation results
- Task requirements
- Must return JSON with: verdict (PASS/FAIL), critical_issues, recommendations

### Dashboard Port

Default: `8765`

Change with:
```bash
amplifier-swarm start --dashboard-port 9000 ...
```

Or disable:
```bash
amplifier-swarm start --no-dashboard ...
```

## Migration from Old System

If you're migrating from `webword-pm` or similar:

### Before (webword-pm)
```bash
python tools/webword-pm/webword_pm.py \
  --task-file tasks.yaml \
  --project-dir /path/to/project
```

**Issues:**
- ❌ No parallelism (serial only)
- ❌ No dashboard
- ❌ Race conditions with concurrent runs
- ❌ No graceful shutdown
- ❌ Limited error recovery

### After (amplifier-swarm)
```bash
# One-time: Import tasks
amplifier-swarm import-tasks tasks.yaml --db tasks.db

# Run with parallel workers
amplifier-swarm start \
  --db tasks.db \
  --project-root /path/to/project \
  --builder-agent foundation:modular-builder \
  --validator-agent recipes:result-validator \
  --workers 3
```

**Benefits:**
- ✅ Parallel execution (N workers)
- ✅ Real-time web dashboard
- ✅ Atomic task claiming (no races)
- ✅ Graceful + emergency shutdown
- ✅ Automatic orphan recovery
- ✅ Worker crash resilience

## Troubleshooting

### Tasks stuck in "claimed" status

Workers may have crashed. Run:
```bash
amplifier-swarm status --db tasks.db
```

The orchestrator automatically resets orphaned tasks after 30 minutes.

### Dashboard not loading

Check if port 8765 is available:
```bash
lsof -i :8765
```

Use a different port:
```bash
amplifier-swarm start --dashboard-port 9000 ...
```

### Workers not starting

Check logs for errors. Run with verbose logging:
```bash
amplifier-swarm start --verbose ...
```

### High memory usage

Reduce number of workers:
```bash
amplifier-swarm start --workers 1 ...
```

Or disable validation:
```bash
amplifier-swarm start --no-validation ...
```

### Tasks failing repeatedly

Check task details:
```bash
amplifier-swarm task-info <task-id> --db tasks.db
```

Review execution log to see what's failing. You can manually retry after fixing issues:
```bash
amplifier-swarm retry <task-id> --db tasks.db
```

## Advanced Usage

### Custom Graceful Shutdown Timeout

Default is 5 minutes. To change:
```bash
python -m amplifier_swarm.orchestrator \
  --db tasks.db \
  --graceful-timeout 600 \
  ...
```

### Export Completed Tasks

```bash
amplifier-swarm export-tasks tasks.db completed.yaml --status completed
```

### Manual Orphan Recovery

```python
from amplifier_swarm.database import TaskDatabase

db = TaskDatabase("tasks.db")
orphans = db.find_orphaned_tasks(timeout_minutes=30)
print(f"Found {len(orphans)} orphaned tasks")

db.reset_orphaned_tasks(timeout_minutes=30)
```

### Emergency Stop Signal

Send SIGUSR1 to orchestrator process:
```bash
pkill -SIGUSR1 -f "amplifier_swarm.orchestrator"
```

Or use the dashboard "Emergency Stop" button.

## Development

### Running Tests

```bash
cd tools/amplifier-swarm
pytest tests/
```

### Running Components Separately

**Worker only:**
```bash
python -m amplifier_swarm.worker \
  --db tasks.db \
  --worker-id worker-1 \
  --project-root /path/to/project \
  --builder-agent foundation:modular-builder \
  --validator-agent recipes:result-validator
```

**Orchestrator only:**
```bash
python -m amplifier_swarm.orchestrator \
  --db tasks.db \
  --project-root /path/to/project \
  --builder-agent foundation:modular-builder \
  --validator-agent recipes:result-validator \
  --workers 3
```

**Dashboard only:**
```bash
python -m amplifier_swarm.dashboard \
  --db tasks.db \
  --port 8765
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit a pull request

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review execution logs with `--verbose`
3. File an issue on GitHub with logs and reproduction steps
