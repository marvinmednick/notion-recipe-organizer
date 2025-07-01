"""Create enhanced database command for Notion Recipe Organizer."""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import click
from rich.console import Console
from rich.table import Table

from ..utils.config_utils import validate_config_and_connection, get_database_id, get_notion_client
from ..utils.display_utils import (
    print_header, print_success, print_error, print_info, show_completion_message
)
from ..utils.file_utils import resolve_output_path

console = Console()


def _load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print_error(f"Failed to load config from {config_path}: {e}")
        return {}


def _load_enhanced_schema_config() -> Dict[str, Any]:
    """Load schema configuration from YAML files."""
    config_dir = Path("config")
    
    # Load all configuration files
    categories_yaml = _load_yaml_config(config_dir / "categories.yaml")
    cuisines_yaml = _load_yaml_config(config_dir / "cuisines.yaml")
    dietary_tags_yaml = _load_yaml_config(config_dir / "dietary_tags.yaml")
    usage_tags_yaml = _load_yaml_config(config_dir / "usage_tags.yaml")
    
    # Extract options from configs
    categories_list = list(categories_yaml.get("categories", {}).keys())
    cuisines_list = list(cuisines_yaml.get("cuisines", {}).keys())
    dietary_tags_list = list(dietary_tags_yaml.get("dietary_tags", {}).keys())
    usage_tags_list = list(usage_tags_yaml.get("usage_tags", {}).keys())
    
    return {
        "categories": categories_list,
        "cuisines": cuisines_list,
        "dietary_tags": dietary_tags_list,
        "usage_tags": usage_tags_list
    }


@click.command()
@click.option("--database-id", help="Database ID to enhance in-place")
@click.option("--use-analysis-results", is_flag=True, help="Use analysis results for enhanced data")
@click.option("--analysis-file", type=click.Path(exists=True), help="Path to analysis results JSON file")
@click.option("--sample", type=int, help="Enhance only N records for testing")
@click.option("--dry-run", is_flag=True, help="Show what would be enhanced without making changes")
def enhance_database_in_place(
    database_id: Optional[str],
    use_analysis_results: bool,
    analysis_file: Optional[str],
    sample: Optional[int],
    dry_run: bool,
):
    """Enhance existing database with AI categorization properties and data."""
    
    print_header("In-Place Database Enhancement", "🚀")
    
    # Validate config and connection
    if not validate_config_and_connection():
        return
    
    # Get target database ID
    target_db_id = get_database_id(database_id)
    if not target_db_id:
        print_error("No database ID provided. Use --database-id or set NOTION_RECIPES_DATABASE_ID")
        return
    
    # Get client
    notion_client = get_notion_client()
    
    # Verify database access
    print_info(f"Accessing database to enhance: {target_db_id}")
    target_db_info = notion_client.get_database(target_db_id)
    if not target_db_info:
        print_error(f"Could not access database: {target_db_id}")
        return
    
    target_db_title = target_db_info.get("title", [{}])[0].get("plain_text", "Unknown Database")
    print_success(f"Connected to database: {target_db_title}")
    
    # Load analysis results if requested
    analysis_data = None
    if use_analysis_results or analysis_file:
        analysis_path = Path(analysis_file) if analysis_file else (Path("data/processed/analysis_report.json"))
        
        if analysis_path.exists():
            try:
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                print_success(f"Loaded analysis results from: {analysis_path}")
            except Exception as e:
                print_error(f"Failed to load analysis results: {e}")
                if use_analysis_results:
                    return
        else:
            print_error(f"Analysis results not found at: {analysis_path}")
            if use_analysis_results:
                print_info("Run 'analyze' command first or provide --analysis-file path")
                return
    
    # Get existing records
    print_header("Loading database records...", "📄")
    existing_records = notion_client.get_database_records(target_db_id)
    
    if sample:
        existing_records = existing_records[:sample]
        print_info(f"Using sample of {len(existing_records)} records for testing")
    
    print_success(f"Loaded {len(existing_records)} records from database")
    
    # Plan enhancement
    enhancement_plan = _create_enhancement_plan(target_db_info, analysis_data, len(existing_records))
    
    print_header("Enhancement Plan", "📋")
    _display_enhancement_plan(enhancement_plan, target_db_title)
    
    if dry_run:
        print_header("Dry Run Complete", "🔍")
        print_info("No changes made - database not enhanced")
        return
    
    # Confirm enhancement
    if not click.confirm(f"\nProceed with enhancing database '{target_db_title}'?"):
        print_info("Enhancement cancelled")
        return
    
    # Execute enhancement
    success = _execute_enhancement(
        notion_client, 
        target_db_info,
        target_db_id,
        existing_records,
        enhancement_plan, 
        analysis_data
    )
    
    if success:
        print_header("Enhancement Complete", "✅")
        _display_enhancement_summary(enhancement_plan, target_db_id, target_db_title)
        show_completion_message("database enhancement")
    else:
        print_header("Enhancement Failed", "❌")
        print_error("Database enhancement failed")


