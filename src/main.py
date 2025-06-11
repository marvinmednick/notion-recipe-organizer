"""Main CLI entry point for Notion Recipe Organizer.

Version: v4
Last updated: Fixed dry-run display logic and default record limits
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .config import config
from .notion_client.client import NotionClient

console = Console()


def setup_logging(level: str = "INFO"):
    """Setup logging with Rich handler."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.option("--log-level", default="INFO", help="Set logging level")
@click.option("--config-check", is_flag=True, help="Check configuration and exit")
def cli(log_level: str, config_check: bool):
    """Notion Recipe Organizer - Organize your Notion recipes with ease."""
    setup_logging(log_level)

    if config_check:
        check_config()
        return


def check_config():
    """Check configuration and connection."""
    console.print("[bold blue]🔍 Checking Configuration...[/bold blue]")

    try:
        config.validate_required()
        console.print("✅ All required environment variables are set")
    except ValueError as e:
        console.print(f"❌ Configuration Error: [bold red]{e}[/bold red]")
        return

    # Test Notion connection
    console.print("\n[bold blue]🔗 Testing Notion Connection...[/bold blue]")
    notion_client = NotionClient()
    if notion_client.test_connection():
        console.print("✅ Notion connection successful")
    else:
        console.print("❌ Notion connection failed")
        return

    console.print("\n[bold green]🎉 All checks passed![/bold green]")


@cli.command()
@click.option("--database-id", help="Specific database ID to test (optional)")
@click.option("--dry-run", is_flag=True, help="Test connection without making changes")
def test(database_id: Optional[str], dry_run: bool):
    """Test Notion API connection and basic functionality."""

    console.print("[bold blue]🧪 Testing Notion Recipe Organizer[/bold blue]")

    # Check config first
    try:
        config.validate_required()
    except ValueError as e:
        console.print(f"❌ Configuration Error: [bold red]{e}[/bold red]")
        return

    # Initialize client
    notion_client = NotionClient()

    # Test connection
    if not notion_client.test_connection():
        return

    # Test database access
    test_db_id = database_id or config.notion_recipes_database_id

    if test_db_id:
        console.print(
            f"\n[bold blue]🗄️ Testing Database Access: {test_db_id}[/bold blue]"
        )

        # Get database info
        db_info = notion_client.get_database(test_db_id)
        if db_info:
            db_title = db_info.get("title", [{}])[0].get(
                "plain_text", "Unknown Database"
            )
            console.print(
                f"✅ Successfully accessed database: [bold green]{db_title}[/bold green]"
            )

            # Show database schema
            console.print("\n[bold blue]📋 Database Schema:[/bold blue]")
            properties = db_info.get("properties", {})

            table = Table(title="Database Properties")
            table.add_column("Property", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Details", style="green")

            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get("type", "unknown")
                details = ""

                if prop_type == "select":
                    options = prop_data.get("select", {}).get("options", [])
                    details = f"{len(options)} options"
                elif prop_type == "multi_select":
                    options = prop_data.get("multi_select", {}).get("options", [])
                    details = f"{len(options)} options"

                table.add_row(prop_name, prop_type, details)

            console.print(table)

            # Get sample records
            console.print(
                "\n[bold blue]📄 Getting Sample Records (first 3)...[/bold blue]"
            )
            records = notion_client.get_database_records(test_db_id, max_records=3)

            if records:
                record_table = Table(title="Sample Records")
                record_table.add_column("Title", style="cyan")
                record_table.add_column("URL", style="blue")
                record_table.add_column("Tags", style="yellow")
                record_table.add_column("Created", style="green")

                for record in records:
                    # Extract properties
                    props = notion_client._extract_record_properties(record)

                    title = props.get("Name", "Untitled")
                    url = (
                        props.get("URL", "No URL")[:50] + "..."
                        if len(props.get("URL", "")) > 50
                        else props.get("URL", "No URL")
                    )
                    tags = ", ".join(props.get("Tags", [])) or "No tags"
                    created = props.get("Created", "Unknown")[:10]  # Just date part

                    record_table.add_row(title, url, tags, created)

                console.print(record_table)
                console.print(f"\n✅ Found {len(records)} sample records")
            else:
                console.print("📭 No records found")
        else:
            console.print(f"❌ Could not access database: {test_db_id}")
    else:
        console.print(
            "\n[yellow]⚠️  No database ID provided. Use --database-id or set NOTION_RECIPES_DATABASE_ID[/yellow]"
        )

    console.print("\n[bold green]🎉 Test completed![/bold green]")


@cli.command()
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

    console.print("[bold blue]📥 Extracting Recipe Data[/bold blue]")

    # Set smart defaults for dry-run mode
    if dry_run and max_records is None:
        max_records = 3
        console.print(
            "[dim]ℹ️  Dry-run mode: defaulting to 3 records (use --max-records to override)[/dim]"
        )

    # Validate config
    try:
        config.validate_required()
    except ValueError as e:
        console.print(f"❌ Configuration Error: [bold red]{e}[/bold red]")
        return

    # Use provided database ID or config
    db_id = database_id or config.notion_recipes_database_id
    if not db_id:
        console.print(
            "❌ No database ID provided. Use --database-id or set NOTION_RECIPES_DATABASE_ID"
        )
        return

    # Initialize client
    notion_client = NotionClient()

    if not notion_client.test_connection():
        return

    # Verify database access
    console.print(f"\n[bold blue]🗄️ Accessing database: {db_id}[/bold blue]")
    db_info = notion_client.get_database(db_id)
    if not db_info:
        console.print(f"❌ Could not access database: {db_id}")
        return

    db_title = db_info.get("title", [{}])[0].get("plain_text", "Unknown Database")
    console.print(f"✅ Connected to database: [bold green]{db_title}[/bold green]")

    # Extract database records
    console.print(
        f"\n[bold blue]📋 Extracting records{f' (max: {max_records})' if max_records else ''}...[/bold blue]"
    )

    records = notion_client.get_database_records(db_id, max_records=max_records)
    recipes_data = []

    with console.status("[bold green]Processing records...") as status:
        for i, record in enumerate(records):
            status.update(f"[bold green]Processing record {i + 1}/{len(records)}...")

            # Get full record content including page blocks
            recipe_data = notion_client.get_record_content(record["id"])

            # Add database-specific metadata
            recipe_data["database_id"] = db_id
            recipe_data["record_id"] = record["id"]

            recipes_data.append(recipe_data)

    console.print(f"✅ Extracted {len(recipes_data)} recipe records")

    if dry_run:
        console.print(
            f"\n[yellow]🔍 Dry run - showing all {len(recipes_data)} extracted records:[/yellow]"
        )
        for i, recipe in enumerate(recipes_data):
            title = recipe.get("title", "Untitled")
            url = recipe.get("url", "No URL")
            tags = recipe.get("tags", [])
            tag_str = f" (tags: {', '.join(tags)})" if tags else " (no tags)"
            console.print(f"{i + 1}. {title}{tag_str}")
            if url and url != "No URL":
                console.print(f"   URL: {url}")
    else:
        # Save to file
        output_path = (
            Path(output) if output else config.data_dir / "raw" / "recipes.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Include database schema in the output
        export_data = {
            "database_info": db_info,
            "extracted_at": str(datetime.now()),
            "total_records": len(recipes_data),
            "records": recipes_data,
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        console.print(f"💾 Saved to: [bold green]{output_path}[/bold green]")
        console.print(f"📊 Database schema included for analysis")


if __name__ == "__main__":
    cli()
