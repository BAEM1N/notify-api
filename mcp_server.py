"""Notify MCP Server — thin MCP wrapper over the Notify REST API.

Usage:
    uv run mcp_server.py
"""

from __future__ import annotations

import json
import os
from enum import Enum
from typing import Annotated

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NOTIFY_API_URL = os.getenv("NOTIFY_API_URL", "http://localhost:9009")

# ---------------------------------------------------------------------------
# Shared types (mirrors app/models.py, kept minimal)
# ---------------------------------------------------------------------------


class Channel(str, Enum):
    telegram = "telegram"
    email = "email"
    all = "all"


class Level(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(base_url=NOTIFY_API_URL, timeout=30.0)
    return _client


async def _api_request(method: str, path: str, **kwargs) -> dict:
    """Make a request to the Notify REST API and return the JSON response."""
    client = await _get_client()
    response = await client.request(method, path, **kwargs)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "notify_mcp",
    instructions=(
        "Notify MCP Server — send notifications to Telegram and Email "
        "via the BaeumAI Notify API. Use notify_health to check channel "
        "availability before sending."
    ),
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    annotations={
        "title": "Health Check",
        "readOnlyHint": True,
        "openWorldHint": True,
    },
)
async def notify_health() -> str:
    """Check the Notify API health and available channels.

    Returns the API status and which channels (Telegram, Email) are configured.
    Call this first to verify the API is reachable and channels are ready.
    """
    try:
        data = await _api_request("GET", "/health")
        return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.ConnectError:
        return json.dumps(
            {
                "error": f"Cannot connect to Notify API at {NOTIFY_API_URL}. "
                "Ensure the API is running and NOTIFY_API_URL is correct."
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool(
    annotations={
        "title": "Send Telegram Notification",
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def notify_send_telegram(
    title: Annotated[str, Field(description="Notification title (max 200 chars)", max_length=200)],
    message: Annotated[str, Field(description="Notification body (max 4000 chars)", max_length=4000)],
    level: Annotated[
        Level, Field(description="Severity level: info, warning, or critical")
    ] = Level.info,
    source: Annotated[
        str, Field(description="Source service identifier (e.g. 'claude-code', 'ci-pipeline')")
    ] = "",
) -> str:
    """Send a notification to Telegram.

    Requires Telegram Bot Token and Chat ID to be configured on the API server.
    Use notify_health first to check if Telegram is available.
    """
    try:
        data = await _api_request(
            "POST",
            "/notify/telegram",
            json={
                "title": title,
                "message": message,
                "level": level.value,
                "source": source,
            },
        )
        return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            return json.dumps(
                {
                    "error": "Telegram is not configured. "
                    "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the API server's .env file."
                }
            )
        return json.dumps({"error": f"HTTP {e.response.status_code}: {e.response.text}"})
    except httpx.ConnectError:
        return json.dumps(
            {"error": f"Cannot connect to Notify API at {NOTIFY_API_URL}."}
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool(
    annotations={
        "title": "Send Email Notification",
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def notify_send_email(
    title: Annotated[str, Field(description="Notification title (max 200 chars)", max_length=200)],
    message: Annotated[str, Field(description="Notification body (max 4000 chars)", max_length=4000)],
    level: Annotated[
        Level, Field(description="Severity level: info, warning, or critical")
    ] = Level.info,
    source: Annotated[
        str, Field(description="Source service identifier")
    ] = "",
    to: Annotated[
        str, Field(description="Recipient email address (uses default if empty)")
    ] = "",
) -> str:
    """Send a notification via Email.

    Requires SMTP credentials to be configured on the API server.
    Use notify_health first to check if Email is available.
    """
    try:
        data = await _api_request(
            "POST",
            "/notify/email",
            json={
                "title": title,
                "message": message,
                "level": level.value,
                "source": source,
                "to": to,
            },
        )
        return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            return json.dumps(
                {
                    "error": "Email is not configured. "
                    "Set SMTP_USER and SMTP_PASSWORD in the API server's .env file."
                }
            )
        return json.dumps({"error": f"HTTP {e.response.status_code}: {e.response.text}"})
    except httpx.ConnectError:
        return json.dumps(
            {"error": f"Cannot connect to Notify API at {NOTIFY_API_URL}."}
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool(
    annotations={
        "title": "Send Notification",
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def notify_send(
    title: Annotated[str, Field(description="Notification title (max 200 chars)", max_length=200)],
    message: Annotated[str, Field(description="Notification body (max 4000 chars)", max_length=4000)],
    channel: Annotated[
        Channel, Field(description="Target channel: telegram, email, or all")
    ] = Channel.telegram,
    level: Annotated[
        Level, Field(description="Severity level: info, warning, or critical")
    ] = Level.info,
    source: Annotated[
        str, Field(description="Source service identifier")
    ] = "",
) -> str:
    """Send a notification to one or multiple channels.

    This is the unified endpoint — use `channel` to target telegram, email, or all.
    Use notify_health first to check which channels are available.
    """
    try:
        data = await _api_request(
            "POST",
            "/notify",
            json={
                "channel": channel.value,
                "title": title,
                "message": message,
                "level": level.value,
                "source": source,
            },
        )
        return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.ConnectError:
        return json.dumps(
            {"error": f"Cannot connect to Notify API at {NOTIFY_API_URL}."}
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
