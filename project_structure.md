# Notion Recipe Organizer

## Project Structure
```
notion-recipe-organizer/
├── pyproject.toml                 # UV project configuration
├── README.md
├── .env.example                   # Example environment variables
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point
│   ├── config.py                  # Configuration management
│   └── notion_client/
│       ├── __init__.py
│       ├── client.py              # Notion API wrapper
│       ├── extractor.py           # Recipe extraction logic
│       └── analyzer.py            # Recipe analysis & categorization
├── data/                          # Output directory
│   ├── raw/                       # Raw extracted data
│   ├── processed/                 # Analyzed data
│   └── reports/                   # Analysis reports
└── tests/
    └── __init__.py
```

## Current Project Status: ✅ Phase 1.5 Complete!

**Completed & Working:**
- ✅ Complete project setup and Notion API integration  
- ✅ Database extraction functionality working
- ✅ Basic statistical analysis implemented
- ✅ LLM categorization analysis with Azure OpenAI gpt-4.1
- ✅ **Complete configurable YAML-based categorization system**
- ✅ **Batch processing, range specification, timeout controls**
- ✅ **Robust error handling and progress tracking**
- ✅ **Enhanced content quality analysis (Non-recipe detection, title improvements, content summaries)**
- ✅ **Progressive complexity CLI with smart defaults**
- ✅ **Specialized reporting system (content issues, title improvements)**

**Current Status:** Phase 1.5 Complete - Ready for Phase 2 (Database Schema Enhancement)

**Production Status:** All analysis capabilities fully tested and working

## Working CLI Commands (Phase 1.5 Complete)

### Smart Defaults (Layer 1) ✅
```bash
# Just works - comprehensive analysis with smart defaults
uv run python -m src.main analyze
# Equivalent to: --use-llm --include-content-review --batch-size 20 --batch-delay 2 --timeout 30
```

### Quick Shortcuts (Layer 2) ✅
```bash
uv run python -m src.main analyze --quick            # Stats only, no LLM
uv run python -m src.main analyze --sample 5         # Test on 5 recipes
uv run python -m src.main analyze --range 50-100     # Specific range  
uv run python -m src.main analyze --profile production  # Optimized settings
```

### Configuration Profiles (Layer 3) ✅
```bash
uv run python -m src.main analyze --profile testing     # Test mode (10 recipes, 60s timeout)
uv run python -m src.main analyze --profile production  # Optimized (50 batch, fast)
uv run python -m src.main analyze --profile quick       # Stats only
```

### Individual Overrides (Layer 4) ✅
```bash
# Override anything from config or defaults
uv run python -m src.main analyze --profile production --timeout 60
uv run python -m src.main analyze --sample 5 --timeout 90 --no-content-review
uv run python -m src.main analyze --range 86-90 --batch-size 3
```

### Enhanced Analysis Features ✅
- **Content Quality Analysis** - Detects non-recipe items, evaluates titles, generates summaries
- **Quality Scoring** - Rates recipes 1-5 for usefulness
- **Smart Categorization** - Includes "Not a Recipe" category with highest precedence
- **Title Improvements** - Suggests better titles for unclear ones

### Enhanced Reporting System ✅
```
data/processed/
├── analysis_report.json           # Standard categorization results
├── content_issues_report.json     # Non-recipes flagged for review
├── title_improvements.csv         # Only items needing title changes  
├── processing_summary.json        # Batch processing metrics and errors
```

## Progressive Complexity CLI System (To Implement)

### Layer 1: Smart Defaults (Beginner Friendly)
```bash
# Just works - does comprehensive analysis with reasonable settings
uv run python -m src.main analyze
# Equivalent to: --use-llm --include-content-review --batch-size 20 --batch-delay 2 --timeout 30
```

### Layer 2: Quick Shortcuts (Common Variations)  
```bash
uv run python -m src.main analyze --quick            # Stats only, no LLM
uv run python -m src.main analyze --sample 5         # Test on 5 recipes
uv run python -m src.main analyze --range 50-100     # Specific range  
uv run python -m src.main analyze --production       # Optimized for large datasets
```

