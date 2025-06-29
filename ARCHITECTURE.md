# Architecture Overview

## High-Level Design

The Notion Recipe Organizer follows a **modular CLI architecture** with clean separation of concerns between user interface, business logic, and shared utilities.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Commands  │────│  Utility Layer  │────│ Business Logic  │
│   (commands/)   │    │   (utils/)      │    │(notion_client/) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │              ┌─────────────────┐              │
        └──────────────│  Configuration  │──────────────┘
                       │   (config/)     │
                       └─────────────────┘
```

## Directory Structure

```
notion-recipe-organizer/
├── src/
│   ├── main.py                    # CLI entry point (77 lines)
│   ├── config.py                  # Configuration management
│   ├── pipeline.py                # Pipeline orchestration
│   │
│   ├── commands/                  # Individual command modules
│   │   ├── extract_cmd.py         # Extract command (~100 lines)
│   │   ├── analyze_cmd.py         # Analyze command (~240 lines)
│   │   ├── review_cmd.py          # Review commands (~120 lines)
│   │   ├── test_cmd.py            # Test command (~65 lines)
│   │   ├── pipeline_cmd.py        # Pipeline command (~70 lines)
│   │   ├── backup_database_cmd.py # Database backup command (Phase 2)
│   │   └── enhance_database_cmd.py # Database enhancement command (Phase 2)
│   │
│   ├── utils/                     # Shared utility functions
│   │   ├── config_utils.py        # Config validation & connections
│   │   ├── display_utils.py       # Rich console display functions
│   │   └── file_utils.py          # File I/O operations
│   │
│   └── notion_client/             # Business logic layer
│       ├── client.py              # Notion API wrapper
│       ├── extractor.py           # Recipe extraction logic
│       ├── analyzer.py            # AI categorization engine
│       ├── reviewer.py            # Review interface generation
│       ├── profile_loader.py      # Configuration profile management
│       └── config_loader.py       # YAML configuration loading
│
├── config/                        # Configuration files
│   ├── analysis_profiles.yaml     # Analysis profiles & settings
│   ├── categories.yaml            # Recipe categorization rules
│   ├── conflict_rules.yaml        # Category precedence rules
│   └── prompts/
│       └── base_prompt.txt        # LLM categorization prompt
│
├── tests/                         # Testing framework
│   ├── conftest.py                # Shared fixtures
│   ├── unit/                      # Unit tests (24 tests)
│   └── integration/               # Integration tests (16 tests)
│
└── data/                          # Output directory
    ├── raw/                       # Extracted data
    └── processed/                 # Analysis results
```

## Component Responsibilities

### CLI Layer (`src/commands/`)
- **Purpose**: User interaction and command parsing
- **Responsibilities**:
  - Input validation and option handling
  - Progress display and user feedback  
  - Error presentation and help text
  - Parameter conversion for business logic

### Utility Layer (`src/utils/`)
- **Purpose**: Shared cross-cutting concerns
- **Responsibilities**:
  - Configuration validation and connection testing
  - Common file operations and path utilities
  - Reusable display functions with Rich formatting
  - DRY principle implementation

### Business Logic (`src/notion_client/`)
- **Purpose**: Core application functionality
- **Responsibilities**:
  - Notion API integration and data extraction
  - AI-powered recipe analysis and categorization
  - LLM integration with Azure OpenAI
  - Data transformation and validation
  - Review interface generation

### Configuration (`config/`)
- **Purpose**: Declarative system configuration
- **Responsibilities**:
  - YAML-based categorization rules and profiles
  - Analysis settings and LLM prompts
  - Category precedence and conflict resolution
  - Extensible rule definitions

### Pipeline Orchestration (`src/pipeline.py`)
- **Purpose**: Workflow automation and coordination
- **Responsibilities**:
  - Command chaining with shared context
  - Profile-based configuration propagation
  - Error handling and recovery guidance
  - File-based data flow management

## Key Design Decisions

### 1. Direct Function Calls vs. Subprocess
- **Decision**: Use direct function calls in pipeline
- **Rationale**: Better performance, error handling, and debugging
- **Alternative Rejected**: Subprocess approach (too much overhead)

### 2. File-Based Data Flow
- **Decision**: Commands communicate through files (data/raw/, data/processed/)
- **Rationale**: Enables debugging, resumability, and independent testing
- **Alternative Rejected**: In-memory data passing (too complex for CLI tool)

### 3. Modular Command Architecture
- **Decision**: Separate command modules in commands/ directory
- **Rationale**: Single responsibility, easier maintenance, testability
- **Result**: 90% reduction in main.py complexity (738 → 77 lines)

### 4. Shared Utility Layer
- **Decision**: Extract common patterns into utils/ modules
- **Rationale**: DRY principles, consistent patterns, easier testing
- **Benefits**: Reduced code duplication, centralized error handling

## Data Flow

### Phase 1: Extract → Analyze → Review Pipeline
```
1. Extract Command
   └── notion_client/extractor.py
       └── Pulls recipes from Notion API
           └── Saves to data/raw/recipes.json

2. Analyze Command  
   └── notion_client/analyzer.py
       └── Loads data/raw/recipes.json
       └── Processes with Azure OpenAI
           └── Saves to data/processed/*.json

3. Review Command
   └── notion_client/reviewer.py
       └── Loads data/processed/analysis_report.json
           └── Generates HTML/CSV in data/processed/review/
```

### Phase 2: Database Enhancement Pipeline
```
1. Backup Database Command
   └── notion_client/backup.py (planned)
       └── Downloads complete database schema & data
           └── Saves to data/backups/database_backup_[timestamp].json
           └── Creates rollback instructions

2. Enhance Database Command
   └── notion_client/enhancer.py (planned)
       └── Validates backup exists
       └── Reads data/processed/analysis_report.json
       └── Modifies Notion database schema (adds properties)
       └── Populates categorization data from AI analysis
       └── Creates filtered database views
           └── Saves to data/processed/enhancement_report.json
```

### Configuration Flow
```
1. Profile Selection (--profile testing)
   └── profile_loader.py loads analysis_profiles.yaml
       └── Merges with command-line options
           └── Creates execution context
               └── Passes to business logic
```

## Testing Architecture

### Test Categories
- **Unit Tests** (24 tests): Fast tests for utility functions with mocks
- **Integration Tests** (16 tests): CLI command testing with mocked external services
- **External Tests** (marked): Optional real API testing for validation

### Testing Strategy
- **Mock External Dependencies**: Notion API, OpenAI API calls mocked
- **Temporary File Handling**: All file operations use temporary directories
- **CLI Testing**: Click testing utilities for command interface validation
- **Fixture Sharing**: Common test data and configuration in conftest.py

## Performance Characteristics

- **Main.py Complexity**: 90% reduction (738 → 77 lines)
- **Memory Efficiency**: File-based data flow releases memory between steps
- **API Efficiency**: Shared client connections, configurable rate limiting
- **Test Speed**: Unit tests run in < 1 second, full suite in < 3 seconds
- **Pipeline Overhead**: Minimal - direct function calls vs. subprocess elimination

## Extensibility Points

1. **New Commands**: Add modules to commands/ directory
2. **New Utilities**: Extend utils/ with additional shared functions  
3. **New Profiles**: Add configurations to analysis_profiles.yaml
4. **New Categories**: Extend categories.yaml and conflict_rules.yaml
5. **New Tests**: Add to appropriate unit/ or integration/ directories

The architecture supports easy addition of new functionality while maintaining clean separation of concerns and comprehensive test coverage.