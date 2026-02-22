import email.message

import aiosmtplib

from config import settings
from models import LEVEL_EMOJI, Level


def _build_email(
    title: str,
    message: str,
    level: Level,
    source: str,
    to: str,
) -> email.message.EmailMessage:
    emoji = LEVEL_EMOJI.get(level, "")
    msg = email.message.EmailMessage()
    msg["Subject"] = f"{emoji} {title}"
    msg["From"] = settings.smtp_user
    msg["To"] = to or settings.smtp_user

    body_parts = []
    if source:
        body_parts.append(f"[Source: {source}]")
    body_parts.append(message)
    msg.set_content("\n\n".join(body_parts))
    return msg


async def send_email(
    title: str,
    message: str,
    level: Level = Level.info,
    source: str = "",
    to: str = "",
) -> bool:
    if not settings.email_enabled:
        raise RuntimeError("Email not configured (SMTP_USER/SMTP_PASSWORD empty)")

    msg = _build_email(title, message, level, source, to)
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )
    return True
