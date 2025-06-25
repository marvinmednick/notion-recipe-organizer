# Notion Recipe Organizer - Project Plan

## Current Project Status: ✅ Phase 1.9 Complete - Refactored & Tested!

**Latest Achievement: Complete codebase refactoring with comprehensive testing framework**

### **Phase 1.9 Completed & Working - Code Architecture Refactoring:**
- ✅ **90% Main.py Reduction:** Reduced from 738 lines to 77 lines through modular design
- ✅ **Command Module Separation:** Individual command files for better maintainability
- ✅ **Shared Utility Layer:** DRY principles with config, display, and file utilities
- ✅ **Zero Breaking Changes:** Identical CLI behavior preserved during refactoring
- ✅ **Comprehensive Testing:** 24+ unit tests and integration tests with pytest
- ✅ **Production Validation:** Real data testing confirms identical functionality
- ✅ **Developer Experience:** Clean code structure for easy future development

### **Phase 1.8 Completed & Working - Enhanced Categories & Fixed Precedence:**
- ✅ **New "Recipe Components" Category:** Spice mixes, sauces, doughs, marinades properly categorized
- ✅ **New "Substitutions" Category:** Ingredient replacements (dairy-free buttermilk, egg substitutes) recognized as recipes
- ✅ **Fixed Precedence Logic:** Recipe categories now have higher precedence than "Cooking Reference" 
- ✅ **Enhanced Component Detection:** Recipe building blocks treated as recipes, not references
- ✅ **Comprehensive Category System:** 10 distinct categories covering all recipe and content types
- ✅ **Improved Conflict Resolution:** Clear rules for components vs. references vs. educational content

### **Phase 1.7 Completed & Working - Refined Categorization:**
- ✅ **Enhanced Recipe Detection:** Ingredient lists (smoothie ingredients, spice mixes) recognized as recipes
- ✅ **New "Cooking Reference" Category:** Food-related articles/references properly classified
- ✅ **Three-Tier Content Classification:** Not Recipe → Cooking Reference → Actual Recipes
- ✅ **Improved Prompt Logic:** Better handling of edge cases and cooking content types
- ✅ **Real-World Validation:** Based on systematic review feedback and database cleanup
- ✅ **Dynamic Review Interface:** HTML interface fully config-driven with auto-generated dropdowns

### **Phase 1.6 Completed & Working - Review System:**
- ✅ **Interactive HTML Review Interface:** Visual categorization review with filtering/sorting
- ✅ **CSV Export System:** Edit categorizations in spreadsheets with systematic import
- ✅ **Corrections Tracking:** JSON-based system for documenting and applying fixes
- ✅ **Review Summary Reports:** Statistical analysis of categorization quality
- ✅ **Issue-Focused Views:** Specialized exports for problem items only
- ✅ **Complete CLI Integration:** `review` and `apply-corrections` commands working

### **Phase 1.5 Completed & Working - Foundation:**
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

## Current Status: Production-Ready Analysis System

The system now provides a comprehensive, maintainable, and well-tested solution for recipe organization with:
- Complete categorization covering all cooking content types
- Refactored codebase with clean architecture
- Extensive testing framework ensuring reliability
- Production validation with real data

## Working CLI Commands

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

### Review System ✅
```bash
uv run python -m src.main review --html                    # Interactive HTML review
uv run python -m src.main review --csv --issues-only       # Export problem items
uv run python -m src.main apply-corrections --input fixes.csv  # Import corrections
```

### Testing Commands ✅
```bash
uv run pytest                        # Run all tests
uv run pytest tests/unit/           # Unit tests only
uv run pytest --cov=src             # With coverage
uv run pytest -m "not external"     # Exclude external dependencies
```

## Enhanced Reporting System ✅

```
data/processed/
├── analysis_report.json           # Standard categorization results
├── content_issues_report.json     # Non-recipes flagged for review
├── title_improvements.csv         # Only items needing title changes  
├── processing_summary.json        # Batch processing metrics and errors
└── review/                        # ✅ Review System Complete
    ├── review_report.html          # Interactive HTML review interface
    ├── categorization_review.csv   # Editable CSV for corrections
    ├── categorization_issues.csv   # CSV focused on problem items only
    ├── corrections.json            # Tracked corrections to apply
    └── review_summary.json         # Review session metrics and priorities
```

## Next Phase: Database Schema Enhancement ⏳ READY TO START

**Phase 2: Database Schema Enhancement**
**Goal:** Add enhanced properties to Notion database using Phase 1.9 analysis results

