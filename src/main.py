"""Main CLI entry point for Notion Recipe Organizer.

Version: v8
Last updated: Added review system for Phase 1.6
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .config import config
from .notion_client.client import NotionClient
from .notion_client.analyzer import RecipeAnalyzer
from .notion_client.profile_loader import ProfileLoader
from .notion_client.reviewer import RecipeReviewer

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
# Progressive complexity options
@click.option(
    "--profile", help="Use configuration profile (e.g., 'testing', 'production')"
)
@click.option("--quick", is_flag=True, help="Quick mode: statistics only, no LLM")
@click.option("--sample", type=int, help="Test mode: analyze N recipes only")
# Range specification
@click.option("--start-index", type=int, help="Start analysis from this recipe index")
@click.option("--end-index", type=int, help="End analysis at this recipe index")
@click.option("--range", "range_spec", help="Recipe range (e.g., '50-100')")
# Processing controls
@click.option("--batch-size", type=int, help="Process recipes in batches of this size")
@click.option("--batch-delay", type=float, help="Delay in seconds between batches")
@click.option("--timeout", type=int, help="Timeout for individual LLM calls (seconds)")
# Feature toggles
@click.option("--use-llm/--no-llm", default=None, help="Enable/disable LLM analysis")
@click.option(
    "--include-content-review/--no-content-review",
    default=None,
    help="Enable/disable content quality analysis",
)
@click.option(
    "--basic-only", is_flag=True, help="Run only basic statistics analysis (legacy)"
)
def analyze(
    input_file: Optional[str],
    output: Optional[str],
    profile: Optional[str],
    quick: bool,
    sample: Optional[int],
    start_index: Optional[int],
    end_index: Optional[int],
    range_spec: Optional[str],
    batch_size: Optional[int],
    batch_delay: Optional[float],
    timeout: Optional[int],
    use_llm: Optional[bool],
    include_content_review: Optional[bool],
    basic_only: bool,
):
    """Analyze extracted recipe data and suggest categorizations.

    Examples:
      analyze                           # Smart defaults (LLM + content review)
      analyze --quick                   # Statistics only
      analyze --sample 5                # Test with 5 recipes
      analyze --profile testing         # Use testing profile
      analyze --range 50-100            # Analyze recipes 50-100
      analyze --profile production      # Optimized for large datasets
    """

    console.print("[bold blue]📊 Analyzing Recipe Data[/bold blue]")

    # Load configuration profiles
    profile_loader = ProfileLoader()

    # Step 1: Get base settings (smart defaults)
    settings = profile_loader.get_default_settings()

    # Step 2: Apply shortcuts
    if quick:
        shortcut_profile = profile_loader.get_shortcut_profile("quick")
        if shortcut_profile:
            settings = profile_loader.apply_profile_to_settings(
                settings, shortcut_profile
            )
        else:
            settings.update({"use_llm": False, "include_content_review": False})

    # Step 3: Apply profile
    if profile:
        settings = profile_loader.apply_profile_to_settings(settings, profile)

    # Step 4: Apply sample shortcut
    if sample:
        settings["sample_size"] = sample
        # Remove any conflicting range settings
        settings.pop("start_index", None)
        settings.pop("end_index", None)

    # Step 5: Handle range specification
    if range_spec:
        try:
            start_str, end_str = range_spec.split("-")
            start_index = int(start_str)
            end_index = int(end_str)
        except ValueError:
            console.print(
                f"[red]❌ Invalid range format: {range_spec}. Use format like '50-100'[/red]"
            )
            return

    # Step 6: Apply individual overrides (highest priority)
    if start_index is not None:
        settings["start_index"] = start_index
    if end_index is not None:
        settings["end_index"] = end_index
    if batch_size is not None:
        settings["batch_size"] = batch_size
    if batch_delay is not None:
        settings["batch_delay"] = batch_delay
    if timeout is not None:
        settings["timeout"] = timeout
    if use_llm is not None:
        settings["use_llm"] = use_llm
    if include_content_review is not None:
        settings["include_content_review"] = include_content_review

    # Step 7: Handle legacy basic-only flag
    if basic_only:
        settings["use_llm"] = False
        settings["include_content_review"] = False

    # Validate parameter combinations
    if settings.get("sample_size") and (
        settings.get("start_index") is not None or settings.get("end_index") is not None
    ):
        console.print("[yellow]⚠️  Sample mode overrides range specification[/yellow]")
        settings.pop("start_index", None)
        settings.pop("end_index", None)

    # Display effective settings
    _display_analysis_settings(settings, profile, quick, sample)

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

    # Run basic statistics analysis
    console.print("\n[bold blue]🔍 Running Basic Analysis...[/bold blue]")
    basic_stats = analyzer.analyze_basic_stats(recipe_data)
    analyzer.display_basic_stats(basic_stats)

    categorization_results = None

    # Run LLM analysis if enabled
    if settings.get("use_llm", False):
        try:
            config.validate_required()  # Check Azure OpenAI config

            categorization_results = analyzer.categorize_recipes_llm(
                recipe_data=recipe_data,
                sample_size=settings.get("sample_size"),
                start_index=settings.get("start_index"),
                end_index=settings.get("end_index"),
                batch_size=settings.get("batch_size"),
                batch_delay=settings.get("batch_delay", 0),
                timeout=settings.get("timeout", 30),
                include_content_review=settings.get("include_content_review", True),
            )
            analyzer.display_categorization_results(categorization_results)

        except ValueError as e:
            console.print(f"❌ Configuration Error: [bold red]{e}[/bold red]")
            console.print("LLM analysis requires Azure OpenAI configuration")
            return
        except Exception as e:
            console.print(f"❌ LLM Analysis Error: [bold red]{e}[/bold red]")
            return

    # Save results
    if output or settings.get("use_llm", False):
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
                "settings_used": settings,
            }

        analyzer.save_analysis_results(basic_stats, categorization_results, output_path)

    # Show recommendations
    _show_analysis_recommendations(
        settings, basic_stats, categorization_results, profile_loader
    )

    console.print("\n[bold green]🎉 Analysis completed![/bold green]")


@cli.command()
@click.option(
    "--input",
    "input_file", 
    type=click.Path(exists=True),
    help="Input analysis JSON file to review"
)
@click.option("--output", type=click.Path(), help="Output directory for review files")
@click.option("--html", is_flag=True, help="Generate HTML review interface")
@click.option("--csv", is_flag=True, help="Export to CSV for editing")
@click.option("--summary", is_flag=True, help="Generate review summary")
@click.option("--issues-only", is_flag=True, help="Focus on items with issues only")
def review(
    input_file: Optional[str],
    output: Optional[str], 
    html: bool,
    csv: bool,
    summary: bool,
    issues_only: bool
):
    """Generate review interfaces for categorization results.
    
    Examples:
      review --html                     # Generate interactive HTML review
      review --csv --issues-only        # Export problem items to CSV
      review --summary                  # Generate review summary report
      review --html --csv               # Generate both HTML and CSV
    """
    
    console.print("[bold blue]🔍 Generating Review Interface[/bold blue]")
    
    # Determine input file
    if not input_file:
        input_file = config.data_dir / "processed" / "analysis_report.json"
        if not input_file.exists():
            console.print(f"❌ No analysis file found at {input_file}")
            console.print("Run 'analyze' command first or specify --input path")
            return
    else:
        input_file = Path(input_file)
    
    # Determine output directory
    if not output:
        output_dir = config.data_dir / "processed" / "review"
    else:
        output_dir = Path(output)
    
    # Initialize reviewer
    reviewer = RecipeReviewer()
    
    # Default to HTML if no specific format requested
    if not any([html, csv, summary]):
        html = True
        console.print("[dim]No format specified, defaulting to HTML review interface[/dim]")
    
    generated_files = []
    
    # Generate HTML review interface
    if html:
        html_file = reviewer.generate_html_review(input_file, output_dir)
        if html_file:
            generated_files.append(html_file)
    
    # Generate CSV export
    if csv:
        csv_file = reviewer.export_to_csv(input_file, output_dir, focus_on_issues=issues_only)
        if csv_file:
            generated_files.append(csv_file)
    
    # Generate review summary
    if summary:
        summary_file = reviewer.generate_review_summary(input_file, output_dir)
        if summary_file:
            generated_files.append(summary_file)
    
    if generated_files:
        console.print(f"\n[bold green]✅ Generated {len(generated_files)} review file(s)[/bold green]")
        
        # Show next steps
        console.print("\n[bold blue]💡 Next Steps[/bold blue]")
        if html and any("review_report.html" in str(f) for f in generated_files):
            console.print("• Open the HTML file in your browser to review categorizations")
        if csv and any(".csv" in str(f) for f in generated_files):
            console.print("• Edit the CSV file and use 'apply-corrections' to import changes")
            console.print("• Use 'apply-corrections --input your_edited_file.csv'")
        
        console.print("• After making corrections, re-run analysis to test improvements")
    else:
        console.print("[yellow]⚠️  No review files were generated[/yellow]")


@cli.command("apply-corrections")
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True),
    required=True,
    help="CSV file with corrections to apply"
)
@click.option("--output", type=click.Path(), help="Output directory for corrections")
@click.option("--dry-run", is_flag=True, help="Preview corrections without saving")
def apply_corrections(
    input_file: str,
    output: Optional[str],
    dry_run: bool
):
    """Apply corrections from edited CSV file.
    
    Examples:
      apply-corrections --input corrected_recipes.csv
      apply-corrections --input fixes.csv --dry-run    # Preview only
    """
    
    console.print("[bold blue]🔄 Applying Recipe Corrections[/bold blue]")
    
    input_path = Path(input_file)
    
    # Determine output directory  
    if not output:
        output_dir = config.data_dir / "processed" / "review"
    else:
        output_dir = Path(output)
    
    # Initialize reviewer
    reviewer = RecipeReviewer()
    
    if dry_run:
        console.print("[yellow]🔍 Dry run mode - previewing corrections only[/yellow]")
        # TODO: Add dry-run preview functionality
        console.print("Dry-run functionality will be implemented in the next update")
        return
    
    # Import corrections
    corrections_file = reviewer.import_corrections(input_path, output_dir)
    
    if corrections_file:
        console.print(f"\n[bold green]✅ Corrections imported successfully[/bold green]")
        console.print("\n[bold blue]💡 Next Steps[/bold blue]")
        console.print("• Review the corrections.json file to verify imported changes")
        console.print("• Use these corrections to improve your LLM prompts and configuration")
        console.print("• Re-run analysis to test the improved categorization")
    else:
        console.print("[yellow]⚠️  No corrections were imported[/yellow]")


def _display_analysis_settings(
    settings: Dict[str, Any], profile: Optional[str], quick: bool, sample: Optional[int]
) -> None:
    """Display the effective analysis settings."""
    console.print("\n[dim]📋 Analysis Settings:[/dim]")

    if profile:
        console.print(f"[dim]Profile: {profile}[/dim]")
    if quick:
        console.print(f"[dim]Quick mode: statistics only[/dim]")
    if sample:
        console.print(f"[dim]Sample mode: {sample} recipes[/dim]")

    # Show key settings
    use_llm = settings.get("use_llm", False)
    include_content_review = settings.get("include_content_review", False)

    if use_llm:
        mode_desc = "LLM analysis"
        if include_content_review:
            mode_desc += " + content review"
        console.print(f"[dim]Mode: {mode_desc}[/dim]")

        # Show processing settings
        if settings.get("batch_size"):
            console.print(
                f"[dim]Batch size: {settings['batch_size']}, delay: {settings.get('batch_delay', 0)}s[/dim]"
            )
        console.print(f"[dim]Timeout: {settings.get('timeout', 30)}s per recipe[/dim]")
    else:
        console.print(f"[dim]Mode: Basic statistics only[/dim]")


def _show_analysis_recommendations(
    settings: Dict[str, Any],
    basic_stats: Dict[str, Any],
    categorization_results: Optional[Dict[str, Any]],
    profile_loader: ProfileLoader,
) -> None:
    """Show recommendations for next steps."""
    console.print("\n[bold blue]💡 Next Steps[/bold blue]")

    if not settings.get("use_llm", False):
        console.print(
            "• Run with LLM analysis: [bold cyan]analyze[/bold cyan] (uses smart defaults)"
        )
        console.print("• Quick test: [bold cyan]analyze --sample 5[/bold cyan]")

    if settings.get("sample_size") or (settings.get("start_index") is not None):
        console.print(
            "• Analyze all recipes: [bold cyan]analyze[/bold cyan] (remove sample/range limits)"
        )

    if basic_stats.get("recipes_with_tags", 0) > 0:
        console.print(
            f"• You have {basic_stats['recipes_with_tags']} recipes with existing tags to preserve"
        )

    if categorization_results:
        # Content quality recommendations
        content_stats = categorization_results.get("content_quality_stats", {})
        non_recipes = content_stats.get("non_recipes", 0)
        title_improvements = content_stats.get("titles_needing_improvement", 0)

        if non_recipes > 0:
            console.print(
                f"• [yellow]{non_recipes} non-recipe items found[/yellow] - check content_issues_report.json"
            )
        if title_improvements > 0:
            console.print(
                f"• [cyan]{title_improvements} titles need improvement[/cyan] - check title_improvements.csv"
            )

        # Processing recommendations
        failed_count = len(categorization_results.get("failed_analyses", []))
        if failed_count > 0:
            console.print(
                f"• [yellow]{failed_count} recipes failed analysis[/yellow] - consider increasing --timeout"
            )

    # Show available profiles
    console.print(
        "• Available profiles: [bold cyan]--profile testing[/bold cyan], [bold cyan]--profile production[/bold cyan]"
    )
    console.print(
        "• Quick options: [bold cyan]--quick[/bold cyan], [bold cyan]--sample N[/bold cyan]"
    )

    # Show review system recommendations
    if categorization_results and categorization_results.get("total_analyzed", 0) > 0:
        console.print("\n[bold blue]🔍 Review System Available[/bold blue]")
        console.print("• Generate review interface: [bold cyan]review --html[/bold cyan]")
        console.print("• Export for editing: [bold cyan]review --csv --issues-only[/bold cyan]")


if __name__ == "__main__":
    cli()