# Jira MCP Setup Guide for Team Members

This guide helps you set up Atlassian Jira integration with Claude Code so you can use the `/task` command and other Jira features.

## Prerequisites

- Claude Code installed
- Access to the ALOHAMOB Jira project
- Atlassian account with appropriate permissions

## Step 1: Generate Atlassian API Token

1. **Go to Atlassian Account Settings:**
   - Visit: https://id.atlassian.com/manage-profile/security/api-tokens
   - Or navigate to: Your Profile → Settings → Security → API Tokens

2. **Create API Token:**
   - Click "Create API token"
   - Label: `Claude Code MCP` (or any name you prefer)
   - Click "Create"
   - **IMPORTANT:** Copy the token immediately - you won't see it again!

3. **Store Securely:**
   - Save the token in a password manager
   - Never commit this token to git!

## Step 2: Install Atlassian MCP Server

The Atlassian MCP server should already be configured in the project's `.claude/config.json`, but you need to provide your own credentials.

### Option A: Using Environment Variables (Recommended)

1. **Add to your shell profile** (`~/.bashrc`, `~/.zshrc`, or `~/.profile`):

```bash
# Atlassian MCP Credentials
export ATLASSIAN_EMAIL="your-email@example.com"
export ATLASSIAN_API_TOKEN="your-api-token-here"
```

2. **Reload your shell:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

3. **Test the connection:**
```bash
# Start Claude Code and try:
echo $ATLASSIAN_EMAIL
echo $ATLASSIAN_API_TOKEN
```

### Option B: Using Claude Code Config (Alternative)

If you prefer, you can configure credentials directly in Claude Code's user config (not the project config).

**IMPORTANT:** Never add credentials to the project's `.claude/config.json` as it may be committed to git!

## Step 3: Verify Your Setup

1. **Start Claude Code** in this repository directory

2. **Test Jira connection:**
   ```
   Can you fetch task ALOHAMOB-39 from Jira?
   ```

3. **If successful, you should see:**
   - Task title and description
   - Status, assignee, and other details

4. **If it fails:**
   - Check your email and token are correct
   - Verify you have access to the ALOHAMOB project in Jira
   - Check the token hasn't expired

## Step 4: Using Jira Features

Once set up, you can:

### Fetch Tasks
```
/task ALOHAMOB-40
```

### Search Tasks
```
Show me all tasks in phase 2 that are in "To Do" status
```

### Update Tasks
```
Move ALOHAMOB-40 to "In Progress" and add comment "Starting work on race condition fix"
```

### Create Tasks
```
Create a new task in ALOHAMOB for fixing the camera timeout issue
```

## Required Jira Permissions

To use all features, you need these permissions in the ALOHAMOB project:

- ✅ **Browse Projects** - View issues
- ✅ **Create Issues** - Create new tasks
- ✅ **Edit Issues** - Update task details
- ✅ **Add Comments** - Comment on tasks
- ✅ **Transition Issues** - Change task status (To Do → In Progress → Done)
- ✅ **Link Issues** - Create relationships between tasks

**To request permissions:** Contact the project admin or team lead.

## Security Best Practices

1. **Never commit credentials:**
   - The `.gitignore` already excludes credential files
   - Always use environment variables or user-level config

2. **Use environment variables:**
   - Keep credentials in your shell profile
   - They won't be visible to others

3. **Rotate tokens regularly:**
   - Regenerate API tokens every 90 days
   - Revoke old tokens when creating new ones

4. **Don't share tokens:**
   - Each person should use their own API token
   - This ensures proper attribution in Jira

## Troubleshooting

### "Authentication failed"
- Verify email and token are correct
- Check token hasn't been revoked
- Ensure environment variables are loaded (`echo $ATLASSIAN_EMAIL`)

### "Permission denied"
- Contact project admin to grant permissions
- Verify you can access ALOHAMOB project in Jira web UI

### "MCP server not found"
- Check `.claude/config.json` exists in project root
- Verify Claude Code is started in the correct directory

### "Can't find Jira project"
- Verify the cloudId is correct for your Atlassian instance
- Try: `Show me accessible Atlassian resources`

## Getting Help

If you encounter issues:
1. Check this troubleshooting section
2. Verify your setup following Step 3
3. Ask in team chat/slack
4. Contact the person who set up the repository

---

**Setup complete!** You can now use Claude Code with full Jira integration. Try the `/task` command to get started!
