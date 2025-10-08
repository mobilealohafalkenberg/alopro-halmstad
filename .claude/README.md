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
- `/task` - Start work on a Jira task (fetch, branch, setup)

More commands coming soon!
