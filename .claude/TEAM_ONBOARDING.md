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

### Easy Method: Let Claude Help You! 🤖

1. **Generate API Token:**
   - Go to: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Name it: `Claude Code MCP`
   - **Copy the token** (you won't see it again!)

2. **Start Claude Code** in this repo directory

3. **Ask Claude to set it up:**
   ```
   Help me set up my Atlassian credentials for Jira integration
   ```

4. **Claude will:**
   - Detect your shell (bash/zsh)
   - Find the right config file (~/.bashrc or ~/.zshrc)
   - Ask for your email and API token
   - Add them securely to your shell config
   - Test that everything works
   - Tell you to restart Claude Code

5. **Restart Claude Code** and you're done! ✅

### Manual Method (If You Prefer)

If you'd rather do it manually:

**Step 1: Generate API Token** (same as above)

**Step 2: Configure Environment Variables**

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

**Step 3: Restart Claude Code**

Exit (Ctrl+D) and restart Claude Code for changes to take effect.

**Step 4: Verify Setup**

Test with:
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
