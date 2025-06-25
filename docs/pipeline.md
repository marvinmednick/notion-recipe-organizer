# Pipeline Workflows

The pipeline command enables automated workflows by chaining extract, analyze, and review commands together with shared configuration.

## Basic Pipeline Usage

### Full Workflow
```bash
# Complete recipe organization pipeline
uv run python -m src.main pipeline extract analyze review
```

### Partial Workflows
```bash
# Skip extraction (use existing data)
uv run python -m src.main pipeline analyze review

# Stop before review (just extract and analyze)
uv run python -m src.main pipeline extract analyze

# Single step (equivalent to running command directly)
uv run python -m src.main pipeline analyze
```

## Pipeline Options

### Global Options
Options that apply to all compatible pipeline steps:

```bash
# Profile-based configuration
uv run python -m src.main pipeline --profile testing extract analyze review

# Limit processing
uv run python -m src.main pipeline --limit 10 extract analyze review

# Dry run mode (where supported)
uv run python -m src.main pipeline --dry-run extract analyze

# Timeout for LLM calls
uv run python -m src.main pipeline --timeout 60 extract analyze review

# Quick mode (statistics only)
uv run python -m src.main pipeline --quick analyze review

# Database ID for extraction
uv run python -m src.main pipeline --database-id abc123 extract analyze review
```

### Option Inheritance
- `--profile`: Applies to all steps
- `--limit`: Applies to extract (as max-records) and analyze (as sample)
- `--timeout`: Applies to analyze step only
- `--dry-run`: Applies to extract step only
- `--quick`: Applies to analyze step only
- `--database-id`: Applies to extract step only

## Configuration Profiles

Profiles provide predefined settings for common use cases:

### Testing Profile
```bash
uv run python -m src.main pipeline --profile testing extract analyze review
```
- Extract: 10 records maximum
- Analyze: 10 recipes, 60s timeout, 1s batch delay
- Review: HTML format

### Production Profile
```bash
uv run python -m src.main pipeline --profile production extract analyze review
```
- Extract: No record limit
- Analyze: 50 batch size, 1s delay, 45s timeout
- Review: HTML format

### Quick Profile
```bash
uv run python -m src.main pipeline --profile quick analyze review
```
- Analyze: Statistics only, no LLM calls
- Review: HTML format

### Small Sample Profile
```bash
uv run python -m src.main pipeline --profile small_sample extract analyze review
```
- Extract: 5 records maximum
- Analyze: 5 recipes, 30s timeout, 10 batch size
- Review: HTML format

## Data Flow

The pipeline uses file-based data flow for reliability and debugging:

```
1. Extract Step
   └── Saves to: data/raw/recipes.json
   
2. Analyze Step
   └── Reads from: data/raw/recipes.json
   └── Saves to: data/processed/analysis_report.json
   └── Saves to: data/processed/title_improvements.csv
   └── Saves to: data/processed/processing_summary.json
   
3. Review Step
   └── Reads from: data/processed/analysis_report.json
   └── Saves to: data/processed/review/review_report.html
   └── Saves to: data/processed/review/*.csv (if --csv)
```

## Error Handling

### Stop on First Error
The pipeline stops at the first failed step:

```bash
$ uv run python -m src.main pipeline extract analyze review

🔄 Running Pipeline: extract → analyze → review

📋 Step 1/3: Extract
✅ Extraction completed successfully

📋 Step 2/3: Analyze  
❌ Pipeline failed at step 'analyze': Connection timeout

💡 Fix the error and restart with: pipeline analyze review
```

### Recovery and Restart
Since data is saved between steps, you can resume from any point:

```bash
# Fix the issue, then restart from the failed step
uv run python -m src.main pipeline analyze review
```

## Advanced Workflows

### Development Workflow
```bash
# Extract sample data
uv run python -m src.main pipeline --profile small_sample extract

# Test analysis with different settings
uv run python -m src.main pipeline --quick analyze review
uv run python -m src.main pipeline --timeout 90 analyze review

# Full analysis when ready
uv run python -m src.main pipeline analyze review
```

### Production Workflow
```bash
# Full extraction and analysis
uv run python -m src.main pipeline --profile production extract analyze

# Generate multiple review formats
uv run python -m src.main review --html
uv run python -m src.main review --csv --issues-only
```

### Incremental Analysis
```bash
# Extract new data
uv run python -m src.main extract

# Analyze specific range
uv run python -m src.main analyze --range 100-150

# Review just the new results
uv run python -m src.main review --html
```

## Performance Considerations

### Pipeline Efficiency
- **Direct Function Calls**: No subprocess overhead
- **Shared Context**: Configuration and connections reused
- **Memory Management**: Data released between steps via file I/O
- **Error Recovery**: Can restart from any step without reprocessing

### Batch Processing
```bash
# Large datasets - optimize batch processing
uv run python -m src.main pipeline --profile production extract analyze review

# Quick testing - small batches
uv run python -m src.main pipeline --profile small_sample extract analyze review
```

### Resource Management
- **API Rate Limiting**: Controlled through batch-delay settings
- **Memory Usage**: File-based flow prevents memory accumulation
- **Timeout Handling**: Configurable per-recipe timeouts prevent hanging
- **Connection Reuse**: Shared Notion and OpenAI clients

## Troubleshooting

### Common Issues

**Pipeline fails at extract:**
```bash
# Check configuration
uv run python -m src.main --config-check

# Test with dry run
uv run python -m src.main pipeline --dry-run extract
```

**Pipeline fails at analyze:**
```bash
# Check if extract data exists
ls data/raw/recipes.json

# Try quick mode first
uv run python -m src.main pipeline --quick analyze

# Increase timeout
uv run python -m src.main pipeline --timeout 90 analyze
```

**Pipeline fails at review:**
```bash
# Check if analysis data exists
ls data/processed/analysis_report.json

# Try review directly
uv run python -m src.main review --html
```

### Debugging Tips

1. **Check intermediate files** between steps
2. **Use dry-run mode** for extract testing
3. **Start with small samples** (--profile small_sample)
4. **Review processing_summary.json** for analysis errors
5. **Use quick mode** to test pipeline flow without LLM calls

## Best Practices

1. **Start Small**: Use `--profile small_sample` for initial testing
2. **Profile-Driven**: Use profiles instead of manual option combinations
3. **Error Recovery**: Take advantage of file-based resumability
4. **Batch Optimization**: Adjust batch sizes based on your API limits
5. **Regular Validation**: Use review interfaces to verify results
6. **Incremental Processing**: Process new recipes in ranges rather than full re-analysis