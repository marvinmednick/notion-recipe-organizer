"""Main CLI entry point for Notion Recipe Organizer.

Version: v6
Last updated: Added batch processing, range specification, and timeout controls
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
from .notion_client.analyzer import RecipeAnalyzer

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


@cli.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True),
    help="Input JSON file with extracted recipes",
)
@click.option("--output", type=click.Path(), help="Output file for analysis results")
@click.option(
    "--sample-size",
    type=int,
    help="Number of recipes to analyze with LLM (for testing)",
)
@click.option("--start-index", type=int, help="Start analysis from this recipe index")
@click.option("--end-index", type=int, help="End analysis at this recipe index")
@click.option("--batch-size", type=int, help="Process recipes in batches of this size")
@click.option(
    "--batch-delay", type=float, default=0, help="Delay in seconds between batches"
)
@click.option(
    "--timeout", type=int, default=30, help="Timeout for individual LLM calls (seconds)"
)
@click.option(
    "--use-llm", is_flag=True, help="Enable LLM-powered categorization analysis"
)
@click.option("--basic-only", is_flag=True, help="Run only basic statistics analysis")
def analyze(
    input_file: Optional[str],
    output: Optional[str],
    sample_size: Optional[int],
    start_index: Optional[int],
    end_index: Optional[int],
    batch_size: Optional[int],
    batch_delay: float,
    timeout: int,
    use_llm: bool,
    basic_only: bool,
):
    """Analyze extracted recipe data and suggest categorizations."""

    console.print("[bold blue]📊 Analyzing Recipe Data[/bold blue]")

    # Validate parameter combinations
    if sample_size and (start_index is not None or end_index is not None):
        console.print(
            "[yellow]⚠️  --sample-size cannot be used with --start-index or --end-index[/yellow]"
        )
        console.print("Using range specification, ignoring --sample-size")
        sample_size = None

    # Determine input file
    if not input_file:
        input_file = config.data_dir / "raw" / "recipes.json"
        if not input_file.exists():
            console.print(f"❌ No input file found at {input_file}")
            console.print("Run 'extract' command first or specify --input path")
            return
    else:
        input_file = Path(input_file)

    # Initialize analyzer
    analyzer = RecipeAnalyzer()

    # Load recipe data
    recipe_data = analyzer.load_recipes(input_file)
    if not recipe_data:
        return

    # Show processing parameters
    total_recipes = len(recipe_data.get("records", []))
    if start_index is not None or end_index is not None:
        start_idx = start_index or 0
        end_idx = end_index or total_recipes - 1
        console.print(f"[dim]Processing range: {start_idx} to {end_idx}[/dim]")
    elif sample_size:
        console.print(f"[dim]Sample mode: processing first {sample_size} recipes[/dim]")

    if batch_size:
        console.print(
            f"[dim]Batch processing: {batch_size} recipes per batch, {batch_delay}s delay[/dim]"
        )

    if use_llm:
        console.print(f"[dim]LLM timeout: {timeout} seconds per recipe[/dim]")

    # Run basic statistics analysis
    console.print("\n[bold blue]🔍 Running Basic Analysis...[/bold blue]")
    basic_stats = analyzer.analyze_basic_stats(recipe_data)
    analyzer.display_basic_stats(basic_stats)

    categorization_results = None

    # Run LLM analysis if requested and not basic-only
    if use_llm and not basic_only:
        try:
            config.validate_required()  # Check Azure OpenAI config

            categorization_results = analyzer.categorize_recipes_llm(
                recipe_data=recipe_data,
                sample_size=sample_size,
                start_index=start_index,
                end_index=end_index,
                batch_size=batch_size,
                batch_delay=batch_delay,
                timeout=timeout,
            )
            analyzer.display_categorization_results(categorization_results)

        except ValueError as e:
            console.print(f"❌ Configuration Error: [bold red]{e}[/bold red]")
            console.print("LLM analysis requires Azure OpenAI configuration")
            return
        except Exception as e:
            console.print(f"❌ LLM Analysis Error: [bold red]{e}[/bold red]")
            return

    elif use_llm and basic_only:
        console.print("[yellow]⚠️  --basic-only flag overrides --use-llm[/yellow]")

    # Save results if requested
    if output or not basic_only:
        output_path = (
            Path(output)
            if output
            else config.data_dir / "processed" / "analysis_report.json"
        )

        # Create a summary even without LLM analysis
        if not categorization_results:
            categorization_results = {
                "total_analyzed": 0,
                "note": "LLM analysis not performed. Use --use-llm flag to enable.",
            }

        analyzer.save_analysis_results(basic_stats, categorization_results, output_path)

    # Show recommendations
    console.print("\n[bold blue]💡 Next Steps[/bold blue]")
    if not use_llm:
        console.print(
            "• Run with [bold cyan]--use-llm[/bold cyan] to get AI-powered categorization suggestions"
        )
    if sample_size or (start_index is not None and end_index is not None):
        console.print("• Remove range/sample limits to analyze all recipes")
    if basic_stats["recipes_with_tags"] > 0:
        console.print(
            f"• You have {basic_stats['recipes_with_tags']} recipes with existing tags to preserve"
        )
    if categorization_results and categorization_results.get("failed_analyses"):
        failed_count = len(categorization_results["failed_analyses"])
        console.print(
            f"• [yellow]{failed_count} recipes failed analysis - consider increasing --timeout[/yellow]"
        )

    console.print("\n[bold green]🎉 Analysis completed![/bold green]")


if __name__ == "__main__":
    cli()
