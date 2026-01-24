# Amplifier Swarm - Example Workflow

This guide walks through a complete example of using Amplifier Swarm.

## Scenario

You have 50 implementation tasks for the WebWord project and want to execute them in parallel with 3 workers.

## Step 1: Prepare Your Tasks

Ensure your task file is in YAML format. Example structure:

```yaml
tasks:
  - id: "2.6.1.a"
    name: "Implement user authentication"
    phase: "implementation"
    type: "implementation"
    status: "not_started"
    priority: "high"
    estimated_hours: 2.5
    description: "Implement JWT-based authentication..."
    acceptance_criteria: "- Users can log in\n- Tokens expire after 24h"
    files:
      - "src/auth/authentication.py"
      - "tests/test_authentication.py"
    design_docs:
      - "docs/auth-design.md"
```

## Step 2: Import Tasks to Database

```bash
cd /mnt/c/ANext/Webword

# Import tasks
amplifier-swarm import-tasks tasks.yaml --db swarm.db

# Verify import
amplifier-swarm status --db swarm.db
```

Expected output:
```
📊 Task Progress
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Status      ┃ Count ┃ Hours ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ Not Started │    50 │  85.5h│
│ Total       │    50 │  85.5h│
└─────────────┴───────┴───────┘
```

## Step 3: Start the Swarm (3 Workers)

```bash
amplifier-swarm start \
  --db swarm.db \
  --project-root /mnt/c/ANext/Webword \
  --builder-agent foundation:modular-builder \
  --validator-agent recipes:result-validator \
  --workers 3 \
  --dashboard-port 8765
```

You'll see:
```
🐝 Starting Amplifier Swarm
Starting dashboard on http://localhost:8765
✓ Dashboard running at http://localhost:8765
Starting orchestrator...
Orchestrator starting with 3 worker(s) (serial mode: False)
Worker worker-1-1737710620 starting (PID: 12345)
Worker worker-2-1737710620 starting (PID: 12346)
Worker worker-3-1737710620 starting (PID: 12347)
```

## Step 4: Monitor via Dashboard

Open http://localhost:8765 in your browser. You'll see:

**Task Progress:**
- Total: 50 tasks, 85.5h
- Not Started: 47
- In Progress: 3
- Completed: 0
- Failed: 0

**Workers:**
- Active Workers: 3/3
- Worker 1: Processing task 2.6.1.a
- Worker 2: Processing task 2.6.1.b
- Worker 3: Processing task 2.6.2.a

**Progress Bar:**
```
████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 6.0%
```

## Step 5: Monitor via CLI (in another terminal)

```bash
# Overall status
amplifier-swarm status --db swarm.db

# List in-progress tasks
amplifier-swarm list-tasks --db swarm.db --status in_progress

# Watch a specific task
amplifier-swarm task-info 2.6.1.a --db swarm.db
```

Output:
```
Task: 2.6.1.a
Name: Implement user authentication
Status: in_progress
Phase: implementation
Worker: worker-1-1737710620
Claimed: 2026-01-24 09:30:15
Started: 2026-01-24 09:30:20

Execution Log:
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Time                ┃ Event    ┃ Message                    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-01-24 09:30:20 │ started  │ Task execution started     │
│ 2026-01-24 09:30:15 │ claimed  │ Task claimed by worker-1   │
└─────────────────────┴──────────┴────────────────────────────┘
```

## Step 6: Handle Failures

If a task fails, the dashboard shows it in red. You can:

**Via Dashboard:**
1. Click on the failed task
2. Review the error message
3. Click "🔄 Retry" button

**Via CLI:**
```bash
# See failed tasks
amplifier-swarm list-tasks --db swarm.db --status failed

# Get failure details
amplifier-swarm task-info 2.6.1.c --db swarm.db

# Retry after fixing issues
amplifier-swarm retry 2.6.1.c --db swarm.db
```

## Step 7: Graceful Shutdown

When you're ready to stop (let workers finish current tasks):

**Via Dashboard:**
- Click "⏸️ Graceful Stop" button

**Via CLI:**
```bash
# Send SIGTERM to orchestrator
pkill -TERM -f "amplifier_swarm.orchestrator"
```

**Via Ctrl+C:**
- Just press Ctrl+C in the orchestrator terminal

Workers will:
1. Stop claiming new tasks
2. Finish current task execution
3. Update task status
4. Gracefully exit

