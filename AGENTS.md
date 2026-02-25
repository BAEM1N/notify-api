# AGENTS.md — AI Agent Integration Guide

This file is designed for AI Agents (LLMs, autonomous agents, MCP tools) to quickly understand and use the Notify API.

## What This Service Does

Notify API is a self-hosted REST API that sends notifications to **Telegram** and **Email**. Any service, script, or AI Agent can call it to deliver alerts to humans.

## Base URL

```
http://<host>:9009
```

Replace `<host>` with the server IP or hostname where Notify API is running.

## Authentication

None required. The API is designed for internal/private network use.

## Endpoints

### GET /health

Check if the service is running and which channels are available.

**Response:**
```json
{"status": "ok", "channels": {"telegram": true, "email": false}}
```

### POST /notify/telegram

Send a Telegram message.

**Request Body (JSON):**
```json
{
  "title": "string (required, max 200)",
  "message": "string (required, max 4000)",
  "level": "info | warning | critical (optional, default: info)",
  "source": "string (optional, identifies the sender)"
}
```

**Response:**
```json
{"ok": true, "channels": {"telegram": true}, "errors": {}}
```

### POST /notify/email

Send an email. Requires SMTP to be configured on the server.

**Request Body (JSON):**
```json
{
  "title": "string (required, max 200)",
  "subject": "string (optional, alias of title for legacy clients)",
  "message": "string (required, max 4000)",
  "level": "info | warning | critical (optional, default: info)",
  "source": "string (optional)",
  "to": "string (optional, recipient email)"
}
```

Email sender profile is auto-selected from `source` keywords:
- `ddok.ai` → ddok sender profile
- `baeum.ai.kr`, `baeum.io.kr`, `baeum.ai` → baeum sender profile
- no match → baeum sender profile (default)

### POST /notify

Unified endpoint. Send to one or all channels.

**Request Body (JSON):**
```json
{
  "channel": "telegram | email | all (optional, default: telegram)",
  "title": "string (required, max 200)",
  "message": "string (required, max 4000)",
  "level": "info | warning | critical (optional, default: info)",
  "source": "string (optional)"
}
```

## Level Indicators

| Level | Emoji | Use When |
|-------|-------|----------|
| `info` | `ℹ️` | Normal events, completions, status updates |
| `warning` | `⚠️` | Degraded performance, approaching thresholds |
| `critical` | `🚨` | Service down, data loss risk, immediate action needed |

## Agent Usage Patterns

### Report task completion
```json
POST /notify/telegram
{"title": "Task Complete", "message": "Data pipeline finished. 1,234 records processed.", "level": "info", "source": "data-agent"}
```

### Report an error
```json
POST /notify/telegram
{"title": "Pipeline Failed", "message": "ETL job failed at transform stage: connection timeout to DB", "level": "critical", "source": "data-agent"}
```

### Send a periodic summary
```json
POST /notify/telegram
{"title": "Daily Summary", "message": "Processed: 50 tasks\nSuccess: 48\nFailed: 2\nAvg time: 3.2s", "level": "info", "source": "orchestrator"}
```

### Alert on threshold breach
```json
POST /notify/telegram
{"title": "Cost Alert", "message": "API spend reached $45.00 (budget: $50.00)", "level": "warning", "source": "cost-monitor"}
```

## Integration Code Snippets

### Python (httpx)
```python
import httpx

NOTIFY_URL = "http://<host>:9009"

async def notify(title: str, message: str, level: str = "info", source: str = "agent"):
    async with httpx.AsyncClient() as client:
        await client.post(f"{NOTIFY_URL}/notify/telegram", json={
            "title": title, "message": message, "level": level, "source": source
        })
```

### Python (requests)
```python
import requests

def notify(title, message, level="info", source="agent"):
    requests.post("http://<host>:9009/notify/telegram", json={
        "title": title, "message": message, "level": level, "source": source
    })
```

### curl
```bash
curl -X POST http://<host>:9009/notify/telegram \
  -H "Content-Type: application/json" \
  -d '{"title":"Alert","message":"Something happened","level":"warning","source":"script"}'
```

### JavaScript/TypeScript (fetch)
```typescript
await fetch("http://<host>:9009/notify/telegram", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "Alert",
    message: "Something happened",
    level: "warning",
    source: "agent",
  }),
});
```

## MCP Server (Recommended for AI Agents)

If your agent supports [MCP](https://modelcontextprotocol.io/), use the built-in MCP server instead of REST calls. It provides the same functionality with native tool integration.

### Setup

```bash
# Add to Claude Code
claude mcp add --transport stdio --scope user notify_mcp \
  -e NOTIFY_API_URL=http://<host>:9009 \
  -- uv run --directory /path/to/notify-api mcp_server.py
```

### MCP Tools

| Tool | Description | Annotations |
|------|-------------|-------------|
| `notify_health` | Check API health and channel status | readOnly |
| `notify_send_telegram` | Send Telegram notification | openWorld |
| `notify_send_email` | Send Email notification | openWorld |
| `notify_send` | Unified send (channel: telegram/email/all) | openWorld |

### MCP Usage Example

```
# In Claude Code or any MCP client:
call notify_send_telegram(title="Task Complete", message="Pipeline finished", level="info", source="agent")
```

All MCP tools return JSON with the same schema as the REST API responses. Errors include actionable messages (e.g., "Telegram not configured. Set TELEGRAM_BOT_TOKEN...").

## Error Handling

- `200` — Success
- `422` — Validation error (check required fields)
- `503` — Channel not configured (e.g., email SMTP not set)

On failure, the response includes an `errors` field:
```json
{"ok": false, "channels": {"telegram": false}, "errors": {"telegram": "Connection timeout"}}
```

## Self-Hosting

```bash
git clone https://github.com/BAEM1N/notify-api.git
cd notify-api
cp .env.example .env
# Edit .env with your Telegram bot token and chat ID
docker compose up -d
```

The service runs on port `9009` by default.
