"""Unit tests for notion_utils module."""

import pytest
from src.utils.notion_utils import extract_notion_text_content, create_notion_text_property


class TestNotionUtils:
    """Test Notion API utility functions."""

    def test_extract_notion_text_content_rich_text(self):
        """Test extracting content from rich_text property."""
        prop_data = {
            "rich_text": [
                {"text": {"content": "Hello "}},
                {"text": {"content": "World"}}
            ]
        }
        
        result = extract_notion_text_content(prop_data, "rich_text")
        assert result == "Hello World"

    def test_extract_notion_text_content_title(self):
        """Test extracting content from title property."""
        prop_data = {
            "title": [
                {"text": {"content": "Recipe Title"}}
            ]
        }
        
        result = extract_notion_text_content(prop_data, "title")
        assert result == "Recipe Title"

    def test_extract_notion_text_content_auto_detect(self):
        """Test auto-detection of property type."""
        # Test with rich_text
        rich_text_data = {
            "rich_text": [{"text": {"content": "Rich text content"}}]
        }
        result = extract_notion_text_content(rich_text_data, "auto")
        assert result == "Rich text content"
        
        # Test with title
        title_data = {
            "title": [{"text": {"content": "Title content"}}]
        }
        result = extract_notion_text_content(title_data, "auto")
        assert result == "Title content"

    def test_extract_notion_text_content_string_input(self):
        """Test handling of simple string input."""
        result = extract_notion_text_content("Simple string", "rich_text")
        assert result == "Simple string"

    def test_extract_notion_text_content_empty(self):
        """Test handling of empty or invalid input."""
        assert extract_notion_text_content({}, "rich_text") == ""
        assert extract_notion_text_content(None, "rich_text") == ""
        assert extract_notion_text_content({"wrong_key": []}, "rich_text") == ""

    def test_create_notion_text_property_rich_text(self):
        """Test creating rich_text property."""
        result = create_notion_text_property("Test content", "rich_text")
        expected = {
            "rich_text": [{"text": {"content": "Test content"}}]
        }
        assert result == expected

    def test_create_notion_text_property_title(self):
        """Test creating title property."""
        result = create_notion_text_property("Test title", "title")
        expected = {
            "title": [{"text": {"content": "Test title"}}]
        }
        assert result == expected

    def test_create_notion_text_property_default(self):
        """Test creating property with default type."""
        result = create_notion_text_property("Default content")
        expected = {
            "rich_text": [{"text": {"content": "Default content"}}]
        }
        assert result == expected