from dataclasses import dataclass

from pydantic_settings import BaseSettings


@dataclass
class EmailProfile:
    smtp_user: str
    smtp_password: str
    from_email: str
    from_name: str


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    # Default SMTP credentials (fallback)
    smtp_user: str = ""
    smtp_password: str = ""

    # Sender routing by service URL/source
    smtp_from_baeum: str = "no-reply@baeum.ai.kr"
    smtp_from_name_baeum: str = "배움 에이아이"
    smtp_user_baeum: str = ""
    smtp_password_baeum: str = ""

    smtp_from_ddok: str = "no-reply@ddok.ai"
    smtp_from_name_ddok: str = "주식회사 똑똑한청년들"
    smtp_user_ddok: str = ""
    smtp_password_ddok: str = ""

    smtp_url_keywords_baeum: str = "baeum.ai.kr,baeum.io.kr,baeum.ai"
    smtp_url_keywords_ddok: str = "ddok.ai"

    gmail_credentials_path: str = "/app/credentials/credentials.json"

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def email_enabled(self) -> bool:
        # At least one usable profile exists.
        return (
            self._has_credentials(self.smtp_user_baeum, self.smtp_password_baeum)
            or self._has_credentials(self.smtp_user_ddok, self.smtp_password_ddok)
            or self._has_credentials(self.smtp_user, self.smtp_password)
        )

    @staticmethod
    def _has_credentials(user: str, password: str) -> bool:
        return bool(user and password)

    @staticmethod
    def _parse_keywords(value: str) -> list[str]:
        return [part.strip().lower() for part in value.split(",") if part.strip()]

    @staticmethod
    def _contains_any(source: str, keywords: list[str]) -> bool:
        lowered = source.lower()
        return any(keyword in lowered for keyword in keywords)

    def resolve_email_profile(self, source: str = "") -> EmailProfile:
        source = source or ""
        baeum_keywords = self._parse_keywords(self.smtp_url_keywords_baeum)
        ddok_keywords = self._parse_keywords(self.smtp_url_keywords_ddok)

        if self._contains_any(source, ddok_keywords):
            return self._profile_ddok()
        if self._contains_any(source, baeum_keywords):
            return self._profile_baeum()

        # Default route: baeum profile first
        return self._profile_baeum()

    def _profile_baeum(self) -> EmailProfile:
        smtp_user = self.smtp_user_baeum or self.smtp_user
        smtp_password = self.smtp_password_baeum or self.smtp_password
        from_email = self.smtp_from_baeum or smtp_user
        if not self._has_credentials(smtp_user, smtp_password):
            raise RuntimeError("Email not configured for baeum sender")
        return EmailProfile(
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=self.smtp_from_name_baeum or "배움 에이아이",
        )

    def _profile_ddok(self) -> EmailProfile:
        smtp_user = self.smtp_user_ddok or self.smtp_user
        smtp_password = self.smtp_password_ddok or self.smtp_password
        from_email = self.smtp_from_ddok or smtp_user
        if not self._has_credentials(smtp_user, smtp_password):
            raise RuntimeError("Email not configured for ddok sender")
        return EmailProfile(
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=self.smtp_from_name_ddok or "주식회사 똑똑한청년들",
        )


settings = Settings()
