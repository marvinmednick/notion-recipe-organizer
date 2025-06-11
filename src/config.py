"""Configuration management for Notion Recipe Organizer.

Version: v8
Last updated: Updated for database operations with Azure OpenAI gpt-4.1
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""

    # Notion Configuration
    notion_token: str = Field(..., description="Notion integration token")
    notion_recipes_database_id: Optional[str] = Field(
        None, description="Recipes database ID"
    )

    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI endpoint")
    azure_openai_key: str = Field(..., description="Azure OpenAI API key")
    azure_openai_deployment: str = Field(
        default="gpt-4.1", description="Azure OpenAI deployment name"
    )
    azure_openai_version: str = Field(
        default="2025-04-01-preview", description="Azure OpenAI API version"
    )

    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    max_retries: int = Field(default=3, description="Max API retries")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

        return cls(
            notion_token=os.getenv("NOTION_TOKEN", ""),
            notion_recipes_database_id=os.getenv("NOTION_RECIPES_DATABASE_ID"),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            azure_openai_key=os.getenv("AZURE_OPENAI_KEY", ""),
            azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
            azure_openai_version=os.getenv(
                "AZURE_OPENAI_VERSION", "2025-04-01-preview"
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            data_dir=Path(os.getenv("DATA_DIR", "data")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
        )

    def validate_required(self) -> None:
        """Validate that required configuration is present."""
        missing = []

        if not self.notion_token:
            missing.append("NOTION_TOKEN")
        if not self.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self.azure_openai_key:
            missing.append("AZURE_OPENAI_KEY")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


# Global config instance
config = Config.from_env()

