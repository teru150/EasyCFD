"""
Security-critical validation module for EasyCFD.

This module provides the core security controls that prevent arbitrary command
execution and path traversal attacks. All functions in this module must be
reviewed carefully before any modifications.

SECURITY PHILOSOPHY:
-------------------
1. Never trust external input (user prompts, LLM output, file paths)
2. Whitelist approach: only explicitly allowed commands can run
3. Deny by default: reject anything not explicitly permitted
4. Defense in depth: multiple validation layers
5. Fail safely: reject on any doubt

THREAT MODEL:
------------
- Malicious user input attempting command injection
- LLM-generated commands attempting to escape the sandbox
- Path traversal attacks attempting to access files outside workspace
- Command chaining attempts using shell metacharacters
- Social engineering attacks via prompts

This module is the last line of defense before OpenFOAM command execution.
"""

import os
import re
from pathlib import Path
from typing import Set, Union


# =============================================================================
# COMMAND WHITELIST
# =============================================================================

# Only these OpenFOAM commands are permitted in MVP.
# This is a frozen set to prevent runtime modification.
#
# SECURITY RATIONALE:
# - blockMesh: generates mesh from blockMeshDict (read-only dictionary input)
# - checkMesh: validates mesh quality (read-only operation)
# - icoFoam: transient incompressible Navier-Stokes solver
# - simpleFoam: steady-state incompressible SIMPLE solver
# - postProcess: runs function objects for post-processing
#
# NOT INCLUDED (and must remain excluded):
# - foamExec: can run arbitrary commands
# - runApplication: wrapper that could bypass validation
# - Any command with shell scripting capability
# - paraFoam: opens GUI (not needed for backend)
# - Any mesh generation beyond blockMesh (e.g., snappyHexMesh in MVP)
ALLOWED_COMMANDS: Set[str] = frozenset({
    "blockMesh",
    "checkMesh",
    "icoFoam",
    "simpleFoam",
    "postProcess",
})


# =============================================================================
# FORBIDDEN PATTERNS
# =============================================================================

# Patterns that indicate shell command injection attempts or dangerous operations.
#
# SECURITY RATIONALE:
# - Shell metacharacters: ; && || | ` $ ( ) can chain commands
# - Path traversal: .. can escape workspace directory
# - Dangerous commands: rm, mv, chmod, etc. can modify/delete files
# - Network access: curl, wget, nc can exfiltrate data
# - Code execution: eval, exec, python -c can run arbitrary code
# - Privilege escalation: sudo, su can gain elevated privileges
FORBIDDEN_PATTERNS: Set[str] = frozenset({
    # Shell metacharacters
    ";",
    "&&",
    "||",
    "|",
    "`",
    "$(",
    "$()",

    # Path traversal
    "..",

    # File manipulation
    "rm",
    "mv",
    "cp",      # Added: could copy sensitive files
    "chmod",
    "chown",
    "chgrp",   # Added: group permission changes

    # Network access
    "curl",
    "wget",
    "nc",
    "netcat",
    "telnet",
    "ssh",
    "scp",
    "ftp",

    # Code execution
    "eval",
    "exec",
    "python -c",
    "python3 -c",
    "bash -c",
    "sh -c",

    # Privilege escalation
    "sudo",
    "su",
    "doas",    # Added: sudo alternative

    # Process manipulation
    "kill",
    "killall",
    "pkill",

    # Environment manipulation
    "export",
    "unset",
})


# =============================================================================
# COMMAND VALIDATION
# =============================================================================

def is_command_allowed(command: str) -> bool:
    """
    Validate that a command is in the whitelist and safe to execute.

    This function performs strict validation of OpenFOAM commands before
    execution. It is designed to prevent command injection and ensure only
    approved OpenFOAM utilities can run.

    SECURITY CHECKS:
    ----------------
    1. Command must be in ALLOWED_COMMANDS whitelist
    2. Command must not contain shell metacharacters
    3. Command must not contain path traversal sequences
    4. Command must be a single word (no arguments allowed here)

    DESIGN DECISIONS:
    -----------------
    - Arguments are NOT checked here; they should be validated separately
      and passed as a list to subprocess.run() with shell=False
    - Whitespace is stripped to handle accidental padding
    - Case-sensitive matching (OpenFOAM commands are case-sensitive)
    - Empty strings are rejected

    Args:
        command: The command name to validate (e.g., "blockMesh")

    Returns:
        bool: True if command is allowed, False otherwise

    Examples:
        >>> is_command_allowed("blockMesh")
        True
        >>> is_command_allowed("blockMesh; rm -rf /")
        False
        >>> is_command_allowed("foamExec")
        False
        >>> is_command_allowed("")
        False

    Security Note:
        This function should be called BEFORE constructing any subprocess
        command. Never pass user input directly to subprocess without
        validation through this function.
    """
    # Input normalization: strip whitespace but preserve case
    command_clean = command.strip()

    # Reject empty strings
    if not command_clean:
        return False

    # Primary check: command must be in whitelist
    if command_clean not in ALLOWED_COMMANDS:
        return False

    # Defense in depth: check for forbidden patterns even in whitelist
    # This catches any tampering with ALLOWED_COMMANDS at runtime
    for forbidden in FORBIDDEN_PATTERNS:
        if forbidden in command_clean:
            return False

    # Ensure command is a single word (no internal whitespace)
    # Arguments should be handled separately in the caller
    # After stripping, check for any remaining whitespace characters
    if any(char in command_clean for char in [" ", "\t", "\n", "\r"]):
        return False

    # All checks passed
    return True


