"""Review commands for Notion Recipe Organizer."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..config import config
from ..notion_client.reviewer import RecipeReviewer

console = Console()


@click.command()
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


@click.command("apply-corrections")
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