from enum import Enum

from pydantic import BaseModel, Field


class Channel(str, Enum):
    telegram = "telegram"
    email = "email"
    all = "all"


class Level(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


LEVEL_EMOJI = {
    Level.info: "ℹ️",
    Level.warning: "⚠️",
    Level.critical: "🚨",
}


class NotifyRequest(BaseModel):
    channel: Channel = Channel.telegram
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=4000)
    level: Level = Level.info
    source: str = ""


class TelegramRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=4000)
    level: Level = Level.info
    source: str = ""


class EmailRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=4000)
    level: Level = Level.info
    source: str = ""
    to: str = ""


class NotifyResponse(BaseModel):
    ok: bool
    channels: dict[str, bool] = {}
    errors: dict[str, str] = {}