def _create_enhancement_plan(
    target_db_info: Dict[str, Any], 
    analysis_data: Optional[Dict[str, Any]], 
    record_count: int
) -> Dict[str, Any]:
    """Create detailed enhancement plan."""
    
    existing_properties = target_db_info.get("properties", {})
    
    # Load schema configuration from YAML files
    schema_config = _load_enhanced_schema_config()
    
    # Define enhanced properties using configuration
    enhanced_properties = {
        "Primary_Category": {
            "type": "select",
            "description": "Primary recipe category",
            "options": schema_config["categories"]
        },
        "Cuisine_Type": {
            "type": "select", 
            "description": "Culinary tradition classification",
            "options": schema_config["cuisines"]
        },
        "Dietary_Tags": {
            "type": "multi_select",
            "description": "Dietary restriction and lifestyle tags",
            "options": schema_config["dietary_tags"]
        },
        "Usage_Tags": {
            "type": "multi_select",
            "description": "Personal usage patterns and preferences", 
            "options": schema_config["usage_tags"]
        },
        "Source_Domain": {
            "type": "rich_text",
            "description": "Website domain where recipe was found"
        },
        "Proposed_Title": {
            "type": "rich_text",
            "description": "Suggested title improvements for manual review"
        }
    }
    
    # Check which properties already exist
    properties_to_add = {}
    for prop_name, prop_config in enhanced_properties.items():
        if prop_name not in existing_properties:
            properties_to_add[prop_name] = prop_config
    
    # Calculate analysis stats
    analysis_stats = {}
    if analysis_data:
        analysis_stats = _calculate_analysis_stats(analysis_data, record_count)
    
    return {
        "existing_properties": existing_properties,
        "enhanced_properties": enhanced_properties,
        "properties_to_add": properties_to_add,
        "total_properties_after": len(existing_properties) + len(properties_to_add),
        "records_to_enhance": record_count,
        "analysis_stats": analysis_stats,
        "has_analysis_data": analysis_data is not None
    }


def _calculate_analysis_stats(analysis_data: Dict[str, Any], record_count: int) -> Dict[str, Any]:
    """Calculate statistics from analysis data."""
    
    recipes_analyzed = analysis_data.get("llm_categorization", {}).get("categorizations", [])
    
    stats = {
        "total_analyzed": len(recipes_analyzed),
        "will_enhance": min(len(recipes_analyzed), record_count),
        "with_categories": 0,
        "with_quality": 0,
        "category_distribution": {},
        "quality_distribution": {}
    }
    
    for recipe in recipes_analyzed[:record_count]:
        if recipe.get("primary_category"):
            stats["with_categories"] += 1
            category = recipe["primary_category"]
            stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
        
        if recipe.get("quality_score"):
            stats["with_quality"] += 1
            quality = f"Score {recipe['quality_score']}"
            stats["quality_distribution"][quality] = stats["quality_distribution"].get(quality, 0) + 1
    
    return stats


