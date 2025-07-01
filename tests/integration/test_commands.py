"""Integration tests for CLI commands."""

import pytest
import json
from click.testing import CliRunner
from unittest.mock import Mock, patch

from src.main import cli


class TestCommandIntegration:
    """Test CLI command integration."""

    def test_cli_help(self):
        """Test that CLI help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Notion Recipe Organizer" in result.output
        assert "extract" in result.output
        assert "analyze" in result.output
        assert "review" in result.output

    def test_extract_help(self):
        """Test extract command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', '--help'])
        
        assert result.exit_code == 0
        assert "Extract recipe data" in result.output
        assert "--database-id" in result.output
        assert "--dry-run" in result.output

    def test_analyze_help(self):
        """Test analyze command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', '--help'])
        
        assert result.exit_code == 0
        assert "Analyze extracted recipe data" in result.output
        assert "--quick" in result.output
        assert "--sample" in result.output

    def test_review_help(self):
        """Test review command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['review', '--help'])
        
        assert result.exit_code == 0

    def test_create_enhanced_database_help(self):
        """Test create-enhanced-database command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['create-enhanced-database', '--help'])
        
        assert result.exit_code == 0
        assert "Create enhanced database with improved schema" in result.output
        assert "--source-database-id" in result.output
        assert "--use-analysis-results" in result.output
        assert "--sample" in result.output
        assert "--dry-run" in result.output

    @patch('src.utils.config_utils.validate_config')
    @patch('src.utils.config_utils.test_notion_connection')
    def test_config_check(self, mock_test_conn, mock_validate):
        """Test config check functionality."""
        mock_validate.return_value = True
        mock_test_conn.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--config-check'])
        
        assert result.exit_code == 0
        assert "All checks passed" in result.output

    @pytest.mark.slow
    @patch('src.commands.extract_cmd.validate_config_and_connection')
    @patch('src.commands.extract_cmd.get_notion_client')
    def test_extract_dry_run(self, mock_get_client, mock_validate, temp_dir):
        """Test extract command in dry-run mode."""
        # Setup mocks
        mock_validate.return_value = True
        mock_client = Mock()
        mock_client.get_database.return_value = {
            "title": [{"plain_text": "Test DB"}]
        }
        mock_client.get_database_records.return_value = [
            {"id": "123"},
            {"id": "456"}
        ]
        mock_client.get_record_content.side_effect = [
            {"title": "Recipe 1", "url": "http://example.com/1", "tags": []},
            {"title": "Recipe 2", "url": "http://example.com/2", "tags": []}
        ]
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract', 
            '--dry-run', 
            '--max-records', '2',
            '--database-id', 'test_db'
        ])
        
        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "Recipe 1" in result.output
        assert "Recipe 2" in result.output

    @patch('src.commands.analyze_cmd.RecipeAnalyzer')
    def test_analyze_quick_mode(self, mock_analyzer_class, sample_recipe_file):
        """Test analyze command in quick mode."""
        # Setup mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.load_recipes.return_value = {"records": []}
        mock_analyzer.analyze_basic_stats.return_value = {
            "total_recipes": 2,
            "recipes_with_urls": 2,
            "recipes_with_tags": 0
        }
        mock_analyzer.display_basic_stats.return_value = None
        mock_analyzer_class.return_value = mock_analyzer

        runner = CliRunner()
        result = runner.invoke(cli, [
            'analyze',
            '--input', str(sample_recipe_file),
            '--quick'
        ])
        
        assert result.exit_code == 0
        assert "Quick mode" in result.output
        assert "Analysis completed" in result.output

    @pytest.mark.external
    def test_real_config_check(self):
        """Test config check with real configuration (if available)."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--config-check'])
        
        # This test will pass/fail based on actual config
        # Use this to test real environment
        if result.exit_code == 0:
            assert "All checks passed" in result.output
        else:
            assert "Configuration Error" in result.output