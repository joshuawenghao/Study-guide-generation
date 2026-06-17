---
name: feedback_update_codebase_state
description: Always update CODEBASE_STATE.md alongside TASK_STATUS.md when completing tasks
metadata:
  type: feedback
---

Always update `CODEBASE_STATE.md` (the live plain-language codebase summary) when closing a task, in addition to `TASK_STATUS.md`. Both files must be updated before the task commit is made.

**Why:** The user flagged that tasks 22.1 and 22.2 were committed without updating CODEBASE_STATE.md, leaving the live summary out of sync with shipped code.

**How to apply:** After the done gate passes, update both `TASK_STATUS.md` (task-level status) and `CODEBASE_STATE.md` (codebase narrative) before running `git commit`. Add a bullet to the Executive Summary for significant changes, add entries under the relevant "Shipped Frontend" or "Shipped Backend" section, and update "Current Product Gaps" if the work closes a known gap.
