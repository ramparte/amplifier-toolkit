# Continuous Code Review Example

**Inspired by**: [roborev](https://github.com/wesm/roborev)  
**Built with**: Amplifier's composable primitives

## Overview

This example demonstrates how to build a roborev-like continuous code review system using Amplifier. Instead of a fixed Go binary with daemon architecture, we provide **building blocks** that users can compose into their own workflows.

## What This Example Provides

### 1. Git Hook Integration (`GitHookInstaller`)
- Install post-commit hooks that trigger reviews automatically
- Uninstall hooks safely
- Background execution (reviews don't block commits)

### 2. Review Management (`ReviewDashboard`)
- List recent reviews with statistics
- View detailed review results
- Track review trends (issues vs clean commits)

### 3. Four Interactive Scenarios
1. **Install Hooks** - Set up automatic reviews
2. **View Reviews** - Browse results and statistics
3. **Uninstall Hooks** - Clean removal
4. **Manual Review** - Try without hooks (test workflow)

## Quick Start

```bash
# Run the interactive demo
python 23_continuous_code_review.py

# Choose scenario 4 to try a manual review (no git setup needed)
# Or choose scenario 1 to install hooks in a real repo
```

## How It Works

### Automatic Review Flow

```
1. You commit code
   ↓
2. Post-commit hook fires
   ↓
3. Hook spawns Amplifier session in background
   ↓
4. Session reviews the changes
   ↓
5. Results logged to .amplifier/review-logs/
   ↓
6. View results via dashboard (scenario 2)
```

### The Post-Commit Hook

When installed, creates `.git/hooks/post-commit`:

```bash
#!/bin/bash
COMMIT_SHA=$(git rev-parse HEAD)
REVIEW_LOG=".amplifier/review-logs/$COMMIT_SHA.log"

echo "🔍 Code review queued for commit $COMMIT_SHA"

# Run review in background, log output
nohup bash -c 'amplifier run "Review commit $COMMIT_SHA" 2>&1' > "$REVIEW_LOG" &
```

**Key features:**
- Non-blocking (`nohup` and `&` run in background)
- One log file per commit (named by SHA)
- Works with any Amplifier bundle

## Comparison: roborev vs Amplifier

| Feature | roborev | This Example |
|---------|---------|--------------|
| **Architecture** | Go binary, daemon | Python, session-based |
| **Workflow** | Fixed (review → refine) | Fully customizable |
| **Review types** | Single-agent | Multi-agent capable |
| **Customization** | Config file | Full recipe DSL |
| **Queue** | PostgreSQL for sync | File-based logs |
| **TUI** | Interactive ncurses | Terminal output |
| **Integration** | Git-centric | Ecosystem-wide |

## Extending This Example

### Custom Review Bundle

Create a bundle with specialized review criteria:

```yaml
# my-review-bundle.yaml
---
bundle:
  name: my-code-reviewer
  version: 1.0.0

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

instruction: |
  You are a code reviewer for Python projects.
  
  Focus on:
  - PEP 8 compliance
  - Type hints coverage
  - Security vulnerabilities
  - Performance considerations
  
  Be thorough but concise.
---
```

Install with custom bundle:

```bash
# In scenario 1, when prompted "Use custom review bundle?"
# Enter: ./my-review-bundle.yaml
```

### Multi-Agent Reviews

Modify the hook to use multiple specialized reviewers:

```bash
# In .git/hooks/post-commit
amplifier run "Use architect agent to review design, then security-guardian to review security" &
```

### Review Recipe

For more complex workflows, create a recipe:

```yaml
# continuous-review-recipe.yaml
name: "continuous-review"
steps:
  - id: "get-changes"
    agent: "foundation:git-ops"
    prompt: "List changed files in commit {{commit_sha}}"
    
  - id: "review-quality"
    agent: "foundation:zen-architect"
    prompt: "Review code quality in {{changed_files}}"
    
  - id: "review-security"
    agent: "foundation:security-guardian"
    prompt: "Security review of {{changed_files}}"
    
  - id: "aggregate"
    agent: "foundation:zen-architect"
    prompt: "Combine reviews: {{quality}} {{security}}"
```

### Conditional Reviews

Only review certain file types:

```bash
# In post-commit hook
FILES=$(git diff-tree --no-commit-id --name-only -r HEAD)

if echo "$FILES" | grep -q '\.py$'; then
  echo "🔍 Python files changed, running review..."
  amplifier run "Review Python changes in commit $COMMIT_SHA" &
fi
```

## Advanced Patterns

### 1. Pre-PR Quality Gate

```bash
# In .git/hooks/pre-push
REVIEWS=$(ls .amplifier/review-logs/*.log 2>/dev/null | wc -l)
ISSUES=$(grep -l "issue\|problem\|bug" .amplifier/review-logs/*.log 2>/dev/null | wc -l)

if [ $ISSUES -gt 0 ]; then
  echo "⚠️  Warning: $ISSUES commits have review issues"
  echo "Review before pushing? (y/N)"
  read -r response
  if [ "$response" != "y" ]; then
    exit 1
  fi
fi
```

### 2. Team Dashboard

Build a web dashboard that aggregates reviews across team members:

```python
# Simple Flask app
from flask import Flask, render_template
from pathlib import Path

app = Flask(__name__)

@app.route("/")
def dashboard():
    reviews = ReviewDashboard.aggregate_team_reviews()
    return render_template("dashboard.html", reviews=reviews)
```

### 3. Slack/Teams Integration

Post review summaries to chat:

```python
# Add to post-commit hook
if review.has_issues:
    requests.post(SLACK_WEBHOOK, json={
        "text": f"🔍 Review for {commit_sha[:8]} found issues",
        "attachments": [{"text": review.summary}]
    })
```

## Troubleshooting

### Hook not firing

```bash
# Check if hook exists and is executable
ls -la .git/hooks/post-commit

# Should show: -rwxr-xr-x (executable)
# If not:
chmod +x .git/hooks/post-commit
```

### Reviews not appearing

```bash
# Check if background process is running
ps aux | grep amplifier

# Check logs directory
ls -la .amplifier/review-logs/

# Check last review PID
cat .amplifier/review-logs/.last_review_pid
```

### Hook errors

```bash
# Run hook manually to see errors
.git/hooks/post-commit

# Or check last log
tail .amplifier/review-logs/*.log | tail -20
```

## Philosophy: Building Blocks Over Applications

This example demonstrates Amplifier's philosophy:

**Don't integrate roborev** (complete application)  
**Provide building blocks** (composable primitives)

Users can:
- Customize review criteria
- Add specialized agents
- Build team-specific dashboards
- Create complex workflows via recipes
- Integrate with their tools

**The right answer isn't to integrate roborev—it's to make it possible for users to build something better than roborev using Amplifier's composable primitives.**

## Next Steps

### Phase 2: If Demand Exists

Create reusable modules:

1. **`tool-git-hooks`** - First-class git hook management tool
2. **`behaviors/git-hooks.yaml`** - Packaged behavior bundle
3. **Template recipes** in `amplifier-bundle-recipes/templates/`
4. **`review-dashboard` agent** in foundation

### Phase 3: Ecosystem Growth

Let community build:
- TUI interfaces (ncurses, Rich)
- Web dashboards (Flask, FastAPI)
- Mobile notifications (webhooks, Firebase)
- Multi-machine sync (PostgreSQL, Redis)

**Foundation provides mechanism, apps provide policy.**

## Key Takeaways

1. ✅ **Git hook integration** - Seamless automation
2. ✅ **Background execution** - Non-blocking workflow
3. ✅ **Flexible** - Use with any bundle or recipe
4. ✅ **Composable** - Building blocks, not rigid app
5. ✅ **Amplifier-native** - Uses sessions, not daemons

This is the "bricks and studs" philosophy in action.
