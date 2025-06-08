"""Simple MCP Server with GitHub OAuth Authentication."""

import logging
import secrets
import time
from typing import Any, Literal

import click
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.applications import Starlette

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp.server import FastMCP
from mcp.shared._httpx_utils import create_mcp_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

logger = logging.getLogger(__name__)


class ServerSettings(BaseSettings):
    """Settings for the simple GitHub MCP server."""

    model_config = SettingsConfigDict(env_prefix="MCP_GITHUB_", env_file=".env")

    # Server settings
    host: str = "0.0.0.0"
    port: int = 9090
    server_url: AnyHttpUrl = AnyHttpUrl("https://mcp.evolutio.io")

    # GitHub OAuth settings - MUST be provided via environment variables
    github_client_id: str  # Type: MCP_GITHUB_GITHUB_CLIENT_ID env var
    github_client_secret: str  # Type: MCP_GITHUB_GITHUB_CLIENT_SECRET env var
    github_callback_path: str = "https://mcp.evolutio.io/github/callback"
    

    # GitHub OAuth URLs
    github_auth_url: str = "https://github.com/login/oauth/authorize"
    github_token_url: str = "https://github.com/login/oauth/access_token"

    mcp_scope: str = "claudeai"
    github_scope: str = "read:user"

    def __init__(self, **data):
        """Initialize settings with values from environment variables.

        Note: github_client_id and github_client_secret are required but can be
        loaded automatically from environment variables (MCP_GITHUB_GITHUB_CLIENT_ID
        and MCP_GITHUB_GITHUB_CLIENT_SECRET) and don't need to be passed explicitly.
        """
        super().__init__(**data)