### Layer 3: Configuration Profiles (Power Users)
```yaml
# config/analysis_profiles.yaml
profiles:
  default: {use_llm: true, include_content_review: true, batch_size: 20, timeout: 30}
  testing: {use_llm: true, sample_size: 10, timeout: 60}
  production: {use_llm: true, batch_size: 50, batch_delay: 1, timeout: 45}
```

```bash
uv run python -m src.main analyze --profile testing
uv run python -m src.main analyze --profile production
```

### Layer 4: Individual Overrides (Expert Control)
```bash
# Override anything from config or defaults
uv run python -m src.main analyze --profile production --timeout 60
uv run python -m src.main analyze --sample 5 --timeout 90
```

### Priority Order: CLI flags > Profile settings > Shortcuts > Smart defaults

## Enhanced Reporting System (To Implement)

### Standard Analysis Report
- Recipe categorization results
- Distribution statistics
- Processing metrics

### Content Quality Reports
- **Non-recipe items report:** Items flagged as "Not a Recipe" for review/removal
- **Title improvements report:** Only items with proposed title changes
- **Content issues summary:** Overview of quality concerns found

### Report Outputs
```
data/processed/
├── analysis_report.json           # Standard categorization results
├── content_issues_report.json     # Non-recipes and quality issues  
├── title_improvements.csv         # Only items needing title changes
└── processing_summary.json        # Batch processing metrics and errors
```

## Development Phases (Updated)

### Phase 1: Data Discovery & Analysis ✅ COMPLETE
**Goal:** Extract and analyze current database structure without disrupting workflow

**Completed Commands:**
- ✅ `python -m src.main extract --database-id your_db_id` - Full extraction working
- ✅ `python -m src.main analyze --basic-only` - Basic statistics working
- ✅ `python -m src.main analyze --use-llm --sample-size 5` - LLM sample analysis working
- ✅ `python -m src.main analyze --use-llm --start-index 86 --end-index 86 --timeout 60` - Targeted analysis with new features

**Advanced Features Implemented:**
- ✅ **Range specification:** `--start-index 50 --end-index 100`
- ✅ **Batch processing:** `--batch-size 20 --batch-delay 3`
- ✅ **Timeout control:** `--timeout 45`
- ✅ **Error resilience:** Individual recipe failures don't crash analysis
- ✅ **Progress tracking:** Clear indication of current batch/recipe being processed

**Outputs Achieved:**
- ✅ Complete database extraction with schema (`data/raw/recipes.json`)
- ✅ Basic analysis showing tag usage, URL patterns, collection stats
- ✅ LLM categorization with configurable YAML rules
- ✅ Failed analysis tracking and recommendations

### Phase 2: Schema Enhancement & Preparation  
**Goal:** Design enhanced database schema while preserving current workflow

**Commands:**
- `python -m src.main design-schema --analysis analysis_report.json` - Generate enhanced schema
- `python -m src.main preview-migration --schema schema.json --sample 20` - Preview what migration would look like
- `python -m src.main backup-database --database-id your_db_id` - Create safety backup

**Outputs:**
- `enhanced_schema.json` - New property definitions (Primary Category, Cuisine Type, etc.)
- `migration_preview.html` - Visual preview of how recipes would be categorized
- `database_backup.json` - Complete backup of current database

### Phase 2: Database Schema Enhancement ⏳ READY TO START
**Goal:** Add enhanced properties to Notion database using Phase 1.5 analysis results

**Approach - Non-Disruptive Enhancement:**
- ✅ **Analysis System Complete:** Content quality and categorization working perfectly
- ✅ **Enhanced Categories Ready:** Including "Not a Recipe" for content cleanup
- 🎯 **Add new optional properties:** All categories with refined precedence rules
- 🎯 **Create database views:** Filtered views for each category + content quality
- 🎯 **Database backup:** Complete backup before schema changes

