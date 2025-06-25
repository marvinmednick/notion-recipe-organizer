"""Test command for Notion Recipe Organizer."""

from typing import Optional
import click

from ..utils.config_utils import validate_config_and_connection, get_database_id, get_notion_client
from ..utils.display_utils import (
    print_header, print_success, print_error, print_warning, 
    create_database_properties_table, create_sample_records_table, show_completion_message
)


@click.command()
@click.option("--database-id", help="Specific database ID to test (optional)")
@click.option("--dry-run", is_flag=True, help="Test connection without making changes")
def test(database_id: Optional[str], dry_run: bool):
    """Test Notion API connection and basic functionality."""

    print_header("Testing Notion Recipe Organizer", "🧪")

    # Validate config and connection
    if not validate_config_and_connection():
        return

    # Get client and database ID
    notion_client = get_notion_client()
    test_db_id = get_database_id(database_id)

    if test_db_id:
        print_header(f"Testing Database Access: {test_db_id}", "🗄️")

        # Get database info
        db_info = notion_client.get_database(test_db_id)
        if db_info:
            db_title = db_info.get("title", [{}])[0].get(
                "plain_text", "Unknown Database"
            )
            print_success(f"Successfully accessed database: {db_title}")

            # Show database schema
            print_header("Database Schema", "📋")
            properties = db_info.get("properties", {})
            table = create_database_properties_table(properties)
            
            from rich.console import Console
            console = Console()
            console.print(table)

            # Get sample records
            print_header("Getting Sample Records (first 3)...", "📄")
            records = notion_client.get_database_records(test_db_id, max_records=3)

            if records:
                record_table = create_sample_records_table(records, notion_client._extract_record_properties)
                console.print(record_table)
                print_success(f"Found {len(records)} sample records")
            else:
                print_warning("No records found")
        else:
            print_error(f"Could not access database: {test_db_id}")
    else:
        print_warning("No database ID provided. Use --database-id or set NOTION_RECIPES_DATABASE_ID")

    show_completion_message("test")