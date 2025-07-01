# Features Reference

Complete command documentation for the Notion Recipe Organizer CLI.

## Core Commands

### `extract` - Extract Recipe Data

Extract recipe data from your Notion database.

**Basic Usage:**
```bash
uv run python -m src.main extract
uv run python -m src.main extract --database-id your_db_id
uv run python -m src.main extract --max-records 50
```

**Options:**
- `--database-id TEXT` - Notion database ID (or set NOTION_RECIPES_PAGE_ID)
- `--output PATH` - Output file path (default: data/raw/recipes.json)
- `--max-records INTEGER` - Maximum number of records to extract
- `--dry-run` - Show what would be extracted without saving

**Examples:**
```bash
# Extract all recipes
uv run python -m src.main extract

# Extract specific database with limit
uv run python -m src.main extract --database-id abc123 --max-records 100

# Test extraction without saving
uv run python -m src.main extract --dry-run --max-records 5
```

**Output:**
- Saves to `data/raw/recipes.json` with metadata
- Includes database schema for analysis
- Shows progress during extraction

---

### `analyze` - AI-Powered Recipe Analysis

Analyze extracted recipes using AI to suggest categorizations.

**Basic Usage:**
```bash
uv run python -m src.main analyze
uv run python -m src.main analyze --quick
uv run python -m src.main analyze --profile testing
```

**Options:**
- `--input PATH` - Input JSON file (default: data/raw/recipes.json)
- `--output PATH` - Output directory (default: data/processed/)
- `--profile TEXT` - Configuration profile (testing, production, quick)
- `--quick` - Statistics only, no LLM analysis
- `--sample INTEGER` - Analyze only N recipes

**Range Specification:**
- `--start-index INTEGER` - Start analysis from recipe index
- `--end-index INTEGER` - End analysis at recipe index
- `--range TEXT` - Specify range like "50-100"

**Processing Control:**
- `--batch-size INTEGER` - Recipes per batch (default: 20)
- `--batch-delay FLOAT` - Seconds between batches (default: 2)
- `--timeout INTEGER` - Timeout per recipe in seconds (default: 30)

**Feature Toggles:**
- `--use-llm / --no-llm` - Enable/disable LLM analysis
- `--include-content-review / --no-content-review` - Content quality analysis

**Examples:**
```bash
# Full analysis with smart defaults
uv run python -m src.main analyze

# Quick statistics only
uv run python -m src.main analyze --quick

# Test with sample data
uv run python -m src.main analyze --sample 5

# Analyze specific range
uv run python -m src.main analyze --range 50-100

# Production optimized
uv run python -m src.main analyze --profile production

# Custom batch processing
uv run python -m src.main analyze --batch-size 10 --timeout 60
```

**Output Files:**
- `data/processed/analysis_report.json` - Main categorization results
- `data/processed/title_improvements.csv` - Suggested title improvements
- `data/processed/processing_summary.json` - Processing metrics and errors

---

### `review` - Generate Review Interfaces

Generate review interfaces for categorization results.

**Basic Usage:**
```bash
uv run python -m src.main review --html
uv run python -m src.main review --csv --issues-only
```

**Options:**
- `--input PATH` - Input analysis file (default: data/processed/analysis_report.json)
- `--output PATH` - Output directory (default: data/processed/review/)
- `--html` - Generate interactive HTML review interface
- `--csv` - Export to CSV for spreadsheet editing
- `--summary` - Generate review summary report
- `--issues-only` - Focus on items with issues only

**Examples:**
```bash
# Interactive HTML review
uv run python -m src.main review --html

# CSV export for editing
uv run python -m src.main review --csv

# Focus on problem items
uv run python -m src.main review --csv --issues-only

# Generate all formats
uv run python -m src.main review --html --csv --summary
```

**Output Files:**
- `data/processed/review/review_report.html` - Interactive HTML interface
- `data/processed/review/categorization_review.csv` - Editable CSV
- `data/processed/review/categorization_issues.csv` - Problem items only
- `data/processed/review/review_summary.json` - Review metrics

---

### `pipeline` - Automated Workflows

Chain multiple commands together with shared configuration.

**Basic Usage:**
```bash
uv run python -m src.main pipeline extract analyze review
uv run python -m src.main pipeline --profile testing extract analyze review
```

**Workflow Options:**
```bash
# Full pipeline
pipeline extract analyze review

# Skip extraction (use existing data)
pipeline analyze review

# Stop before review
pipeline extract analyze

# Single step
pipeline analyze
```

**Global Options:**
- `--profile TEXT` - Configuration profile for all steps
- `--database-id TEXT` - Database ID for extract step
- `--limit INTEGER` - Limit records/recipes processed
- `--timeout INTEGER` - Timeout for LLM calls (analyze step)
- `--dry-run` - Dry run mode (extract step)
- `--quick` - Quick mode (analyze step)