**Final Enhanced Schema (Phase 1.5 Analysis Ready):**
```yaml
Primary Category (single-select, optional):
  Not a Recipe (precedence 0), Breakfast (1), Desserts (2), Baking (3), 
  Beef/Chicken/Pork/Seafood/Vegetarian (4), Sides & Appetizers (5)

Cuisine Type (single-select, optional):
  Mexican, Italian, Asian, American, Mediterranean, Indian, French, Other

Dietary Tags (multi-select, optional):
  Food Allergy Safe, Vegetarian, Vegan, Gluten-Free, Dairy-Free, 
  Low-Carb, Keto, Quick & Easy, One Pot, Make Ahead

Usage Tags (multi-select, optional):
  Favorite, Tried & Tested, Want to Try, Holiday/Special Occasion, 
  Family Recipe, Experimental

Content Quality (optional - from Phase 1.5):
  Content Summary (text), Proposed Title (text), Quality Score (1-5)
```

**Commands to Implement:**
- 🎯 `python -m src.main backup-database --database-id your_db_id`
- 🎯 `python -m src.main enhance-schema --add-properties`  
- 🎯 `python -m src.main create-views --database-id your_db_id`
- 🎯 `python -m src.main populate-categories --use-analysis-results`

### Phase 4: Batch Categorization Assistant + Page Organization
**Goal:** Organize existing recipes when you want to, not when you save

**Commands:**
- `python -m src.main categorize --batch-size 10` - Categorize recipes in small batches
- `python -m src.main categorize --filter uncategorized --auto` - Auto-categorize uncategorized recipes
- `python -m src.main categorize --review-mode` - Manual review and override mode
- `python -m src.main categorize --dietary-tags` - Special focus on food allergy safe tagging
- `python -m src.main organize-pages --create-hierarchy` - Build browseable page structure
- `python -m src.main organize-pages --move-recipes` - Move categorized recipes to appropriate folders

**Features:**
- Process recipes in manageable batches
- LLM-powered auto-categorization with human review
- Preserve existing useful tags (like "Food Allergy Safe")
- Create browseable page hierarchy alongside database organization
- Dual organization: database views AND page folders for different browsing styles
- Undo/rollback capability for corrections

**Page Structure Created:**
```
Recipes/
├── Recipe Database (enhanced database with views)
├── All Recipe Pages/ (flat list - current structure preserved)
├── Uncategorized/ (new recipes default here)
├── By Primary Category/
│   ├── Beef/ (pages linked/moved here)
│   ├── Chicken/
│   ├── Breakfast/
│   └── [etc...]
└── By Cuisine/
    ├── Mexican/
    ├── Italian/
    └── [etc...]
```

## Technology Stack & Architecture (Current Status)

### ✅ Fully Implemented & Working:
- **Python with UV** for environment management
- **Click + Rich** for beautiful CLI interface
- **Notion API** with database operations and ID cleaning
- **Azure OpenAI** integration (gpt-4.1, API version 2025-04-01-preview)
- **Pydantic** for data validation
- **YAML configuration system** for maintainable categorization (PyYAML)
- **Batch processing** with timeout and error handling
- **Range specification** for targeted analysis

### File Versions & Status (Current):
- ✅ `config.py` - v8 (Azure OpenAI gpt-4.1 configured)
- ✅ `notion_client/client.py` - v2 (Database operations, ID cleaning) 
- ✅ `main.py` - v6 (Complete CLI with batch processing, range specification)
- ✅ `notion_client/analyzer.py` - v1 (Complete analysis engine with YAML integration)
- ✅ `notion_client/config_loader.py` - v1 (YAML config and template system)
- ✅ `config/*.yaml` - v1 (Complete categorization system)
- ✅ `config/prompts/base_prompt.txt` - v1 (LLM prompt template)

