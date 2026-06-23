from __future__ import annotations

import os
from typing import Literal

DEFAULT_DB_URL = "sqlite:///./plan_governor.db"
McpTransport = Literal["stdio", "sse", "streamable-http"]
DEFAULT_MCP_TRANSPORT: McpTransport = "stdio"
MCP_TRANSPORTS: frozenset[str] = frozenset({"stdio", "sse", "streamable-http"})


def get_db_url() -> str:
    return os.environ.get("PLAN_GOVERNOR_DB_URL", DEFAULT_DB_URL)


def get_mcp_transport() -> McpTransport:
    value = os.environ.get("PLAN_GOVERNOR_MCP_TRANSPORT", DEFAULT_MCP_TRANSPORT)
    if value in MCP_TRANSPORTS:
        return value
    return DEFAULT_MCP_TRANSPORT