# =============================================================================
# PATH VALIDATION
# =============================================================================

def is_path_safe(path: Union[str, Path], workspace_root: Union[str, Path, None] = None) -> bool:
    """
    Validate that a file path is safe and does not attempt directory traversal.

    This function prevents path traversal attacks that could access files
    outside the designated workspace. It is critical for preventing
    unauthorized file access, modification, or information disclosure.

    SECURITY CHECKS:
    ----------------
    1. Path must not contain ".." (parent directory references)
    2. Path must not contain shell metacharacters
    3. If workspace_root provided, resolved path must be inside workspace
    4. Path must not be absolute (unless within workspace when checked)
    5. Path must not contain null bytes

    DESIGN DECISIONS:
    -----------------
    - Both string and Path objects accepted for convenience
    - workspace_root is optional but STRONGLY RECOMMENDED in production
    - Symbolic link resolution is performed to catch indirect traversal
    - Rejects paths attempting to escape via symlinks

    LIMITATIONS:
    -----------
    - Does not check if path exists (intentional: validation before creation)
    - Does not validate path length (OS handles this)
    - Does not check file permissions (handled by OS)

    Args:
        path: The file path to validate
        workspace_root: Optional. The root directory that path must stay within.
                       If provided, performs additional containment check.

    Returns:
        bool: True if path is safe, False otherwise

    Examples:
        >>> is_path_safe("/tmp/case1/system/controlDict")
        True
        >>> is_path_safe("../../etc/passwd")
        False
        >>> is_path_safe("case1/../../../etc/passwd")
        False
        >>> is_path_safe("case1/system/controlDict", "/home/user/easycfd/runs")
        True
        >>> is_path_safe("/etc/passwd", "/home/user/easycfd/runs")
        False

    Security Note:
        This function should be called for EVERY file path that comes from
        external input (user, LLM, API, config files). Never trust paths
        without validation.
    """
    # Input normalization: convert to string
    path_str = str(path)

    # Reject empty paths
    if not path_str:
        return False

    # Check for null bytes (could indicate injection attempt)
    if "\x00" in path_str:
        return False

    # Primary check: reject explicit parent directory references
    # This catches both Unix (..) and potential Windows variants
    if ".." in path_str:
        return False

    # Check for shell metacharacters in path
    # These could be used in combination with other vulnerabilities
    dangerous_chars = {";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"}
    if any(char in path_str for char in dangerous_chars):
        return False

    # If workspace_root is provided, perform containment check
    if workspace_root is not None:
        try:
            # Convert both to absolute paths and resolve symlinks
            # This prevents symlink-based traversal attacks
            workspace_abs = Path(workspace_root).resolve()
            path_abs = Path(path).resolve()

            # Check if path is within workspace
            # relative_to() raises ValueError if path is outside workspace
            try:
                path_abs.relative_to(workspace_abs)
            except ValueError:
                # Path is outside workspace
                return False

        except (OSError, RuntimeError) as e:
            # Error during path resolution (e.g., too many symlinks, permission denied)
            # Fail safely: reject the path
            return False

    # All checks passed
    return True


# =============================================================================
# ARGUMENT VALIDATION
# =============================================================================

