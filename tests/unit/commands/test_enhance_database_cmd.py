"""Unit tests for enhance_database_in_place command."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.commands.enhance_database_cmd import (
    enhance_database_in_place, 
    _create_enhancement_plan,
    _calculate_analysis_stats
)


class TestEnhanceDatabaseInPlaceCommand:
    """Test enhance_database_in_place command functionality."""

    def test_enhance_database_in_place_help(self):
        """Test enhance_database_in_place command help."""
        runner = CliRunner()
        result = runner.invoke(enhance_database_in_place, ['--help'])
        
        assert result.exit_code == 0
        assert "Enhance existing database with AI categorization" in result.output
        assert "--database-id" in result.output
        assert "--use-analysis-results" in result.output
        assert "--sample" in result.output
        assert "--dry-run" in result.output

    @patch('src.commands.enhance_database_cmd.get_database_id')
    @patch('src.commands.enhance_database_cmd.validate_config_and_connection')
    def test_enhance_database_in_place_no_database_id(self, mock_validate, mock_get_db_id):
        """Test enhance_database_in_place fails when no database ID provided."""
        mock_validate.return_value = True
        mock_get_db_id.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(enhance_database_in_place, [])
        
        assert result.exit_code == 0  # Function returns rather than exits
        mock_validate.assert_called_once()
        mock_get_db_id.assert_called_once()

    @patch('src.commands.enhance_database_cmd.validate_config_and_connection')
    def test_enhance_database_in_place_invalid_config(self, mock_validate):
        """Test enhance_database_in_place fails with invalid config."""
        mock_validate.return_value = False
        
        runner = CliRunner()
        result = runner.invoke(enhance_database_in_place, [])
        
        assert result.exit_code == 0  # Function returns rather than exits
        mock_validate.assert_called_once()

    def test_enhance_database_in_place_dry_run_basic(self):
        """Test enhance_database_in_place command help includes dry-run option."""
        runner = CliRunner()
        result = runner.invoke(enhance_database_in_place, ['--help'])
        
        assert result.exit_code == 0
        assert "--dry-run" in result.output

    def test_create_enhancement_plan_no_analysis(self):
        """Test _create_enhancement_plan without analysis data."""
        db_info = {
            "properties": {
                "Name": {"type": "title"},
                "Tags": {"type": "multi_select"}
            }
        }
        
        plan = _create_enhancement_plan(db_info, None, 5)
        
        assert "existing_properties" in plan
        assert "enhanced_properties" in plan
        assert len(plan["enhanced_properties"]) > 0
        assert plan["has_analysis_data"] is False

    def test_create_enhancement_plan_with_analysis(self):
        """Test _create_enhancement_plan with analysis data."""
        db_info = {
            "properties": {
                "Name": {"type": "title"},
                "Tags": {"type": "multi_select"}
            }
        }
        analysis_data = {
            "llm_categorization": {
                "categorizations": [
                    {"primary_category": "Breakfast"},
                    {"primary_category": "Dinner"}
                ]
            }
        }
        
        plan = _create_enhancement_plan(db_info, analysis_data, 5)
        
        assert "existing_properties" in plan
        assert "enhanced_properties" in plan
        assert "analysis_stats" in plan
        assert plan["has_analysis_data"] is True

    def test_calculate_analysis_stats(self):
        """Test _calculate_analysis_stats function."""
        analysis_data = {
            "llm_categorization": {
                "categorizations": [
                    {"primary_category": "Breakfast", "quality_score": 8},
                    {"primary_category": "Dinner", "quality_score": 9},
                    {"primary_category": "Breakfast", "quality_score": 7}
                ]
            }
        }
        
        stats = _calculate_analysis_stats(analysis_data, 10)
        
        assert stats["total_analyzed"] == 3
        assert stats["with_categories"] == 3
        assert "category_distribution" in stats
        assert "quality_distribution" in stats

    def test_calculate_analysis_stats_with_limit(self):
        """Test _calculate_analysis_stats with record limit."""
        analysis_data = {
            "llm_categorization": {
                "categorizations": [
                    {"primary_category": "Breakfast"},
                    {"primary_category": "Dinner"}
                ]
            }
        }
        
        stats = _calculate_analysis_stats(analysis_data, 5)
        
        assert stats["total_analyzed"] == 2
        assert stats["will_enhance"] == 2
        assert "category_distribution" in stats