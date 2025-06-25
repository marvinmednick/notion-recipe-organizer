"""Pipeline orchestration for chaining extract, analyze, and review commands."""

from typing import Dict, Any, List, Optional
from rich.console import Console

from .config import config
from .utils.config_utils import get_notion_client
from .notion_client.profile_loader import ProfileLoader

console = Console()


class PipelineStepError(Exception):
    """Exception raised when a pipeline step fails."""
    
    def __init__(self, step: str, message: str):
        self.step = step
        self.message = message
        super().__init__(f"Pipeline step '{step}' failed: {message}")


class PipelineContext:
    """Shared context for pipeline execution."""
    
    def __init__(self, profile_settings: Dict[str, Any], global_options: Dict[str, Any]):
        self.profile_settings = profile_settings
        self.global_options = global_options
        self.config = config
        self._notion_client = None
        
    def get_notion_client(self):
        """Get shared Notion client instance."""
        if self._notion_client is None:
            self._notion_client = get_notion_client()
        return self._notion_client


def _run_extract_step(ctx: PipelineContext) -> None:
    """Execute extract step with pipeline context."""
    from .commands.extract_cmd import extract
    
    # Get settings from context
    extract_settings = ctx.profile_settings.get("extract", {})
    limit = ctx.global_options.get("limit") or extract_settings.get("records")
    
    try:
        # Call extract function directly
        extract.callback(
            database_id=ctx.global_options.get("database_id"),
            output=None,  # Use default output path
            max_records=limit,
            dry_run=ctx.global_options.get("dry_run", False)
        )
    except Exception as e:
        raise PipelineStepError("extract", str(e))


def _run_analyze_step(ctx: PipelineContext) -> None:
    """Execute analyze step with pipeline context."""
    from .commands.analyze_cmd import analyze
    
    # Get settings from context
    analyze_settings = ctx.profile_settings.get("analyze", {})
    limit = ctx.global_options.get("limit") or analyze_settings.get("recipes")
    timeout = ctx.global_options.get("timeout") or analyze_settings.get("timeout")
    batch_size = analyze_settings.get("batch_size")
    batch_delay = analyze_settings.get("batch_delay")
    
    try:
        # Call analyze function directly
        analyze.callback(
            input_file=None,  # Use default input file
            output=None,  # Use default output file
            profile=ctx.global_options.get("profile"),
            quick=ctx.global_options.get("quick", False),
            sample=limit,
            start_index=None,
            end_index=None,
            range_spec=None,
            batch_size=batch_size,
            batch_delay=batch_delay,
            timeout=timeout,
            use_llm=analyze_settings.get("use_llm", True),
            include_content_review=analyze_settings.get("include_content_review", True),
            basic_only=False
        )
    except Exception as e:
        raise PipelineStepError("analyze", str(e))


def _run_review_step(ctx: PipelineContext) -> None:
    """Execute review step with pipeline context."""
    from .commands.review_cmd import review
    
    # Get settings from context
    review_settings = ctx.profile_settings.get("review", {})
    
    try:
        # Call review function directly
        review.callback(
            input_file=None,  # Use default input file
            output=None,  # Use default output directory
            html=True,  # Always generate HTML by default
            csv=review_settings.get("csv", False),
            issues_only=review_settings.get("issues_only", False),
            summary=review_settings.get("summary", False)
        )
    except Exception as e:
        raise PipelineStepError("review", str(e))


def run_pipeline(
    steps: List[str],
    profile: Optional[str] = None,
    global_options: Optional[Dict[str, Any]] = None
) -> None:
    """Run a pipeline of commands in sequence.
    
    Args:
        steps: List of step names to execute ("extract", "analyze", "review")
        profile: Configuration profile to use
        global_options: Global options to apply across steps
    """
    if global_options is None:
        global_options = {}
    
    # Validate steps
    valid_steps = ["extract", "analyze", "review"]
    invalid_steps = [step for step in steps if step not in valid_steps]
    
    if invalid_steps:
        console.print(f"[red]❌ Invalid steps: {', '.join(invalid_steps)}[/red]")
        console.print(f"Valid steps: {', '.join(valid_steps)}")
        return
    
    console.print(f"[bold blue]🔄 Running Pipeline: {' → '.join(steps)}[/bold blue]")
    
    if profile:
        console.print(f"[dim]Using profile: {profile}[/dim]")
    
    # Load profile settings
    profile_loader = ProfileLoader()
    profile_settings: Dict[str, Any] = {}
    if profile:
        try:
            profile_settings = profile_loader.get_profile_settings(profile)
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not load profile '{profile}': {e}[/yellow]")
    
    # Create pipeline context
    ctx = PipelineContext(profile_settings, global_options)
    
    # Step function mapping
    step_functions = {
        "extract": _run_extract_step,
        "analyze": _run_analyze_step,
        "review": _run_review_step
    }
    
    # Execute steps in sequence
    for i, step in enumerate(steps):
        console.print(f"\n[bold cyan]📋 Step {i+1}/{len(steps)}: {step.title()}[/bold cyan]")
        
        try:
            step_functions[step](ctx)
        except PipelineStepError as e:
            console.print(f"[red]❌ Pipeline failed at step '{e.step}': {e.message}[/red]")
            
            # Show helpful restart guidance
            remaining_steps = steps[i:]
            if len(remaining_steps) > 1:
                console.print(f"[dim]💡 Fix the error and restart with: pipeline {' '.join(remaining_steps)}[/dim]")
            return
        except Exception as e:
            console.print(f"[red]❌ Unexpected error in step '{step}': {e}[/red]")
            return
    
    console.print(f"\n[bold green]🎉 Pipeline completed successfully![/bold green]")