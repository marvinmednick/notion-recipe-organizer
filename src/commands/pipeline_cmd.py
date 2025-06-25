"""Pipeline command for chaining extract, analyze, and review operations."""

from typing import List, Optional
import click

from ..pipeline import run_pipeline


@click.command()
@click.argument("steps", nargs=-1, required=True)
@click.option(
    "--profile", 
    help="Use configuration profile for all steps"
)
@click.option(
    "--database-id",
    help="Database ID for extract step"
)
@click.option(
    "--limit", 
    type=int, 
    help="Limit number of items processed (applies to compatible steps)"
)
@click.option(
    "--timeout", 
    type=int, 
    help="Timeout for LLM calls (applies to analyze step)"
)
@click.option(
    "--dry-run", 
    is_flag=True, 
    help="Dry run mode (applies to compatible steps)"
)
@click.option(
    "--quick", 
    is_flag=True, 
    help="Quick mode for analyze step (statistics only)"
)
def pipeline(
    steps: List[str],
    profile: Optional[str],
    database_id: Optional[str],
    limit: Optional[int],
    timeout: Optional[int],
    dry_run: bool,
    quick: bool
) -> None:
    """Run multiple commands in sequence.
    
    Execute extract, analyze, and review commands as a coordinated pipeline.
    Each step uses the output from the previous step automatically.
    
    Examples:
    
      pipeline extract analyze review           # Full pipeline
      
      pipeline analyze review                   # Skip extraction
      
      pipeline extract analyze                  # Stop before review
      
      pipeline extract analyze review --limit 10
      
      pipeline --profile testing extract analyze review
      
      pipeline --dry-run extract analyze       # Test mode
    """
    # Build global options dictionary
    global_options = {}
    
    if database_id:
        global_options["database_id"] = database_id
    if limit:
        global_options["limit"] = limit
    if timeout:
        global_options["timeout"] = timeout
    if dry_run:
        global_options["dry_run"] = dry_run
    if quick:
        global_options["quick"] = quick
    if profile:
        global_options["profile"] = profile
    
    # Execute pipeline
    run_pipeline(list(steps), profile, global_options)