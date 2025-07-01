"""Integration tests for pipeline command."""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch

from src.main import cli


class TestPipelineIntegration:
    """Test pipeline command integration."""

    def test_pipeline_help(self):
        """Test that pipeline help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline', '--help'])
        
        assert result.exit_code == 0
        assert "Run multiple commands in sequence" in result.output
        assert "extract analyze review" in result.output
        assert "--profile" in result.output
        assert "--limit" in result.output

    def test_pipeline_invalid_steps(self):
        """Test pipeline with invalid step names."""
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline', 'invalid', 'step'])
        
        assert result.exit_code == 0  # Pipeline handles error gracefully
        assert "Invalid steps" in result.output
        assert "invalid, step" in result.output
        assert "Valid steps" in result.output
        # Should include new commands in valid steps
        assert "create-enhanced-database" in result.output

    def test_pipeline_no_steps(self):
        """Test pipeline with no steps provided."""
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline'])
        
        assert result.exit_code != 0  # Click should fail for missing required argument
        assert "Missing argument" in result.output or "Usage:" in result.output

    @patch('src.pipeline._run_extract_step')
    @patch('src.pipeline._run_analyze_step')
    @patch('src.pipeline._run_review_step')
    @patch('src.pipeline.ProfileLoader')
    def test_pipeline_single_step(self, mock_profile_loader, mock_review, mock_analyze, mock_extract):
        """Test pipeline with single step."""
        # Setup mocks
        mock_profile_loader.return_value.get_profile_settings.return_value = {}
        
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline', 'extract'])
        
        assert result.exit_code == 0
        assert "Running Pipeline: extract" in result.output
        assert "Step 1/1: Extract" in result.output
        assert "Pipeline completed successfully" in result.output
        
        # Verify only extract was called
        mock_extract.assert_called_once()
        mock_analyze.assert_not_called()
        mock_review.assert_not_called()

    @patch('src.pipeline._run_extract_step')
    @patch('src.pipeline._run_analyze_step')
    @patch('src.pipeline._run_review_step')
    @patch('src.pipeline.ProfileLoader')
    def test_pipeline_full_workflow(self, mock_profile_loader, mock_review, mock_analyze, mock_extract):
        """Test full pipeline workflow."""
        # Setup mocks
        mock_profile_loader.return_value.get_profile_settings.return_value = {}
        
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline', 'extract', 'analyze', 'review'])
        
        assert result.exit_code == 0
        assert "Running Pipeline: extract → analyze → review" in result.output
        assert "Step 1/3: Extract" in result.output
        assert "Step 2/3: Analyze" in result.output
        assert "Step 3/3: Review" in result.output
        assert "Pipeline completed successfully" in result.output
        
        # Verify all steps were called
        mock_extract.assert_called_once()
        mock_analyze.assert_called_once()
        mock_review.assert_called_once()

    @patch('src.pipeline._run_create_enhanced_database_step')
    @patch('src.pipeline.ProfileLoader')
    def test_pipeline_phase_2_workflow(self, mock_profile_loader, mock_create_enhanced):
        """Test Phase 2.0 database enhancement workflow."""
        # Setup mocks
        mock_profile_loader.return_value.get_profile_settings.return_value = {}
        
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline', 'analyze', 'create-enhanced-database'])
        
        assert result.exit_code == 0
        assert "Running Pipeline: analyze → create-enhanced-database" in result.output
        assert "Step 1/2: Analyze" in result.output
        assert "Step 2/2: Create-Enhanced-Database" in result.output
        assert "Pipeline completed successfully" in result.output
        
        # Verify the step was called
        mock_create_enhanced.assert_called_once()

    @patch('src.pipeline._run_extract_step')
    @patch('src.pipeline._run_analyze_step')
    @patch('src.pipeline.ProfileLoader')
    def test_pipeline_with_profile(self, mock_profile_loader, mock_analyze, mock_extract):
        """Test pipeline with profile."""
        # Setup mocks
        mock_profile_settings = {
            "extract": {"records": 10},
            "analyze": {"batch_size": 5, "timeout": 30}
        }
        mock_profile_loader.return_value.get_profile_settings.return_value = mock_profile_settings
        
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline', '--profile', 'testing', 'extract', 'analyze'])
        
        assert result.exit_code == 0
        assert "Using profile: testing" in result.output
        assert "Pipeline completed successfully" in result.output
        
        # Verify steps were called
        mock_extract.assert_called_once()
        mock_analyze.assert_called_once()

    @patch('src.pipeline._run_extract_step')
    @patch('src.pipeline._run_analyze_step')
    @patch('src.pipeline.ProfileLoader')
    def test_pipeline_error_handling(self, mock_profile_loader, mock_analyze, mock_extract):
        """Test pipeline error handling."""
        # Setup mocks
        mock_profile_loader.return_value.get_profile_settings.return_value = {}
        mock_extract.side_effect = Exception("Extract failed")
        
        runner = CliRunner()
        result = runner.invoke(cli, ['pipeline', 'extract', 'analyze'])
        
        assert result.exit_code == 0  # Pipeline handles error gracefully
        assert "Unexpected error in step 'extract'" in result.output
        assert "Extract failed" in result.output
        
        # Verify extract was called but analyze was not
        mock_extract.assert_called_once()
        mock_analyze.assert_not_called()

    @patch('src.pipeline._run_extract_step')
    @patch('src.pipeline._run_analyze_step')
    @patch('src.pipeline.ProfileLoader')
    def test_pipeline_with_global_options(self, mock_profile_loader, mock_analyze, mock_extract):
        """Test pipeline with global options."""
        # Setup mocks
        mock_profile_loader.return_value.get_profile_settings.return_value = {}
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'pipeline', 
            '--limit', '5', 
            '--timeout', '60',
            '--dry-run',
            'extract', 
            'analyze'
        ])
        
        assert result.exit_code == 0
        assert "Pipeline completed successfully" in result.output
        
        # Verify steps were called
        mock_extract.assert_called_once()
        mock_analyze.assert_called_once()
        
        # Verify context was passed with global options
        extract_call_args = mock_extract.call_args[0][0]  # Get PipelineContext
        assert extract_call_args.global_options["limit"] == 5
        assert extract_call_args.global_options["timeout"] == 60
        assert extract_call_args.global_options["dry_run"] is True