**Examples:**
```bash
# Full workflow with testing profile
uv run python -m src.main pipeline --profile testing extract analyze review

# Production workflow
uv run python -m src.main pipeline --profile production extract analyze review

# Limited processing
uv run python -m src.main pipeline --limit 10 extract analyze review

# Skip extraction, analyze existing data
uv run python -m src.main pipeline analyze review

# Development workflow
uv run python -m src.main pipeline --dry-run extract
uv run python -m src.main pipeline --quick analyze review
```

---

### `apply-corrections` - Apply CSV Corrections

Apply corrections from edited CSV files back to the analysis results.

**Usage:**
```bash
uv run python -m src.main apply-corrections --input corrections.csv
```

**Options:**
- `--input PATH` - Input CSV file with corrections

---

## Phase 2: Database Enhancement Commands

### `backup-database` - Backup Notion Database

Create a complete backup of your Notion database before making schema changes.

**Usage:**
```bash
uv run python -m src.main backup-database
uv run python -m src.main backup-database --database-id your_db_id --verify
```

**Options:**
- `--database-id TEXT` - Notion database ID (or use config default)
- `--verify` - Verify backup integrity after creation
- `--output-dir PATH` - Backup directory (default: data/backups/)

**What it backs up:**
- Complete database schema (properties, types, options)
- All recipe data and property values
- Database metadata and configuration
- Creates rollback instructions for recovery

**Examples:**
```bash
# Basic backup with verification
uv run python -m src.main backup-database --verify

# Backup specific database
uv run python -m src.main backup-database --database-id abc123 --verify

# Custom backup location
uv run python -m src.main backup-database --output-dir ./my-backups/ --verify
```

---

### `enhance-database-in-place` - Enhance Database Schema and Data

Add categorization properties to your existing Notion database and populate with AI analysis results.

**Usage:**
```bash
uv run python -m src.main enhance-database-in-place --use-analysis-results
uv run python -m src.main enhance-database-in-place --sample 10 --dry-run
```

**Options:**
- `--use-analysis-results` - Apply AI categorization from analysis step
- `--sample INTEGER` - Test with limited number of records
- `--dry-run` - Show what would be enhanced without making changes
- `--database-id TEXT` - Target database ID to enhance

**What it enhances:**
- **Schema**: Adds new properties to existing database (Primary Category, Cuisine Type, Dietary Tags, Usage Tags, Source Domain, Proposed_Title)
- **Data**: Populates existing records with AI-suggested categorization
- **Title Suggestions**: Populates Proposed_Title field with AI-suggested improvements (no Name modification)
- **Preservation**: All existing properties and content remain unchanged

**Examples:**
```bash
# Full database enhancement
uv run python -m src.main enhance-database-in-place --use-analysis-results

# Test with sample data first
uv run python -m src.main enhance-database-in-place --sample 5 --dry-run

# Enhance specific database
uv run python -m src.main enhance-database-in-place --database-id abc123 --use-analysis-results
```

**Enhancement Details:**
- **Primary Category**: Single-select (Breakfast, Desserts, Baking, Recipe Components, etc.)
- **Cuisine Type**: Single-select (Italian, Mexican, Asian, Mediterranean, etc.)
- **Dietary Tags**: Multi-select (Vegetarian, Gluten-Free, Keto, Quick & Easy, etc.)
- **Usage Tags**: Multi-select (Favorite, Tried & Tested, Want to Try, etc.)
- **Source Domain**: Rich text field with website domain extracted from URL
- **Proposed_Title**: Rich text field for AI-suggested title improvements (manual review required)

**Safety Features:**
- **In-Place Enhancement**: No database copying, all records stay in their original location
- **Property Preservation**: Never modifies existing properties (Name, URL, Tags, etc.)
- **Content Preservation**: All page content blocks remain unchanged
- **Incremental**: Only adds properties that don't already exist
- **Name Field Behavior**: Original Name field behavior preserved (opens page panel when clicked)

---

### `apply-title-improvements` - Apply Title Improvements

Apply title improvements from the Proposed_Title field to the actual Title field.

**Usage:**
```bash
uv run python -m src.main apply-title-improvements
uv run python -m src.main apply-title-improvements --dry-run --sample 5
```

**Options:**
- `--database-id TEXT` - Target enhanced database ID
- `--sample INTEGER` - Test with limited number of records
- `--dry-run` - Show what would be changed without modifying titles
- `--force` - Apply changes without confirmation prompt

**How it works:**
- Only processes records where Proposed_Title field is non-empty
- Copies Proposed_Title content to Title field
- Preserves original titles where Proposed_Title is blank/empty
- No separate flag field needed - empty Proposed_Title means no change required

