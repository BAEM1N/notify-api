import httpx

from config import settings
from models import LEVEL_EMOJI, Level

API_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


def _format_message(title: str, message: str, level: Level, source: str) -> str:
    emoji = LEVEL_EMOJI.get(level, "")
    parts = [f"{emoji} <b>{title}</b>"]
    if source:
        parts.append(f"<code>[{source}]</code>")
    parts.append("")
    parts.append(message)
    return "\n".join(parts)


async def send_telegram(
    title: str,
    message: str,
    level: Level = Level.info,
    source: str = "",
) -> bool:
    text = _format_message(title, message, level, source)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
        )
        resp.raise_for_status()
        return resp.json().get("ok", False)
