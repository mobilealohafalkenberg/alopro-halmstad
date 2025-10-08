# Claude Code Configuration

This directory contains Claude Code configuration and team documentation.

## Files in this directory

- **JIRA_MCP_SETUP.md** - Complete guide for setting up Jira integration with your personal credentials
- **mcp-config-template.json** - Template MCP configuration (uses environment variables for credentials)
- **settings.local.json** - Project-specific permissions and settings
- **commands/** - Custom slash commands for the team

## For New Team Members

1. Read [JIRA_MCP_SETUP.md](JIRA_MCP_SETUP.md) to set up Jira integration
2. Configure your environment variables (never commit credentials!)
3. Test with: `/task ALOHAMOB-39`

## Security Notes

- **Never commit credentials** to this directory
- Use environment variables for sensitive data
- The `.gitignore` protects common credential file patterns
- Each team member should use their own Atlassian API token

## Current MCP Servers

- **Atlassian/Jira** - For task management and integration with ALOHAMOB project
  - Requires: `ATLASSIAN_EMAIL` and `ATLASSIAN_API_TOKEN` environment variables
  - See: [JIRA_MCP_SETUP.md](JIRA_MCP_SETUP.md)

## Available Slash Commands

See the `commands/` directory for available slash commands:

### `/task [task_id]`
Start work on a Jira task - fetches details, creates branch, sets up workspace

**Usage:**
```bash
/task 2.6              # Using task number (easiest!)
/task ALOHAMOB-39      # Using full Jira ID
```

**What it does:**
1. Fetches task from Jira (supports both task number and full ID)
2. Creates properly named feature branch
3. Updates task status to "In Progress" in Jira
4. Sets up workspace with relevant files
5. Creates todo list from task description
6. Asks how you'd like to proceed

### `/done`
Complete current task - updates CHANGELOG, commits, updates Jira

**Usage:**
```bash
/done
```

**What it does:**
1. Identifies task from current branch name
2. Reviews all changes made
3. Runs tests if applicable
4. **Generates detailed CHANGELOG entry** following project template
5. Commits all changes with proper message format
6. Updates Jira task to "Done" status
7. Offers to push branch and create PR
8. Suggests next task to work on

**CHANGELOG Generation:**
- Automatically follows the exact template from CHANGELOG.md
- Includes: Summary, Problem, Solution, Code Changes, Impact, Testing
- Adds proper line numbers and file references
- Maintains consistent formatting
