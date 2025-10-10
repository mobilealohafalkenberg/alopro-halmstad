# Development Workflow Guide

Quick reference for the standard development workflow using Claude Code and Jira integration.

## Overview

This workflow automates the entire task lifecycle from Jira to completion, including automatic CHANGELOG generation.

```
Jira Task → /task → Branch → Code → Test → /done → CHANGELOG → Commit → PR → Review → Merge
```

## Workflow Steps

### 1. Pick a Task from Jira

Browse tasks in the ALOHAMOB project or check the current sprint board.

**Recommended order:**
- Phase 1 (Arm Controller): Complete ✅
- Phase 2 (Gripper Controller): In Progress ⏳
- Start with HIGH priority tasks (2.6-2.9)

### 2. Start Work: `/task`

```bash
# Using task number (simplest)
/task 2.6

# Or using full Jira ID
/task ALOHAMOB-39
```

**Claude will automatically:**
1. ✅ Fetch task details from Jira
2. ✅ Verify you're on `dev` branch and it's up to date
3. ✅ Create feature branch: `feature/2-6-emergency-stop`
4. ✅ Update Jira status to "In Progress"
5. ✅ Add comment in Jira with branch name
6. ✅ Analyze task and identify files to modify
7. ✅ Create todo list from task description
8. ✅ Mark first todo as in_progress

**Example output:**
```
✅ Ready to work on Task 2.6!

📋 Task: ALOHAMOB-39 - Add Emergency Stop State Management
🌿 Branch: feature/2-6-emergency-stop
📊 Status: In Progress (updated in Jira)
⏱️  Estimated: 4-6 hours

📝 Todo List:
  ⏳ [In Progress] Add ERROR state to GripperState enum
  ⬜ [Pending] Implement emergency_stop() method
  ⬜ [Pending] Implement resume_after_stop() method
  ⬜ [Pending] Add ERROR state checks to movement methods
  ⬜ [Pending] Create test file
  ⬜ [Pending] Update CHANGELOG.md

💡 Files to modify:
- gemini-live/gripper_controller.py (lines 45-67, 89-102)
- gemini-live/test/test_gripper/test_emergency_stop.py (new)

What would you like to do first?
1. Read gripper_controller.py to understand current implementation
2. Start implementing changes
3. Explain the task in detail
```

### 3. Implement Changes

Work through the task requirements. Claude will help you:
- Read and understand existing code
- Implement changes following best practices
- Create test files with proper structure
- Follow project conventions and patterns

**Tips:**
- Update the todo list as you complete items
- Run tests incrementally
- Ask Claude to review code before finalizing

### 4. Complete Task: `/done`

```bash
/done
```

**Claude will automatically:**
1. ✅ Identify task from branch name (`feature/2-6-emergency-stop` → Task 2.6)
2. ✅ Review all changes with git diff
3. ✅ Run tests (if test file exists)
4. ✅ **Generate detailed CHANGELOG entry** following exact template:
   - Summary of what was accomplished
   - Problem that was identified
   - Solution implemented (with line numbers)
   - Before/after code snippets
   - Impact analysis
   - Files modified with line ranges
   - Testing instructions and status
5. ✅ Insert CHANGELOG entry in correct Phase section
6. ✅ Create commit with proper message format
7. ✅ Update Jira status to "Done"
8. ✅ Add completion comment in Jira
9. ✅ Offer to push branch
10. ✅ Suggest next task

**Example output:**
```
✅ Task 2.6 Complete!

📊 Jira: ALOHAMOB-39 → Done
💾 Commit: abc1234 "Task 2.6: Add emergency stop state management"
📝 CHANGELOG: Updated (Phase 2 section, 156 lines added)
🚀 Ready to push: origin/feature/2-6-emergency-stop

📋 CHANGELOG Entry Preview:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### Task 2.6: Add Emergency Stop State Management

**Date**: 2025-10-08
**Phase**: 2 (Gripper Controller)
**Task ID**: 2.6
**Author**: your-name
**Branch**: `feature/2-6-emergency-stop`

#### Summary
Implemented emergency stop functionality in gripper_controller.py...

#### Solution Implemented
1. **Added ERROR state** to GripperState enum (Line 45)
2. **Implemented emergency_stop()** method (Lines 89-102)
...

#### Testing
**Test File:** `test/test_gripper/test_emergency_stop.py`
**Test Status:** ✅ PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What would you like to do next?
1. Push branch to remote
2. Create pull request
3. Start next task (/task 2.7)
4. Keep working locally
```

### 5. Push and Create PR

After `/done` completes, you can:

