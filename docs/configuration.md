# Configuration Guide

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# Notion Integration
NOTION_TOKEN=secret_your_notion_integration_token
NOTION_RECIPES_PAGE_ID=your_recipes_database_id

# Azure OpenAI Configuration  
OPENAI_API_KEY=your_azure_openai_key
OPENAI_API_BASE=https://your-resource.openai.azure.com/
OPENAI_API_VERSION=2025-04-01-preview
OPENAI_DEPLOYMENT_NAME=gpt-4.1

# Optional Settings
LOG_LEVEL=INFO
```

### Configuration Validation

Test your configuration:
```bash
uv run python -m src.main --config-check
```

## Analysis Profiles

Profiles provide predefined settings for different use cases. Located in `config/analysis_profiles.yaml`.

### Available Profiles

#### `testing` - Development and Testing
```yaml
extract:
  records: 10                    # Extract only 10 recipes
analyze:
  use_llm: true
  include_content_review: true
  recipes: 10                    # Analyze 10 recipes  
  timeout: 60                    # 60 second timeout per recipe
  batch_delay: 1                 # 1 second between batches
review:
  format: html
```

**Usage:**
```bash
uv run python -m src.main analyze --profile testing
uv run python -m src.main pipeline --profile testing extract analyze review
```

#### `production` - Optimized for Large Datasets
```yaml
extract:
  records: null                  # No limit
analyze:
  use_llm: true
  include_content_review: true
  batch_size: 50                 # Process 50 recipes per batch
  batch_delay: 1                 # Fast processing
  timeout: 45                    # 45 second timeout
review:
  format: html
```

**Usage:**
```bash
uv run python -m src.main analyze --profile production
```

#### `quick` - Statistics Only
```yaml
analyze:
  use_llm: false                 # Skip LLM analysis
  include_content_review: false  # Skip content review
review:
  format: html
```

**Usage:**
```bash
uv run python -m src.main analyze --profile quick
```

#### `small_sample` - Quick Testing
```yaml
extract:
  records: 5                     # Just 5 recipes
analyze:
  use_llm: true
  include_content_review: true
  recipes: 5
  timeout: 30
  batch_size: 10
review:
  format: html
```

#### `content_cleanup` - Focus on Content Quality
```yaml
analyze:
  use_llm: true
  include_content_review: true
  batch_size: 15                 # Smaller batches for careful analysis
  batch_delay: 3                 # Slower processing
  timeout: 45
review:
  format: csv                    # CSV for easy editing
  issues_only: true              # Only problematic items
```

### Profile Shortcuts

Short aliases for common profiles:

```bash
# These are equivalent
uv run python -m src.main analyze --profile quick
uv run python -m src.main analyze --quick

# These are equivalent  
uv run python -m src.main analyze --profile small_sample
uv run python -m src.main analyze --sample 5
```

## Command-Specific Configuration

### Extract Command Options

```bash
# Database and output
--database-id TEXT              # Notion database ID
--output PATH                   # Output file path
--max-records INTEGER           # Maximum records to extract

# Operation modes
--dry-run                       # Show what would be extracted
```

### Analyze Command Options

```bash
# Input/output
--input PATH                    # Input JSON file  
--output PATH                   # Output directory

# Analysis control
--profile TEXT                  # Use configuration profile
--quick                         # Statistics only, no LLM
--sample INTEGER                # Analyze N recipes only

# Range specification
--start-index INTEGER           # Start from recipe index
--end-index INTEGER             # End at recipe index  
--range TEXT                    # Range like "50-100"

# Processing control
--batch-size INTEGER            # Recipes per batch
--batch-delay FLOAT             # Seconds between batches
--timeout INTEGER               # Timeout per LLM call

# Feature toggles
--use-llm / --no-llm           # Enable/disable LLM analysis
--include-content-review / --no-content-review  # Content quality analysis
```

### Review Command Options

```bash
# Input/output
--input PATH                    # Input analysis file
--output PATH                   # Output directory

