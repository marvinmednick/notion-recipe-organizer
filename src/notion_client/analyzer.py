"""Recipe analysis engine with LLM-powered categorization.

Version: v2
Last updated: Enhanced analysis with content quality assessment and title evaluation
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from openai import AzureOpenAI
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import config
from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)
console = Console()


class RecipeAnalyzer:
    """Analyze recipe data and provide categorization insights."""

    def __init__(self):
        """Initialize the analyzer with Azure OpenAI client."""
        self.openai_client = AzureOpenAI(
            api_key=config.azure_openai_key,
            api_version=config.azure_openai_version,
            azure_endpoint=config.azure_openai_endpoint,
        )

    def load_recipes(self, file_path: Path) -> Dict[str, Any]:
        """Load recipe data from JSON file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            console.print(
                f"✅ Loaded {data.get('total_records', 0)} recipes from {file_path}"
            )
            return data
        except Exception as e:
            console.print(f"❌ Failed to load recipes: {e}")
            return {}

    def analyze_basic_stats(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze basic statistics about the recipe collection."""
        records = recipe_data.get("records", [])

        stats = {
            "total_recipes": len(records),
            "recipes_with_urls": 0,
            "recipes_with_tags": 0,
            "unique_tags": set(),
            "tag_usage": Counter(),
            "title_patterns": [],
            "url_domains": Counter(),
        }

        for record in records:
            # URL analysis
            url = record.get("url", "")
            if url and url != "No URL":
                stats["recipes_with_urls"] += 1
                try:
                    # Extract domain from URL
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc
                    if domain:
                        stats["url_domains"][domain] += 1
                except:
                    pass

            # Tag analysis
            tags = record.get("tags", [])
            if tags:
                stats["recipes_with_tags"] += 1
                for tag in tags:
                    stats["unique_tags"].add(tag)
                    stats["tag_usage"][tag] += 1

            # Title patterns
            title = record.get("title", "")
            if title:
                stats["title_patterns"].append(title)

        # Convert set to list for JSON serialization
        stats["unique_tags"] = list(stats["unique_tags"])

        return stats

    def display_basic_stats(self, stats: Dict[str, Any]) -> None:
        """Display basic statistics in a nice format."""
        console.print("\n[bold blue]📊 Recipe Collection Statistics[/bold blue]")

        # Basic counts
        console.print(
            f"Total Recipes: [bold green]{stats['total_recipes']}[/bold green]"
        )
        console.print(
            f"Recipes with URLs: [bold cyan]{stats['recipes_with_urls']}[/bold cyan] ({stats['recipes_with_urls'] / stats['total_recipes'] * 100:.1f}%)"
        )
        console.print(
            f"Recipes with Tags: [bold yellow]{stats['recipes_with_tags']}[/bold yellow] ({stats['recipes_with_tags'] / stats['total_recipes'] * 100:.1f}%)"
        )
        console.print(
            f"Unique Tags: [bold magenta]{len(stats['unique_tags'])}[/bold magenta]"
        )

        # Tag usage table
        if stats["tag_usage"]:
            console.print("\n[bold blue]🏷️ Current Tag Usage[/bold blue]")
            tag_table = Table()
            tag_table.add_column("Tag", style="cyan")
            tag_table.add_column("Count", style="green")
            tag_table.add_column("% of Total", style="yellow")

            for tag, count in stats["tag_usage"].most_common():
                percentage = count / stats["total_recipes"] * 100
                tag_table.add_row(tag, str(count), f"{percentage:.1f}%")

            console.print(tag_table)

        # Top URL domains
        if stats["url_domains"]:
            console.print("\n[bold blue]🌐 Recipe Sources (Top Domains)[/bold blue]")
            domain_table = Table()
            domain_table.add_column("Domain", style="cyan")
            domain_table.add_column("Count", style="green")

            for domain, count in stats["url_domains"].most_common(10):
                domain_table.add_row(domain, str(count))

            console.print(domain_table)

    def categorize_recipes_llm(
        self,
        recipe_data: Dict[str, Any],
        sample_size: Optional[int] = None,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        batch_size: Optional[int] = None,
        batch_delay: float = 0,
        timeout: int = 30,
        include_content_review: bool = True,
    ) -> Dict[str, Any]:
        """Use LLM to categorize recipes based on titles and content."""
        records = recipe_data.get("records", [])

        # Apply range filtering first
        if start_index is not None or end_index is not None:
            start_idx = start_index or 0
            end_idx = end_index or len(records)
            records = (
                records[start_idx : end_idx + 1]
                if end_index is not None
                else records[start_idx:]
            )

        # Apply sample size (for backward compatibility)
        elif sample_size:
            records = records[:sample_size]

        total_recipes = len(records)

        categorization_results = {
            "total_analyzed": 0,
            "total_attempted": total_recipes,
            "categorizations": [],
            "category_distribution": defaultdict(int),
            "cuisine_distribution": defaultdict(int),
            "dietary_tags_distribution": defaultdict(int),
            "usage_tags_distribution": defaultdict(int),
            "failed_analyses": [],
            "content_quality_stats": {
                "non_recipes": 0,
                "titles_needing_improvement": 0,
                "average_quality_score": 0,
                "quality_distribution": defaultdict(int),
            },
            "processing_info": {
                "start_index": start_index or 0,
                "end_index": end_index,
                "batch_size": batch_size,
                "timeout": timeout,
                "include_content_review": include_content_review,
            },
        }

        console.print(
            f"\n[bold blue]🤖 Analyzing {total_recipes} recipes with LLM...[/bold blue]"
        )

        if include_content_review:
            console.print(
                "[dim]Enhanced analysis: content quality + categorization[/dim]"
            )
        else:
            console.print("[dim]Standard analysis: categorization only[/dim]")

        if start_index is not None or end_index is not None:
            range_info = f"Range: {start_index or 0} to {end_index or len(recipe_data.get('records', [])) - 1}"
            console.print(f"[dim]{range_info}[/dim]")

        if batch_size:
            num_batches = (
                total_recipes + batch_size - 1
            ) // batch_size  # Ceiling division
            console.print(
                f"[dim]Processing in {num_batches} batches of {batch_size} recipes[/dim]"
            )
            if batch_delay > 0:
                console.print(f"[dim]{batch_delay}s delay between batches[/dim]")

        # Process in batches or all at once
        if batch_size and batch_size < total_recipes:
            self._process_in_batches(
                records,
                categorization_results,
                batch_size,
                batch_delay,
                timeout,
                start_index or 0,
                include_content_review,
            )
        else:
            self._process_single_batch(
                records,
                categorization_results,
                timeout,
                start_index or 0,
                include_content_review,
            )

        # Calculate content quality statistics
        self._calculate_content_quality_stats(categorization_results)

        return categorization_results

    def _process_in_batches(
        self,
        records: List[Dict],
        results: Dict,
        batch_size: int,
        batch_delay: float,
        timeout: int,
        start_offset: int,
        include_content_review: bool,
    ) -> None:
        """Process recipes in batches with delays."""
        import time

        num_batches = (len(records) + batch_size - 1) // batch_size

        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(records))
            batch_records = records[start_idx:end_idx]

            actual_start_idx = start_offset + start_idx
            actual_end_idx = start_offset + end_idx - 1

            console.print(
                f"\n[bold cyan]Batch {batch_num + 1}/{num_batches}: Recipes {actual_start_idx}-{actual_end_idx} ({len(batch_records)} recipes)[/bold cyan]"
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Processing batch {batch_num + 1}...", total=len(batch_records)
                )

                for i, record in enumerate(batch_records):
                    recipe_idx = actual_start_idx + i
                    progress.update(
                        task,
                        advance=1,
                        description=f"Analyzing recipe {recipe_idx} ({i + 1}/{len(batch_records)})",
                    )

                    self._analyze_and_store_recipe(
                        record, results, timeout, recipe_idx, include_content_review
                    )

            console.print(
                f"✅ Batch {batch_num + 1} complete: {len(batch_records)} recipes processed"
            )

            # Delay between batches (except for last batch)
            if batch_delay > 0 and batch_num < num_batches - 1:
                console.print(
                    f"[dim]⏳ Waiting {batch_delay}s before next batch...[/dim]"
                )
                time.sleep(batch_delay)

    def _process_single_batch(
        self,
        records: List[Dict],
        results: Dict,
        timeout: int,
        start_offset: int,
        include_content_review: bool,
    ) -> None:
        """Process all recipes in a single batch."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing recipes...", total=len(records))

            for i, record in enumerate(records):
                recipe_idx = start_offset + i
                progress.update(
                    task,
                    advance=1,
                    description=f"Analyzing recipe {recipe_idx} ({i + 1}/{len(records)})",
                )

                self._analyze_and_store_recipe(
                    record, results, timeout, recipe_idx, include_content_review
                )

    def _analyze_and_store_recipe(
        self,
        record: Dict,
        results: Dict,
        timeout: int,
        recipe_idx: int,
        include_content_review: bool,
    ) -> None:
        """Analyze a single recipe and store results."""
        title = record.get("title", "Untitled")
        existing_tags = record.get("tags", [])

        # Analyze recipe with timeout and error handling
        categorization = self._analyze_single_recipe(
            title, existing_tags, timeout, recipe_idx, include_content_review
        )

        if categorization:
            categorization["original_title"] = title
            categorization["existing_tags"] = existing_tags
            categorization["record_id"] = record.get("record_id", "")
            categorization["recipe_index"] = recipe_idx

            results["categorizations"].append(categorization)
            results["total_analyzed"] += 1

            # Update distributions
            if categorization.get("primary_category"):
                results["category_distribution"][
                    categorization["primary_category"]
                ] += 1
            if categorization.get("cuisine_type"):
                results["cuisine_distribution"][categorization["cuisine_type"]] += 1
            for tag in categorization.get("dietary_tags", []):
                results["dietary_tags_distribution"][tag] += 1
            for tag in categorization.get("usage_tags", []):
                results["usage_tags_distribution"][tag] += 1

            # Update content quality stats
            if include_content_review:
                if not categorization.get("is_recipe", True):
                    results["content_quality_stats"]["non_recipes"] += 1
                if categorization.get("title_needs_improvement", False):
                    results["content_quality_stats"]["titles_needing_improvement"] += 1
                quality_score = categorization.get("quality_score", 0)
                if quality_score > 0:
                    results["content_quality_stats"]["quality_distribution"][
                        quality_score
                    ] += 1
        else:
            # Record failed analysis
            results["failed_analyses"].append(
                {
                    "recipe_index": recipe_idx,
                    "title": title,
                    "existing_tags": existing_tags,
                }
            )

    def _analyze_single_recipe(
        self,
        title: str,
        existing_tags: List[str],
        timeout: int = 30,
        recipe_idx: Optional[int] = None,
        include_content_review: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single recipe using LLM with timeout and error handling."""
        # Load configuration and build prompt
        config_loader = ConfigLoader()
        prompt = self._build_prompt_from_config(
            title, existing_tags, config_loader, include_content_review
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=config.azure_openai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a culinary expert helping categorize recipes. Always respond with valid JSON in the exact format requested.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=600,  # Increased for enhanced analysis
                timeout=timeout,
            )

            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                result = json.loads(response_text)

                # Validate required fields for enhanced analysis
                if include_content_review:
                    required_fields = [
                        "is_recipe",
                        "content_summary",
                        "title_needs_improvement",
                        "proposed_title",
                        "quality_score",
                        "primary_category",
                    ]
                    missing_fields = [
                        field for field in required_fields if field not in result
                    ]
                    if missing_fields:
                        logger.warning(
                            f"Missing enhanced analysis fields for recipe {recipe_idx}: {missing_fields}"
                        )

                return result
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid JSON response for recipe {recipe_idx} '{title}': {response_text}"
                )
                return None

        except Exception as e:
            error_msg = f"LLM analysis failed for recipe {recipe_idx} '{title}': {e}"
            if "timeout" in str(e).lower():
                logger.error(f"Timeout ({timeout}s) for recipe {recipe_idx} '{title}'")
            else:
                logger.error(error_msg)
            return None

    def _build_prompt_from_config(
        self,
        title: str,
        existing_tags: List[str],
        config_loader: ConfigLoader,
        include_content_review: bool = True,
    ) -> str:
        """Build LLM prompt from YAML configuration files."""
        # Load the base prompt template
        base_prompt_path = Path("config/prompts/base_prompt.txt")

        if not base_prompt_path.exists():
            # Fallback to hardcoded prompt if template file doesn't exist
            return self._build_fallback_prompt(
                title, existing_tags, include_content_review
            )

        try:
            with open(base_prompt_path, "r") as f:
                template = f.read()

            # Replace template variables with actual content
            formatted_prompt = template.replace("{{recipe_title}}", title)
            formatted_prompt = formatted_prompt.replace(
                "{{existing_tags}}", str(existing_tags) if existing_tags else "None"
            )
            formatted_prompt = formatted_prompt.replace(
                "{{primary_categories}}", config_loader.format_categories_for_prompt()
            )
            formatted_prompt = formatted_prompt.replace(
                "{{cuisine_types}}", config_loader.format_cuisines_for_prompt()
            )
            formatted_prompt = formatted_prompt.replace(
                "{{dietary_tags}}", config_loader.format_dietary_tags_for_prompt()
            )
            formatted_prompt = formatted_prompt.replace(
                "{{usage_tags}}", config_loader.format_usage_tags_for_prompt()
            )
            formatted_prompt = formatted_prompt.replace(
                "{{conflict_rules}}", config_loader.format_conflict_rules_for_prompt()
            )

            return formatted_prompt

        except Exception as e:
            logger.warning(f"Failed to load prompt template: {e}, using fallback")
            return self._build_fallback_prompt(
                title, existing_tags, include_content_review
            )

    def _build_fallback_prompt(
        self, title: str, existing_tags: List[str], include_content_review: bool = True
    ) -> str:
        """Fallback prompt if YAML config system fails."""
        base_prompt = f"""
Analyze this recipe and categorize it:

Recipe Title: "{title}"
Existing Tags: {existing_tags if existing_tags else "None"}

PRIMARY CATEGORY (choose exactly one):
- Not a Recipe, Breakfast, Beef, Chicken, Pork, Seafood, Vegetarian, Baking, Sides & Appetizers, Desserts

CUISINE TYPE: Mexican, Italian, Asian, American, Mediterranean, Indian, French, Other

DIETARY TAGS: Food Allergy Safe, Vegetarian, Vegan, Gluten-Free, Dairy-Free, Low-Carb, Keto, Quick & Easy, One Pot, Make Ahead

USAGE TAGS: Want to Try, Holiday/Special Occasion

Respond in JSON format:
"""

        if include_content_review:
            return (
                base_prompt
                + """
{
    "is_recipe": true/false,
    "content_summary": "Brief description of content",
    "title_needs_improvement": true/false,
    "proposed_title": "Suggested title or same if good",
    "quality_score": 3,
    "primary_category": "category_name",
    "cuisine_type": "cuisine_name_or_Other",
    "dietary_tags": ["tag1", "tag2"],
    "usage_tags": ["tag1", "tag2"],
    "confidence": 4,
    "reasoning": "Brief explanation"
}
"""
            )
        else:
            return (
                base_prompt
                + """
{
    "primary_category": "category_name",
    "cuisine_type": "cuisine_name_or_Other",
    "dietary_tags": ["tag1", "tag2"],
    "usage_tags": ["tag1", "tag2"],
    "confidence": 4,
    "reasoning": "Brief explanation"
}
"""
            )

    def _calculate_content_quality_stats(self, results: Dict[str, Any]) -> None:
        """Calculate content quality statistics from analysis results."""
        if not results["categorizations"]:
            return

        quality_scores = []
        for cat in results["categorizations"]:
            quality_score = cat.get("quality_score", 0)
            if quality_score > 0:
                quality_scores.append(quality_score)

        if quality_scores:
            results["content_quality_stats"]["average_quality_score"] = sum(
                quality_scores
            ) / len(quality_scores)

    def display_categorization_results(self, results: Dict[str, Any]) -> None:
        """Display categorization results in a nice format."""
        console.print(f"\n[bold blue]🎯 LLM Categorization Results[/bold blue]")
        console.print(
            f"Analyzed: [bold green]{results['total_analyzed']}[/bold green] / {results['total_attempted']} recipes"
        )

        # Show failed analyses if any
        if results["failed_analyses"]:
            console.print(
                f"Failed: [bold red]{len(results['failed_analyses'])}[/bold red] recipes"
            )
            console.print("[dim]Check logs for timeout or error details[/dim]")

        # Content quality overview (if enhanced analysis was performed)
        if results.get("processing_info", {}).get("include_content_review"):
            self._display_content_quality_overview(results)

        # Primary category distribution
        console.print("\n[bold blue]📂 Primary Category Distribution[/bold blue]")
        category_table = Table()
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Count", style="green")
        category_table.add_column("% of Analyzed", style="yellow")

        total = results["total_analyzed"]
        if total > 0:
            for category, count in sorted(results["category_distribution"].items()):
                percentage = count / total * 100
                category_table.add_row(category, str(count), f"{percentage:.1f}%")

        console.print(category_table)

        # Cuisine distribution
        if results["cuisine_distribution"]:
            console.print("\n[bold blue]🌍 Cuisine Type Distribution[/bold blue]")
            cuisine_table = Table()
            cuisine_table.add_column("Cuisine", style="cyan")
            cuisine_table.add_column("Count", style="green")

            for cuisine, count in sorted(
                results["cuisine_distribution"].items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                cuisine_table.add_row(cuisine, str(count))

            console.print(cuisine_table)

        # Dietary tags
        if results["dietary_tags_distribution"]:
            console.print("\n[bold blue]🏷️ Dietary Tags Distribution[/bold blue]")
            dietary_table = Table()
            dietary_table.add_column("Dietary Tag", style="cyan")
            dietary_table.add_column("Count", style="green")

            for tag, count in sorted(
                results["dietary_tags_distribution"].items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                dietary_table.add_row(tag, str(count))

            console.print(dietary_table)

        # Usage tags
        if results["usage_tags_distribution"]:
            console.print("\n[bold blue]📋 Usage Tags Distribution[/bold blue]")
            usage_table = Table()
            usage_table.add_column("Usage Tag", style="cyan")
            usage_table.add_column("Count", style="green")

            for tag, count in sorted(
                results["usage_tags_distribution"].items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                usage_table.add_row(tag, str(count))

            console.print(usage_table)

    def _display_content_quality_overview(self, results: Dict[str, Any]) -> None:
        """Display content quality analysis overview."""
        quality_stats = results.get("content_quality_stats", {})

        console.print("\n[bold blue]📊 Content Quality Overview[/bold blue]")

        # Non-recipe items
        non_recipes = quality_stats.get("non_recipes", 0)
        if non_recipes > 0:
            console.print(
                f"Non-recipe items: [bold yellow]{non_recipes}[/bold yellow] (flagged for review)"
            )

        # Title improvements
        title_improvements = quality_stats.get("titles_needing_improvement", 0)
        if title_improvements > 0:
            console.print(
                f"Titles needing improvement: [bold cyan]{title_improvements}[/bold cyan]"
            )

        # Average quality score
        avg_quality = quality_stats.get("average_quality_score", 0)
        if avg_quality > 0:
            console.print(
                f"Average quality score: [bold green]{avg_quality:.1f}/5[/bold green]"
            )

        # Quality distribution
        quality_dist = quality_stats.get("quality_distribution", {})
        if quality_dist:
            console.print("\n[bold blue]⭐ Quality Score Distribution[/bold blue]")
            quality_table = Table()
            quality_table.add_column("Score", style="cyan")
            quality_table.add_column("Count", style="green")
            quality_table.add_column("Description", style="yellow")

            score_descriptions = {
                1: "Poor/Not useful",
                2: "Below average",
                3: "Average/Decent",
                4: "Good/Useful",
                5: "Excellent/Very useful",
            }

            for score in sorted(quality_dist.keys()):
                count = quality_dist[score]
                description = score_descriptions.get(score, "Unknown")
                quality_table.add_row(str(score), str(count), description)

            console.print(quality_table)

    def save_analysis_results(
        self, stats: Dict[str, Any], categorization: Dict[str, Any], output_path: Path
    ) -> None:
        """Save analysis results to file."""
        results = {
            "analysis_timestamp": str(datetime.now()),
            "basic_stats": stats,
            "llm_categorization": categorization,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        console.print(
            f"💾 Analysis results saved to: [bold green]{output_path}[/bold green]"
        )

        # Save specialized reports if enhanced analysis was performed
        if categorization.get("processing_info", {}).get("include_content_review"):
            self._save_specialized_reports(categorization, output_path.parent)

    def _save_specialized_reports(
        self, categorization_results: Dict[str, Any], output_dir: Path
    ) -> None:
        """Save specialized reports for content issues and title improvements."""
        categorizations = categorization_results.get("categorizations", [])

        # Content issues report (non-recipes)
        non_recipes = [cat for cat in categorizations if not cat.get("is_recipe", True)]
        if non_recipes:
            content_issues_path = output_dir / "content_issues_report.json"
            content_issues = {
                "timestamp": str(datetime.now()),
                "total_non_recipes": len(non_recipes),
                "non_recipe_items": non_recipes,
            }

            with open(content_issues_path, "w") as f:
                json.dump(content_issues, f, indent=2, default=str)

            console.print(
                f"📋 Content issues report saved to: [bold yellow]{content_issues_path}[/bold yellow]"
            )

        # Title improvements report
        title_improvements = [
            cat for cat in categorizations if cat.get("title_needs_improvement", False)
        ]
        if title_improvements:
            title_improvements_path = output_dir / "title_improvements.csv"

            import csv

            with open(
                title_improvements_path, "w", newline="", encoding="utf-8"
            ) as csvfile:
                fieldnames = [
                    "recipe_index",
                    "original_title",
                    "proposed_title",
                    "reasoning",
                    "record_id",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for cat in title_improvements:
                    writer.writerow(
                        {
                            "recipe_index": cat.get("recipe_index", ""),
                            "original_title": cat.get("original_title", ""),
                            "proposed_title": cat.get("proposed_title", ""),
                            "reasoning": cat.get("reasoning", ""),
                            "record_id": cat.get("record_id", ""),
                        }
                    )

            console.print(
                f"📝 Title improvements report saved to: [bold cyan]{title_improvements_path}[/bold cyan]"
            )

        # Processing summary
        processing_summary_path = output_dir / "processing_summary.json"
        processing_summary = {
            "timestamp": str(datetime.now()),
            "total_analyzed": categorization_results.get("total_analyzed", 0),
            "total_attempted": categorization_results.get("total_attempted", 0),
            "failed_analyses_count": len(
                categorization_results.get("failed_analyses", [])
            ),
            "content_quality_stats": categorization_results.get(
                "content_quality_stats", {}
            ),
            "processing_info": categorization_results.get("processing_info", {}),
            "failed_analyses": categorization_results.get("failed_analyses", []),
        }

        with open(processing_summary_path, "w") as f:
            json.dump(processing_summary, f, indent=2, default=str)

        console.print(
            f"📊 Processing summary saved to: [bold green]{processing_summary_path}[/bold green]"
        )

