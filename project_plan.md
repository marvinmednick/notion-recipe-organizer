# Notion Recipe Organizer - Project Summary & Context

## Problem Statement

**Current Situation:**
- User has a Notion workspace with a "recipes" collection that is actually a **Notion DATABASE** (not pages)
- Each recipe is a database record/page with schema: Name, Created, Updated, Tags, URL
- Current database has ~X recipes (exact count from extraction)
- Tags field is mostly empty and inconsistently used (a few have "Food Allergy Safe" concept)
- User saves recipes via web clipper/browser extension and relies on global search
- **Data Successfully Extracted:** Complete database export completed to `data/raw/recipes.json`

**Real-World Discoveries (New):**
- **Non-recipe content:** Items like books accidentally saved to recipe database
- **Poor titles:** Many recipes have unclear or unhelpful titles that need improvement
- **Content variety:** Collection includes various content types that need different handling
- **CLI complexity:** Command-line flags becoming unwieldy, need progressive complexity system

**Decision:** Enhance analysis to include content quality assessment and redesign CLI for usability

## Major Discoveries & Evolved Requirements

### 1. Real Usage Patterns
**Discovery:** User has recipes that fall into different usage categories:
- **Frequently used favorites** (make monthly+)
- **Tried and tested** (made successfully before)
- **Collected but unused** (e.g., multiple variations of the same dish)
- **Want to try** (saved for future)

**Decision:** Need usage-based tags in addition to content-based categorization

### 2. Configurable Categorization System Required
**Discovery:** Initial hardcoded categories in LLM prompts are not maintainable
**Evolution:** Built comprehensive YAML-based configuration system with:
- Separate config files for different tag types
- Detailed criteria and examples for each category
- Conflict resolution rules
- Template-based prompt generation

### 3. Successful Technical Implementation
**Current Status:** ✅ Phase 1 ~95% complete
- Database extraction working (with ID cleaning for view parameters)
- Basic analysis completed  
- LLM sample analysis successful
- Configurable categorization system designed

## Key Discoveries & Decisions

### 1. Database vs Page Structure
**Discovery:** User's recipes are in a Notion database, not a page hierarchy
**Decision:** Work with the existing database structure rather than migrating to pages
**Reasoning:** Databases are actually better for recipe management (filtering, sorting, structured data)

### 2. Workflow Preservation
**Decision:** Maintain user's current save-recipe workflow without disruption
**Reasoning:** User likes the simplicity of save-and-search; adding friction would hurt adoption
**Implementation:** New fields are optional with smart defaults; categorization happens separately

### 5. Progressive Complexity CLI System (To Implement)

**Discovery:** Current CLI is becoming unwieldy with too many flags
**Solution:** Layer-based command system with smart defaults

**CLI Evolution:**
```bash
# Current (complex):
uv run python -m src.main analyze --use-llm --include-content-review --batch-size 20 --batch-delay 3 --timeout 30

# New (simple defaults):
uv run python -m src.main analyze                    # Smart defaults do the right thing
uv run python -m src.main analyze --sample 5         # Quick test mode
uv run python -m src.main analyze --profile testing  # Config-driven
```

**Progressive Layers:**
1. **Smart defaults** - "just works" with reasonable settings
2. **Quick shortcuts** - common variations (`--sample`, `--quick`, `--production`)  
3. **Configuration profiles** - reusable settings in YAML files
4. **Individual overrides** - any setting can be customized

### 6. Enhanced Content Analysis (To Implement)

**New Analysis Capabilities:**
```json
{
  // Standard categorization (existing)
  "primary_category": "Not a Recipe",  // NEW category for non-recipes
  "cuisine_type": "Other",
  "dietary_tags": [],
  
  // NEW content quality analysis
  "content_summary": "Book about kitchen equipment, not a recipe",
  "title_needs_improvement": true,
  "proposed_title": "Kitchen Equipment Guide", 
  "is_recipe": false,
  "quality_score": 2
}
```

**Enhanced Reporting:**
- **Content issues report** - Non-recipes flagged for review/removal
- **Title improvements report** - Only items needing title changes  
- **Quality assessment** - Overall content scoring and recommendations

### 4. Dual Organization System
**Decision:** Implement both database views AND browseable page hierarchy
**Reasoning:** 
- Database views: Power filtering, sorting, complex queries
- Page hierarchy: Visual browsing, mobile-friendly, intuitive navigation
- Different users/scenarios benefit from different access patterns

