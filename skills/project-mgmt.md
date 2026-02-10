# Project Management

AI-native project management that lives alongside code. Lightweight task tracking with team-aware assignment recommendations.

## Overview

This skill enables self-service project management for teams using Amplifier. Tasks live in a public `TASKS.md` file in the repo. Team rosters and capabilities ("superpowers") live in a private `.amplifier/team.yaml` file (gitignored). Anyone on the team -- human or AI -- can add, claim, complete, and reassign tasks.

## Global Preferences

These conventions apply across ALL projects using this tool:

| Preference | Value | Rationale |
|------------|-------|-----------|
| Task file | `TASKS.md` at repo root | Visible, GitHub-rendered, PR-friendly |
| Team file | `.amplifier/team.yaml` | Private, gitignored, per-repo |
| Team backup | dev-memory | Restore from memory if team.yaml lost |
| Task IDs | Prefixed: `{PROJECT}-{NNN}` | Cross-project visibility (e.g., `DISTRO-001`) |
| Superpowers | Free-form tags | No fixed taxonomy, team-defined |
| Modification | Open (anyone: human or AI) | Honor system, no gatekeeper |
| Roadmap integration | Tasks reference phases via tags | Roadmap stays high-level, tasks are granular |
| Format | Markdown with checkboxes | Human-readable, GitHub-native, clean diffs |

## File Formats

### TASKS.md (Public, Committed)

```markdown
# Tasks: {project-name}

<!-- project-id: {PREFIX} -->
<!-- repo: {org/repo} -->
<!-- managed with amplifier project-mgmt skill -->

## Active

- [ ] **{PREFIX}-001**: Short description of the task
  - Assigned: @github_handle
  - Priority: high | medium | low
  - Added: YYYY-MM-DD
  - Tags: phase-1, area-name

## Backlog

- [ ] **{PREFIX}-002**: Something planned but not yet started
  - Priority: medium
  - Tags: phase-2, area-name

## Completed

- [x] **{PREFIX}-003**: Something finished
  - Assigned: @github_handle
  - Completed: YYYY-MM-DD
  - Tags: phase-0
```

**Rules:**
- Tasks move between sections: Backlog -> Active -> Completed
- `Assigned` is optional (unassigned tasks are fair game)
- `Priority` is one of: `high`, `medium`, `low`
- `Tags` are free-form, but should include phase references where applicable
- `Added` and `Completed` dates use YYYY-MM-DD
- Task IDs are monotonically increasing within a project, never reused

### .amplifier/team.yaml (Private, Gitignored)

```yaml
# Team roster and capabilities - PRIVATE (gitignored)
project: {project-name}
project_id: {PREFIX}
repos:
  - org/repo-name

team:
  - name: Full Name
    github: github_handle
    role: lead | contributor | advisor
    superpowers:
      - free-form-skill-tag
      - another-skill
    current_load: low | medium | high  # inferred from active task count

# Load inference rules (auto-updated by AI):
# 0 active tasks = low
# 1-2 active tasks = medium
# 3+ active tasks = high
```

## Commands (Natural Language)

The AI recognizes these patterns. No special syntax needed.

### Task Management

| User says | AI does |
|-----------|---------|
| "Add a task: {description}" | Appends to Active or Backlog (based on urgency), auto-generates next ID |
| "Add to backlog: {description}" | Appends to Backlog section |
| "I'll take {ID}" or "Assign {ID} to me" | Sets `Assigned: @user` on that task |
| "Assign {ID} to @user" | Sets `Assigned: @user` |
| "{ID} is done" or "Close {ID}" | Moves to Completed, checks box, adds completion date |
| "Reopen {ID}" | Moves back to Active, unchecks box, removes completion date |
| "Drop {ID}" or "Unassign {ID}" | Removes assignment |
| "Change priority of {ID} to high" | Updates priority field |
| "Add tag {tag} to {ID}" | Appends to tags list |

### Queries

| User says | AI does |
|-----------|---------|
| "Show me the board" or "Task status" | Summary: active/backlog/completed counts, who's working on what |
| "What should I work on?" | Recommends tasks based on user's superpowers, current load, and priority |
| "Who should do what?" | Full assignment recommendation for all unassigned tasks |
| "What's blocking?" | High-priority unassigned tasks, overloaded team members |
| "What's @user working on?" | Lists their active assignments |
| "Show backlog" | Lists all backlog items |

### Team Management

| User says | AI does |
|-----------|---------|
| "Add @user to the team" | Adds to team.yaml with empty superpowers |
| "Set superpowers for @user: x, y, z" | Updates superpowers list in team.yaml |
| "{User}'s superpower is {skill}" | Appends to their superpowers |
| "Update load for @user" | Recalculates based on active task count |

### Project Setup

| User says | AI does |
|-----------|---------|
| "Set up project management for {repo}" | Creates TASKS.md + .amplifier/team.yaml, adds to .gitignore |
| "Initialize tasks from {file}" | Parses existing roadmap/TODO into TASKS.md format |

## Assignment Algorithm

When recommending "who should do what," the AI considers:

### Inputs
1. **Superpowers** - Does the person have relevant skills for this task?
2. **Current load** - How many active tasks do they have?
3. **Priority** - Higher priority tasks get assigned first
4. **Tags** - Match task tags against superpowers (fuzzy)
5. **Role** - Leads get complex/architectural tasks, contributors get focused work

### Scoring (Conceptual)
```
score = superpower_match * 3 + (1 / (load + 1)) * 2 + priority_weight
```

- **superpower_match**: How many of the person's superpowers overlap with task tags (0-1 normalized)
- **load**: Current active task count (lower = more available)
- **priority_weight**: high=3, medium=2, low=1

### Output Format
```
Recommended assignments:

DISTRO-005 "Implement voice WebRTC testing" -> @robotdad
  Reason: Superpowers match (webrtc, testing), low load (1 active task)

DISTRO-006 "Slack emoji reaction handling" -> @dluc
  Reason: Superpowers match (slack, integrations), medium load (2 active tasks)

DISTRO-007 "Setup CI pipeline" -> unassigned (no strong match)
  Reason: No team member has CI/devops superpowers. Consider adding capability.
```

## Workflow Integration

### With Existing Roadmaps
Tasks should reference phases from the project roadmap via tags:
- `Tags: phase-0, core` means this task is part of Phase 0
- The roadmap (in AGENTS.md or ROADMAP.md) stays as the high-level plan
- TASKS.md is the granular execution layer

### With Git
- TASKS.md changes can be committed directly or via PR
- Task state changes make clean, readable diffs
- Team members can review task assignments in PRs

### Cross-Project Views
Task IDs are prefixed (e.g., `DISTRO-001`, `TOOLKIT-001`) so that:
- A unified view across projects is possible
- References in conversations are unambiguous
- "What's @user working on across all projects?" becomes answerable

## Recovery

If `.amplifier/team.yaml` is lost:
1. Check dev-memory: "what do you remember about {project} team?"
2. Reconstruct from memory backup
3. Ask team members to re-confirm superpowers

## Anti-Patterns

- **Don't over-tag**: 2-4 tags per task is plenty
- **Don't micro-manage load**: Let the AI infer it from task counts
- **Don't gate on AI**: Anyone can edit TASKS.md directly -- the AI is a helper, not a bottleneck
- **Don't duplicate the roadmap**: Tasks reference phases, they don't restate the roadmap
