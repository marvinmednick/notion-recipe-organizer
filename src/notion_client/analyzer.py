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
        self, recipe_data: Dict[str, Any], sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Use LLM to categorize recipes based on titles and content."""
        records = recipe_data.get("records", [])

        # Sample recipes if requested
        if sample_size:
            records = records[:sample_size]

        categorization_results = {
            "total_analyzed": len(records),
            "categorizations": [],
            "category_distribution": defaultdict(int),
            "cuisine_distribution": defaultdict(int),
            "dietary_tags_distribution": defaultdict(int),
        }

        console.print(
            f"\n[bold blue]🤖 Analyzing {len(records)} recipes with LLM...[/bold blue]"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing recipes...", total=len(records))

            for i, record in enumerate(records):
                progress.update(
                    task,
                    advance=1,
                    description=f"Analyzing recipe {i + 1}/{len(records)}",
                )

                title = record.get("title", "Untitled")
                existing_tags = record.get("tags", [])

                # Create prompt for LLM analysis
                categorization = self._analyze_single_recipe(title, existing_tags)

                if categorization:
                    categorization["original_title"] = title
                    categorization["existing_tags"] = existing_tags
                    categorization["record_id"] = record.get("record_id", "")

                    categorization_results["categorizations"].append(categorization)

                    # Update distributions
                    if categorization.get("primary_category"):
                        categorization_results["category_distribution"][
                            categorization["primary_category"]
                        ] += 1
                    if categorization.get("cuisine_type"):
                        categorization_results["cuisine_distribution"][
                            categorization["cuisine_type"]
                        ] += 1
                    for tag in categorization.get("dietary_tags", []):
                        categorization_results["dietary_tags_distribution"][tag] += 1

        return categorization_results

    def _analyze_single_recipe(
        self, title: str, existing_tags: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single recipe using LLM."""
        prompt = f"""
Analyze this recipe and categorize it according to the schema below.

Recipe Title: "{title}"
Existing Tags: {existing_tags if existing_tags else "None"}

Please categorize this recipe using the following schema:

PRIMARY CATEGORY (choose exactly one):
- Breakfast
- Beef
- Chicken  
- Pork
- Seafood
- Vegetarian
- Baking
- Sides & Appetizers
- Desserts

CUISINE TYPE (choose one if applicable, or "Other"):
- Mexican
- Italian
- American
- Asian
- Mediterranean
- Indian
- French
- Other

DIETARY TAGS (select all that apply):
- Food Allergy Safe
- Vegetarian
- Vegan
- Gluten-Free
- Dairy-Free
- Low-Carb
- Keto
- Quick & Easy (under 30 minutes)
- One Pot

CONFIDENCE (1-5 scale):
Rate your confidence in this categorization from 1 (uncertain) to 5 (very confident).

Respond in this exact JSON format:
{{
    "primary_category": "category_name",
    "cuisine_type": "cuisine_name_or_Other",
    "dietary_tags": ["tag1", "tag2"],
    "confidence": 4,
    "reasoning": "Brief explanation of your categorization choices"
}}
"""

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
            )

            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response for '{title}': {response_text}")
                return None

        except Exception as e:
            logger.error(f"LLM analysis failed for '{title}': {e}")
            return None

    def display_categorization_results(self, results: Dict[str, Any]) -> None:
        """Display categorization results in a nice format."""
        console.print(f"\n[bold blue]🎯 LLM Categorization Results[/bold blue]")
        console.print(
            f"Analyzed: [bold green]{results['total_analyzed']}[/bold green] recipes"
        )

        # Primary category distribution
        console.print("\n[bold blue]📂 Primary Category Distribution[/bold blue]")
        category_table = Table()
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Count", style="green")
        category_table.add_column("% of Total", style="yellow")

        total = results["total_analyzed"]
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

