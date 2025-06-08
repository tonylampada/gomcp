"""Main entry point for simple MCP server with GitHub OAuth authentication."""

import sys

from mcp_simple_auth.server import main

if __name__ == "__main__":
    # Click will handle command line arguments
    main()