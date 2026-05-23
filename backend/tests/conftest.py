"""
Pytest configuration and shared fixtures for EasyCFD tests.

This file is automatically loaded by pytest and provides:
- Custom pytest markers
- Shared fixtures
- Test configuration
"""

import pytest
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import easycfd_core
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def pytest_configure(config):
    """
    Register custom pytest markers.

    Markers help categorize and filter tests.
    """
    config.addinivalue_line(
        "markers",
        "security: marks tests as security-critical (always run these)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )


@pytest.fixture
def temp_workspace(tmp_path):
    """
    Provide a temporary workspace directory for testing.

    This fixture creates a temporary directory that simulates
    the runs/ workspace for tests that need file operations.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Returns:
        Path: Path to the temporary workspace directory
    """
    workspace = tmp_path / "runs"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_case_directory(temp_workspace):
    """
    Provide a mock OpenFOAM case directory structure.

    Creates a minimal valid case directory for testing with
    the standard OpenFOAM directory structure:
    - system/ (controlDict, fvSchemes, fvSolution)
    - constant/ (transportProperties, turbulenceProperties)
    - 0/ (initial conditions: U, p)

    Args:
        temp_workspace: The temporary workspace fixture

    Returns:
        Path: Path to the mock case directory
    """
    case_dir = temp_workspace / "test_case"
    case_dir.mkdir()

    # Create standard OpenFOAM directories
    (case_dir / "system").mkdir()
    (case_dir / "constant").mkdir()
    (case_dir / "0").mkdir()

    return case_dir


@pytest.fixture
def allowed_commands():
    """
    Provide the list of allowed OpenFOAM commands.

    This fixture ensures tests use the same whitelist as the application.

    Returns:
        set: Set of allowed command names
    """
    return {"blockMesh", "checkMesh", "icoFoam", "simpleFoam", "postProcess"}


@pytest.fixture
def dangerous_commands():
    """
    Provide a list of dangerous commands that should always be blocked.

    This fixture helps ensure consistent testing of blocked commands.

    Returns:
        list: List of dangerous command names
    """
    return [
        "rm", "sudo", "curl", "wget", "python", "bash", "sh",
        "chmod", "chown", "mv", "cp", "dd", "mkfs", "mount",
        "umount", "kill", "killall", "reboot", "shutdown"
    ]


@pytest.fixture
def shell_metacharacters():
    """
    Provide a list of shell metacharacters that should be rejected.

    These characters can be used for command injection and must
    be blocked in commands and arguments.

    Returns:
        list: List of dangerous shell metacharacters
    """
    return [";", "&&", "||", "|", "&", ">", "<", ">>", "`", "$", "(", ")"]
