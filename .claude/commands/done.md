---
description: Mark current task as complete - updates CHANGELOG, Jira status, commits changes, and prepares for PR
args: []
---

You are helping a developer complete their current task. Follow these steps:

## Step 1: Identify Current Task

1. **Get current git branch:**
   ```bash
   git branch --show-current
   ```

2. **Parse task number from branch name:**
   - Branch format: `<type>/<phase>-<task-number>-<description>`
   - Example: `feature/2-6-emergency-stop` → Task number is "2.6"
   - Extract the task number

3. **Search for Jira task:**
   - Search: `project = ALOHAMOB AND summary ~ "<task-number>"`
   - Find matching task
   - Confirm with user: "Working on Task ALOHAMOB-##: <title>?"

## Step 2: Review Changes

1. **Check git status:**
   ```bash
   git status
   ```

2. **Show summary of changes:**
   - List modified files
   - List new files
   - Show diff summary

3. **Ask user:**
   ```
   I see the following changes:
   Modified:
   - gemini-live/gripper_controller.py (lines 45-67, 89-102)
   - gemini-live/test/test_gripper/test_emergency_stop.py (new file)

   Untracked:
   - docs/MIGRATION_GUIDE.md

   Would you like me to review these changes and prepare completion?
   ```

## Step 3: Run Tests (if applicable)

1. **Check if test file exists for this task:**
   - Look in task description for test file path
   - Check `test/` directory for related tests

2. **Ask user:**
   ```
   Should I run tests before marking as done?
   - test/test_gripper/test_emergency_stop.py
   ```

3. **If user confirms, run tests:**
   ```bash
   cd gemini-live/test
   python3 test_gripper/test_emergency_stop.py
   ```

4. **Record test results:**
   - If tests pass: Note for CHANGELOG
   - If tests fail: Show errors, ask if they want to continue anyway

## Step 4: Generate CHANGELOG Entry

**Follow the exact structure from CHANGELOG.md:**

1. **Read the task details from Jira** to get:
   - Full task description
   - Steps that were supposed to be completed
   - Dependencies
   - Priority

2. **Analyze git diff** to identify:
   - Specific files modified
   - Line numbers changed
   - Nature of changes (added methods, fixed logic, etc.)

3. **Create CHANGELOG entry** following this template:

```markdown
### Task <task-number>: <Task Title from Jira>

**Date**: <YYYY-MM-DD>
**Phase**: <phase-number> (<Phase Name>)
**Task ID**: <task-number>
**Task Name**: <Task Title>
**Test File**: <test-file-path>
**Author**: <git-user-name>
**Branch**: `<branch-name>`

#### Summary
<2-3 sentences describing what was accomplished and why it was important>

#### Problem Identified
<Describe the issue that was fixed or feature that was missing>
- Bullet point 1
- Bullet point 2
- Bullet point 3

#### Solution Implemented
<Numbered list of changes made>
1. **<Action 1>** - <Description> (Line X or Lines X-Y)
2. **<Action 2>** - <Description> (Line X or Lines X-Y)
3. **<Action 3>** - <Description> (Line X or Lines X-Y)

#### Code Changes
**Before (Lines X-Y):**
```python
<relevant old code snippet if applicable>
```

**After (Lines X-Y):**
```python
<relevant new code snippet>
```

#### Impact
- **<Impact Category>**: <Description of impact>
- **<Impact Category>**: <Description of impact>

#### Files Modified
- `<file-path>` (lines X-Y, X-Y)
- `<file-path>` (lines X-Y)
- `<file-path>` (new file)

#### Testing
**Test File:** `<test-file-path>`
**Test Status:** ✅ PASS / ❌ FAIL / ⏳ PENDING

**To run test:**
```bash
cd gemini-live/test
python3 <test-file-path>
```

**Expected behavior:**
- <Expected result 1>
- <Expected result 2>

#### Dependencies
<If applicable, list any dependencies on other tasks>
- Depends on Task X.X
- Required for Task X.X

#### Next Steps
<If applicable, mention follow-up work or recommendations>
- [ ] <Next step 1>
- [ ] <Next step 2>

---
```

4. **Insert CHANGELOG entry:**
   - Find the correct Phase section in CHANGELOG.md
   - Add entry at the top of that phase section (after the phase header)
   - Maintain chronological order (newest first)

5. **Show preview to user:**
   ```
   I've generated the CHANGELOG entry. Here's a preview:

   ### Task 2.6: Add Emergency Stop State Management

   **Summary**: Implemented emergency stop functionality...

   Would you like me to:
   1. Insert this into CHANGELOG.md
   2. Let you review/edit it first
   3. Skip CHANGELOG update
   ```

## Step 5: Commit Changes

1. **Stage all relevant files:**
   ```bash
   git add <modified-files> CHANGELOG.md
   ```

