"""File operation utilities."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from ..config import config


def get_default_input_path() -> Path:
    """Get the default input file path for recipes."""
    return config.data_dir / "raw" / "recipes.json"


def get_default_output_path(output_type: str = "analysis") -> Path:
    """Get default output path based on type."""
    if output_type == "analysis":
        return config.data_dir / "processed" / "analysis_report.json"
    elif output_type == "review":
        return config.data_dir / "processed" / "review"
    elif output_type == "raw":
        return config.data_dir / "raw" / "recipes.json"
    else:
        return config.data_dir / "processed" / f"{output_type}.json"


def resolve_input_file(provided_path: Optional[str]) -> Optional[Path]:
    """Resolve input file path, return None if file doesn't exist."""
    if provided_path:
        input_path = Path(provided_path)
    else:
        input_path = get_default_input_path()
    
    return input_path if input_path.exists() else None


def resolve_output_path(provided_path: Optional[str], default_type: str = "analysis") -> Path:
    """Resolve output file path."""
    if provided_path:
        return Path(provided_path)
    return get_default_output_path(default_type)


def ensure_directory_exists(file_path: Path) -> None:
    """Ensure the parent directory of a file path exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def save_json_with_metadata(data: Dict[str, Any], output_path: Path, 
                           metadata: Optional[Dict[str, Any]] = None) -> None:
    """Save data to JSON with optional metadata."""
    ensure_directory_exists(output_path)
    
    # Add default metadata
    export_data = {
        "exported_at": str(datetime.now()),
        "total_records": len(data.get("records", [])) if "records" in data else 0,
        **(metadata or {}),
        **data
    }
    
    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2, default=str)


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file and return data, None if error."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None