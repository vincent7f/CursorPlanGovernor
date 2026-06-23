from __future__ import annotations

import os
import socket
from typing import Literal

DEFAULT_DB_URL = "sqlite:///./plan_governor.db"
DEFAULT_MCP_HOST = "0.0.0.0"
DEFAULT_MCP_PORT = 8000
DEFAULT_MCP_HTTP_PATH = "/mcp"
McpTransport = Literal["stdio", "sse", "streamable-http"]
DEFAULT_MCP_TRANSPORT: McpTransport = "streamable-http"
MCP_TRANSPORTS: frozenset[str] = frozenset({"stdio", "sse", "streamable-http"})


def get_db_url() -> str:
    return os.environ.get("PLAN_GOVERNOR_DB_URL", DEFAULT_DB_URL)


def get_mcp_host() -> str:
    return os.environ.get(
        "PLAN_GOVERNOR_MCP_HOST",
        os.environ.get("FASTMCP_HOST", DEFAULT_MCP_HOST),
    )


def get_mcp_port() -> int:
    raw = os.environ.get(
        "PLAN_GOVERNOR_MCP_PORT",
        os.environ.get("FASTMCP_PORT", str(DEFAULT_MCP_PORT)),
    )
    return int(raw)


def get_mcp_http_path() -> str:
    path = os.environ.get(
        "PLAN_GOVERNOR_MCP_HTTP_PATH",
        os.environ.get("FASTMCP_STREAMABLE_HTTP_PATH", DEFAULT_MCP_HTTP_PATH),
    )
    return path if path.startswith("/") else f"/{path}"


def get_mcp_transport() -> McpTransport:
    value = os.environ.get("PLAN_GOVERNOR_MCP_TRANSPORT", DEFAULT_MCP_TRANSPORT)
    if value in MCP_TRANSPORTS:
        return value
    return DEFAULT_MCP_TRANSPORT


def get_lan_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def build_mcp_http_url(host: str | None = None, port: int | None = None) -> str:
    bind_host = host or get_mcp_host()
    bind_port = port or get_mcp_port()
    path = get_mcp_http_path()
    if bind_host in ("0.0.0.0", "::", ""):
        client_host = get_lan_ip() or "127.0.0.1"
    else:
        client_host = bind_host
    return f"http://{client_host}:{bind_port}{path}"