2. **Create commit message:**
   - Format follows CLAUDE.md template:

   ```
   Task <task-number>: <Brief description>

   <Detailed explanation of changes>
   - Change 1
   - Change 2
   - Change 3

   Impact: <Brief impact summary>

   Test: <test-file-path>
   Status: PASS/FAIL

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: <user-name> <user-email>
   ```

3. **Get git user info:**
   ```bash
   git config user.name
   git config user.email
   ```

4. **Commit:**
   ```bash
   git commit -m "$(cat <<'EOF'
   <commit-message>
   EOF
   )"
   ```

5. **Show commit summary:**
   ```
   ✓ Committed: <commit-sha>
   Files: <count> files changed, <insertions> insertions(+), <deletions> deletions(-)
   ```

## Step 6: Update Jira Task

**If user has write permissions:**

1. **Get available transitions:**
   - Fetch transitions for the task
   - Look for "Done", "Complete", or "Close" transition

2. **Transition to Done:**
   - Move task to "Done" status
   - Show: `✓ Task marked as Done in Jira`

3. **Add completion comment:**
   ```
   Task completed ✓

   Branch: <branch-name>
   Commit: <commit-sha>

   Changes:
   - <file1> (lines X-Y)
   - <file2> (lines X-Y)

   Tests: PASS

   CHANGELOG entry added.

   🤖 Generated with Claude Code
   ```

**If permission error:**
- Skip status update
- Remind user to update manually in Jira

## Step 7: Prepare for Next Steps

1. **Ask user about next steps:**
   ```
   ✅ Task <task-number> Complete!

   📊 Jira: Marked as Done
   💾 Committed: <commit-sha>
   📝 CHANGELOG: Updated

   What would you like to do next?

   1. Push branch to remote (git push -u origin <branch>)
   2. Create pull request
   3. Start next task (/task <next-task>)
   4. Keep working locally
   ```

2. **If push:**
   ```bash
   git push -u origin <branch-name>
   ```
   - Show remote URL
   - Show PR creation link if GitHub

3. **If create PR:**
   - Check if `gh` CLI is available
   - Generate PR description from CHANGELOG entry
   - Create PR with formatted description

4. **Show final summary:**
   ```
   ✅ Task 2.6 Complete!

   📊 Jira: ALOHAMOB-39 → Done
   💾 Commit: abc1234
   📝 CHANGELOG: Updated (Phase 2 section)
   🚀 Pushed: origin/feature/2-6-emergency-stop
   🔗 PR: https://github.com/.../pull/##

   Summary of changes:
   - Added emergency stop state management
   - Created test file with 100% coverage
   - Updated safety constraints

   Ready for the next task? Suggested:
   - Task 2.7: Fix Race Condition in Gripper Position Monitor
   - Task 2.8: Deprecate Global Controller Singleton Pattern

   Try: /task 2.7
   ```

## Error Handling

**If no current task found:**
- Show: "❌ Couldn't determine current task from branch name"
- Suggest: "Are you on a task branch? Current branch: <branch>"

**If uncommitted changes:**
- Show warning
- Ask if they want to review/commit first

**If tests fail:**
- Show test output
- Ask: "Tests failed. Do you want to continue marking as done anyway?"
- Note in CHANGELOG: "Test Status: ❌ FAIL - See test output"

**If CHANGELOG.md doesn't exist:**
- Warn user
- Offer to create basic structure

**If git commit fails:**
- Show error
- Check for pre-commit hooks
- Ask if they want to retry with --no-verify

## Important Notes

- **Always follow CHANGELOG.md template exactly** - use the same format as existing entries
- **Be detailed in CHANGELOG** - include line numbers, before/after code, specific changes
- **Run tests if they exist** - don't mark done without testing
- **Update Jira automatically** - saves manual work
- **Generate helpful commit messages** - follow project conventions
- **Suggest next tasks** - help maintain workflow

## CHANGELOG Quality Checklist

Before finalizing, ensure CHANGELOG entry has:
- ✅ All required fields (Date, Phase, Task ID, Author, Branch)
- ✅ Clear Summary (2-3 sentences)
- ✅ Detailed Problem Identified section
- ✅ Numbered Solution Implemented steps with line numbers
- ✅ Code Changes with before/after (if applicable)
- ✅ Impact section with specific impacts
- ✅ Files Modified with line numbers
- ✅ Testing section with test file path and status
- ✅ Clear testing instructions
- ✅ Proper markdown formatting

---

**Example Usage:**

```bash
# After finishing work on task 2.6
/done

# Claude will:
# 1. Identify task from branch: feature/2-6-emergency-stop → Task 2.6
# 2. Review changes in gripper_controller.py
# 3. Run test/test_gripper/test_emergency_stop.py
# 4. Generate detailed CHANGELOG entry following template
# 5. Insert into CHANGELOG.md under Phase 2
# 6. Commit all changes with proper message
# 7. Update Jira to "Done" with comment
# 8. Offer to push and create PR
# 9. Suggest next task
```