### 5. Phased Implementation Approach
**Decision:** Build incrementally with non-disruptive phases
**Reasoning:** Allows testing, validation, and maintains current workflow throughout development

## Current Technical Status (Phase 1.5 Complete!)

### ✅ Fully Production Ready:
- **Project Setup:** UV environment, PyYAML dependency, all dependencies working
- **Notion Integration:** Database operations with ID cleaning (v2)
- **Data Extraction:** Complete database successfully extracted and analyzed
- **Enhanced Analysis Engine:** Content quality assessment + LLM categorization working
- **Azure OpenAI:** gpt-4.1 with API version 2025-04-01-preview
- **YAML Configuration:** Complete categorization rules, conflict resolution, prompt templates
- **Progressive CLI:** Smart defaults, shortcuts, profiles, individual overrides
- **Enhanced Reporting:** Specialized reports for content issues and title improvements
- **Content Quality:** Non-recipe detection, title evaluation, quality scoring

### Production-Ready Commands (All Working):
```bash
# Smart defaults - comprehensive analysis  
uv run python -m src.main analyze

# Quick shortcuts
uv run python -m src.main analyze --quick            # Stats only
uv run python -m src.main analyze --sample 5         # Test 5 recipes
uv run python -m src.main analyze --range 50-100     # Specific range

# Configuration profiles
uv run python -m src.main analyze --profile testing     # 10 recipes, 60s timeout
uv run python -m src.main analyze --profile production  # 50 batch, optimized

# Individual overrides  
uv run python -m src.main analyze --sample 5 --timeout 90 --no-content-review
uv run python -m src.main analyze --profile production --batch-size 10
```

### Enhanced Analysis Results (Working):
- **Content Quality Detection:** Identifies non-recipe items (books, articles)
- **Title Improvement Suggestions:** Recommends better titles for unclear ones
- **Quality Scoring:** Rates recipes 1-5 for usefulness
- **Comprehensive Categorization:** Including "Not a Recipe" category
- **Specialized Reports:** Separate outputs for different review purposes

### File Status & Versions (All Complete & Tested):
```
✅ config.py (v8) - Azure OpenAI configured  
✅ notion_client/client.py (v2) - Database ops + ID cleaning
✅ main.py (v7) - Progressive complexity CLI working
✅ notion_client/analyzer.py (v2) - Enhanced analysis engine working
✅ notion_client/config_loader.py (v1) - Template engine working
✅ notion_client/profile_loader.py (v1) - Profile system working
✅ config/*.yaml (v2) - Enhanced categorization system with "Not a Recipe"
✅ config/analysis_profiles.yaml (v1) - Complete profile system
✅ config/prompts/base_prompt.txt (v1) - Enhanced LLM prompt template
```

## Implementation Phases

### Phase 1: Data Discovery & Analysis
- Extract current database records
- Analyze existing structure and tag usage
- LLM-powered categorization analysis

### Phase 2: Schema Enhancement & Preparation
- Design enhanced database schema
- Create migration preview
- Database backup for safety

### Phase 3: Database Enhancement (Non-Disruptive)
- Add new optional properties to existing database
- Create organized database views
- Preserve existing workflow

### Phase 4: Batch Categorization Assistant + Page Organization
- Build categorization assistant for processing recipes in batches
- Create browseable page hierarchy
- Dual organization: database properties + page folders

## Key Requirements & Constraints

**Must Preserve:**
- Current recipe saving workflow (web clipper → database)
- All existing recipe data and URLs
- Global search functionality
- Simplicity of daily use

**Must Add:**
- Systematic categorization for better discovery
- Food allergy-safe recipe identification
- Multiple ways to browse/find recipes
- Batch organization capabilities

**Technical Requirements:**
- WSL environment
- Existing Notion integration token
- Azure OpenAI access
- CLI-based tooling

## Success Criteria

1. **Workflow Unchanged:** User can save recipes exactly as before
2. **Better Organization:** Clear categorization with multiple browsing methods
3. **Food Allergy Support:** Easy filtering for daughter's dietary needs
4. **Flexible Access:** Both power-user database views and casual page browsing
5. **Maintainable:** Easy to categorize new recipes when convenient

## Current Status

- Project structure designed and approved
- Basic Notion API connection working
- Database structure discovered and analyzed
- Enhanced schema planned with hybrid approach
- Ready to begin Phase 1: Database extraction and analysis

## Next Steps

1. Update code to handle database operations instead of page operations
2. Extract current database records for analysis
3. Implement LLM-powered categorization analysis
4. Build categorization assistant with dual organization system
