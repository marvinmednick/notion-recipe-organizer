# Notion Recipe Organizer

A powerful CLI tool for organizing and categorizing recipes stored in a Notion database using AI-powered analysis.

## Quick Start

### Prerequisites
- Python 3.11+
- UV package manager
- Notion integration token
- Azure OpenAI API key

### Installation
```bash
git clone <repository-url>
cd notion-recipe-organizer
uv sync
```

### Configuration
1. Copy `.env.example` to `.env`
2. Add your API keys:
```bash
NOTION_TOKEN=your_notion_integration_token
NOTION_RECIPES_PAGE_ID=your_recipes_page_id
OPENAI_API_KEY=your_openai_key_for_analysis
```

### Basic Usage

**Extract recipes from Notion:**
```bash
uv run python -m src.main extract
```

**Analyze and categorize recipes:**
```bash
uv run python -m src.main analyze
```

**Generate review interface:**
```bash
uv run python -m src.main review --html
```

**Run full pipeline:**
```bash
uv run python -m src.main pipeline extract analyze review
```

## What It Does

1. **Extracts** recipe data from your Notion database
2. **Analyzes** recipes using AI to suggest categories, cuisine types, and dietary tags
3. **Reviews** results through interactive HTML interface or CSV exports
4. **Organizes** your recipe collection with consistent categorization

## Key Features

- **AI-Powered Categorization** - Uses Azure OpenAI to intelligently categorize recipes
- **Pipeline Workflows** - Chain commands together for automated processing
- **Configuration Profiles** - Predefined settings for different use cases
- **Interactive Review** - HTML interface for validating and correcting results
- **Comprehensive Testing** - 40+ automated tests ensure reliability

## Documentation

- [Current Status](STATUS.md) - Project phase and recent changes
- [Architecture](ARCHITECTURE.md) - Codebase structure and design
- [Pipeline Workflows](docs/pipeline.md) - Automation and chaining commands
- [Configuration](docs/configuration.md) - Profiles and settings
- [Testing Guide](docs/testing.md) - How to run and write tests
- [Features Reference](FEATURES.md) - Complete command documentation
- [Changelog](CHANGELOG.md) - Major project milestones

## Support

- Check configuration: `uv run python -m src.main --config-check`
- Run tests: `uv run pytest`
- Get help: `uv run python -m src.main --help`

## License

[Add your license information here]