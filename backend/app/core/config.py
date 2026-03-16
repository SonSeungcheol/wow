from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KR Corporate Accounting Assistant"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    database_url: str = "sqlite:///./app.db"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
