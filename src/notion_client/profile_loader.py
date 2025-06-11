"""Analysis profile loader for progressive complexity CLI.

Version: v1
Last updated: Initial profile loading system for smart defaults and configuration
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()


class ProfileLoader:
    """Load and manage analysis configuration profiles."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize profile loader with config directory."""
        self.config_dir = config_dir or Path("config")
        self._profiles = None

    def load_profiles(self) -> Dict[str, Any]:
        """Load analysis profiles from YAML file."""
        if self._profiles is None:
            profiles_file = self.config_dir / "analysis_profiles.yaml"

            if not profiles_file.exists():
                console.print(
                    f"[yellow]⚠️  Profiles file not found: {profiles_file}[/yellow]"
                )
                return self._get_default_profiles()

            try:
                with open(profiles_file, "r") as f:
                    data = yaml.safe_load(f) or {}
                self._profiles = data
            except Exception as e:
                console.print(f"[red]❌ Error loading profiles: {e}[/red]")
                return self._get_default_profiles()

        return self._profiles

    def get_profile_settings(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get settings for a specific profile."""
        profiles_data = self.load_profiles()
        profiles = profiles_data.get("profiles", {})

        if profile_name in profiles:
            return profiles[profile_name]

        console.print(f"[yellow]⚠️  Profile '{profile_name}' not found[/yellow]")
        return None

    def get_shortcut_profile(self, shortcut_name: str) -> Optional[str]:
        """Get the profile name for a shortcut."""
        profiles_data = self.load_profiles()
        shortcuts = profiles_data.get("shortcuts", {})

        if shortcut_name in shortcuts:
            return shortcuts[shortcut_name].get("profile")

        return None

    def get_default_settings(self) -> Dict[str, Any]:
        """Get default settings for analysis."""
        profiles_data = self.load_profiles()

        # Try to get from flag_defaults in config
        defaults = profiles_data.get("flag_defaults", {})
        if defaults:
            return defaults

        # Fallback to default profile
        default_profile = self.get_profile_settings("default")
        if default_profile:
            return default_profile

        # Ultimate fallback
        return self._get_fallback_defaults()

    def list_available_profiles(self) -> Dict[str, str]:
        """Get list of available profiles with descriptions."""
        profiles_data = self.load_profiles()
        profiles = profiles_data.get("profiles", {})

        profile_list = {}
        for name, settings in profiles.items():
            description = settings.get("description", "No description")
            profile_list[name] = description

        return profile_list

    def list_available_shortcuts(self) -> Dict[str, str]:
        """Get list of available shortcuts with descriptions."""
        profiles_data = self.load_profiles()
        shortcuts = profiles_data.get("shortcuts", {})

        shortcut_list = {}
        for name, settings in shortcuts.items():
            description = settings.get("description", "No description")
            shortcut_list[name] = description

        return shortcut_list

    def apply_profile_to_settings(
        self, base_settings: Dict[str, Any], profile_name: str
    ) -> Dict[str, Any]:
        """Apply a profile to base settings."""
        profile_settings = self.get_profile_settings(profile_name)
        if profile_settings:
            # Create a copy and update with profile settings
            updated_settings = base_settings.copy()
            # Remove description from settings before applying
            profile_data = {
                k: v for k, v in profile_settings.items() if k != "description"
            }
            updated_settings.update(profile_data)
            return updated_settings

        return base_settings

    def _get_default_profiles(self) -> Dict[str, Any]:
        """Get hardcoded default profiles if file doesn't exist."""
        return {
            "profiles": {
                "default": {
                    "description": "Smart defaults for comprehensive analysis",
                    "use_llm": True,
                    "include_content_review": True,
                    "batch_size": 20,
                    "batch_delay": 2,
                    "timeout": 30,
                },
                "quick": {
                    "description": "Fast analysis - statistics only",
                    "use_llm": False,
                    "include_content_review": False,
                },
                "testing": {
                    "description": "Test mode with sample recipes",
                    "use_llm": True,
                    "include_content_review": True,
                    "sample_size": 10,
                    "timeout": 60,
                },
            },
            "shortcuts": {
                "quick": {"profile": "quick", "description": "Statistics only"},
                "test": {"profile": "testing", "description": "Test with 10 recipes"},
            },
            "flag_defaults": {
                "use_llm": True,
                "include_content_review": True,
                "batch_size": 20,
                "batch_delay": 2,
                "timeout": 30,
            },
        }

    def _get_fallback_defaults(self) -> Dict[str, Any]:
        """Ultimate fallback defaults."""
        return {
            "use_llm": True,
            "include_content_review": True,
            "batch_size": 20,
            "batch_delay": 2,
            "timeout": 30,
        }
