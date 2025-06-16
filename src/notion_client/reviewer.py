"""Recipe review system for systematic review and correction of categorization results.

Version: v1
Created for Phase 1.6: Review System & Prompt Refinement
"""

import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


class RecipeReviewer:
    """Generate review interfaces and handle corrections for recipe categorization."""

    def __init__(self):
        """Initialize the reviewer."""
        pass

    def generate_html_review(
        self, analysis_file: Path, output_dir: Path, include_all: bool = True
    ) -> Path:
        """Generate an interactive HTML review interface."""
        console.print("[bold blue]🌐 Generating HTML Review Interface...[/bold blue]")

        # Load analysis results
        analysis_data = self._load_analysis_results(analysis_file)
        if not analysis_data:
            return None

        categorizations = analysis_data.get("llm_categorization", {}).get(
            "categorizations", []
        )

        if not categorizations:
            console.print(
                "[yellow]⚠️  No categorization results found to review[/yellow]"
            )
            return None

        # Generate HTML content
        html_content = self._generate_html_content(categorizations, analysis_data)

        # Save HTML file
        output_dir.mkdir(parents=True, exist_ok=True)
        html_file = output_dir / "review_report.html"

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        console.print(
            f"✅ HTML review interface saved to: [bold green]{html_file}[/bold green]"
        )
        console.print(
            f"[dim]Open in browser to review categorizations interactively[/dim]"
        )

        return html_file

    def export_to_csv(
        self, analysis_file: Path, output_dir: Path, focus_on_issues: bool = False
    ) -> Path:
        """Export categorization results to CSV for editing."""
        console.print("[bold blue]📊 Exporting to CSV for Review...[/bold blue]")

        # Load analysis results
        analysis_data = self._load_analysis_results(analysis_file)
        if not analysis_data:
            return None

        categorizations = analysis_data.get("llm_categorization", {}).get(
            "categorizations", []
        )

        if not categorizations:
            console.print(
                "[yellow]⚠️  No categorization results found to export[/yellow]"
            )
            return None

        # Filter data if focusing on issues
        if focus_on_issues:
            categorizations = [
                cat
                for cat in categorizations
                if not cat.get("is_recipe", True)
                or cat.get("title_needs_improvement", False)
                or cat.get("quality_score", 5) < 3
            ]
            console.print(
                f"[dim]Focusing on {len(categorizations)} items with potential issues[/dim]"
            )

        # Generate CSV
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = output_dir / (
            "categorization_issues.csv"
            if focus_on_issues
            else "categorization_review.csv"
        )

        fieldnames = [
            "recipe_index",
            "record_id",
            "original_title",
            "proposed_title",
            "title_needs_improvement",
            "is_recipe",
            "primary_category",
            "cuisine_type",
            "dietary_tags",
            "usage_tags",
            "quality_score",
            "content_summary",
            "confidence",
            "reasoning",
            "existing_tags",
            # Review fields
            "corrected_title",
            "corrected_category",
            "corrected_is_recipe",
            "review_notes",
            "approved",
        ]

        with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for cat in categorizations:
                row = {
                    "recipe_index": cat.get("recipe_index", ""),
                    "record_id": cat.get("record_id", ""),
                    "original_title": cat.get("original_title", ""),
                    "proposed_title": cat.get("proposed_title", ""),
                    "title_needs_improvement": cat.get(
                        "title_needs_improvement", False
                    ),
                    "is_recipe": cat.get("is_recipe", True),
                    "primary_category": cat.get("primary_category", ""),
                    "cuisine_type": cat.get("cuisine_type", ""),
                    "dietary_tags": "; ".join(cat.get("dietary_tags", [])),
                    "usage_tags": "; ".join(cat.get("usage_tags", [])),
                    "quality_score": cat.get("quality_score", ""),
                    "content_summary": cat.get("content_summary", ""),
                    "confidence": cat.get("confidence", ""),
                    "reasoning": cat.get("reasoning", ""),
                    "existing_tags": "; ".join(cat.get("existing_tags", [])),
                    # Empty review fields for user to fill
                    "corrected_title": "",
                    "corrected_category": "",
                    "corrected_is_recipe": "",
                    "review_notes": "",
                    "approved": "",
                }
                writer.writerow(row)

        console.print(f"✅ CSV export saved to: [bold green]{csv_file}[/bold green]")
        console.print(
            f"[dim]Edit in Excel/Google Sheets and use apply-corrections to import changes[/dim]"
        )

        return csv_file

    def import_corrections(self, csv_file: Path, output_dir: Path) -> Path:
        """Import corrections from edited CSV file."""
        console.print("[bold blue]🔄 Importing Corrections from CSV...[/bold blue]")

        if not csv_file.exists():
            console.print(f"[red]❌ CSV file not found: {csv_file}[/red]")
            return None

        corrections = []
        issues_found = []

        with open(csv_file, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row_num, row in enumerate(
                reader, start=2
            ):  # Start at 2 because header is row 1
                correction = self._process_csv_row(row, row_num, issues_found)
                if correction:
                    corrections.append(correction)

        # Report any issues
        if issues_found:
            console.print(
                f"[yellow]⚠️  Found {len(issues_found)} issues in CSV:[/yellow]"
            )
            for issue in issues_found[:5]:  # Show first 5 issues
                console.print(f"[dim]Row {issue['row']}: {issue['message']}[/dim]")
            if len(issues_found) > 5:
                console.print(f"[dim]... and {len(issues_found) - 5} more issues[/dim]")

        # Save corrections
        if corrections:
            output_dir.mkdir(parents=True, exist_ok=True)
            corrections_file = output_dir / "corrections.json"

            corrections_data = {
                "timestamp": str(datetime.now()),
                "source_csv": str(csv_file),
                "total_corrections": len(corrections),
                "corrections": corrections,
                "import_issues": issues_found,
            }

            with open(corrections_file, "w") as f:
                json.dump(corrections_data, f, indent=2, default=str)

            console.print(
                f"✅ Imported {len(corrections)} corrections to: [bold green]{corrections_file}[/bold green]"
            )

            # Show summary
            self._display_corrections_summary(corrections)

            return corrections_file
        else:
            console.print("[yellow]⚠️  No corrections found in CSV file[/yellow]")
            return None

    def _load_analysis_results(self, analysis_file: Path) -> Optional[Dict]:
        """Load analysis results from JSON file."""
        try:
            with open(analysis_file, "r") as f:
                return json.load(f)
        except Exception as e:
            console.print(
                f"[red]❌ Failed to load analysis file {analysis_file}: {e}[/red]"
            )
            return None

    def _generate_html_content(
        self, categorizations: List[Dict], analysis_data: Dict
    ) -> str:
        """Generate the HTML content for the review interface."""

        # Get summary statistics
        basic_stats = analysis_data.get("basic_stats", {})
        llm_stats = analysis_data.get("llm_categorization", {})

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recipe Categorization Review</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .filters {{
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #eee;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .filter-group label {{
            font-weight: 600;
            color: #333;
        }}
        select, input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .search-box {{
            flex: 1;
            min-width: 200px;
            max-width: 400px;
        }}
        .table-container {{
            overflow-x: auto;
            max-height: 800px;
            overflow-y: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 12px 8px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .recipe-title {{
            font-weight: 600;
            color: #333;
            max-width: 250px;
            word-wrap: break-word;
        }}
        .proposed-title {{
            font-style: italic;
            color: #666;
            max-width: 250px;
            word-wrap: break-word;
        }}
        .category {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            white-space: nowrap;
        }}
        .category.not-recipe {{
            background: #ffebee;
            color: #c62828;
        }}
        .category.breakfast {{
            background: #fff3e0;
            color: #f57c00;
        }}
        .category.desserts {{
            background: #fce4ec;
            color: #c2185b;
        }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            max-width: 200px;
        }}
        .tag {{
            background: #f1f3f4;
            color: #5f6368;
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 11px;
            white-space: nowrap;
        }}
        .quality-score {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .stars {{
            color: #ffd700;
        }}
        .confidence {{
            width: 60px;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
        }}
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ff4444, #ffaa00, #00aa00);
            transition: width 0.3s ease;
        }}
        .needs-review {{
            background-color: #fff3cd !important;
            border-left: 4px solid #ffc107;
        }}
        .not-recipe-row {{
            background-color: #f8d7da !important;
            border-left: 4px solid #dc3545;
        }}
        .title-issue {{
            background-color: #cff4fc !important;
            border-left: 4px solid #0dcaf0;
        }}
        .summary {{
            max-width: 300px;
            font-size: 12px;
            color: #666;
            line-height: 1.4;
        }}
        .reasoning {{
            max-width: 250px;
            font-size: 12px;
            color: #666;
            line-height: 1.4;
        }}
        .export-buttons {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 1px solid #eee;
            display: flex;
            gap: 15px;
            justify-content: center;
        }}
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s ease;
        }}
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        .btn-primary:hover {{
            background: #5a67d8;
        }}
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍳 Recipe Categorization Review</h1>
            <p>Review and validate LLM categorization results</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{llm_stats.get("total_analyzed", 0)}</div>
                <div class="stat-label">Recipes Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{llm_stats.get("content_quality_stats", {}).get("non_recipes", 0)}</div>
                <div class="stat-label">Non-Recipe Items</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{llm_stats.get("content_quality_stats", {}).get("titles_needing_improvement", 0)}</div>
                <div class="stat-label">Title Improvements</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(llm_stats.get("failed_analyses", []))}</div>
                <div class="stat-label">Failed Analyses</div>
            </div>
        </div>

        <div class="filters">
            <div class="filter-group">
                <label for="categoryFilter">Category:</label>
                <select id="categoryFilter">
                    <option value="">All Categories</option>
                    <option value="Not a Recipe">Not a Recipe</option>
                    <option value="Breakfast">Breakfast</option>
                    <option value="Beef">Beef</option>
                    <option value="Chicken">Chicken</option>
                    <option value="Pork">Pork</option>
                    <option value="Seafood">Seafood</option>
                    <option value="Vegetarian">Vegetarian</option>
                    <option value="Baking">Baking</option>
                    <option value="Sides & Appetizers">Sides & Appetizers</option>
                    <option value="Desserts">Desserts</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label for="issueFilter">Show:</label>
                <select id="issueFilter">
                    <option value="">All Items</option>
                    <option value="needs-review">Items Needing Review</option>
                    <option value="not-recipe">Non-Recipe Items</option>
                    <option value="title-issues">Title Issues</option>
                    <option value="low-quality">Low Quality (≤2 stars)</option>
                </select>
            </div>

            <input type="text" id="searchBox" class="search-box" placeholder="Search by title or content...">
        </div>

        <div class="table-container">
            <table id="reviewTable">
                <thead>
                    <tr>
                        <th>Index</th>
                        <th>Original Title</th>
                        <th>Proposed Title</th>
                        <th>Is Recipe?</th>
                        <th>Category</th>
                        <th>Cuisine</th>
                        <th>Dietary Tags</th>
                        <th>Quality</th>
                        <th>Confidence</th>
                        <th>Content Summary</th>
                        <th>Reasoning</th>
                    </tr>
                </thead>
                <tbody id="reviewTableBody">
