"""Main CLI entry point for Notion Recipe Organizer.

Version: v9 (Refactored)
Last updated: Split commands into separate modules for better maintainability
"""

import logging
from rich.console import Console
from rich.logging import RichHandler
import click

from .config import config
from .notion_client.client import NotionClient

# Import commands
from .commands.extract_cmd import extract
from .commands.test_cmd import test
from .commands.analyze_cmd import analyze
from .commands.review_cmd import review, apply_corrections
from .commands.pipeline_cmd import pipeline

console = Console()


def setup_logging(level: str = "INFO"):
    """Setup logging with Rich handler."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


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


@click.group(invoke_without_command=True)
@click.option("--log-level", default="INFO", help="Set logging level")
@click.option("--config-check", is_flag=True, help="Check configuration and exit")
@click.pass_context
def cli(ctx, log_level: str, config_check: bool):
    """Notion Recipe Organizer - Organize your Notion recipes with ease."""
    setup_logging(log_level)

    if config_check:
        check_config()
        return
    
    # If no command provided and not config-check, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register commands
cli.add_command(extract)
cli.add_command(test)
cli.add_command(analyze)
cli.add_command(review)
cli.add_command(apply_corrections)
cli.add_command(pipeline)


if __name__ == "__main__":
    cli()