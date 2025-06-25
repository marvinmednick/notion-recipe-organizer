# Testing Guide

## Overview

This project uses pytest for testing with comprehensive unit and integration tests.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual functions
│   ├── test_config_utils.py # Tests for config utilities
│   ├── test_file_utils.py   # Tests for file utilities
│   └── test_display_utils.py # Tests for display utilities
├── integration/             # Integration tests for full commands
│   └── test_commands.py     # Tests for CLI commands
└── fixtures/                # Test data and fixtures
```

## Running Tests

### All Tests
```bash
uv run pytest
```

### Unit Tests Only
```bash
uv run pytest tests/unit/ -m unit
```

### Integration Tests Only
```bash
uv run pytest tests/integration/ -m integration
```

### With Coverage
```bash
uv run pytest --cov=src --cov-report=html
```

### Excluding External Dependencies
```bash
uv run pytest -m "not external"
```

## Test Categories

### Markers
- `unit`: Fast unit tests for individual functions
- `integration`: Tests for full CLI commands
- `slow`: Tests that take more than a few seconds
- `external`: Tests requiring external APIs (Notion, OpenAI)

### Test Types

1. **Unit Tests**: Test individual utility functions with mocks
   - Config validation
   - File operations
   - Display utilities
   - Data processing

2. **Integration Tests**: Test CLI commands end-to-end
   - Command help text
   - Dry-run functionality
   - Mocked external services
   - Error handling

3. **External Tests**: Test with real services (optional)
   - Real Notion API calls
   - Real OpenAI API calls
   - Full pipeline tests

## Mocking Strategy

### External Services
- Notion API calls are mocked using `unittest.mock`
- OpenAI API calls are mocked
- File system operations use temporary directories

### Test Data
- Sample recipe data provided in fixtures
- Temporary files for testing file operations
- Mock configuration objects

## Adding New Tests

### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch
from src.utils.your_module import your_function

def test_your_function():
    # Arrange
    mock_dependency = Mock()
    mock_dependency.method.return_value = "expected"
    
    # Act
    with patch('src.utils.your_module.dependency', mock_dependency):
        result = your_function("input")
    
    # Assert
    assert result == "expected"
    mock_dependency.method.assert_called_once_with("input")
```

### Integration Test Example
```python
from click.testing import CliRunner
from src.main import cli

def test_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['command', '--option', 'value'])
    
    assert result.exit_code == 0
    assert "expected output" in result.output
```

## Continuous Integration

Tests are designed to run in CI environments with:
- No external dependencies by default
- Mocked services
- Temporary file handling
- Fast execution

## Coverage Targets

- **Unit Tests**: >90% coverage for utility modules
- **Integration Tests**: All CLI commands covered
- **Critical Paths**: 100% coverage for data processing

## Running Specific Test Groups

```bash
# Fast tests only (unit tests)
uv run pytest -m "unit and not slow"

# All tests except external dependencies
uv run pytest -m "not external"

# Integration tests with coverage
uv run pytest tests/integration/ --cov=src

# Verbose output with detailed failures
uv run pytest -v --tb=long

# Run specific test file
uv run pytest tests/unit/test_file_utils.py

# Run specific test method
uv run pytest tests/unit/test_file_utils.py::TestFileUtils::test_load_json_file_success
```