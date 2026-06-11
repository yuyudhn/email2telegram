from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    email_address: str
    email_password: SecretStr
    imap_server: str
    imap_port: int = 993

    telegram_bot_token: SecretStr
    telegram_chat_id: str

    filter_subject: str = ""
    filter_body: str = ""

    check_interval_seconds: int = 30
    log_level: str = "INFO"
