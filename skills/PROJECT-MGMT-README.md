# Project Management with Amplifier

A lightweight, AI-native project management system that lives alongside your code.

## What Is This?

Instead of Jira, Linear, or a spreadsheet, your project tasks live in a `TASKS.md` file at the root of each repo. You manage tasks by talking to Amplifier in natural language -- or by editing the file directly. Either works.

The AI knows who's on the team, what their strengths are, and what they're currently working on. It can recommend assignments, flag overload, and keep the board up to date.

## Quick Start (For Team Members)

### 1. You already have access

If you can see the repo, you can see the task list. Open `TASKS.md` in the repo root. That's the board.

### 2. Claim a task

In any Amplifier session in the repo:

```
I'll take DISTRO-005
```

Or just edit `TASKS.md` directly and add `Assigned: @your_github_handle`.

### 3. Complete a task

```
DISTRO-005 is done
```

### 4. Add a task

```
Add a task: Implement retry logic for voice bridge reconnection
```

The AI will generate the next ID, pick a priority, and slot it into Active or Backlog.

### 5. Ask for recommendations

```
What should I work on?
```

The AI looks at your skills, your current load, and the priority of unassigned tasks, then recommends what to pick up next.

## Common Commands

Just talk naturally. These are patterns the AI recognizes, not exact syntax.

### Managing Tasks

| Say this | What happens |
|----------|-------------|
| "Add a task: {description}" | New task appended with auto-generated ID |
| "I'll take {ID}" | Task assigned to you |
| "{ID} is done" | Task moved to Completed section |
| "Reopen {ID}" | Moved back to Active |
| "Change priority of {ID} to high" | Priority updated |
| "Add tag containers to {ID}" | Tag appended |

### Asking Questions

| Say this | What happens |
|----------|-------------|
| "Show me the board" | Summary of all tasks by status |
| "What should I work on?" | Personalized recommendation |
| "Who should do what?" | Assignment recommendations for all unassigned tasks |
| "What's @marklicata working on?" | That person's active tasks |
| "What's blocking?" | High-priority unassigned tasks, overloaded members |

## How It Works

### TASKS.md (Public -- committed to the repo)

This is the task board. It's markdown with checkboxes, so GitHub renders it nicely. The format:

```markdown
## Active

- [ ] **DISTRO-010**: Onboarding and wizard flow design
  - Assigned: @samschillace
  - Priority: high
  - Added: 2026-02-10
  - Tags: ui-flows, onboarding

## Backlog

- [ ] **DISTRO-015**: TUI surface development
  - Priority: low
  - Tags: phase-2, tui

## Completed

- [x] **DISTRO-099**: Something finished
  - Assigned: @robotdad
  - Completed: 2026-02-10
```

Anyone can edit this file. Human or AI. No gatekeeping.

### Team roster (Private -- NOT committed)

The file `.amplifier/team.yaml` stores who's on the team and what their strengths are. It's gitignored so personal notes about skills stay private. You don't need to set this up yourself -- the project lead does it once. If it gets lost, it's backed up in dev-memory.

### Task IDs

Every task has a prefixed ID like `DISTRO-001` or `TOOLKIT-003`. The prefix comes from the project, and IDs are unique and never reused. This means you can reference tasks across projects unambiguously:

> "I'm blocked on DISTRO-017, which depends on CORE-042."

### Assignment Recommendations

When you ask "who should do what?", the AI scores each person against each unassigned task based on:

1. **Skill match** -- Do their superpowers overlap with the task's tags?
2. **Current load** -- How many active tasks do they already have?
3. **Priority** -- Higher priority tasks get assigned first
4. **Role** -- Leads get architectural tasks, contributors get focused work

It's a recommendation, not an order. You can always override.

## Editing Directly vs. Using Amplifier

Both work. The file is just markdown.

**Use Amplifier when:**
- You want auto-generated IDs and dates
- You want assignment recommendations
- You want to ask "what should I work on?"

**Edit directly when:**
- You're already in the file and it's faster
- You're doing a bulk reorganization
- You don't have an Amplifier session open

## Setting Up a New Project

If you're starting project management for a new repo:

```
Set up project management for ramparte/my-new-project
```

This creates:
- `TASKS.md` with the standard format
- `.amplifier/team.yaml` with an empty roster
- Adds `team.yaml` to `.gitignore`

## FAQ

**Q: Can I edit TASKS.md in a PR?**
Yes. Task changes make clean diffs. You can review assignments in PRs just like code.

**Q: What if two people edit TASKS.md at the same time?**
Standard git merge. Since tasks are separate lines, conflicts are rare and easy to resolve.

**Q: Do I need the project-mgmt skill loaded?**
The AI works best with it loaded (`load_skill(skill_name="project-mgmt")`), but even without it, TASKS.md is just markdown -- anyone can read and edit it.

**Q: How do tasks relate to the roadmap?**
Tasks reference roadmap phases via tags (e.g., `Tags: phase-2, bridges`). The roadmap stays high-level in ROADMAP.md; TASKS.md is the granular execution layer.

**Q: Where are my superpowers stored?**
In `.amplifier/team.yaml` (private, gitignored). Only the project lead manages this. If you're curious what the AI thinks your strengths are, just ask.
