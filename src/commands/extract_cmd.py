"""Extract command for Notion Recipe Organizer."""

from typing import Optional
import click

from ..utils.config_utils import validate_config_and_connection, get_database_id, get_notion_client
from ..utils.display_utils import (
    print_header, print_success, print_error, print_info, show_dry_run_results, show_completion_message
)
from ..utils.file_utils import resolve_output_path, save_json_with_metadata


@click.command()
@click.option("--database-id", help="Database ID to extract from")
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--max-records", type=int, help="Maximum number of records to extract")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be extracted without saving"
)
def extract(
    database_id: Optional[str],
    output: Optional[str],
    max_records: Optional[int],
    dry_run: bool,
):
    """Extract recipe data from Notion database."""

    print_header("Extracting Recipe Data", "📥")

    # Set smart defaults for dry-run mode
    if dry_run and max_records is None:
        max_records = 3
        print_info("Dry-run mode: defaulting to 3 records (use --max-records to override)")

    # Validate config and connection
    if not validate_config_and_connection():
        return

    # Get database ID
    db_id = get_database_id(database_id)
    if not db_id:
        print_error("No database ID provided. Use --database-id or set NOTION_RECIPES_DATABASE_ID")
        return

    # Get client
    notion_client = get_notion_client()

    # Verify database access
    print_header(f"Accessing database: {db_id}", "🗄️")
    db_info = notion_client.get_database(db_id)
    if not db_info:
        print_error(f"Could not access database: {db_id}")
        return

    db_title = db_info.get("title", [{}])[0].get("plain_text", "Unknown Database")
    print_success(f"Connected to database: {db_title}")

    # Extract database records
    print_header(f"Extracting records{f' (max: {max_records})' if max_records else ''}...", "📋")

    records = notion_client.get_database_records(db_id, max_records=max_records)
    recipes_data = []

    from rich.console import Console
    console = Console()
    with console.status("[bold green]Processing records...") as status:
        for i, record in enumerate(records):
            status.update(f"[bold green]Processing record {i + 1}/{len(records)}...")

            # Get full record content including page blocks
            recipe_data = notion_client.get_record_content(record["id"])

            # Add database-specific metadata
            recipe_data["database_id"] = db_id
            recipe_data["record_id"] = record["id"]

            recipes_data.append(recipe_data)

    print_success(f"Extracted {len(recipes_data)} recipe records")

    if dry_run:
        show_dry_run_results(recipes_data)
    else:
        # Save to file
        output_path = resolve_output_path(output, "raw")
        
        # Include database schema in the output
        export_data = {
            "database_info": db_info,
            "records": recipes_data,
        }

        save_json_with_metadata(export_data, output_path)

        print_success(f"Saved to: {output_path}")
        print_info("Database schema included for analysis")
        
    show_completion_message("extraction")