def _display_enhancement_plan(plan: Dict[str, Any], target_db_name: str) -> None:
    """Display the enhancement plan in a readable format."""
    
    console.print(f"\n[bold blue]🎯 Database to Enhance: {target_db_name}[/bold blue]")
    
    # Schema information
    console.print(f"\n[bold blue]🔧 Database Schema Changes[/bold blue]")
    print_info(f"Existing properties: {len(plan['existing_properties'])}")
    print_info(f"Properties to add: {len(plan['properties_to_add'])}")
    print_info(f"Total properties after enhancement: {plan['total_properties_after']}")
    
    if len(plan['properties_to_add']) == 0:
        print_info("All enhanced properties already exist - will populate with data only")
        return
    
    # Properties to add table
    console.print("\n[bold blue]✨ New Properties to Add[/bold blue]")
    schema_table = Table()
    schema_table.add_column("Property", style="cyan")
    schema_table.add_column("Type", style="green")
    schema_table.add_column("Description", style="dim")
    
    for prop_name, prop_config in plan["properties_to_add"].items():
        schema_table.add_row(
            prop_name,
            prop_config["type"],
            prop_config.get("description", "")
        )
    
    console.print(schema_table)
    
    # Enhancement stats
    console.print(f"\n[bold blue]📊 Enhancement Statistics[/bold blue]")
    print_info(f"Records to enhance: {plan['records_to_enhance']}")
    
    if plan["has_analysis_data"]:
        stats = plan["analysis_stats"]
        print_info(f"Records with AI analysis: {stats['will_enhance']}")
        print_info(f"Records with categories: {stats['with_categories']}")
        print_info(f"Records with quality ratings: {stats['with_quality']}")
        
        if stats["category_distribution"]:
            console.print("\n[dim]Category Distribution:[/dim]")
            for category, count in sorted(stats["category_distribution"].items()):
                console.print(f"  {category}: {count}")
    else:
        print_info("No AI analysis data - enhanced properties will be empty")


def _execute_enhancement(
    notion_client,
    target_db_info: Dict[str, Any],
    target_db_id: str,
    existing_records: List[Dict[str, Any]],
    plan: Dict[str, Any],
    analysis_data: Optional[Dict[str, Any]]
) -> bool:
    """Execute the database enhancement."""
    
    try:
        # Step 1: Add New Properties to Database Schema
        if len(plan['properties_to_add']) > 0:
            print_header("Adding new properties to database schema...", "🔧")
            
            success = _add_properties_to_database(
                notion_client,
                target_db_id,
                plan['properties_to_add']
            )
            
            if not success:
                return False
            
            print_success(f"Added {len(plan['properties_to_add'])} new properties to database")
        else:
            print_info("All properties already exist - skipping schema modification")
        
        # Step 2: Populate Enhanced Data
        print_header("Populating enhanced data in existing records...", "📋")
        
        enhanced_count = _populate_enhanced_data(
            notion_client,
            existing_records,
            analysis_data
        )
        
        print_success(f"Enhanced {enhanced_count} records with AI categorization")
        
        return True
        
    except Exception as e:
        print_error(f"Enhancement failed: {e}")
        return False


def _add_properties_to_database(
    notion_client,
    database_id: str,
    properties_to_add: Dict[str, Any]
) -> bool:
    """Add new properties to existing database."""
    
    try:
        # Convert properties to Notion API format
        notion_properties = {}
        
        for prop_name, prop_config in properties_to_add.items():
            if prop_config["type"] == "select":
                notion_properties[prop_name] = {
                    "select": {
                        "options": [{"name": option} for option in prop_config.get("options", [])]
                    }
                }
            elif prop_config["type"] == "multi_select":
                notion_properties[prop_name] = {
                    "multi_select": {
                        "options": [{"name": option} for option in prop_config.get("options", [])]
                    }
                }
            elif prop_config["type"] == "number":
                notion_properties[prop_name] = {"number": {"format": "number"}}
            elif prop_config["type"] == "rich_text":
                notion_properties[prop_name] = {"rich_text": {}}
            elif prop_config["type"] == "date":
                notion_properties[prop_name] = {"date": {}}
        
        # Update the database schema
        notion_client.client.databases.update(
            database_id=database_id,
            properties=notion_properties
        )
        
        return True
        
    except Exception as e:
        print_error(f"Failed to add properties to database: {e}")
        return False