**Approach - Non-Disruptive Enhancement:**
- ✅ **Analysis System Complete:** Content quality and categorization working perfectly with refined accuracy
- ✅ **Enhanced Categories Ready:** Including "Cooking Reference" for content organization
- ✅ **Refactored Codebase:** Clean architecture ready for new features
- 🎯 **Add new optional properties:** All categories with refined precedence rules
- 🎯 **Create database views:** Filtered views for each category + content quality + cooking references
- 🎯 **Database backup:** Complete backup before schema changes

**Final Enhanced Schema (Phase 1.9 Analysis Ready):**
```yaml
Primary Category (single-select, optional):
  Not a Recipe (precedence 0), Breakfast (1), Desserts (2), Baking (3),
  Recipe Components (4), Substitutions (5), 
  Beef/Chicken/Pork/Seafood/Vegetarian (6), Sides & Appetizers (7),
  Cooking Reference (8)

Cuisine Type (single-select, optional):
  Mexican, Italian, Asian, American, Mediterranean, Indian, French, Other

Dietary Tags (multi-select, optional):
  Food Allergy Safe, Vegetarian, Vegan, Gluten-Free, Dairy-Free, 
  Low-Carb, Keto, Quick & Easy, One Pot, Make Ahead

Usage Tags (multi-select, optional):
  Favorite, Tried & Tested, Want to Try, Holiday/Special Occasion, 
  Family Recipe, Experimental

Content Quality (optional - from Phase 1.9):
  Content Summary (text), Proposed Title (text), Quality Score (1-5)
```

**Commands to Implement:**
- 🎯 `python -m src.main backup-database --database-id your_db_id`
- 🎯 `python -m src.main enhance-schema --add-properties`  
- 🎯 `python -m src.main create-views --database-id your_db_id`
- 🎯 `python -m src.main populate-categories --use-analysis-results`

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
- **pytest Testing Framework** with comprehensive unit and integration tests
- **Modular Architecture** with clean separation of concerns

### Refactored File Structure (Phase 1.9):
```
src/
├── main.py                         # 77 lines (was 738) - 90% reduction
├── commands/                       # Command modules
│   ├── __init__.py
│   ├── extract_cmd.py             # Extract command (~100 lines)
│   ├── test_cmd.py                # Test command (~65 lines)
│   ├── analyze_cmd.py             # Analyze command (~240 lines)
│   └── review_cmd.py              # Review commands (~120 lines)
├── utils/                         # NEW - Shared utilities
│   ├── __init__.py
│   ├── config_utils.py            # Configuration & connection utilities
│   ├── display_utils.py           # Rich console display functions
│   └── file_utils.py              # File I/O operations
├── notion_client/                 # Existing business logic (unchanged)
│   ├── client.py
│   ├── analyzer.py
│   ├── extractor.py
│   ├── profile_loader.py
│   ├── reviewer.py
│   └── config_loader.py
└── config.py                      # Configuration management
```

### Testing Infrastructure (Phase 1.9):
```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests (24 tests)
│   ├── test_config_utils.py       # Config utility tests
│   └── test_file_utils.py         # File utility tests
├── integration/                   # Integration tests
│   └── test_commands.py           # CLI command tests
└── TESTING.md                     # Comprehensive testing guide
```

### Error Handling & Safety Features:
- ✅ ID cleaning for Notion URLs with view parameters  
- ✅ Timeout controls for LLM calls (configurable per recipe)
- ✅ Individual recipe failure handling (doesn't crash whole analysis)
- ✅ Batch processing with configurable delays (rate limiting protection)
- ✅ Range specification for targeting problematic recipes
- ✅ Comprehensive progress tracking and error reporting
- ✅ Failed analysis tracking with recommendations
- ✅ **Automated Testing** ensuring reliability across changes

## Configuration (.env)
```
NOTION_TOKEN=your_notion_integration_token
NOTION_RECIPES_PAGE_ID=your_recipes_page_id
OPENAI_API_KEY=your_openai_key_for_analysis
LOG_LEVEL=INFO
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

### Enhanced Database Views + Page Hierarchy (Future)
- **Database views** for filtering and sorting (power users, quick access)
- **Page hierarchy** for visual browsing and discovery
- Multiple filtered/grouped database views without changing underlying data
- Organized page folders that mirror database categorization

### Safety Features
- Complete database backup before any changes
- `--dry-run` flags for all operations
- Rollback capabilities for categorization
- Incremental processing with resume functionality
- **Comprehensive testing** ensuring code reliability

### Developer Experience
- **Clean modular architecture** for easy maintenance
- **Comprehensive test suite** for confident changes
- **Utility functions** eliminating code duplication
- **Clear separation of concerns** between CLI, business logic, and utilities

The system is now **production-ready** with a solid foundation for Phase 2 database enhancement work.