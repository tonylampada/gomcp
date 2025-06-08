# Simple MCP Server with GitHub OAuth Authentication

This MCP server demonstrates OAuth authentication using GitHub as the identity provider. It runs on port 9090 by default.

## Features

- GitHub OAuth authentication flow
- MCP-compliant OAuth token management
- Simple tool (`get_user_profile`) that requires authentication
- Support for both SSE and streamable-http transports

## Prerequisites

1. Create a GitHub OAuth App:
   - Go to GitHub Settings → Developer settings → OAuth Apps → New OAuth App
   - Set Application name: `MCP Simple Auth Demo`
   - Set Homepage URL: `http://localhost:9090`
   - Set Authorization callback URL: `http://localhost:9090/github/callback`
   - Click "Register application"
   - Note the Client ID and generate a new Client Secret

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

## Configuration

Set the following environment variables:

```bash
export MCP_GITHUB_GITHUB_CLIENT_ID="your_client_id_here"
export MCP_GITHUB_GITHUB_CLIENT_SECRET="your_client_secret_here"
```

## Running the Server

Run the server on port 9090 (default):

```bash
uv run mcp-simple-auth
```

Or specify a different port:

```bash
uv run mcp-simple-auth --port 8080
```

To use streamable-http transport instead of SSE:

```bash
uv run mcp-simple-auth --transport streamable-http
```

## Testing with Inspector

The easiest way to test this server is with the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

1. Install the inspector
2. Run the server with your GitHub OAuth credentials
3. Connect to `http://localhost:9090`
4. The inspector will guide you through the OAuth flow
5. Once authenticated, you can use the `get_user_profile` tool

## How It Works

1. **Client Registration**: MCP clients register with the server
2. **Authorization**: Server redirects to GitHub OAuth page
3. **Callback**: GitHub redirects back with auth code
4. **Token Exchange**: Server exchanges codes for tokens
5. **API Access**: Authenticated clients can call protected tools

The server maintains a mapping between MCP tokens and GitHub tokens, allowing it to make authenticated API calls on behalf of users.

## Troubleshooting

- **Port already in use**: Change the port with `--port` flag
- **Environment variables not set**: Check that both CLIENT_ID and CLIENT_SECRET are exported
- **GitHub callback error**: Ensure the callback URL in your GitHub app matches exactly
- **Token errors**: Tokens expire after 1 hour; re-authenticate if needed