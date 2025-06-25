"""Unit tests for file utilities."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.utils.file_utils import (
    get_default_input_path,
    get_default_output_path,
    resolve_input_file,
    resolve_output_path,
    ensure_directory_exists,
    save_json_with_metadata,
    load_json_file
)


class TestFileUtils:
    """Test file utility functions."""

    @patch('src.utils.file_utils.config')
    def test_get_default_input_path(self, mock_config):
        """Test getting default input path."""
        mock_config.data_dir = Path("/test")
        result = get_default_input_path()
        assert result == Path("/test/raw/recipes.json")

    @patch('src.utils.file_utils.config')
    def test_get_default_output_path_analysis(self, mock_config):
        """Test getting default output path for analysis."""
        mock_config.data_dir = Path("/test")
        result = get_default_output_path("analysis")
        assert result == Path("/test/processed/analysis_report.json")

    @patch('src.utils.file_utils.config')
    def test_get_default_output_path_review(self, mock_config):
        """Test getting default output path for review."""
        mock_config.data_dir = Path("/test")
        result = get_default_output_path("review")
        assert result == Path("/test/processed/review")

    def test_resolve_input_file_provided_exists(self, temp_dir):
        """Test resolving input file when provided path exists."""
        test_file = temp_dir / "test.json"
        test_file.write_text('{"test": true}')
        
        result = resolve_input_file(str(test_file))
        assert result == test_file

    def test_resolve_input_file_provided_not_exists(self):
        """Test resolving input file when provided path doesn't exist."""
        result = resolve_input_file("/nonexistent/file.json")
        assert result is None

    @patch('src.utils.file_utils.get_default_input_path')
    def test_resolve_input_file_default_exists(self, mock_get_default, temp_dir):
        """Test resolving input file using default when it exists."""
        test_file = temp_dir / "default.json"
        test_file.write_text('{"test": true}')
        mock_get_default.return_value = test_file
        
        result = resolve_input_file(None)
        assert result == test_file

    def test_resolve_output_path_provided(self):
        """Test resolving output path when provided."""
        result = resolve_output_path("/custom/path.json")
        assert result == Path("/custom/path.json")

    @patch('src.utils.file_utils.get_default_output_path')
    def test_resolve_output_path_default(self, mock_get_default):
        """Test resolving output path using default."""
        mock_get_default.return_value = Path("/default/path.json")
        result = resolve_output_path(None, "analysis")
        assert result == Path("/default/path.json")
        mock_get_default.assert_called_once_with("analysis")

    def test_ensure_directory_exists(self, temp_dir):
        """Test ensuring directory exists."""
        test_file = temp_dir / "subdir" / "file.json"
        ensure_directory_exists(test_file)
        assert test_file.parent.exists()

    def test_save_json_with_metadata(self, temp_dir):
        """Test saving JSON with metadata."""
        test_file = temp_dir / "output.json"
        data = {"records": [{"id": 1}, {"id": 2}]}
        metadata = {"source": "test"}
        
        save_json_with_metadata(data, test_file, metadata)
        
        assert test_file.exists()
        with open(test_file) as f:
            saved_data = json.load(f)
        
        assert "exported_at" in saved_data
        assert saved_data["total_records"] == 2
        assert saved_data["source"] == "test"
        assert saved_data["records"] == data["records"]

    def test_load_json_file_success(self, temp_dir):
        """Test loading JSON file successfully."""
        test_file = temp_dir / "test.json"
        test_data = {"test": "data"}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(test_file)
        assert result == test_data

    def test_load_json_file_not_found(self):
        """Test loading non-existent JSON file."""
        result = load_json_file(Path("/nonexistent.json"))
        assert result is None

    def test_load_json_file_invalid_json(self, temp_dir):
        """Test loading invalid JSON file."""
        test_file = temp_dir / "invalid.json"
        test_file.write_text("invalid json content")
        
        result = load_json_file(test_file)
        assert result is None