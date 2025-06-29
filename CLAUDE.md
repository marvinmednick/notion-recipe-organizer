# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Setup
```bash
uv sync                                    # Install dependencies
uv run python -m src.main --config-check  # Validate configuration
```

### Core CLI Commands
```bash
uv run python -m src.main extract         # Extract recipes from Notion
uv run python -m src.main analyze         # AI-powered categorization
uv run python -m src.main review --html   # Generate HTML review interface
uv run python -m src.main pipeline extract analyze review  # Full workflow
```

### Testing
```bash
uv run pytest                    # Run all tests
uv run pytest tests/unit/        # Unit tests only
uv run pytest tests/integration/ # Integration tests only
uv run pytest -m "not external"  # Skip external API tests
uv run pytest --cov             # Run with coverage
```

### Single Test Execution
```bash
uv run pytest tests/unit/test_extractor.py::test_extract_recipes  # Specific test
uv run pytest -k "test_name"                                      # Tests matching pattern
```

## Architecture Overview

### Core Structure
- **src/main.py** - CLI entry point (77 lines, heavily refactored from 738 lines)
- **src/pipeline.py** - Orchestrates command chaining with shared context
- **src/commands/** - Individual CLI commands as separate modules
- **src/notion_client/** - Business logic layer with Notion API integration
- **src/utils/** - Shared utilities (config, display, file operations)

### Key Design Patterns
- **Modular CLI Architecture** - Commands are separated into individual modules under `src/commands/`
- **Pipeline Pattern** - Commands can be chained together via `pipeline` command with shared context
- **Configuration-Driven** - YAML files in `config/` directory control behavior
- **File-Based Data Flow** - Commands communicate via JSON files in `data/` directory

### Data Flow
1. **Extract** ’ `data/raw/recipes.json`
2. **Analyze** ’ `data/processed/analysis_results.json`
3. **Review** ’ `data/processed/review_interface.html` or CSV exports

### Configuration System
- **Profiles** - Defined in `config/analysis_profiles.yaml` (testing, production, quick, small_sample)
- **Categories** - Recipe categories in `config/categories.yaml`
- **Conflict Rules** - Category precedence in `config/conflict_rules.yaml`
- **AI Prompts** - Base prompt in `config/prompts/base_prompt.txt`

## Environment Setup

### Required Environment Variables
```bash
# Notion API
NOTION_TOKEN=your_notion_integration_token
NOTION_RECIPES_DATABASE_ID=your_database_id

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_VERSION=2025-04-01-preview

# Optional Application Settings
LOG_LEVEL=INFO
DATA_DIR=data
MAX_RETRIES=3
```

## Testing Architecture

### Test Structure
- **tests/unit/** - 24 unit tests with comprehensive mocking
- **tests/integration/** - 16 integration tests for end-to-end workflows
- **Markers** - Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.external`

### Key Test Patterns
- External APIs are mocked using `pytest-mock`
- File I/O operations use temporary directories
- Configuration uses test profiles to avoid side effects

## Recent Refactoring (Phase 1.9)

The codebase underwent major refactoring to improve maintainability:
- **main.py** reduced from 738 to 77 lines
- Commands extracted to separate modules in `src/commands/`
- Direct function calls replaced subprocess architecture
- Zero breaking changes to CLI interface
- 40+ tests ensure stability

## Key Utilities

### Config Management
- `src/config.py` - Central configuration object
- `src/utils/config_utils.py` - Validation and client creation
- `src/notion_client/profile_loader.py` - Profile-based settings

### Display and Output
- `src/utils/display_utils.py` - Rich console formatting
- All CLI output uses Rich library for consistent formatting

### Error Handling
- `PipelineStepError` for pipeline failures
- Comprehensive error messages with context
- Graceful handling of API failures with retries

## Development Notes

### Adding New Commands
1. Create new file in `src/commands/new_cmd.py`
2. Follow existing command patterns with Click decorators
3. Import and register in `src/main.py`
4. Add corresponding tests in `tests/unit/commands/`

### Configuration Changes
- Most behavior is controlled via YAML files in `config/`
- Use profiles for different execution modes
- Test configuration changes with `--config-check`

### Pipeline Integration
- New commands can be integrated into pipeline via `src/pipeline.py`
- Use `PipelineContext` for shared state between commands
- Follow file-based data passing conventions