"""

        # Add table rows
        for cat in categorizations:
            is_recipe = cat.get("is_recipe", True)
            title_needs_improvement = cat.get("title_needs_improvement", False)
            quality_score = cat.get("quality_score", 5)

            # Determine row classes
            row_classes = []
            if not is_recipe:
                row_classes.append("not-recipe-row")
            elif title_needs_improvement:
                row_classes.append("title-issue")
            elif quality_score <= 2:
                row_classes.append("needs-review")

            row_class = " ".join(row_classes)

            # Generate star rating
            stars = "★" * quality_score + "☆" * (5 - quality_score)

            # Format tags
            dietary_tags = cat.get("dietary_tags", [])
            dietary_tags_html = "".join(
                [f'<span class="tag">{tag}</span>' for tag in dietary_tags]
            )

            # Confidence bar
            confidence = cat.get("confidence", 3)
            confidence_percent = (confidence / 5) * 100

            # Category styling
            category = cat.get("primary_category", "")
            category_class = category.lower().replace(" ", "-").replace("&", "")

            html += f"""
                    <tr class="{row_class}" data-category="{category}" data-is-recipe="{is_recipe}" data-title-issue="{title_needs_improvement}" data-quality="{quality_score}">
                        <td>{cat.get("recipe_index", "")}</td>
                        <td class="recipe-title">{cat.get("original_title", "")}</td>
                        <td class="proposed-title">{cat.get("proposed_title", "")}</td>
                        <td>{"✅" if is_recipe else "❌"}</td>
                        <td><span class="category {category_class}">{category}</span></td>
                        <td>{cat.get("cuisine_type", "")}</td>
                        <td><div class="tags">{dietary_tags_html}</div></td>
                        <td>
                            <div class="quality-score">
                                <span class="stars">{stars}</span>
                                <span>({quality_score})</span>
                            </div>
                        </td>
                        <td>
                            <div class="confidence">
                                <div class="confidence-fill" style="width: {confidence_percent}%"></div>
                            </div>
                            <small>{confidence}/5</small>
                        </td>
                        <td class="summary">{cat.get("content_summary", "")}</td>
                        <td class="reasoning">{cat.get("reasoning", "")}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>

        <div class="export-buttons">
            <button class="btn btn-primary" onclick="exportFiltered()">Export Filtered Results</button>
            <button class="btn btn-secondary" onclick="exportIssuesOnly()">Export Issues Only</button>
        </div>
    </div>

    <script>
        // Filter functionality
        function applyFilters() {
            const categoryFilter = document.getElementById('categoryFilter').value;
            const issueFilter = document.getElementById('issueFilter').value;
            const searchText = document.getElementById('searchBox').value.toLowerCase();
            const rows = document.querySelectorAll('#reviewTableBody tr');

            rows.forEach(row => {
                let show = true;

                // Category filter
                if (categoryFilter && row.dataset.category !== categoryFilter) {
                    show = false;
                }

                // Issue filter
                if (issueFilter) {
                    switch (issueFilter) {
                        case 'needs-review':
                            show = show && (row.dataset.isRecipe === 'false' || row.dataset.titleIssue === 'true' || parseInt(row.dataset.quality) <= 2);
                            break;
                        case 'not-recipe':
                            show = show && row.dataset.isRecipe === 'false';
                            break;
                        case 'title-issues':
                            show = show && row.dataset.titleIssue === 'true';
                            break;
                        case 'low-quality':
                            show = show && parseInt(row.dataset.quality) <= 2;
                            break;
                    }
                }

                // Search filter
                if (searchText) {
                    const rowText = row.textContent.toLowerCase();
                    show = show && rowText.includes(searchText);
                }

                row.style.display = show ? '' : 'none';
            });
        }

        // Event listeners
        document.getElementById('categoryFilter').addEventListener('change', applyFilters);
        document.getElementById('issueFilter').addEventListener('change', applyFilters);
        document.getElementById('searchBox').addEventListener('input', applyFilters);

        // Export functions
        function exportFiltered() {
            alert('Export functionality would generate a CSV of currently filtered results for editing.');
        }

        function exportIssuesOnly() {
            alert('Export functionality would generate a CSV of only items needing review.');
        }

        // Initialize
        applyFilters();
    </script>
