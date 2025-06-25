"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for testing."""
    return {
        "database_info": {
            "title": [{"plain_text": "Test Recipes"}],
            "properties": {
                "Name": {"type": "title"},
                "URL": {"type": "url"},
                "Tags": {"type": "multi_select", "multi_select": {"options": []}}
            }
        },
        "records": [
            {
                "title": "Test Recipe 1",
                "url": "https://example.com/recipe1",
                "tags": ["dinner"],
                "record_id": "123",
                "database_id": "abc"
            },
            {
                "title": "Test Recipe 2", 
                "url": "https://example.com/recipe2",
                "tags": [],
                "record_id": "456",
                "database_id": "abc"
            }
        ]
    }

@pytest.fixture
def sample_recipe_file(temp_dir, sample_recipe_data):
    """Create a sample recipe JSON file."""
    file_path = temp_dir / "test_recipes.json"
    with open(file_path, 'w') as f:
        json.dump(sample_recipe_data, f)
    return file_path

@pytest.fixture
def mock_notion_client():
    """Mock Notion client for testing."""
    client = Mock()
    client.test_connection.return_value = True
    client.get_database.return_value = {
        "title": [{"plain_text": "Test Database"}],
        "properties": {"Name": {"type": "title"}}
    }
    client.get_database_records.return_value = []
    client._extract_record_properties.return_value = {
        "Name": "Test Recipe",
        "URL": "https://example.com",
        "Tags": [],
        "Created": "2023-01-01"
    }
    return client

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.data_dir = Path("/tmp/test_data")
    config.notion_recipes_database_id = "test_db_id"
    config.validate_required.return_value = None
    return config