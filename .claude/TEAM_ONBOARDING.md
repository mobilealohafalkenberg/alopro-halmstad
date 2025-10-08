# Team Onboarding - Claude Code with Jira

Welcome! This guide helps you get started with Claude Code and Jira integration for the ALOHA project.

## What You Get

Once set up, you can:

- ✅ **Fetch Jira tasks** directly in Claude Code
- ✅ **Auto-create branches** from task details
- ✅ **Update task status** (To Do → In Progress → Done)
- ✅ **Add comments** to tasks
- ✅ **Search and filter** tasks
- ✅ **Use `/task` command** to start work instantly

## Prerequisites

1. **Claude Code installed** (you have this if you're reading this!)
2. **Access to ALOHAMOB Jira project** (request from team lead)
3. **Atlassian account** with appropriate permissions

## Setup Steps (5 minutes)

### Step 1: Generate API Token

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it: `Claude Code MCP`
4. **Copy the token** (you won't see it again!)
5. Save it securely (password manager recommended)

### Step 2: Configure Environment Variables

Add to your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
# Atlassian MCP Credentials
export ATLASSIAN_EMAIL="your-email@example.com"
export ATLASSIAN_API_TOKEN="your-api-token-here"
```

Reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Step 3: Verify Setup

Start Claude Code in this repo and test:

```
Can you fetch task ALOHAMOB-39 from Jira?
```

If you see task details, you're all set! 🎉

## Using Jira Features

### Start Work on a Task

```bash
/task ALOHAMOB-40
```

Claude will:
1. Fetch the task from Jira
2. Create a properly named branch
3. Set up your workspace
4. Create a todo list
5. Mark task as "In Progress" in Jira

### Other Commands

```bash
# Search for tasks
Show me all HIGH priority tasks in Phase 2

# Update task status
Move ALOHAMOB-40 to "In Progress"

# Add comments
Add comment to ALOHAMOB-40: "Fixed race condition issue"

# View task details
What are the details of ALOHAMOB-41?
```

## Troubleshooting

### "Authentication failed"
- Check email and token are correct
- Verify environment variables are set: `echo $ATLASSIAN_EMAIL`
- Reload shell after editing profile

### "Permission denied"
- Ensure you have access to ALOHAMOB project
- Request permissions from team lead
- Verify you can view the project in Jira web UI

### "Can't find MCP server"
- Make sure you're in the project directory
- Check `.claude/` directory exists
- Try restarting Claude Code

## Security Reminders

⚠️ **Never commit credentials to git!**
- Use environment variables only
- Check `.gitignore` includes credential files
- Keep your API token private

✅ **Best Practices:**
- Use your personal Atlassian account (not shared)
- Rotate API tokens every 90 days
- Store tokens in password manager
- Don't share tokens with others

## Need Help?

1. **Full setup guide:** See [JIRA_MCP_SETUP.md](JIRA_MCP_SETUP.md)
2. **Configuration details:** See [README.md](README.md)
3. **Ask the team:** Post in team chat/Slack
4. **Project docs:** Check [CLAUDE.md](../CLAUDE.md)

---

**Welcome to the team!** Once you're set up, you'll have powerful Jira integration right in Claude Code. Happy coding! 🚀
