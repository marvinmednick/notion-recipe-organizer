"""Unit tests for create_enhanced_database command."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.commands.enhance_database_cmd import (
    create_enhanced_database, 
    _create_migration_plan,
    _calculate_analysis_stats,
    _convert_property_for_creation,
    _migrate_records_with_enhancements
)


class TestCreateEnhancedDatabaseCommand:
    """Test create_enhanced_database command functionality."""

    def test_create_enhanced_database_help(self):
        """Test create_enhanced_database command help."""
        runner = CliRunner()
        result = runner.invoke(create_enhanced_database, ['--help'])
        
        assert result.exit_code == 0
        assert "Create enhanced database with improved schema" in result.output
        assert "--source-database-id" in result.output
        assert "--use-analysis-results" in result.output
        assert "--sample" in result.output
        assert "--dry-run" in result.output

    @patch('src.commands.enhance_database_cmd.validate_config_and_connection')
    @patch('src.commands.enhance_database_cmd.get_database_id')
    def test_create_enhanced_database_no_source_database_id(self, mock_get_db_id, mock_validate):
        """Test create_enhanced_database fails when no source database ID provided."""
        mock_validate.return_value = True
        mock_get_db_id.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(create_enhanced_database, [])
        
        assert result.exit_code == 0
        mock_validate.assert_called_once()
        mock_get_db_id.assert_called_once()

    @patch('src.commands.enhance_database_cmd.validate_config_and_connection')
    def test_create_enhanced_database_invalid_config(self, mock_validate):
        """Test create_enhanced_database fails with invalid config."""
        mock_validate.return_value = False
        
        runner = CliRunner()
        result = runner.invoke(create_enhanced_database, [])
        
        assert result.exit_code == 0
        mock_validate.assert_called_once()

    @patch('src.commands.enhance_database_cmd.validate_config_and_connection')
    @patch('src.commands.enhance_database_cmd.get_database_id')
    @patch('src.commands.enhance_database_cmd.get_notion_client')
    @patch('src.commands.enhance_database_cmd._create_migration_plan')
    @patch('src.commands.enhance_database_cmd._display_migration_plan')
    def test_create_enhanced_database_dry_run(self, mock_display_plan, mock_create_plan, mock_get_client, mock_get_db_id, mock_validate):
        """Test create_enhanced_database dry run mode."""
        mock_validate.return_value = True
        mock_get_db_id.return_value = "test-db-id"
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_db_info = {
            "title": [{"plain_text": "Test Database"}],
            "properties": {"Name": {"type": "title"}}
        }
        mock_client.get_database.return_value = mock_db_info
        mock_client.get_database_records.return_value = [{"id": "record1"}]
        
        mock_plan = {
            "source_properties": {"Name": {"type": "title"}},
            "enhanced_properties": {},
            "total_properties": 1,
            "records_to_migrate": 1,
            "analysis_stats": {},
            "has_analysis_data": False
        }
        mock_create_plan.return_value = mock_plan
        
        runner = CliRunner()
        result = runner.invoke(create_enhanced_database, ['--dry-run'])
        
        assert result.exit_code == 0
        mock_validate.assert_called_once()
        mock_create_plan.assert_called_once()
        mock_display_plan.assert_called_once()

    def test_create_migration_plan_no_analysis(self):
        """Test _create_migration_plan without analysis data."""
        db_info = {
            "properties": {
                "Name": {"type": "title"},
                "Tags": {"type": "multi_select"}
            }
        }
        
        plan = _create_migration_plan(db_info, None, 5)
        
        assert "source_properties" in plan
        assert "enhanced_properties" in plan
        assert len(plan["enhanced_properties"]) > 0
        assert plan["records_to_migrate"] == 5
        assert plan["has_analysis_data"] is False

    def test_create_migration_plan_with_analysis(self):
        """Test _create_migration_plan with analysis data."""
        db_info = {
            "properties": {
                "Name": {"type": "title"}
            }
        }
        
        analysis_data = {
            "llm_analysis": {
                "recipes_analyzed": [
                    {
                        "record_id": "1",
                        "suggested_category": "Breakfast",
                        "content_quality": {"overall_quality": "Good"}
                    },
                    {
                        "record_id": "2", 
                        "suggested_category": "Dinner",
                        "content_quality": {"overall_quality": "Excellent"}
                    }
                ]
            }
        }
        
        plan = _create_migration_plan(db_info, analysis_data, 2)
        
        assert plan["has_analysis_data"] is True
        assert plan["analysis_stats"]["total_analyzed"] == 2
        assert plan["analysis_stats"]["will_enhance"] == 2
        assert plan["analysis_stats"]["with_categories"] == 2
        assert plan["analysis_stats"]["with_quality"] == 2

    def test_calculate_analysis_stats(self):
        """Test _calculate_analysis_stats function."""
        analysis_data = {
            "llm_analysis": {
                "recipes_analyzed": [
                    {
                        "record_id": "1",
                        "suggested_category": "Breakfast",
                        "content_quality": {"overall_quality": "Good"}
                    },
                    {
                        "record_id": "2",
                        "suggested_category": "Breakfast", 
                        "content_quality": {"overall_quality": "Excellent"}
                    },
                    {
                        "record_id": "3",
                        "suggested_category": "Dinner"
                        # No content quality
                    }
                ]
            }
        }
        
        stats = _calculate_analysis_stats(analysis_data, 3)
        
        assert stats["total_analyzed"] == 3
        assert stats["will_enhance"] == 3
        assert stats["with_categories"] == 3
        assert stats["with_quality"] == 2
        assert stats["category_distribution"]["Breakfast"] == 2
        assert stats["category_distribution"]["Dinner"] == 1
        assert stats["quality_distribution"]["Good"] == 1
        assert stats["quality_distribution"]["Excellent"] == 1

    def test_calculate_analysis_stats_with_limit(self):
        """Test _calculate_analysis_stats with record limit."""
        analysis_data = {
            "llm_analysis": {
                "recipes_analyzed": [
                    {"record_id": "1", "suggested_category": "Breakfast"},
                    {"record_id": "2", "suggested_category": "Dinner"},
                    {"record_id": "3", "suggested_category": "Lunch"}
                ]
            }
        }
        
        stats = _calculate_analysis_stats(analysis_data, 2)
        
        assert stats["total_analyzed"] == 3
        assert stats["will_enhance"] == 2  # Limited by record_count
        assert stats["with_categories"] == 2

    def test_convert_property_for_creation(self):
        """Test _convert_property_for_creation function."""
        
        # Test title property
        title_prop = {"type": "title"}
        result = _convert_property_for_creation(title_prop)
        assert result == {"title": {}}
        
        # Test select property
        select_prop = {
            "type": "select",
            "select": {
                "options": [{"name": "Option1"}, {"name": "Option2"}]
            }
        }
        result = _convert_property_for_creation(select_prop)
        assert result == {"select": {"options": [{"name": "Option1"}, {"name": "Option2"}]}}
        
        # Test multi_select property
        multi_select_prop = {
            "type": "multi_select",
            "multi_select": {
                "options": [{"name": "Tag1"}, {"name": "Tag2"}]
            }
        }
        result = _convert_property_for_creation(multi_select_prop)
        assert result == {"multi_select": {"options": [{"name": "Tag1"}, {"name": "Tag2"}]}}
        
        # Test number property
        number_prop = {
            "type": "number",
            "number": {"format": "dollar"}
        }
        result = _convert_property_for_creation(number_prop)
        assert result == {"number": {"format": "dollar"}}
        
        # Test unsupported type
        unsupported_prop = {"type": "formula"}
        result = _convert_property_for_creation(unsupported_prop)
        assert result == {"rich_text": {}}

    def test_migrate_records_with_enhancements_no_analysis(self):
        """Test _migrate_records_with_enhancements without analysis data."""
        mock_client = Mock()
        mock_client.client = Mock()
        mock_client.get_record_content.return_value = {
            "id": "record1",
            "properties": {
                "Name": {"title": [{"text": {"content": "Test Recipe"}}]},
                "URL": {"url": "https://example.com/recipe"}
            },
            "blocks": []
        }
        mock_client.client.pages.create.return_value = {"id": "new-record1"}
        
        source_records = [{"id": "record1"}]
        
        result = _migrate_records_with_enhancements(
            mock_client, 
            "enhanced-db-id", 
            source_records, 
            None  # No analysis data
        )
        
        assert result == 1
        mock_client.client.pages.create.assert_called_once()
        
        # Check the properties passed to create
        call_args = mock_client.client.pages.create.call_args
        properties = call_args[1]["properties"]
        
        # Should have original properties
        assert "Name" in properties
        assert "URL" in properties
        
        # Should have enhancement metadata
        assert "Enhancement_Date" in properties
        assert "Enhancement_Version" in properties
        assert "Source_Domain" in properties

    def test_migrate_records_with_enhancements_with_analysis(self):
        """Test _migrate_records_with_enhancements with analysis data."""
        mock_client = Mock()
        mock_client.client = Mock()
        mock_client.get_record_content.return_value = {
            "id": "record1",
            "properties": {
                "Name": {"title": [{"text": {"content": "Test Recipe"}}]}
            },
            "blocks": []
        }
        mock_client.client.pages.create.return_value = {"id": "new-record1"}
        
        source_records = [{"id": "record1"}]
        analysis_data = {
            "llm_analysis": {
                "recipes_analyzed": [
                    {
                        "record_id": "record1",
                        "suggested_category": "Breakfast",
                        "content_quality": {"overall_quality": "Good"}
                    }
                ]
            }
        }
        
        result = _migrate_records_with_enhancements(
            mock_client, 
            "enhanced-db-id", 
            source_records, 
            analysis_data
        )
        
        assert result == 1
        
        # Check that AI enhancements were added
        call_args = mock_client.client.pages.create.call_args
        properties = call_args[1]["properties"]
        
        assert "AI_Category" in properties
        assert properties["AI_Category"]["select"]["name"] == "Breakfast"
        assert "Content_Quality" in properties
        assert properties["Content_Quality"]["select"]["name"] == "Good"

    def test_migrate_records_handles_failures(self):
        """Test _migrate_records_with_enhancements handles individual record failures."""
        mock_client = Mock()
        mock_client.client = Mock()
        
        # First record succeeds, second fails
        mock_client.get_record_content.side_effect = [
            {
                "id": "record1",
                "properties": {"Name": {"title": [{"text": {"content": "Recipe 1"}}]}},
                "blocks": []
            },
            Exception("API Error")
        ]
        mock_client.client.pages.create.return_value = {"id": "new-record1"}
        
        source_records = [{"id": "record1"}, {"id": "record2"}]
        
        result = _migrate_records_with_enhancements(
            mock_client, 
            "enhanced-db-id", 
            source_records, 
            None
        )
        
        # Should return 1 (only first record succeeded)
        assert result == 1
        # Should only create one page
        assert mock_client.client.pages.create.call_count == 1