### Error Handling & Safety Features:
- ✅ ID cleaning for Notion URLs with view parameters  
- ✅ Timeout controls for LLM calls (configurable per recipe)
- ✅ Individual recipe failure handling (doesn't crash whole analysis)
- ✅ Batch processing with configurable delays (rate limiting protection)
- ✅ Range specification for targeting problematic recipes
- ✅ Comprehensive progress tracking and error reporting
- ✅ Failed analysis tracking with recommendations

### Working CLI Commands (Ready to Use):
```bash
# Database extraction
uv run python -m src.main extract                    # Full extraction
uv run python -m src.main extract --dry-run          # Test mode

# Analysis with all new features
uv run python -m src.main analyze --basic-only       # Statistics only
uv run python -m src.main analyze --use-llm --sample-size 5  # Quick test
uv run python -m src.main analyze --use-llm --start-index 86 --end-index 86 --timeout 60  # Target problem recipes
uv run python -m src.main analyze --use-llm --batch-size 20 --batch-delay 3 --timeout 30  # Production run

# Configuration validation
uv run python -m src.main test --dry-run             # Test connections
```

## Configuration (.env)
```
NOTION_TOKEN=your_notion_integration_token
NOTION_RECIPES_PAGE_ID=your_recipes_page_id
OPENAI_API_KEY=your_openai_key_for_analysis
LOG_LEVEL=INFO
```

## CLI Interface Design

```bash
# Phase 1: Discovery
uv run python -m src.main extract --page-id "recipes_page_id" --output recipes.json
uv run python -m src.main analyze --input recipes.json --use-llm

# Phase 2: Schema
uv run python -m src.main design-schema --analysis analysis_report.json
uv run python -m src.main preview-categorization --schema schema.json --sample 20

# Phase 3: Migration
uv run python -m src.main create-database --schema schema.json --name "Recipe Database"
uv run python -m src.main migrate --recipes recipes.json --database-id "new_db_id"
uv run python -m src.main organize-pages --hierarchy-config hierarchy.json
```

## Key Features

### Workflow Preservation
- **No disruption** to current recipe saving process
- New properties added as optional with smart defaults
- Categorization happens separately from daily use

### Smart Categorization Assistant
- LLM-powered analysis of recipe names and content
- Batch processing in manageable chunks
- Human review and override capabilities
- Special handling for dietary restrictions and food allergies

### Enhanced Database Views + Page Hierarchy
- **Database views** for filtering and sorting (power users, quick access)
- **Page hierarchy** for visual browsing and discovery
- Multiple filtered/grouped database views without changing underlying data
- "All Recipes" (current default view preserved)
- "By Primary Category" (Beef, Chicken, Breakfast, etc.)
- "By Cuisine" (Mexican, Italian, etc.)
- "Food Allergy Safe" (special filtered view)
- "Uncategorized" (for new/unprocessed recipes)
- Organized page folders that mirror database categorization
- Dual-access: find recipes via database filtering OR page browsing

### Safety Features
- Complete database backup before any changes
- `--dry-run` flags for all operations
- Rollback capabilities for categorization
- Incremental processing with resume functionality

## Initial Development Steps

1. **Setup Project Structure** ✅ (Completed)
   ```bash
   uv init notion-recipe-organizer
   cd notion-recipe-organizer
   uv add notion-client python-dotenv rich click pydantic
   ```

2. **Update Code for Database Operations**
   - Modify extractor to work with database records instead of page children
   - Add database schema analysis capabilities
   - Build database property management tools

3. **Build Database Record Extraction**
   - Extract first 5 database records to verify structure
   - Analyze existing properties and data quality
   - Scale to full database extraction

4. **Implement LLM Analysis + Page Management Pipeline**
   - Category distribution analysis
   - Auto-categorization suggestions based on recipe names/content
   - Generate enhancement recommendations
   - Page organization and hierarchy management tools

Would you like me to start with the basic project setup and Notion API connection, or would you prefer to review/modify this structure first?