# Output formats
--html                          # Generate HTML review interface
--csv                           # Export to CSV
--summary                       # Generate summary report
--issues-only                   # Focus on problem items only
```

### Pipeline Command Options

```bash
# Global options (apply to compatible steps)
--profile TEXT                  # Configuration profile
--database-id TEXT              # For extract and backup-database steps
--limit INTEGER                 # Records/recipes to process
--timeout INTEGER               # For analyze step
--dry-run                       # For extract and enhance-database steps
--quick                         # For analyze step
--sample INTEGER                # For enhance-database testing
```

### Phase 2: Database Enhancement Command Options

#### `backup-database` Command
```bash
--database-id TEXT              # Notion database ID
--verify                        # Verify backup integrity
--output-dir PATH               # Backup directory (default: data/backups/)
```

#### `enhance-database` Command  
```bash
--use-analysis-results          # Apply AI categorization data
--sample INTEGER                # Test with N recipes only
--dry-run                       # Show changes without applying
--database-id TEXT              # Target database ID
```

## Category Configuration

### Category Definitions (`config/categories.yaml`)

Defines available recipe categories with descriptions:

```yaml
categories:
  "Not a Recipe":
    description: "Non-recipe content"
    precedence: 0
    
  "Breakfast":
    description: "Breakfast dishes and morning foods"
    precedence: 1
    
  "Recipe Components":
    description: "Spice mixes, sauces, doughs, marinades"
    precedence: 4
    
  "Substitutions":
    description: "Ingredient replacements and alternatives"
    precedence: 5
```

### Conflict Resolution (`config/conflict_rules.yaml`)

Handles category precedence and conflicts:

```yaml
precedence_rules:
  # Higher numbers = higher precedence
  "Recipe Components": 4
  "Substitutions": 5
  "Beef": 6
  "Cooking Reference": 8

conflict_resolution:
  # Specific conflict handling
  - categories: ["Breakfast", "Baking"]
    rule: "breakfast_precedence"
    winner: "Breakfast"
```

### Cuisine Types (`config/cuisines.yaml`)

Available cuisine classifications:

```yaml
cuisine_types:
  - Mexican
  - Italian  
  - Asian
  - American
  - Mediterranean
  - Indian
  - French
  - Other
```

### Dietary Tags (`config/dietary_tags.yaml`)

Available dietary restriction tags:

```yaml
dietary_tags:
  food_safety:
    - "Food Allergy Safe"
  
  diet_types:
    - "Vegetarian"
    - "Vegan"
    - "Gluten-Free"
    - "Dairy-Free"
    - "Low-Carb"
    - "Keto"
    
  convenience:
    - "Quick & Easy"
    - "One Pot"
    - "Make Ahead"
```

## LLM Prompt Configuration

### Base Prompt (`config/prompts/base_prompt.txt`)

The core prompt used for LLM categorization. This defines:
- Categorization instructions
- Output format requirements
- Category definitions and precedence rules
- Quality scoring criteria

**Customization:**
Edit this file to adjust how the AI categorizes recipes. Changes take effect immediately for new analysis runs.

## Advanced Configuration

### Custom Profiles

Add new profiles to `config/analysis_profiles.yaml`:

```yaml
profiles:
  my_custom_profile:
    description: "Custom settings for my workflow"
    extract:
      records: 25
    analyze:
      use_llm: true
      batch_size: 10
      timeout: 30
    review:
      format: html
      csv: true
```

### Profile Inheritance

Profiles can reference shared settings:

```yaml
# Global defaults
flag_defaults:
  analyze:
    use_llm: true
    batch_size: 20
    timeout: 30

# Profile overrides only specific settings
profiles:
  fast_analysis:
    analyze:
      batch_size: 50    # Override default
      batch_delay: 0.5  # Add new setting
    # use_llm and timeout inherit from defaults
```

### Pipeline-Specific Settings

Configure pipeline behavior:

```yaml
pipeline_settings:
  default_steps: [extract, analyze, review]
  error_handling: stop_on_failure
  progress_reporting: true
```

## Troubleshooting Configuration

### Common Issues

**"Configuration Error" messages:**
1. Check `.env` file exists and has correct variable names
2. Verify API keys are valid and not expired
3. Ensure Notion database ID is correct format

**Profile not found:**
1. Check spelling of profile name
2. Verify profile exists in `config/analysis_profiles.yaml`
3. Use `--help` to see available profiles

**LLM timeout issues:**
1. Increase `timeout` setting in profile or command line
2. Reduce `batch_size` for more reliable processing
3. Increase `batch_delay` to avoid rate limits

### Validation Commands

```bash
# Test configuration
uv run python -m src.main --config-check

# Test Notion connection
uv run python -m src.main test

# List available profiles
uv run python -m src.main analyze --help

# Test with dry run
uv run python -m src.main extract --dry-run --max-records 1
```