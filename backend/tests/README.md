# EasyCFD Backend Tests

This directory contains all tests for the EasyCFD backend.

## Test Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py           # Shared pytest fixtures and configuration
├── README.md             # This file
├── test_safety.py        # Security validation tests (CRITICAL)
└── ... (more test files as the project grows)
```

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run only security tests
```bash
pytest -m security
```

### Run a specific test file
```bash
pytest tests/test_safety.py
```

### Run a specific test function
```bash
pytest tests/test_safety.py::TestCommandValidation::test_allowed_commands_pass
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage report
```bash
pytest --cov=easycfd_core --cov-report=html
```

## Test Categories

### Security Tests (`@pytest.mark.security`)
These tests validate security-critical functionality:
- Command whitelist validation
- Path traversal prevention
- Shell metacharacter detection
- Argument validation

**These tests must ALWAYS pass before merging code.**

### Integration Tests (`@pytest.mark.integration`)
Tests that validate multiple components working together.

### Slow Tests (`@pytest.mark.slow`)
Tests that take significant time to run. Skip with:
```bash
pytest -m "not slow"
```

## Test Requirements

### Dependencies
```bash
pip install pytest pytest-cov
```

### Environment
- Python 3.8 or higher
- The tests add `backend/` to `sys.path` automatically via `conftest.py`

## Writing New Tests

### Test File Naming
- Name test files as `test_*.py`
- Place in the `tests/` directory

### Test Class Naming
- Name test classes as `Test*`
- Group related tests in the same class

### Test Function Naming
- Name test functions as `test_*`
- Use descriptive names that explain what is being tested

### Example Test
```python
import pytest
from easycfd_core.validation import safety

class TestMyFeature:
    def test_feature_works(self):
        """Test that my feature works correctly."""
        result = safety.some_function("input")
        assert result == "expected_output"

    @pytest.mark.security
    def test_feature_rejects_dangerous_input(self):
        """Test that dangerous input is rejected."""
        with pytest.raises(ValueError):
            safety.some_function("../../../etc/passwd")
```

## Test Philosophy

1. **Security First**: All security-critical code must have comprehensive tests
2. **Clear Test Names**: Test names should explain what is being tested
3. **Docstrings**: Every test should have a docstring explaining its purpose
4. **Fail Fast**: Tests should fail immediately when validation fails
5. **No Mocking of Security**: Security validation logic should use real implementations

## Test Coverage Goals

- **Security modules**: 100% coverage required
- **Core logic**: 80%+ coverage target
- **Integration points**: Key workflows tested

## Continuous Integration

Security tests run automatically on:
- Every commit
- Every pull request
- Before deployment

**No code is merged if security tests fail.**

## Debugging Failed Tests

### View detailed output
```bash
pytest -vv --tb=long
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Run only failed tests
```bash
pytest --lf  # last failed
pytest --ff  # failed first, then rest
```

## Security Test Requirements

The `test_safety.py` file tests the following critical security functions:

1. **Command Whitelist** (`is_command_allowed`)
   - Only allows: blockMesh, checkMesh, icoFoam, simpleFoam, postProcess
   - Blocks all other commands

2. **Path Validation** (`is_path_safe`)
   - Prevents path traversal with `..`
   - Ensures paths are within workspace
   - Blocks absolute paths outside workspace

3. **Argument Validation** (`are_arguments_safe`)
   - Checks for shell metacharacters
   - Validates path arguments
   - Prevents command injection

4. **Full Validation** (`validate_command_execution`)
   - Validates command, arguments, and case directory together
   - Provides defense in depth

## Agent Notes

This test suite was created by Agent 3 (Test Specialist) as part of the EasyCFD project.

The tests assume Agent 1 (Backend Core Specialist) is implementing the actual `safety.py` module with these functions:
- `is_command_allowed(command: str) -> bool`
- `is_path_safe(path: str) -> bool`
- `are_arguments_safe(args: list[str]) -> bool`
- `validate_command_execution(command: str, args: list[str], case_dir: str) -> bool`
- `validate_command_or_raise(command: str) -> None`
- `validate_path_or_raise(path: str) -> None`

If the implementation differs, these tests should be updated accordingly.