class SimpleGitHubOAuthProvider(OAuthAuthorizationServerProvider):
    """Simple GitHub OAuth provider with essential functionality."""

    def __init__(self, settings: ServerSettings):
        self.settings = settings
        self.clients: dict[str, OAuthClientInformationFull] = {}
        self.auth_codes: dict[str, AuthorizationCode] = {}
        self.tokens: dict[str, AccessToken] = {}
        self.state_mapping: dict[str, dict[str, str]] = {}
        # Store GitHub tokens with MCP tokens using the format:
        # {"mcp_token": "github_token"}
        self.token_mapping: dict[str, str] = {}
        
        # Pre-register the cached client ID from Claude.ai
        from mcp.shared.auth import OAuthClientInformationFull
        from pydantic import AnyUrl
        cached_client = OAuthClientInformationFull(
            client_id="91be729f-30be-4614-b93f-f2b4a7ec8a98",
            redirect_uris=[AnyUrl("https://claude.ai/api/mcp/auth_callback")],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="none",
            scope="claudeai",
            client_name="claudeai"
        )
        self.clients[cached_client.client_id] = cached_client

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """Get OAuth client information."""
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull):
        """Register a new OAuth client."""
        logger.info(f"=== CLIENT REGISTRATION ===")
        logger.info(f"Client ID: {client_info.client_id}")
        logger.info(f"Redirect URIs: {client_info.redirect_uris}")
        logger.info(f"Grant types: {client_info.grant_types}")
        logger.info(f"Response types: {client_info.response_types}")
        logger.info(f"Token auth method: {client_info.token_endpoint_auth_method}")
        logger.info(f"Scope: {client_info.scope}")
        logger.info(f"Full client info: {client_info}")
        self.clients[client_info.client_id] = client_info

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Generate an authorization URL for GitHub OAuth flow."""
        state = params.state or secrets.token_hex(16)

        # Store the state mapping
        self.state_mapping[state] = {
            "redirect_uri": str(params.redirect_uri),
            "code_challenge": params.code_challenge,
            "redirect_uri_provided_explicitly": str(
                params.redirect_uri_provided_explicitly
            ),
            "client_id": client.client_id,
        }

        # Build GitHub authorization URL
        auth_url = (
            f"{self.settings.github_auth_url}"
            f"?client_id={self.settings.github_client_id}"
            f"&redirect_uri={self.settings.github_callback_path}"
            f"&scope={self.settings.github_scope}"
            f"&state={state}"
        )

        return auth_url

    async def handle_github_callback(self, code: str, state: str) -> str:
        """Handle GitHub OAuth callback."""
        state_data = self.state_mapping.get(state)
        if not state_data:
            raise HTTPException(400, "Invalid state parameter")

        redirect_uri = state_data["redirect_uri"]
        code_challenge = state_data["code_challenge"]
        redirect_uri_provided_explicitly = (
            state_data["redirect_uri_provided_explicitly"] == "True"
        )
        client_id = state_data["client_id"]

        # Exchange code for token with GitHub
        async with create_mcp_http_client() as client:
            response = await client.post(
                self.settings.github_token_url,
                data={
                    "client_id": self.settings.github_client_id,
                    "client_secret": self.settings.github_client_secret,
                    "code": code,
                    "redirect_uri": self.settings.github_callback_path,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                raise HTTPException(400, "Failed to exchange code for token")

            data = response.json()

            if "error" in data:
                raise HTTPException(400, data.get("error_description", data["error"]))

            github_token = data["access_token"]

            # Create MCP authorization code
            new_code = f"mcp_{secrets.token_hex(16)}"
            auth_code = AuthorizationCode(
                code=new_code,
                client_id=client_id,
                redirect_uri=AnyHttpUrl(redirect_uri),
                redirect_uri_provided_explicitly=redirect_uri_provided_explicitly,
                expires_at=time.time() + 300,
                scopes=[self.settings.mcp_scope],
                code_challenge=code_challenge,
            )
            self.auth_codes[new_code] = auth_code

            # Store GitHub token - we'll map the MCP token to this later
            self.tokens[github_token] = AccessToken(
                token=github_token,
                client_id=client_id,
                scopes=[self.settings.github_scope],
                expires_at=None,
            )

        del self.state_mapping[state]
        return construct_redirect_uri(redirect_uri, code=new_code, state=state)

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        """Load an authorization code."""
        return self.auth_codes.get(authorization_code)

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        """Exchange authorization code for tokens."""
        if authorization_code.code not in self.auth_codes:
            raise ValueError("Invalid authorization code")

        # Generate MCP access token
        mcp_token = f"mcp_{secrets.token_hex(32)}"

        # Store MCP token
        self.tokens[mcp_token] = AccessToken(
            token=mcp_token,
            client_id=client.client_id,
            scopes=authorization_code.scopes,
            expires_at=int(time.time()) + 3600,
        )

        # Find GitHub token for this client
        github_token = next(
            (
                token
                for token, data in self.tokens.items()
                # see https://github.blog/engineering/platform-security/behind-githubs-new-authentication-token-formats/
                # which you get depends on your GH app setup.
                if (token.startswith("ghu_") or token.startswith("gho_"))
                and data.client_id == client.client_id
            ),
            None,
        )

        # Store mapping between MCP token and GitHub token
        if github_token:
            self.token_mapping[mcp_token] = github_token

        del self.auth_codes[authorization_code.code]

        return OAuthToken(
            access_token=mcp_token,
            token_type="bearer",
            expires_in=3600,
            scope=" ".join(authorization_code.scopes),
        )

    async def load_access_token(self, token: str) -> AccessToken | None:
        """Load and validate an access token."""
        access_token = self.tokens.get(token)
        if not access_token:
            return None

        # Check if expired
        if access_token.expires_at and access_token.expires_at < time.time():
            del self.tokens[token]
            return None

        return access_token

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        """Load a refresh token - not supported."""
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Exchange refresh token"""
        raise NotImplementedError("Not supported")

    async def revoke_token(
        self, token: str, token_type_hint: str | None = None
    ) -> None:
        """Revoke a token."""
        if token in self.tokens:
            del self.tokens[token]


