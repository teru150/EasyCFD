"""
Validation module for EasyCFD.

This module provides security-critical validation functions and schemas.

Submodules:
  - safety: Command and path validation (security-critical)
  - schemas: Pydantic validation schemas
"""

from .safety import (
    ALLOWED_COMMANDS,
    FORBIDDEN_PATTERNS,
    is_command_allowed,
    is_path_safe,
    is_argument_safe,
    is_case_directory_valid,
    validate_command_execution,
)

__all__ = [
    "ALLOWED_COMMANDS",
    "FORBIDDEN_PATTERNS",
    "is_command_allowed",
    "is_path_safe",
    "is_argument_safe",
    "is_case_directory_valid",
    "validate_command_execution",
]
