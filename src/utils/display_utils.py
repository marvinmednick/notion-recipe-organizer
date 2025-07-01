"""Display utilities for Rich console output."""

from rich.console import Console
from rich.table import Table
from typing import List, Dict, Any

console = Console()


def print_header(text: str, icon: str = "🔧"):
    """Print a formatted header."""
    console.print(f"[bold blue]{icon} {text}[/bold blue]")


def print_success(text: str):
    """Print a success message."""
    console.print(f"✅ {text}")


def print_error(text: str):
    """Print an error message."""
    console.print(f"❌ {text}")


def print_warning(text: str):
    """Print a warning message."""
    console.print(f"[yellow]⚠️  {text}[/yellow]")


def print_info(text: str):
    """Print an info message."""
    console.print(f"[dim]ℹ️  {text}[/dim]")


def create_database_properties_table(properties: Dict[str, Any]) -> Table:
    """Create a table showing database properties."""
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
    
    return table


def create_sample_records_table(records: List[Dict[str, Any]], extract_props_func) -> Table:
    """Create a table showing sample records."""
    table = Table(title="Sample Records")
    table.add_column("Title", style="cyan")
    table.add_column("URL", style="blue")
    table.add_column("Tags", style="yellow")
    table.add_column("Created", style="green")

    for record in records:
        # Extract properties using provided function
        props = extract_props_func(record)

        title = props.get("Name", "Untitled")
        url = (
            props.get("URL", "No URL")[:50] + "..."
            if len(props.get("URL", "")) > 50
            else props.get("URL", "No URL")
        )
        tags = ", ".join(props.get("Tags", [])) or "No tags"
        created = props.get("Created", "Unknown")[:10]  # Just date part

        table.add_row(title, url, tags, created)
    
    return table


def show_dry_run_results(recipes_data: List[Dict[str, Any]]):
    """Display dry run results."""
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


def show_completion_message(message: str = "completed"):
    """Show completion message."""
    console.print(f"\n[bold green]🎉 {message.title()}![/bold green]")