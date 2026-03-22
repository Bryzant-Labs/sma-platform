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
    groq_api_key: str = ""
    gemini_api_key: str = ""

    # LLM routing: which provider to use for claim extraction
    # Options: "groq", "gemini", "openai", "anthropic"
    extraction_llm: str = "groq"
    # Whether to run Claude validation on extracted claims (costs API credits)
    validate_with_claude: bool = False

    # Slack notifications
    slack_bot_token: str = ""
    slack_channel_id: str = ""

    # Admin
    sma_admin_key: str = ""
    enable_docs: bool = True

    # NVIDIA NIMs (DiffDock v2.2, OpenFold3, GenMol)
    nvidia_api_key: str = ""
    nvidia_api_key_2: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8100
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
