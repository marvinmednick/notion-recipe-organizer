"""Configuration and template loader for recipe categorization.

Version: v1
Last updated: Initial YAML config and template system
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console

console = Console()


class ConfigLoader:
    """Load and manage categorization configuration from YAML files."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config loader with config directory."""
        self.config_dir = config_dir or Path("config")
        self._categories = None
        self._cuisines = None
        self._dietary_tags = None
        self._usage_tags = None
        self._conflict_rules = None
    
    def load_categories(self) -> Dict[str, Any]:
        """Load primary categories configuration."""
        if self._categories is None:
            self._categories = self._load_yaml_file("categories.yaml")
        return self._categories
    
    def load_cuisines(self) -> Dict[str, Any]:
        """Load cuisine types configuration."""
        if self._cuisines is None:
            self._cuisines = self._load_yaml_file("cuisines.yaml")
        return self._cuisines
    
    def load_dietary_tags(self) -> Dict[str, Any]:
        """Load dietary tags configuration."""
        if self._dietary_tags is None:
            self._dietary_tags = self._load_yaml_file("dietary_tags.yaml")
        return self._dietary_tags
    
    def load_usage_tags(self) -> Dict[str, Any]:
        """Load usage tags configuration."""
        if self._usage_tags is None:
            self._usage_tags = self._load_yaml_file("usage_tags.yaml")
        return self._usage_tags
    
    def load_conflict_rules(self) -> Dict[str, Any]:
        """Load conflict resolution rules."""
        if self._conflict_rules is None:
            self._conflict_rules = self._load_yaml_file("conflict_rules.yaml")
        return self._conflict_rules
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file."""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            console.print(f"[yellow]⚠️  Config file not found: {file_path}[/yellow]")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[red]❌ Error loading {filename}: {e}[/red]")
            return {}
    
    def get_primary_categories(self) -> List[str]:
        """Get list of primary category names."""
        categories = self.load_categories()
        return list(categories.get('categories', {}).keys())
    
    def get_cuisine_types(self) -> List[str]:
        """Get list of cuisine type names."""
        cuisines = self.load_cuisines()
        return list(cuisines.get('cuisines', {}).keys())
    
    def get_dietary_tag_names(self) -> List[str]:
        """Get list of dietary tag names."""
        tags = self.load_dietary_tags()
        return list(tags.get('dietary_tags', {}).keys())
    
    def get_auto_assignable_usage_tags(self) -> List[str]:
        """Get usage tags that can be auto-assigned by LLM."""
        tags = self.load_usage_tags()
        auto_tags = []
        
        for tag_name, tag_config in tags.get('usage_tags', {}).items():
            if tag_config.get('assignment') == 'auto':
                auto_tags.append(tag_name)
        
        return auto_tags
    
    def format_categories_for_prompt(self) -> str:
        """Format categories for prompt inclusion."""
        categories = self.load_categories().get('categories', {})
        formatted = []
        
        for name, config in categories.items():
            description = config.get('description', '')
            criteria = config.get('criteria', [])
            examples = config.get('examples', [])
            
            formatted.append(f"- **{name}**: {description}")
            if criteria:
                formatted.append("  - Criteria: " + "; ".join(criteria))
            if examples:
                formatted.append(f"  - Examples: {', '.join(examples)}")
        
        return "\n".join(formatted)
    
    def format_cuisines_for_prompt(self) -> str:
        """Format cuisines for prompt inclusion."""
        cuisines = self.load_cuisines().get('cuisines', {})
        formatted = []
        
        for name, config in cuisines.items():
            description = config.get('description', '')
            indicators = config.get('indicators', [])
            
            formatted.append(f"- **{name}**: {description}")
            if indicators:
                formatted.append("  - Indicators: " + "; ".join(indicators))
        
        return "\n".join(formatted)
    
    def format_dietary_tags_for_prompt(self) -> str:
        """Format dietary tags for prompt inclusion."""
        tags = self.load_dietary_tags().get('dietary_tags', {})
        formatted = []
        
        for name, config in tags.items():
            description = config.get('description', '')
            criteria = config.get('criteria', [])
            notes = config.get('notes', '')
            
            formatted.append(f"- **{name}**: {description}")
            if criteria:
                formatted.append("  - Criteria: " + "; ".join(criteria))
            if notes:
                formatted.append(f"  - Note: {notes}")
        
        return "\n".join(formatted)
    
    def format_usage_tags_for_prompt(self) -> str:
        """Format auto-assignable usage tags for prompt inclusion."""
        tags = self.load_usage_tags().get('usage_tags', {})
        formatted = []
        
        for name, config in tags.
