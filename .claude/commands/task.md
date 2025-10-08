---
description: Start work on a Jira task - fetches task details, creates branch, and sets up workspace
args:
  - name: task_id
    description: Task identifier - either full Jira ID (ALOHAMOB-39) or task number (2.6)
    required: true
---

You are helping a developer start work on a Jira task. Follow these steps:

## Step 1: Parse and Find the Task

**Input received:** {{task_id}}

1. **Determine task identifier type:**
   - If it matches pattern "ALOHAMOB-##" → use directly as Jira issue key
   - If it matches pattern "#.#" or "#.##" (e.g., "2.6", "2.10") → search for task with this number in summary
   - Otherwise → treat as Jira issue key

2. **Search for the task:**
   - If task number format (e.g., "2.6"):
     - Search Jira: `project = ALOHAMOB AND summary ~ "{{task_id}}" ORDER BY created DESC`
     - Pick the most recent match
     - If multiple matches, show list and ask user to clarify
     - If no matches, inform user and suggest checking task number

   - If Jira issue key format:
     - Fetch directly: `getJiraIssue(ALOHAMOB-##)`

3. **Display task summary:**
   - Show: Issue Key, Task Number, Title, Status, Priority, Assignee
   - Show: Description (truncated if long)
   - Confirm with user: "Is this the correct task?"

## Step 2: Create Feature Branch

Once task is confirmed:

1. **Ensure clean working state:**
   - Check git status
   - Warn if there are uncommitted changes
   - Ask user if they want to stash changes

2. **Update dev branch:**
   ```bash
   git checkout dev
   git pull origin dev
   ```

3. **Determine branch type from task:**
   - Look at task summary/title for keywords:
     - "Fix", "Bug" → `fix/`
     - "Test", "Testing" → `test/`
     - "Refactor", "Cleanup" → `refactor/`
     - "Doc", "Documentation" → `docs/`
     - Default → `feature/`

4. **Generate branch name:**
   - Format: `<type>/<phase>-<task-number>-<brief-description>`
   - Examples:
     - Task "2.6 Add Emergency Stop State Management" → `feature/2-6-emergency-stop`
     - Task "2.7 Fix Race Condition in Gripper Position Monitor" → `fix/2-7-race-condition`
     - Task "2.10 Add Parameter Validation" → `feature/2-10-parameter-validation`

   - Rules for description:
     - Take first 3-5 words from task title (after task number)
     - Remove common words: "Add", "the", "to", "for", "in"
     - Convert to kebab-case
     - Keep it short (max 4 words)

5. **Create and checkout branch:**
   ```bash
   git checkout -b <branch-name>
   ```

6. **Confirm branch created:**
   - Show: `✓ Branch created: <branch-name>`

## Step 3: Update Jira Task Status

**If user has write permissions:**

1. **Get available transitions:**
   - Fetch transitions for the task
   - Look for "In Progress" or "Start Progress" transition

2. **Transition to In Progress:**
   - Move task to "In Progress" status
   - Show: `✓ Task status updated to "In Progress"`

3. **Add comment to task:**
   ```
   Started work on this task
   Branch: <branch-name>

   🤖 Generated with Claude Code
   ```

**If permission error:**
- Skip status update
- Inform user they can update manually in Jira

## Step 4: Analyze Task and Set Up Workspace

1. **Read task description carefully:**
   - Identify files that need to be modified
   - Look for test file requirements
   - Note any dependencies on other tasks

2. **Locate relevant files:**
   - Use Glob to find files mentioned in description
   - Example: If task mentions "gripper_controller.py", locate it
   - Show list of files found

3. **Ask user what they want:**
   ```
   I found these files related to this task:
   - gemini-live/gripper_controller.py
   - gemini-live/test/test_gripper/test_emergency_stop.py (needs creation)

   What would you like me to do?
   1. Read the relevant files
   2. Create test file scaffolding
   3. Show me the implementation plan
   4. Start implementing
   ```

## Step 5: Create Todo List

1. **Break down task description into steps:**
   - Parse "Steps to Fix" section from task description
   - Create actionable todo items
   - Add estimated time if available

2. **Use TodoWrite to create list:**
   - Example for "2.6 Add Emergency Stop State Management":
     ```
     - Add ERROR state to GripperState enum
     - Implement emergency_stop() method
     - Implement resume_after_stop() method
     - Add ERROR state checks to movement methods
     - Create test file
     - Update CHANGELOG.md
     ```

3. **Mark first item as in_progress**

## Step 6: Final Summary

Show summary to user:

```
✅ Ready to work on Task {{task_id}}

📋 Task: ALOHAMOB-## - <Task Title>
🌿 Branch: <branch-name>
📊 Status: In Progress (updated in Jira)
⏱️  Estimated: <time> hours

📝 Todo List:
  ⏳ [In Progress] <First item>
  ⬜ [Pending] <Second item>
  ⬜ [Pending] <Third item>
  ...

💡 Next Steps:
- Start with: <first todo item>
- Files to modify: <file list>
- Test file: <test file path>

What would you like to do first?
```

## Error Handling

**If task not found:**
- Show: "❌ Could not find task matching '{{task_id}}'"
- Suggest: "Try using the full Jira ID (e.g., ALOHAMOB-39) or check the task number"
- Offer to search: "Would you like me to search for similar tasks?"

**If multiple matches found:**
- Show all matches with details
- Ask user to specify which one

**If git errors:**
- Show the error
- Suggest solutions
- Ask if they want to continue anyway

## Important Notes

- **Always confirm** the task with user before creating branch
- **Follow naming conventions** from CLAUDE.md
- **Check for dependencies** mentioned in task description
- **Be helpful** - offer to read files, explain code, or start implementing
- **Track progress** - keep todo list updated as work progresses

---

**Example Usage:**

```bash
# Using task number
/task 2.6

# Using full Jira ID
/task ALOHAMOB-39

# Both work the same way!
```
