from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"

    database_url: str

    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str

    gemini_api_key: str
    gemini_embedding_model: str = "gemini-embedding-001"

    groq_api_key: str
    groq_decision_model: str

    recovery_notification_email: str | None = None
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True

    operations_api_key: str = ""

    cors_allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()