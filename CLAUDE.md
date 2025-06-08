# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server implementing GitHub OAuth authentication. The server is deployed at https://mcp.evolutio.io and provides OAuth-protected tools accessible via the MCP protocol.

## Development Setup

```bash
# Always use UV for package management
uv sync

# Set required environment variables
export MCP_GITHUB_GITHUB_CLIENT_ID="your_client_id_here"
export MCP_GITHUB_GITHUB_CLIENT_SECRET="your_client_secret_here"
```

## Common Commands

```bash
# Start server
./start_server.sh

# Monitor MCP protocol activity
./monitor_mcp.sh

# Stop server
./stop_server.sh

# Run server directly
uv run python -m mcp_simple_auth.server --transport streamable-http --port 9090 --host 0.0.0.0

# Run linting (if configured)
uv run ruff check .

# Run tests (if configured)
uv run pytest
```

## Architecture

### Core Components

1. **OAuth Provider** (`SimpleGitHubOAuthProvider` in `server.py`):
   - Handles GitHub OAuth flow
   - Manages token mapping between MCP tokens and GitHub tokens
   - Pre-registers Claude.ai client with ID: `91be729f-30be-4614-b93f-f2b4a7ec8a98`

2. **FastMCP Server**:
   - Uses `streamable-http` transport for production deployment
   - Requires `claudeai` scope for tool access
   - Exposes single tool: `get_user_profile`

3. **Key Endpoints**:
   - `/` - Root endpoint (returns server info)
   - `/mcp` - StreamableHTTP MCP endpoint
   - `/sse` - Server-sent events endpoint
   - `/messages/` - Messages endpoint
   - `/github/callback` - OAuth callback handler

### Important Configuration

- Server URL: `https://mcp.evolutio.io`
- Local port: `9090`
- Required OAuth scope: `claudeai`
- GitHub OAuth callback: `https://mcp.evolutio.io/github/callback`

## Current Issue: Tools Not Visible to Claude.ai

After successful OAuth authentication, Claude.ai reports "no tools available" despite:
- Authentication completing successfully
- Server having `get_user_profile` tool registered
- Correct `claudeai` scope being granted

See `MCP_TOOLS_PROGRESS.md` for investigation details and progress tracking.

## Important Notes

- Always use UV virtual environment for dependency management
- The server requires GitHub OAuth credentials to be set as environment variables
- Logs are stored in `logs/` directory with timestamps
- The `temp/` directory contains the full MCP Python SDK source for reference