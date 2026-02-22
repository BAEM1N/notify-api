# Notify API

[English](README.md) | [한국어](README_ko.md)

A lightweight, self-hosted notification gateway for your infrastructure. Send alerts to Telegram and Email via a single REST API.

Built for developers, DevOps teams, and **AI Agents** who need a simple way to send notifications from any service.

## Features

- **Telegram** notifications via Bot API
- **Email** notifications via SMTP (Gmail, etc.)
- **Unified endpoint** — one API, multiple channels
- **Severity levels** — info, warning, critical (with emoji indicators)
- **Source tagging** — identify which service sent the alert
- **Docker-ready** — single `docker compose up` to deploy
- **AI Agent friendly** — structured API, OpenAPI docs, `AGENTS.md` for LLM integration

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/BAEM1N/notify-api.git
cd notify-api
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 2. Deploy

```bash
docker compose up -d
```

### 3. Test

```bash
curl http://localhost:9009/health
```

## API Reference

### Health Check

```
GET /health
```

```json
{
  "status": "ok",
  "channels": { "telegram": true, "email": false }
}
```

### Send Notification (Unified)

```
POST /notify
Content-Type: application/json
```

```json
{
  "channel": "telegram",
  "title": "Deployment Complete",
  "message": "v2.1.0 deployed to production successfully",
  "level": "info",
  "source": "ci-pipeline"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel` | `telegram` \| `email` \| `all` | No (default: `telegram`) | Target channel(s) |
| `title` | string | Yes | Notification title (max 200 chars) |
| `message` | string | Yes | Notification body (max 4000 chars) |
| `level` | `info` \| `warning` \| `critical` | No (default: `info`) | Severity level |
| `source` | string | No | Source service identifier |

### Send Telegram Only

```
POST /notify/telegram
Content-Type: application/json
```

```json
{
  "title": "Alert",
  "message": "CPU usage exceeded 90%",
  "level": "critical",
  "source": "monitoring"
}
```

### Send Email Only

```
POST /notify/email
Content-Type: application/json
```

```json
{
  "title": "Weekly Report",
  "message": "System uptime: 99.97%",
  "level": "info",
  "to": "team@example.com"
}
```

### Response Format

All endpoints return:

```json
{
  "ok": true,
  "channels": { "telegram": true },
  "errors": {}
}
```

## Telegram Bot Setup

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token**
4. Send a message to your bot, then get your **Chat ID**:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
5. Add both to `.env`

## Email Setup (Optional)

For Gmail SMTP:

1. Enable [2-Step Verification](https://myaccount.google.com/security)
2. Create an [App Password](https://myaccount.google.com/apppasswords)
3. Add to `.env`:
   ```env
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

## Grafana Integration

Notify API works alongside Grafana's built-in Telegram alerting:

```
Grafana Alert Rules → Telegram Contact Point → Telegram
Your Services      → Notify API (:9009)      → Telegram / Email
```

To add Grafana's native Telegram alerting, create a Contact Point via API:

```bash
curl -X POST http://your-grafana:3000/api/v1/provisioning/contact-points \
  -H "Authorization: Basic <base64>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Telegram",
    "type": "telegram",
    "settings": {
      "bottoken": "your-bot-token",
      "chatid": "your-chat-id"
    }
  }'
```

## MCP Server (for AI Agents)

Notify API includes a built-in [MCP](https://modelcontextprotocol.io/) server, so AI agents (Claude Code, etc.) can send notifications directly via MCP protocol — no REST calls needed.

### Setup

```bash
# Install dependencies (one-time)
cd notify-api
uv sync

# Add to Claude Code (user scope)
claude mcp add --transport stdio --scope user notify_mcp \
  -e NOTIFY_API_URL=http://localhost:9009 \
  -- uv run --directory /path/to/notify-api mcp_server.py
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `notify_health` | Check API health and channel availability |
| `notify_send_telegram` | Send a Telegram notification |
| `notify_send_email` | Send an Email notification |
| `notify_send` | Send to one or multiple channels |

### Claude Code Slash Command

With the included skill, use `/notify` in Claude Code:

```
/notify 배포 완료
/notify --critical 서버 다운! 즉시 확인 필요
/notify --email Weekly Report: System uptime 99.97%
/notify --all 점검 공지: 오늘 22시 서버 점검
/notify --health
```

## Usage Examples

### From a shell script

```bash
notify() {
  curl -s -X POST http://localhost:9009/notify/telegram \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"$1\",\"message\":\"$2\",\"level\":\"${3:-info}\",\"source\":\"${4:-shell}\"}"
}

notify "Backup Done" "Database backup completed" "info" "cron"
```

### From Python

```python
import httpx

def notify(title: str, message: str, level: str = "info", source: str = ""):
    httpx.post("http://localhost:9009/notify/telegram", json={
        "title": title,
        "message": message,
        "level": level,
        "source": source,
    })

notify("Training Complete", "Model accuracy: 94.2%", "info", "ml-pipeline")
```

### From an AI Agent

See [AGENTS.md](AGENTS.md) for structured integration instructions.

## Configuration

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram Bot API token |
| `TELEGRAM_CHAT_ID` | Yes | — | Telegram chat/group ID |
| `SMTP_HOST` | No | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USER` | No | — | SMTP username (email) |
| `SMTP_PASSWORD` | No | — | SMTP password / app password |
| `GMAIL_CREDENTIALS_PATH` | No | `/app/credentials/credentials.json` | Gmail API credentials file |

## Tech Stack

- **FastAPI** + **Uvicorn** — async HTTP server
- **httpx** — async Telegram API client
- **aiosmtplib** — async SMTP client
- **pydantic-settings** — env-based configuration
- **Docker** — containerized deployment
- **FastMCP** — MCP server for AI agent integration

## License

[MIT](LICENSE)
