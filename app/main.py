from fastapi import FastAPI, HTTPException

from channels.email import send_email
from channels.telegram import send_telegram
from config import settings
from models import (
    Channel,
    EmailRequest,
    NotifyRequest,
    NotifyResponse,
    TelegramRequest,
)

app = FastAPI(title="BaeumAI Notify API", version="0.1.0")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "channels": {
            "telegram": settings.telegram_enabled,
            "email": settings.email_enabled,
        },
    }


@app.post("/notify/telegram", response_model=NotifyResponse)
async def notify_telegram(req: TelegramRequest):
    if not settings.telegram_enabled:
        raise HTTPException(status_code=503, detail="Telegram not configured")
    try:
        ok = await send_telegram(req.title, req.message, req.level, req.source)
        return NotifyResponse(ok=ok, channels={"telegram": ok})
    except Exception as e:
        return NotifyResponse(ok=False, channels={"telegram": False}, errors={"telegram": str(e)})


@app.post("/notify/email", response_model=NotifyResponse)
async def notify_email(req: EmailRequest):
    if not settings.email_enabled:
        raise HTTPException(status_code=503, detail="Email not configured")
    try:
        ok = await send_email(req.title, req.message, req.level, req.source, req.to)
        return NotifyResponse(ok=ok, channels={"email": ok})
    except Exception as e:
        return NotifyResponse(ok=False, channels={"email": False}, errors={"email": str(e)})


@app.post("/notify", response_model=NotifyResponse)
async def notify(req: NotifyRequest):
    results: dict[str, bool] = {}
    errors: dict[str, str] = {}

    targets = []
    if req.channel in (Channel.telegram, Channel.all):
        targets.append("telegram")
    if req.channel in (Channel.email, Channel.all):
        targets.append("email")

    for target in targets:
        try:
            if target == "telegram":
                if not settings.telegram_enabled:
                    raise RuntimeError("Telegram not configured")
                results["telegram"] = await send_telegram(
                    req.title, req.message, req.level, req.source
                )
            elif target == "email":
                if not settings.email_enabled:
                    raise RuntimeError("Email not configured")
                results["email"] = await send_email(
                    req.title, req.message, req.level, req.source
                )
        except Exception as e:
            results[target] = False
            errors[target] = str(e)

    return NotifyResponse(
        ok=all(results.values()) and len(results) > 0,
        channels=results,
        errors=errors,
    )
