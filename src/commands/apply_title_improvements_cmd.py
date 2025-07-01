"""Apply title improvements command for Notion Recipe Organizer."""

import click
from rich.console import Console
from rich.table import Table
from typing import Optional, List, Dict, Any

from ..utils.config_utils import validate_config_and_connection, get_database_id, get_notion_client
from ..utils.display_utils import (
    print_header, print_success, print_error, print_info, show_completion_message
)
from ..utils.notion_utils import extract_notion_text_content, create_notion_text_property

console = Console()


@click.command()
@click.option("--database-id", help="Enhanced database ID to apply title improvements to")
@click.option("--sample", type=int, help="Test with limited number of records")
@click.option("--dry-run", is_flag=True, help="Show what would be changed without modifying titles")
@click.option("--force", is_flag=True, help="Apply changes without confirmation prompt")
def apply_title_improvements(
    database_id: Optional[str],
    sample: Optional[int],
    dry_run: bool,
    force: bool,
):
    """Apply title improvements from Proposed_Title field to Title field."""
    
    print_header("Apply Title Improvements", "🏷️")
    
    # Validate config and connection
    if not validate_config_and_connection():
        return
    
    # Get enhanced database ID
    enhanced_db_id = get_database_id(database_id)
    if not enhanced_db_id:
        print_error("No enhanced database ID provided. Use --database-id or set NOTION_RECIPES_DATABASE_ID")
        return
    
    # Get client
    notion_client = get_notion_client()
    
    # Verify database access
    print_info(f"Accessing enhanced database: {enhanced_db_id}")
    enhanced_db_info = notion_client.get_database(enhanced_db_id)
    if not enhanced_db_info:
        print_error(f"Could not access enhanced database: {enhanced_db_id}")
        return
    
    enhanced_db_title = enhanced_db_info.get("title", [{}])[0].get("plain_text", "Unknown Database")
    print_success(f"Connected to enhanced database: {enhanced_db_title}")
    
    # Verify database has Proposed_Title field
    properties = enhanced_db_info.get("properties", {})
    if "Proposed_Title" not in properties:
        print_error("Database does not have 'Proposed_Title' field")
        print_info("Run 'enhance-database' command first to create enhanced database with title suggestions")
        return
    
    if "Title" not in properties and "Name" not in properties:
        print_error("Database does not have 'Title' or 'Name' field")
        return
    
    # Determine title field name
    title_field = "Title" if "Title" in properties else "Name"
    print_info(f"Using '{title_field}' field for title updates")
    
    # Get all records from enhanced database
    print_header("Loading database records...", "📄")
    all_records = notion_client.get_database_records(enhanced_db_id)
    
    if sample:
        all_records = all_records[:sample]
        print_info(f"Using sample of {len(all_records)} records for testing")
    
    print_success(f"Loaded {len(all_records)} records from enhanced database")
    
    # Find records with non-empty Proposed_Title
    print_header("Analyzing proposed title improvements...", "🔍")
    records_to_update = []
    
    for record in all_records:
        record_id = record["id"]
        
        # Get full record content to check Proposed_Title
        record_content = notion_client.get_record_content(record_id)
        properties = record_content.get("properties", {})
        
        # Check if Proposed_Title has content
        proposed_title_prop = properties.get("Proposed_Title", {})
        proposed_title_content = extract_notion_text_content(proposed_title_prop, "rich_text")
        
        # Check current title
        current_title_prop = properties.get(title_field, {})
        current_title = extract_notion_text_content(current_title_prop, "auto")
        
        if proposed_title_content and proposed_title_content.strip():
            records_to_update.append({
                "id": record_id,
                "current_title": current_title,
                "proposed_title": proposed_title_content.strip()
            })
    
    print_success(f"Found {len(records_to_update)} records with proposed title improvements")
    
    if len(records_to_update) == 0:
        print_info("No records have non-empty Proposed_Title fields")
        print_info("Either all titles are already optimal, or no title improvements were generated")
        return
    
    # Display proposed changes
    print_header("Proposed Title Changes", "📋")
    _display_title_changes(records_to_update)
    
    if dry_run:
        print_header("Dry Run Complete", "🔍")
        print_info("No changes made - titles not modified")
        return
    
    # Confirm changes
    if not force:
        if not click.confirm(f"\nApply title improvements to {len(records_to_update)} records?"):
            print_info("Title improvements cancelled")
            return
    
    # Apply title improvements
    print_header("Applying title improvements...", "✏️")
    success_count = _apply_title_changes(notion_client, records_to_update, title_field)
    
    if success_count > 0:
        print_header("Title Improvements Applied", "✅")
        print_success(f"Successfully updated {success_count} titles")
        if success_count < len(records_to_update):
            print_info(f"Failed to update {len(records_to_update) - success_count} titles")
        show_completion_message("title improvements")
    else:
        print_header("Title Improvement Failed", "❌")
        print_error("No titles were successfully updated")




def _display_title_changes(records_to_update: List[Dict[str, Any]]) -> None:
    """Display proposed title changes in a table."""
    
    table = Table()
    table.add_column("Current Title", style="dim", max_width=40)
    table.add_column("→", style="bold blue", justify="center", width=3)
    table.add_column("Proposed Title", style="green", max_width=40)
    
    for record in records_to_update[:20]:  # Show first 20 for readability
        current = record["current_title"][:80] + "..." if len(record["current_title"]) > 80 else record["current_title"]
        proposed = record["proposed_title"][:80] + "..." if len(record["proposed_title"]) > 80 else record["proposed_title"]
        
        table.add_row(current, "→", proposed)
    
    console.print(table)
    
    if len(records_to_update) > 20:
        console.print(f"\n[dim]... and {len(records_to_update) - 20} more records[/dim]")


def _apply_title_changes(
    notion_client, 
    records_to_update: List[Dict[str, Any]], 
    title_field: str
) -> int:
    """Apply title changes to the database records."""
    
    success_count = 0
    
    with console.status("[bold green]Updating titles...") as status:
        for i, record in enumerate(records_to_update):
            status.update(f"[bold green]Updating title {i + 1}/{len(records_to_update)}...")
            
            try:
                # Prepare new title property using utility function
                prop_type = "title" if title_field.lower() in ["title", "name"] else "rich_text"
                new_title_prop = create_notion_text_property(record["proposed_title"], prop_type)
                
                # Update the record
                notion_client.client.pages.update(
                    page_id=record["id"],
                    properties={title_field: new_title_prop}
                )
                
                success_count += 1
                
            except Exception as e:
                print_error(f"Failed to update record {record['id']}: {e}")
                continue
    
    return success_count