**Examples:**
```bash
# Apply all proposed title improvements
uv run python -m src.main apply-title-improvements

# Preview changes first
uv run python -m src.main apply-title-improvements --dry-run

# Test with sample data
uv run python -m src.main apply-title-improvements --sample 10 --dry-run

# Apply to specific database
uv run python -m src.main apply-title-improvements --database-id abc123
```

**Title Enhancement Workflow:**
1. **After enhance-database**: Proposed_Title field populated with AI suggestions
2. **Manual Review**: Edit/remove proposed titles in Notion interface
3. **Apply Changes**: Run apply-title-improvements to copy Proposed_Title → Title
4. **Rollback**: Re-run enhance-database from source to restore originals

**Safety Features:**
- Dry-run mode shows exactly what will change
- Sample mode for testing on few records
- Only non-empty Proposed_Title fields are processed
- Source database always contains original titles for rollback

---

### `test` - Test System Components

Test Notion API connection and basic functionality.

**Usage:**
```bash
uv run python -m src.main test
```

**What it tests:**
- Notion API connection
- Database access
- Basic data extraction
- Configuration validation

---

## Global Options

Available for all commands:

- `--log-level TEXT` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--config-check` - Check configuration and exit
- `--help` - Show help message

**Examples:**
```bash
# Check configuration
uv run python -m src.main --config-check

# Enable debug logging
uv run python -m src.main --log-level DEBUG analyze

# Get help for any command
uv run python -m src.main extract --help
```

## Configuration Profiles

Predefined settings for common use cases:

### `testing` - Development Profile
- Extract: 10 records maximum
- Analyze: 10 recipes, 60s timeout, careful processing
- Review: HTML format
- **Use for:** Development, testing new features

### `production` - High-Volume Profile  
- Extract: No limits
- Analyze: 50 batch size, 45s timeout, fast processing
- Review: HTML format
- **Use for:** Processing large recipe collections

### `quick` - Statistics Only
- Analyze: No LLM calls, statistics only
- Review: HTML format
- **Use for:** Quick dataset overview without AI analysis

### `small_sample` - Quick Testing
- Extract: 5 records maximum
- Analyze: 5 recipes, 30s timeout
- Review: HTML format  
- **Use for:** Quick functionality testing

### `content_cleanup` - Quality Focus
- Analyze: Careful processing, longer timeouts
- Review: CSV format, issues only
- **Use for:** Cleaning up content quality issues

**Profile Usage:**
```bash
# Use profile with individual command
uv run python -m src.main analyze --profile testing

# Use profile with pipeline
uv run python -m src.main pipeline --profile production extract analyze review
```

## Output Directory Structure

```
data/
├── raw/
│   └── recipes.json              # Extracted recipe data
├── processed/
│   ├── analysis_report.json      # Main categorization results
│   ├── title_improvements.csv    # Title improvement suggestions
│   ├── processing_summary.json   # Processing metrics
│   └── review/
│       ├── review_report.html    # Interactive HTML review
│       ├── categorization_review.csv     # Editable corrections
│       ├── categorization_issues.csv     # Problem items only
│       └── review_summary.json   # Review session metrics
└── reports/
    └── [timestamped reports]     # Historical analysis reports
```

## Error Handling and Troubleshooting

### Common Commands for Troubleshooting

```bash
# Check system health
uv run python -m src.main --config-check
uv run python -m src.main test

# Test with small samples
uv run python -m src.main extract --dry-run --max-records 3
uv run python -m src.main analyze --sample 3

# Check intermediate files
ls data/raw/
ls data/processed/

# View processing errors
cat data/processed/processing_summary.json
```

### Exit Codes

- `0` - Success
- `1` - General error (configuration, API, processing)
- `2` - User error (invalid arguments, missing files)

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General operational messages (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

**Example:**
```bash
# Enable detailed logging
uv run python -m src.main --log-level DEBUG analyze --sample 5
```

## Integration Examples

### Daily Recipe Processing
```bash
# Morning: Extract new recipes
uv run python -m src.main extract --max-records 20

# Analyze with production settings
uv run python -m src.main analyze --profile production

# Review results
uv run python -m src.main review --html
```

### Quality Cleanup Workflow
```bash
# Focus on content issues
uv run python -m src.main analyze --profile content_cleanup

# Export problems for review
uv run python -m src.main review --csv --issues-only

# After editing CSV, apply corrections
uv run python -m src.main apply-corrections --input fixes.csv
```

### Development Testing
```bash
# Quick test of new features
uv run python -m src.main pipeline --profile small_sample extract analyze review

# Test analysis changes
uv run python -m src.main pipeline --quick analyze review
```