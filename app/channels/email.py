import email.message
from email.utils import formataddr

import aiosmtplib

from config import settings
from models import LEVEL_EMOJI, Level


def _build_email(
    title: str,
    message: str,
    level: Level,
    source: str,
    to: str,
    from_email: str,
    from_name: str,
) -> email.message.EmailMessage:
    emoji = LEVEL_EMOJI.get(level, "")
    msg = email.message.EmailMessage()
    msg["Subject"] = f"{emoji} {title}"
    msg["From"] = formataddr((from_name, from_email))
    msg["To"] = to or from_email

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
        raise RuntimeError("Email not configured (SMTP credentials empty)")

    profile = settings.resolve_email_profile(source)
    msg = _build_email(
        title=title,
        message=message,
        level=level,
        source=source,
        to=to,
        from_email=profile.from_email,
        from_name=profile.from_name,
    )
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=profile.smtp_user,
        password=profile.smtp_password,
        start_tls=True,
    )
    return True
