"""Recipe analysis engine with LLM-powered categorization.

Version: v1
Last updated: Initial analysis tools with Azure OpenAI integration
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
            "processing_info": {
                "start_index": start_index or 0,
                "end_index": end_index,
                "batch_size": batch_size,
                "timeout": timeout,
            },
        }

        console.print(
            f"\n[bold blue]🤖 Analyzing {total_recipes} recipes with LLM...[/bold blue]"
        )

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
            )
        else:
            self._process_single_batch(
                records, categorization_results, timeout, start_index or 0
            )

        return categorization_results

    def _process_in_batches(
        self,
        records: List[Dict],
        results: Dict,
        batch_size: int,
        batch_delay: float,
        timeout: int,
        start_offset: int,
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

                    self._analyze_and_store_recipe(record, results, timeout, recipe_idx)

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
        self, records: List[Dict], results: Dict, timeout: int, start_offset: int
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

                self._analyze_and_store_recipe(record, results, timeout, recipe_idx)

    def _analyze_and_store_recipe(
        self, record: Dict, results: Dict, timeout: int, recipe_idx: int
    ) -> None:
        """Analyze a single recipe and store results."""
        title = record.get("title", "Untitled")
        existing_tags = record.get("tags", [])

        # Analyze recipe with timeout and error handling
        categorization = self._analyze_single_recipe(
            title, existing_tags, timeout, recipe_idx
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
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single recipe using LLM with timeout and error handling."""
        # Load configuration and build prompt
        config_loader = ConfigLoader()
        prompt = self._build_prompt_from_config(title, existing_tags, config_loader)

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
                max_tokens=500,
                timeout=timeout,  # Add timeout
            )

            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                return json.loads(response_text)
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
        self, title: str, existing_tags: List[str], config_loader: ConfigLoader
    ) -> str:
        """Build LLM prompt from YAML configuration files."""
        # Load the base prompt template
        base_prompt_path = Path("config/prompts/base_prompt.txt")

        if not base_prompt_path.exists():
            # Fallback to hardcoded prompt if template file doesn't exist
            return self._build_fallback_prompt(title, existing_tags)

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
            return self._build_fallback_prompt(title, existing_tags)

    def _build_fallback_prompt(self, title: str, existing_tags: List[str]) -> str:
        """Fallback prompt if YAML config system fails."""
        return f"""
Analyze this recipe and categorize it:

Recipe Title: "{title}"
Existing Tags: {existing_tags if existing_tags else "None"}

PRIMARY CATEGORY (choose exactly one):
- Breakfast, Beef, Chicken, Pork, Seafood, Vegetarian, Baking, Sides & Appetizers, Desserts

CUISINE TYPE: Mexican, Italian, Asian, American, Mediterranean, Indian, French, Other

DIETARY TAGS: Food Allergy Safe, Vegetarian, Vegan, Gluten-Free, Dairy-Free, Low-Carb, Keto, Quick & Easy, One Pot, Make Ahead

USAGE TAGS: Want to Try, Holiday/Special Occasion

Respond in JSON format:
{{
    "primary_category": "category_name",
    "cuisine_type": "cuisine_name_or_Other",
    "dietary_tags": ["tag1", "tag2"],
    "usage_tags": ["tag1", "tag2"],
    "confidence": 4,
    "reasoning": "Brief explanation"
}}
"""

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

