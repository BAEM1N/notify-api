from enum import Enum

from pydantic import BaseModel, Field, model_validator


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
    # Backward compatibility for legacy clients that send `subject`.
    subject: str = Field(default="", max_length=200)
    message: str = Field(..., min_length=1, max_length=4000)
    level: Level = Level.info
    source: str = ""
    to: str = ""

    @model_validator(mode="before")
    @classmethod
    def map_subject_to_title(cls, data):
        if isinstance(data, dict):
            title = data.get("title")
            subject = data.get("subject")
            if (title is None or title == "") and subject:
                copied = dict(data)
                copied["title"] = subject
                return copied
        return data


class NotifyResponse(BaseModel):
    ok: bool
    channels: dict[str, bool] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)
