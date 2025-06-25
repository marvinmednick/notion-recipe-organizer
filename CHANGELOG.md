# Changelog

## [Phase 1.9] - 2025-06-25 - Pipeline Implementation & Modular Architecture

**Major Changes:**
- **Pipeline Command**: Added automated workflow command for chaining extract → analyze → review
- **Modular Architecture**: Refactored monolithic main.py (738 lines) into modular structure (77 lines) 
- **Direct Function Calls**: Replaced subprocess approach with direct function calls for better performance
- **Comprehensive Testing**: Added pytest framework with 40+ unit and integration tests
- **Shared Utilities**: Created utils/ layer implementing DRY principles across commands

**New Features:**
- `pipeline` command with profile support and global options
- Individual command modules in `src/commands/` directory
- Shared utility functions in `src/utils/` directory
- Integration tests for pipeline workflows
- Error handling with helpful restart guidance

**Performance Improvements:**
- 90% reduction in main.py complexity (738 → 77 lines)
- Eliminated subprocess overhead in pipeline execution
- Shared client connections and configuration context
- File-based data flow for debugging and resumability

**Testing Infrastructure:**
- 24 unit tests for utility functions
- 16 integration tests for CLI commands and pipeline
- Comprehensive test coverage with mocked external dependencies
- Real-world validation with actual recipe data

**Impact:** Complete workflow automation now available with clean, maintainable architecture

---

## [Phase 1.8] - 2025-06-20 - Enhanced Categories & Fixed Precedence

**Major Changes:**
- **New Categories**: Added "Recipe Components" for spice mixes, sauces, doughs, marinades
- **Substitutions Category**: Added dedicated category for ingredient replacements
- **Precedence Logic**: Fixed category precedence so recipes have higher priority than references
- **Enhanced Detection**: Improved recognition of recipe building blocks vs. reference materials

**Categorization Improvements:**
- Recipe components (spice mixes, marinades) now properly categorized as recipes
- Ingredient substitutions (dairy-free alternatives) recognized as recipes
- Cooking references maintain separate classification
- 10 distinct categories covering all recipe and content types

**Configuration Updates:**
- Updated conflict resolution rules for better category assignment
- Enhanced precedence system with clear hierarchy
- Improved LLM prompt for better component vs. reference distinction

**Impact:** Significantly improved categorization accuracy for edge cases and recipe components

---

## [Phase 1.7] - 2025-06-15 - Refined Categorization System

**Major Changes:**
- **Enhanced Recipe Detection**: Ingredient lists and spice mixes now recognized as recipes
- **Cooking Reference Category**: New category for food-related articles and reference materials
- **Three-Tier Classification**: Clear hierarchy from non-recipe → cooking reference → actual recipes
- **Dynamic Review Interface**: HTML interface now fully config-driven with auto-generated dropdowns

**Categorization Improvements:**
- Better handling of edge cases (smoothie ingredients, spice mix lists)
- Improved prompt logic for cooking content vs. actual recipes
- Systematic review feedback integration for real-world validation

**Impact:** More accurate categorization with better handling of cooking-related content

---

## [Phase 1.6] - 2025-06-10 - Review System Implementation

**Major Changes:**
- **Interactive HTML Review Interface**: Visual categorization review with filtering and sorting
- **CSV Export System**: Edit categorizations in spreadsheets with systematic import capability
- **Corrections Tracking**: JSON-based system for documenting and applying fixes
- **Review Analytics**: Statistical analysis of categorization quality and issues

**New Commands:**
- `review` command with multiple output formats
- `apply-corrections` command for importing CSV edits
- Issue-focused exports for efficient problem resolution

**Features:**
- Complete CLI integration for review workflows
- Review summary reports with quality metrics
- Specialized exports for problem items only

**Impact:** Manual review and correction workflow now fully integrated

---

## [Phase 1.5] - 2025-06-05 - Foundation & Analysis System

**Major Changes:**
- **Complete Project Setup**: Notion API integration and basic CLI structure
- **Database Extraction**: Full recipe data extraction from Notion databases
- **AI Categorization**: LLM-powered analysis using Azure OpenAI GPT-4
- **YAML Configuration**: Flexible, configurable categorization system
- **Statistical Analysis**: Basic recipe collection analysis and reporting

**Core Features:**
- Extract command for Notion database data retrieval
- Analyze command with configurable LLM analysis
- Test command for system validation
- Batch processing with timeout and error handling
- Range specification for targeted analysis

**Configuration System:**
- YAML-based categorization rules and profiles
- Multiple analysis profiles (testing, production, quick)
- Configurable batch processing and rate limiting
- Enhanced content quality analysis

**Reporting:**
- Content issues detection and reporting
- Title improvement suggestions
- Processing summaries with error tracking
- Statistical analysis of recipe collections

**Impact:** Complete foundation for recipe organization with AI-powered categorization

---

## [Phase 1.0-1.4] - Early Development

**Foundation Work:**
- Initial project setup and requirements analysis
- Notion API integration research and implementation
- Basic CLI structure with Click framework
- Azure OpenAI integration and prompt development
- Category system design and initial rule definitions

**Experimental Features:**
- Various approaches to recipe categorization
- Prompt engineering for LLM analysis
- Basic error handling and logging
- Initial configuration system design

**Impact:** Established core project foundation and proved feasibility of AI-powered recipe categorization

---

## Development Principles

Throughout all phases, the project has maintained:

- **Zero Breaking Changes**: CLI interface remains consistent across versions
- **Comprehensive Testing**: Each phase includes appropriate test coverage
- **Production Readiness**: All features are tested with real data before release
- **Modular Design**: Clean separation of concerns and extensible architecture
- **User-Focused**: CLI design prioritizes usability and clear feedback

## Version Numbering

- **Major Phases** (1.x): Significant feature additions or architectural changes
- **Minor Updates** (x.x): Bug fixes, small feature enhancements, configuration updates
- **Patch Releases** (x.x.x): Critical bug fixes and documentation updates