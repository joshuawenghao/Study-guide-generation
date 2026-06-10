---
description: "Runs the full autonomous implement → done gate → docs-drift loop for a single task, looping back on partial completion and stopping only on genuine blockers. Use when you want hands-off execution of a task end-to-end. Triggers on: 'run the loop', 'do the loop', 'autonomous loop', 'implement and close task', 'loop task [id]', 'run task [id] end to end'."
---

# Task Loop

Run the full autonomous delivery loop for a single task: implement → done gate → docs drift, looping back to implement if the done gate fails.

Usage: `/task-loop <task-id>`  (e.g. `/task-loop 4.1`)

If no task ID is given, pick the next `not started` task from `TASK_STATUS.md`.

## Loop Behaviour

Run the following cycle without stopping for user input unless a blocker requires a decision:

```
LOOP:
  1. Read TASKS.md and TASK_STATUS.md
  2. Follow task-implement instructions for the chosen task
  3. Follow task-done instructions (run done gate):
     - If COMPLETE  → proceed to step 4
     - If PARTIAL   → identify the smallest unfinished slice, go back to step 2
     - If BLOCKED   → stop and report the blocker clearly, wait for user input
  4. Follow docs-drift instructions
  5. Re-read TASK_STATUS.md
     - If more work remains on this task → go back to step 2
     - Otherwise → stop and report the outcome
```

## When To Stop Without Asking

Stop and report (do not loop back) when:

- The task is marked `complete` and docs are updated.
- `./scripts/validate-task.sh` fails with an error that is clearly outside the task slice (pre-existing debt) — record it and surface it.
- The done gate has failed **twice** on the same slice — surface the blocker rather than retrying blindly.

## When To Stop And Ask

Pause and wait for user input when:

- A contract type change requires paired frontend + backend edits that span a task boundary.
- The task description is ambiguous and cannot be resolved by reading existing code.
- An external prerequisite (e.g. a deployed service, an env var) is missing.
- Unrelated dirty files would be swept into a commit.

## Progress Updates

After each major step, emit a one-line status:
- `[implement] <what was done>`
- `[done-gate] complete | partial — <reason>`
- `[docs-drift] <what was updated>`

## Expected Final Output

1. Final task status and evidence.
2. Files changed.
3. Validation results.
4. Docs updated.
5. Whether a commit was created (only if the user has opted into iterative commits).
