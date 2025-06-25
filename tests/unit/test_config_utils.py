"""Unit tests for config utilities."""

import pytest
from unittest.mock import Mock, patch

from src.utils.config_utils import (
    validate_config,
    test_notion_connection,
    validate_config_and_connection,
    get_database_id,
    get_notion_client
)


class TestConfigUtils:
    """Test config utility functions."""

    @patch('src.utils.config_utils.config')
    def test_validate_config_success(self, mock_config):
        """Test successful config validation."""
        mock_config.validate_required.return_value = None
        
        result = validate_config()
        assert result is True
        mock_config.validate_required.assert_called_once()

    @patch('src.utils.config_utils.config')
    @patch('src.utils.config_utils.console')
    def test_validate_config_failure(self, mock_console, mock_config):
        """Test failed config validation."""
        mock_config.validate_required.side_effect = ValueError("Missing API key")
        
        result = validate_config()
        assert result is False
        mock_console.print.assert_called_once()

    @patch('src.utils.config_utils.NotionClient')
    def test_test_notion_connection_success(self, mock_client_class):
        """Test successful Notion connection."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        result = test_notion_connection()
        assert result is True

    @patch('src.utils.config_utils.NotionClient')
    def test_test_notion_connection_failure(self, mock_client_class):
        """Test failed Notion connection."""
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        result = test_notion_connection()
        assert result is False

    @patch('src.utils.config_utils.validate_config')
    @patch('src.utils.config_utils.test_notion_connection')
    def test_validate_config_and_connection_success(self, mock_test_conn, mock_validate):
        """Test successful config and connection validation."""
        mock_validate.return_value = True
        mock_test_conn.return_value = True
        
        result = validate_config_and_connection()
        assert result is True

    @patch('src.utils.config_utils.validate_config')
    @patch('src.utils.config_utils.test_notion_connection')
    def test_validate_config_and_connection_config_fails(self, mock_test_conn, mock_validate):
        """Test when config validation fails."""
        mock_validate.return_value = False
        
        result = validate_config_and_connection()
        assert result is False
        mock_test_conn.assert_not_called()

    @patch('src.utils.config_utils.validate_config')
    @patch('src.utils.config_utils.test_notion_connection')
    def test_validate_config_and_connection_connection_fails(self, mock_test_conn, mock_validate):
        """Test when connection fails."""
        mock_validate.return_value = True
        mock_test_conn.return_value = False
        
        result = validate_config_and_connection()
        assert result is False

    @patch('src.utils.config_utils.config')
    def test_get_database_id_provided(self, mock_config):
        """Test getting database ID when provided."""
        mock_config.notion_recipes_database_id = "config_id"
        
        result = get_database_id("provided_id")
        assert result == "provided_id"

    @patch('src.utils.config_utils.config')
    def test_get_database_id_from_config(self, mock_config):
        """Test getting database ID from config."""
        mock_config.notion_recipes_database_id = "config_id"
        
        result = get_database_id(None)
        assert result == "config_id"

    @patch('src.utils.config_utils.NotionClient')
    def test_get_notion_client(self, mock_client_class):
        """Test getting Notion client."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        result = get_notion_client()
        assert result == mock_client
        mock_client_class.assert_called_once()