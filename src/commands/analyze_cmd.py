"""Analyze command for Notion Recipe Organizer."""

from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console

from ..config import config
from ..notion_client.analyzer import RecipeAnalyzer
from ..notion_client.profile_loader import ProfileLoader

console = Console()


@click.command()
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