**Option 1: Let Claude push and create PR**
```
Push branch and create PR
```

Claude will:
- Push branch to origin
- Create PR with description from CHANGELOG
- Provide PR URL

**Option 2: Push manually**
```bash
git push -u origin feature/2-6-emergency-stop
```

Then create PR on GitHub with the CHANGELOG entry as description.

### 6. Move to Next Task

```bash
/task 2.7
```

The cycle continues!

## Quick Reference

| Action | Command | What It Does |
|--------|---------|-------------|
| Start task | `/task 2.6` | Fetch from Jira, create branch, setup workspace |
| Complete task | `/done` | Test, CHANGELOG, commit, update Jira |
| Check status | `git status` | See current changes |
| Run tests | `cd test && python3 test_<component>/test_<feature>.py` | Validate implementation |

## CHANGELOG Structure (Auto-Generated)

When you run `/done`, Claude generates a CHANGELOG entry with:

✅ **Required Sections:**
- Date, Phase, Task ID, Author, Branch
- Summary (2-3 sentences)
- Problem Identified (bullet points)
- Solution Implemented (numbered steps with line numbers)
- Code Changes (before/after snippets)
- Impact (categorized impacts)
- Files Modified (with line ranges)
- Testing (test file, status, instructions)

✅ **Automatic Analysis:**
- Parses git diff for file changes and line numbers
- Extracts code snippets for before/after
- Identifies impact categories
- Formats consistently with existing entries

## Tips for Success

### Before Starting (`/task`)
- ✅ Ensure you're on `dev` branch
- ✅ Pull latest changes
- ✅ Check task dependencies in Jira

### During Development
- ✅ Follow the todo list created by `/task`
- ✅ Update todos as you complete items
- ✅ Run tests incrementally
- ✅ Ask Claude to review your changes

### Before Completing (`/done`)
- ✅ All tests pass
- ✅ Code follows project conventions
- ✅ No uncommitted debug code
- ✅ Ready for peer review

### After `/done`
- ✅ Review CHANGELOG entry for accuracy
- ✅ Push branch to remote
- ✅ Create PR with CHANGELOG as description
- ✅ Request peer review
- ✅ Start next task!

## Common Scenarios

### Scenario 1: Simple Bug Fix
```bash
/task 2.7              # Fix race condition
# ... implement fix ...
/done                  # Auto: test, CHANGELOG, commit, Jira update
# Push and create PR
```
**Time saved:** 15-20 minutes on CHANGELOG and commit formatting

### Scenario 2: Feature with Multiple Files
```bash
/task 2.9              # Add dry-run mode
# ... modify multiple files ...
# ... create tests ...
/done                  # Auto: comprehensive CHANGELOG with all files
# Push and create PR
```
**Time saved:** 25-30 minutes on detailed CHANGELOG and file tracking

### Scenario 3: Working on Multiple Tasks
```bash
/task 2.6              # Start first task
# ... implement ...
/done                  # Complete and document

/task 2.7              # Immediately start next
# ... implement ...
/done                  # Complete and document

# Both have complete CHANGELOG entries!
```
**Time saved:** Continuous workflow, no context switching

## Troubleshooting

### `/task` Issues

**Problem:** "Task not found"
```bash
# Try full Jira ID instead
/task ALOHAMOB-39
```

**Problem:** "Branch already exists"
```bash
# Delete old branch first
git branch -D feature/2-6-emergency-stop
/task 2.6
```

### `/done` Issues

**Problem:** "Tests failed"
```
# Fix tests first, then retry
/done
```

**Problem:** "CHANGELOG entry looks wrong"
```
# Ask Claude to regenerate
Can you review the CHANGELOG entry and update it?
```

**Problem:** "Can't update Jira"
```
# Continue anyway, update Jira manually
# Check your ATLASSIAN_API_TOKEN is valid
```

## Best Practices

1. **Use task numbers** (`/task 2.6`) - faster than full IDs
2. **Let `/done` generate CHANGELOG** - more consistent and complete
3. **Review before pushing** - check the auto-generated CHANGELOG
4. **Keep tasks small** - easier to document and review
5. **Test before `/done`** - ensures test status is accurate

## Getting Help

- **Workflow issues:** See this guide
- **Jira setup:** [JIRA_MCP_SETUP.md](JIRA_MCP_SETUP.md)
- **Command details:** [README.md](README.md)
- **Project conventions:** [../CLAUDE.md](../CLAUDE.md)
- **Team questions:** Ask in team chat

---

**Happy coding!** This workflow should save you 20-30 minutes per task on documentation and process overhead. 🚀