def create_simple_mcp_server(settings: ServerSettings) -> FastMCP:
    """Create a simple FastMCP server with GitHub OAuth."""
    oauth_provider = SimpleGitHubOAuthProvider(settings)

    auth_settings = AuthSettings(
        issuer_url=settings.server_url,
        client_registration_options=ClientRegistrationOptions(
            enabled=True,
            valid_scopes=["user", "claudeai"],
            default_scopes=["user"],
        ),
        required_scopes=[],  # Don't require auth for discovery
    )

    app = FastMCP(
        name="Simple GitHub MCP Server",
        instructions="A simple MCP server with GitHub OAuth authentication",
        host=settings.host,
        port=settings.port,
        debug=True,
        cors=True,  # Enable CORS for remote access
    )
    
    

    @app.custom_route("/", methods=["GET"])
    async def root_endpoint(request: Request) -> Response:
        """Root endpoint for MCP discovery."""
        return JSONResponse({
            "mcp": {
                "version": "1.0"
            },
            "transport": {
                "type": "sse",
                "endpoint": "/sse"
            }
        })
    
    @app.custom_route("/debug/test", methods=["GET"])
    async def debug_test(request: Request) -> Response:
        """Test endpoint."""
        return JSONResponse({"status": "ok", "server": "Simple GitHub MCP Server"})
    
    
    
    @app.custom_route("/sse", methods=["GET"])
    async def debug_sse(request: Request) -> Response:
        """Debug SSE endpoint."""
        logger.info(f"=== SSE REQUEST ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"URL: {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        access_token = None
        try:
            access_token = get_access_token()
            logger.info(f"SSE Access token: {access_token}")
        except Exception as e:
            logger.info(f"SSE Auth error: {e}")
        return JSONResponse({"error": "debug_sse_endpoint", "authenticated": access_token is not None}, status_code=400)
    
    
    # Add OAuth endpoints manually
    @app.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
    async def oauth_discovery(request: Request) -> Response:
        """OAuth authorization server discovery."""
        base_url = str(settings.server_url).rstrip('/')  # Remove trailing slash
        return JSONResponse({
            "issuer": f"{base_url}/",
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/token",
            "registration_endpoint": f"{base_url}/register",
            "scopes_supported": ["user", "claudeai"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": ["client_secret_post"],
            "code_challenge_methods_supported": ["S256"]
        })

    @app.custom_route("/authorize", methods=["GET"])
    async def oauth_authorize(request: Request) -> Response:
        """OAuth authorization endpoint."""
        # Extract parameters
        client_id = request.query_params.get("client_id")
        redirect_uri = request.query_params.get("redirect_uri")
        state = request.query_params.get("state")
        scope = request.query_params.get("scope", "")
        code_challenge = request.query_params.get("code_challenge")
        
        if not client_id:
            raise HTTPException(400, "Missing client_id")
            
        # Get client info
        client = await oauth_provider.get_client(client_id)
        if not client:
            raise HTTPException(400, "Invalid client_id")
            
        # Create authorization params
        from mcp.server.auth.provider import AuthorizationParams
        from pydantic import AnyHttpUrl
        params = AuthorizationParams(
            redirect_uri=AnyHttpUrl(redirect_uri) if redirect_uri else None,
            state=state,
            code_challenge=code_challenge,
            redirect_uri_provided_explicitly=bool(redirect_uri),
            scopes=scope.split() if scope else []  # Add required scopes field
        )
        
        # Get GitHub auth URL
        auth_url = await oauth_provider.authorize(client, params)
        return RedirectResponse(auth_url)

    @app.custom_route("/token", methods=["POST"])
    async def oauth_token(request: Request) -> Response:
        """OAuth token endpoint."""
        form = await request.form()
        grant_type = form.get("grant_type")
        code = form.get("code")
        client_id = form.get("client_id")
        code_verifier = form.get("code_verifier")
        
        if grant_type != "authorization_code":
            raise HTTPException(400, "Unsupported grant type")
            
        if not code or not client_id:
            raise HTTPException(400, "Missing required parameters")
            
        # Get client
        client = await oauth_provider.get_client(client_id)
        if not client:
            raise HTTPException(400, "Invalid client")
            
        # Load authorization code
        auth_code = await oauth_provider.load_authorization_code(client, code)
        if not auth_code:
            raise HTTPException(400, "Invalid authorization code")
            
        # Exchange for token
        token = await oauth_provider.exchange_authorization_code(client, auth_code)
        return JSONResponse({
            "access_token": token.access_token,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
            "scope": token.scope
        })

    @app.custom_route("/github/callback", methods=["GET"])
    async def github_callback_handler(request: Request) -> Response:
        """Handle GitHub OAuth callback."""
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            raise HTTPException(400, "Missing code or state parameter")

        try:
            redirect_uri = await oauth_provider.handle_github_callback(code, state)
            return RedirectResponse(status_code=302, url=redirect_uri)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error", exc_info=e)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "server_error",
                    "error_description": "Unexpected error",
                },
            )

    def get_github_token_for_mcp_token(mcp_token: str) -> str:
        """Get the GitHub token for the given MCP token."""
        if not mcp_token:
            raise ValueError("No MCP token provided")
            
        # Check if MCP token is valid
        access_token = oauth_provider.tokens.get(mcp_token)
        if not access_token:
            raise ValueError("Invalid MCP token")
            
        # Check if token is expired
        if access_token.expires_at and access_token.expires_at < time.time():
            raise ValueError("MCP token expired")

        # Get GitHub token from mapping
        github_token = oauth_provider.token_mapping.get(mcp_token)
        if not github_token:
            raise ValueError("No GitHub token found for user")

        return github_token

    @app.tool()
    async def get_user_profile(mcp_token: str = "") -> dict[str, Any]:
        """Get the authenticated user's GitHub profile information.

        This tool shows your GitHub profile after OAuth authentication.
        Requires GitHub OAuth authentication to function.
        
        Args:
            mcp_token: The MCP authentication token (optional, for manual testing)
        """
        logger.info("=== TOOL CALLED: get_user_profile ===")
        try:
            # For now, just return a simple response to test tool discovery
            return {
                "message": "Tool is visible! OAuth authentication would be required for actual GitHub profile data.",
                "status": "discoverable",
                "auth_required": True,
                "oauth_url": f"{settings.server_url}/.well-known/oauth-authorization-server"
            }
        except Exception as e:
            logger.error(f"Tool error: {e}", exc_info=True)
            raise
    
    # Log tools that are registered
    logger.info(f"=== MCP SERVER CREATED ===")
    logger.info(f"Server initialized with SSE transport")

    return app


@click.command()
@click.option("--port", default=9090, help="Port to listen on")
@click.option("--host", default="localhost", help="Host to bind to")
@click.option(
    "--transport",
    default="sse",
    type=click.Choice(["sse", "streamable-http"]),
    help="Transport protocol to use ('sse' or 'streamable-http')",
)
def main(port: int, host: str, transport: Literal["sse", "streamable-http"]) -> int:
    """Run the simple GitHub MCP server."""
    print(f"Starting MCP server on {host}:{port} with {transport} transport...")
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        print("Loading settings from environment...")
        # No hardcoded credentials - all from environment variables
        settings = ServerSettings(host=host, port=port)
        print(f"Settings loaded successfully: host={settings.host}, port={settings.port}")
    except ValueError as e:
        print(f"ERROR: Failed to load settings: {e}")
        logger.error(
            "Failed to load settings. Make sure environment variables are set:"
        )
        logger.error("  MCP_GITHUB_GITHUB_CLIENT_ID=<your-client-id>")
        logger.error("  MCP_GITHUB_GITHUB_CLIENT_SECRET=<your-client-secret>")
        logger.error(f"Error: {e}")
        return 1

    print("Creating MCP server...")
    mcp_server = create_simple_mcp_server(settings)
    print("MCP server created successfully")
    
    logger.info(f"Starting server with {transport} transport")
    logger.info(f"MCP endpoints should be available at:")
    logger.info(f"  - SSE: https://mcp.evolutio.io/sse")
    logger.info(f"  - Messages: https://mcp.evolutio.io/messages/")
    logger.info(f"  - StreamableHTTP: https://mcp.evolutio.io/mcp")
    
    print(f"Server starting on http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        mcp_server.run(transport=transport)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"ERROR: Server crashed: {e}")
        raise
    
    return 0