def _populate_enhanced_data(
    notion_client,
    existing_records: List[Dict[str, Any]],
    analysis_data: Optional[Dict[str, Any]]
) -> int:
    """Populate enhanced data in existing database records."""
    
    enhanced_count = 0
    
    # Create analysis lookup for faster access
    analysis_lookup = {}
    if analysis_data:
        for recipe in analysis_data.get("llm_categorization", {}).get("categorizations", []):
            if "record_id" in recipe:
                analysis_lookup[recipe["record_id"]] = recipe
    
    with console.status("[bold green]Enhancing records...") as status:
        for i, record in enumerate(existing_records):
            status.update(f"[bold green]Enhancing record {i + 1}/{len(existing_records)}...")
            
            try:
                record_id = record["id"]
                
                # Get analysis data for this record
                analysis_record = analysis_lookup.get(record_id)
                if not analysis_record:
                    continue  # Skip records without analysis data
                
                # Prepare enhanced properties to update
                enhanced_properties = {}
                
                # Primary Category - the main categorization
                if analysis_record.get("primary_category"):
                    enhanced_properties["Primary_Category"] = {
                        "select": {"name": analysis_record["primary_category"]}
                    }
                
                # Cuisine Type
                if analysis_record.get("cuisine_type"):
                    enhanced_properties["Cuisine_Type"] = {
                        "select": {"name": analysis_record["cuisine_type"]}
                    }
                
                # Dietary Tags
                if analysis_record.get("dietary_tags"):
                    enhanced_properties["Dietary_Tags"] = {
                        "multi_select": [{"name": tag} for tag in analysis_record["dietary_tags"]]
                    }
                
                # Usage Tags
                if analysis_record.get("usage_tags"):
                    enhanced_properties["Usage_Tags"] = {
                        "multi_select": [{"name": tag} for tag in analysis_record["usage_tags"]]
                    }
                
                # Proposed Title - Only populate if title needs improvement
                if (analysis_record.get("proposed_title") and 
                    analysis_record.get("title_needs_improvement", False)):
                    enhanced_properties["Proposed_Title"] = {
                        "rich_text": [{"text": {"content": analysis_record["proposed_title"]}}]
                    }
                
                # Extract source domain from URL if available
                record_content = notion_client.get_record_content(record_id)
                url_property = record_content.get("properties", {}).get("URL")
                if url_property:
                    try:
                        # Handle different URL property formats
                        url_value = None
                        if isinstance(url_property, dict) and "url" in url_property:
                            url_value = url_property["url"]
                        elif isinstance(url_property, str):
                            url_value = url_property
                        
                        if url_value:
                            domain = urlparse(url_value).netloc
                            if domain:
                                enhanced_properties["Source_Domain"] = {
                                    "rich_text": [{"text": {"content": domain}}]
                                }
                    except Exception as e:
                        # Skip URL processing if it fails
                        pass
                
                # Update the existing record with enhanced properties
                if enhanced_properties:
                    notion_client.client.pages.update(
                        page_id=record_id,
                        properties=enhanced_properties
                    )
                    enhanced_count += 1
                
            except Exception as e:
                print_error(f"Failed to enhance record {record_id}: {e}")
                continue
    
    return enhanced_count


def _display_enhancement_summary(plan: Dict[str, Any], target_db_id: str, target_db_name: str) -> None:
    """Display summary of completed enhancement."""
    
    console.print(f"\n[bold green]🎉 Enhancement Summary[/bold green]")
    
    print_info(f"Database enhanced: {target_db_name}")
    print_info(f"Database ID: {target_db_id}")
    print_info(f"Properties added: {len(plan['properties_to_add'])}")
    print_info(f"Total properties: {plan['total_properties_after']}")
    print_info(f"Records enhanced: {plan['records_to_enhance']}")
    
    if plan["has_analysis_data"]:
        stats = plan["analysis_stats"]
        print_info(f"Records with AI categorization: {stats['will_enhance']}")
        print_info(f"Categories assigned: {stats['with_categories']}")
        print_info(f"Quality ratings: {stats['with_quality']}")
    
    console.print(f"\n[bold blue]Next Steps:[/bold blue]")
    console.print("1. Review the enhanced properties in your Notion database")
    console.print("2. Test filtering and sorting with new AI categories")
    console.print("3. Create custom views for different recipe types")
    console.print("4. Review proposed titles and edit as needed")
    console.print("5. Run 'apply-title-improvements' when ready to update titles")
    console.print("6. Run 'review --html' to see updated analysis interface")