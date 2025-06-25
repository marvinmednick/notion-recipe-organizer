"""Configuration validation utilities."""

from rich.console import Console
from ..config import config
from ..notion_client.client import NotionClient

console = Console()


def validate_config() -> bool:
    """Validate required configuration and return True if valid."""
    try:
        config.validate_required()
        return True
    except ValueError as e:
        console.print(f"❌ Configuration Error: [bold red]{e}[/bold red]")
        return False


def test_notion_connection() -> bool:
    """Test Notion API connection and return True if successful."""
    notion_client = NotionClient()
    return notion_client.test_connection()


def validate_config_and_connection() -> bool:
    """Validate config and test connection. Return True if both succeed."""
    if not validate_config():
        return False
    return test_notion_connection()


def get_database_id(provided_id: str = None) -> str:
    """Get database ID from parameter or config."""
    return provided_id or config.notion_recipes_database_id


def get_notion_client() -> NotionClient:
    """Get initialized Notion client."""
    return NotionClient()