Timeout: 5 minutes (configurable with `--graceful-timeout`)

## Step 8: Emergency Stop

If something is stuck and you need immediate shutdown:

**Via Dashboard:**
- Click "🛑 Emergency Stop" button

**Via CLI:**
```bash
# Send SIGUSR1 to orchestrator
pkill -USR1 -f "amplifier_swarm.orchestrator"
```

This will:
1. Immediately terminate all workers (SIGKILL)
2. Mark in-progress tasks as failed
3. Exit orchestrator

**Warning:** Current tasks may be left in inconsistent state. Use only in emergencies.

## Step 9: Resume After Interruption

If the swarm was interrupted (crash, power loss, etc.):

```bash
# Check database state
amplifier-swarm status --db swarm.db

# You might see orphaned tasks (claimed but worker dead)
# The orchestrator automatically detects and resets these after 30 minutes

# Or manually reset them
python -c "
from amplifier_swarm.database import TaskDatabase
db = TaskDatabase('swarm.db')
db.reset_orphaned_tasks(timeout_minutes=5)  # More aggressive timeout
"

# Then restart the swarm
amplifier-swarm start --db swarm.db ...
```

## Step 10: Export Results

After completion, export results:

```bash
# Export all tasks
amplifier-swarm export-tasks swarm.db all-results.yaml

# Export only completed tasks
amplifier-swarm export-tasks swarm.db completed.yaml --status completed

# Export only failed tasks for review
amplifier-swarm export-tasks swarm.db failed.yaml --status failed
```

## Performance Notes

### 3 Workers on Typical Hardware

- **CPU:** Each worker is a separate process
- **Memory:** Each worker + 2 Amplifier sessions ≈ 1-2GB
- **Expected:** 3-6 concurrent LLM API calls
- **Throughput:** ~20-30 tasks/hour (depends on task complexity)

### Optimization Tips

1. **Reduce workers if memory-constrained:**
   ```bash
   --workers 1  # Serial mode
   ```

2. **Disable validation for faster iteration:**
   ```bash
   --no-validation
   ```

3. **Use task priorities:**
   Tasks with `priority: "high"` are claimed first

4. **Monitor worker heartbeats:**
   Dashboard shows last heartbeat time - if >90s, worker may be stuck

## Common Patterns

### Serial Mode (Testing)

```bash
# N=1 for predictable, sequential execution
amplifier-swarm start --workers 1 --db swarm.db ...
```

### Parallel Mode (Production)

```bash
# N=3 for balanced throughput
amplifier-swarm start --workers 3 --db swarm.db ...
```

### High-Throughput Mode

```bash
# N=5+ for maximum speed (if you have the resources)
amplifier-swarm start --workers 5 --db swarm.db ...
```

### Validation-Free Mode

```bash
# Skip validator for faster iteration (less thorough)
amplifier-swarm start --no-validation --db swarm.db ...
```

## Troubleshooting Examples

### Stuck Task (>1 hour)

```bash
# Via dashboard: Click task, then "🛑 Kill"

# Via CLI:
amplifier-swarm task-info 2.6.1.a --db swarm.db
# Review log, then kill if needed (dashboard only for now)
```

### Worker Crashed

The orchestrator automatically:
1. Detects crash (heartbeat timeout)
2. Marks worker as crashed in DB
3. Resets task to `not_started`
4. Spawns new worker if tasks remain

No manual intervention needed.

### Database Locked

SQLite uses file locking. If you see "database locked" errors:

```bash
# Ensure no other swarm processes are running
ps aux | grep amplifier_swarm

# If stuck, kill them
pkill -9 -f amplifier_swarm

# Then restart
amplifier-swarm start --db swarm.db ...
```

## Real-World Example

For the WebWord project with 50 tasks:

```bash
# 1. Import
cd /mnt/c/ANext/Webword
amplifier-swarm import-tasks task_file.yaml --db swarm.db

# 2. Start with 3 workers
amplifier-swarm start \
  --db swarm.db \
  --project-root . \
  --builder-agent foundation:modular-builder \
  --validator-agent recipes:result-validator \
  --workers 3

# 3. Monitor at http://localhost:8765

# 4. In another terminal, watch progress
watch -n 5 "amplifier-swarm status --db swarm.db"

# Expected completion time: ~2-3 hours for 50 tasks @ 85h estimated
# (With validation and 3 workers in parallel)
```
