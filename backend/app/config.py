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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()