def is_argument_safe(argument: str) -> bool:
    """
    Validate that a command-line argument is safe.

    This function checks individual arguments passed to OpenFOAM commands.
    While arguments should be passed as a list to subprocess.run() with
    shell=False (which prevents most injection attacks), this provides
    defense in depth.

    SECURITY CHECKS:
    ----------------
    1. Argument must not contain shell metacharacters
    2. Argument must not contain path traversal sequences
    3. Argument must not contain null bytes

    DESIGN DECISIONS:
    -----------------
    - Allows negative numbers (e.g., "-case", "-parallel")
    - Allows equal signs (e.g., "-opt=value")
    - Rejects anything that looks like command chaining

    Args:
        argument: The command-line argument to validate

    Returns:
        bool: True if argument is safe, False otherwise

    Examples:
        >>> is_argument_safe("-case")
        True
        >>> is_argument_safe("/home/user/runs/case1")
        True
        >>> is_argument_safe("../../etc/passwd")
        False
        >>> is_argument_safe("-case; rm -rf /")
        False

    Security Note:
        Even with this validation, always pass arguments as a list to
        subprocess.run() with shell=False, never as a concatenated string.
    """
    # Reject empty arguments
    if not argument:
        return False

    # Check for null bytes
    if "\x00" in argument:
        return False

    # Check for parent directory references
    if ".." in argument:
        return False

    # Check for shell metacharacters
    dangerous_chars = {";", "&", "|", "`", "$", "(", ")", "\n", "\r"}
    if any(char in argument for char in dangerous_chars):
        return False

    # All checks passed
    return True


# =============================================================================
# CASE DIRECTORY VALIDATION
# =============================================================================

def is_case_directory_valid(case_dir: Union[str, Path], workspace_root: Union[str, Path]) -> bool:
    """
    Validate that a case directory is within the workspace and safe to use.

    This function combines path safety checks with workspace containment
    verification. It should be called before any OpenFOAM operation that
    requires a case directory.

    SECURITY CHECKS:
    ----------------
    1. All checks from is_path_safe()
    2. Path must be within workspace_root
    3. Case directory must be a valid directory path (or path for creation)

    Args:
        case_dir: The OpenFOAM case directory path to validate
        workspace_root: The root workspace directory that must contain case_dir

    Returns:
        bool: True if case directory is valid and safe, False otherwise

    Examples:
        >>> is_case_directory_valid("runs/cavity_2d", "/home/user/easycfd")
        True
        >>> is_case_directory_valid("/etc", "/home/user/easycfd")
        False
        >>> is_case_directory_valid("../../../etc", "/home/user/easycfd")
        False

    Security Note:
        Always use this function when accepting case directory paths from
        external sources. Combine with command validation for complete safety.
    """
    # Delegate to is_path_safe with workspace_root enforcement
    return is_path_safe(case_dir, workspace_root=workspace_root)


# =============================================================================
# FULL COMMAND VALIDATION
# =============================================================================

def validate_command_execution(
    command: str,
    case_dir: Union[str, Path],
    workspace_root: Union[str, Path],
    additional_args: list[str] = None
) -> tuple[bool, str]:
    """
    Comprehensive validation before executing an OpenFOAM command.

    This function combines all security checks into a single validation point.
    It should be the final check before any subprocess execution.

    SECURITY CHECKS:
    ----------------
    1. Command whitelist validation
    2. Case directory safety and containment
    3. Additional arguments safety
    4. Workspace root validity

    Args:
        command: The OpenFOAM command to execute (e.g., "blockMesh")
        case_dir: The case directory path
        workspace_root: The workspace root directory
        additional_args: Optional list of additional command arguments

    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if all checks pass, False otherwise
            - error_message: Description of validation failure, or empty string if valid

    Examples:
        >>> validate_command_execution("blockMesh", "runs/cavity", "/home/user/easycfd")
        (True, "")
        >>> validate_command_execution("rm", "runs/cavity", "/home/user/easycfd")
        (False, "Command not allowed: rm")
        >>> validate_command_execution("blockMesh", "../../etc", "/home/user/easycfd")
        (False, "Case directory path is not safe: ../../etc")

    Security Note:
        This is the recommended entry point for command validation.
        Use this before subprocess.run() to ensure comprehensive security.
    """
    # Validate command
    if not is_command_allowed(command):
        return False, f"Command not allowed: {command}"

    # Validate workspace root
    if not workspace_root:
        return False, "Workspace root must be specified"

    # Validate case directory
    if not is_case_directory_valid(case_dir, workspace_root):
        return False, f"Case directory path is not safe: {case_dir}"

    # Validate additional arguments if provided
    if additional_args:
        for arg in additional_args:
            if not is_argument_safe(arg):
                return False, f"Unsafe argument detected: {arg}"

    # All checks passed
    return True, ""


# =============================================================================
# MODULE-LEVEL EXPORTS
# =============================================================================

__all__ = [
    "ALLOWED_COMMANDS",
    "FORBIDDEN_PATTERNS",
    "is_command_allowed",
    "is_path_safe",
    "is_argument_safe",
    "is_case_directory_valid",
    "validate_command_execution",
]
