"""
Tests for MCP Codex Worker validator

These tests verify that the security validator correctly identifies
dangerous patterns and rejects unsafe code.
"""

import pytest

from mcp.codex_worker.validator import validate_generated_code


class TestForbiddenPatterns:
    """Test detection of forbidden patterns."""

    def test_shell_true_is_rejected(self):
        """subprocess with shell=True must be rejected."""
        code = """
import subprocess
subprocess.run("ls", shell=True)
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert not result["valid"]
        assert any("shell=True" in error.lower() for error in result["errors"])

    def test_os_system_is_rejected(self):
        """os.system() calls must be rejected."""
        code = """
import os
os.system("rm -rf /")
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert not result["valid"]
        assert any("os.system" in error.lower() for error in result["errors"])

    def test_eval_is_rejected(self):
        """eval() calls must be rejected."""
        code = """
user_input = input()
result = eval(user_input)
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert not result["valid"]
        assert any("eval" in error.lower() for error in result["errors"])

    def test_exec_is_rejected(self):
        """exec() calls must be rejected."""
        code = """
code_str = "print('hello')"
exec(code_str)
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert not result["valid"]
        assert any("exec" in error.lower() for error in result["errors"])

    def test_path_traversal_is_rejected(self):
        """Path traversal patterns must be rejected."""
        code = """
import os
file_path = "../../../etc/passwd"
with open(file_path) as f:
    data = f.read()
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert not result["valid"]
        assert any("../" in error for error in result["errors"])


class TestSafeCode:
    """Test that safe code passes validation."""

    def test_safe_subprocess_is_allowed(self):
        """subprocess without shell=True is allowed."""
        code = """
import subprocess
result = subprocess.run(["ls", "-la"], capture_output=True, text=True)
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert result["valid"]
        # Should have a warning about subprocess usage
        assert any("subprocess" in warning.lower() for warning in result["warnings"])

    def test_safe_file_operations_are_allowed(self):
        """Normal file operations are allowed."""
        code = """
import pathlib

def read_config(path: str) -> dict:
    config_path = pathlib.Path(path)
    with open(config_path) as f:
        return json.load(f)
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert result["valid"]

    def test_pydantic_schema_passes(self):
        """Valid Pydantic schema should pass."""
        code = """
from pydantic import BaseModel, Field

class CasePlan(BaseModel):
    case_name: str = Field(..., description="Name of the case")
    mesh_size: int = Field(default=20, description="Mesh size")
"""
        result = validate_generated_code(code, "schema", [])
        assert result["valid"]
        assert any("pydantic" in check.lower() for check in result["checks_passed"])


class TestRequiredPatterns:
    """Test that required patterns for task types are enforced."""

    def test_schema_requires_pydantic(self):
        """Schema task type must contain Pydantic imports."""
        code = """
class SomeClass:
    def __init__(self):
        pass
"""
        result = validate_generated_code(code, "schema", [])
        assert not result["valid"]
        assert any("pydantic" in error.lower() for error in result["errors"])

    def test_tests_require_pytest(self):
        """Tests task type must contain pytest."""
        code = """
def some_test():
    assert True
"""
        result = validate_generated_code(code, "tests", [])
        assert not result["valid"]
        assert any("pytest" in error.lower() for error in result["errors"])

    def test_valid_test_passes(self):
        """Valid pytest test should pass."""
        code = """
import pytest

def test_command_whitelist():
    '''Test that whitelisted commands are allowed.'''
    allowed_commands = {"blockMesh", "icoFoam"}
    assert "blockMesh" in allowed_commands
    assert "rm" not in allowed_commands
"""
        result = validate_generated_code(code, "tests", [])
        assert result["valid"]


class TestConstraints:
    """Test that constraints are validated."""

    def test_type_hints_constraint(self):
        """Type hints constraint should be checked."""
        code_with_hints = """
def process_data(data: list[str]) -> dict[str, int]:
    return {item: len(item) for item in data}
"""
        result = validate_generated_code(
            code_with_hints, "boilerplate", ["Use type hints"]
        )
        assert result["valid"]
        assert any("type hint" in check.lower() for check in result["checks_passed"])

    def test_pydantic_v2_constraint(self):
        """Pydantic v2 constraint should be checked."""
        code = """
from pydantic import BaseModel, Field, ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str = Field(...)
"""
        result = validate_generated_code(code, "schema", ["Use Pydantic v2"])
        assert result["valid"]
        assert any("pydantic v2" in check.lower() for check in result["checks_passed"])


class TestEmptyCode:
    """Test handling of empty or invalid code."""

    def test_empty_code_is_rejected(self):
        """Empty code must be rejected."""
        result = validate_generated_code("", "boilerplate", [])
        assert not result["valid"]
        assert any("empty" in error.lower() for error in result["errors"])

    def test_whitespace_only_is_rejected(self):
        """Whitespace-only code must be rejected."""
        result = validate_generated_code("   \n  \n  ", "boilerplate", [])
        assert not result["valid"]
        assert any("empty" in error.lower() for error in result["errors"])

    def test_syntax_error_is_detected(self):
        """Syntax errors should be detected."""
        code = """
def broken_function(
    # Missing closing parenthesis
    return True
"""
        result = validate_generated_code(code, "boilerplate", [])
        assert not result["valid"]
        assert any("syntax" in error.lower() for error in result["errors"])