</body>
</html>
"""
        return html

    def _process_csv_row(self, row: Dict, row_num: int, issues: List) -> Optional[Dict]:
        """Process a single CSV row and extract corrections."""
        try:
            recipe_index = row.get("recipe_index", "").strip()
            if not recipe_index:
                return None

            corrections = {}

            # Check for title corrections
            corrected_title = row.get("corrected_title", "").strip()
            if corrected_title and corrected_title != row.get("original_title", ""):
                corrections["title"] = corrected_title

            # Check for category corrections
            corrected_category = row.get("corrected_category", "").strip()
            if corrected_category and corrected_category != row.get(
                "primary_category", ""
            ):
                corrections["primary_category"] = corrected_category

            # Check for is_recipe corrections
            corrected_is_recipe = row.get("corrected_is_recipe", "").strip().lower()
            if corrected_is_recipe in ["true", "false"]:
                original_is_recipe = str(row.get("is_recipe", "")).lower()
                if corrected_is_recipe != original_is_recipe:
                    corrections["is_recipe"] = corrected_is_recipe == "true"

            # Review notes
            review_notes = row.get("review_notes", "").strip()
            if review_notes:
                corrections["review_notes"] = review_notes

            # Only return if there are actual corrections
            if corrections:
                return {
                    "recipe_index": int(recipe_index),
                    "record_id": row.get("record_id", ""),
                    "original_title": row.get("original_title", ""),
                    "corrections": corrections,
                }

            return None

        except Exception as e:
            issues.append(
                {"row": row_num, "message": f"Error processing row: {str(e)}"}
            )
            return None

    def _display_corrections_summary(self, corrections: List[Dict]) -> None:
        """Display a summary of corrections found."""
        if not corrections:
            return

        console.print(f"\n[bold blue]📝 Corrections Summary[/bold blue]")

        correction_types = defaultdict(int)
        for correction in corrections:
            for correction_type in correction["corrections"].keys():
                correction_types[correction_type] += 1

        table = Table()
        table.add_column("Correction Type", style="cyan")
        table.add_column("Count", style="green")

        for correction_type, count in correction_types.items():
            table.add_row(correction_type.replace("_", " ").title(), str(count))

        console.print(table)

    def generate_review_summary(self, analysis_file: Path, output_dir: Path) -> Path:
        """Generate a summary report for review purposes."""
        console.print("[bold blue]📋 Generating Review Summary...[/bold blue]")

        analysis_data = self._load_analysis_results(analysis_file)
        if not analysis_data:
            return None

        categorizations = analysis_data.get("llm_categorization", {}).get(
            "categorizations", []
        )

        # Generate summary statistics
        summary = {
            "generated_at": str(datetime.now()),
            "total_recipes": len(categorizations),
            "review_priorities": {
                "non_recipes": len(
                    [c for c in categorizations if not c.get("is_recipe", True)]
                ),
                "title_improvements": len(
                    [
                        c
                        for c in categorizations
                        if c.get("title_needs_improvement", False)
                    ]
                ),
                "low_quality": len(
                    [c for c in categorizations if c.get("quality_score", 5) <= 2]
                ),
                "low_confidence": len(
                    [c for c in categorizations if c.get("confidence", 5) <= 2]
                ),
            },
            "category_distribution": {},
            "potential_issues": [],
        }

        # Calculate category distribution
        for cat in categorizations:
            category = cat.get("primary_category", "Unknown")
            summary["category_distribution"][category] = (
                summary["category_distribution"].get(category, 0) + 1
            )

        # Identify potential issues
        for cat in categorizations:
            issues = []
            if not cat.get("is_recipe", True):
                issues.append("marked_as_non_recipe")
            if cat.get("title_needs_improvement", False):
                issues.append("title_needs_improvement")
            if cat.get("quality_score", 5) <= 2:
                issues.append("low_quality")
            if cat.get("confidence", 5) <= 2:
                issues.append("low_confidence")

            if issues:
                summary["potential_issues"].append(
                    {
                        "recipe_index": cat.get("recipe_index"),
                        "title": cat.get("original_title"),
                        "issues": issues,
                        "reasoning": cat.get("reasoning", ""),
                    }
                )

        # Save summary
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_file = output_dir / "review_summary.json"

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        console.print(
            f"✅ Review summary saved to: [bold green]{summary_file}[/bold green]"
        )

        # Display key statistics
        self._display_review_summary_stats(summary)

        return summary_file

    def _display_review_summary_stats(self, summary: Dict) -> None:
        """Display key statistics from the review summary."""
        priorities = summary["review_priorities"]

        console.print(f"\n[bold blue]🎯 Review Priorities[/bold blue]")
        console.print(
            f"Non-recipe items: [bold red]{priorities['non_recipes']}[/bold red]"
        )
        console.print(
            f"Title improvements needed: [bold yellow]{priorities['title_improvements']}[/bold yellow]"
        )
        console.print(
            f"Low quality recipes: [bold orange1]{priorities['low_quality']}[/bold orange1]"
        )
        console.print(
            f"Low confidence categorizations: [bold cyan]{priorities['low_confidence']}[/bold cyan]"
        )

        total_issues = sum(priorities.values())
        total_recipes = summary["total_recipes"]

        if total_issues > 0:
            console.print(
                f"\n[bold yellow]⚠️  {total_issues}/{total_recipes} recipes need review ({total_issues / total_recipes * 100:.1f}%)[/bold yellow]"
            )
        else:
            console.print(
                f"\n[bold green]✅ No major issues found in categorizations[/bold green]"
            )
