"""Application configuration loaded from environment."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///sma_platform.db"

    # NCBI / PubMed
    ncbi_api_key: str = ""
    ncbi_email: str = "christian@bryzant.com"
    ncbi_tool: str = "sma-platform"

    # LLM (for agents)
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Slack notifications
    slack_bot_token: str = ""
    slack_channel_id: str = ""

    # Admin
    sma_admin_key: str = ""
    enable_docs: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8100
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
