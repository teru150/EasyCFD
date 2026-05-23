#!/usr/bin/env python3
"""
MCP Codex Worker Server

This server provides code generation capabilities to Claude Code via the MCP protocol.
It handles task delegation for boilerplate generation, schema creation, test writing, etc.

Security: All generated code must pass validation before being returned to Claude Code.
"""

import asyncio
import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .handlers import (
    handle_generate_schema,
    handle_generate_tests,
    handle_generate_template,
    handle_generate_boilerplate,
)
from .validator import validate_generated_code


# Tool definitions
TOOLS = [
    Tool(
        name="codex_worker",
        description=(
            "Delegate code generation tasks to Codex MCP Worker. "
            "Use for: Pydantic schemas, test code, OpenFOAM templates, boilerplate. "
            "NEVER use for: security-critical code (safety.py, validator.py)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": (
                        "Clear description of what to generate. "
                        "Examples: 'Generate Pydantic schema for CasePlan', "
                        "'Create pytest tests for command whitelist', "
                        "'Generate OpenFOAM controlDict template'"
                    ),
                },
                "context_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of file paths to provide as context. "
                        "Example: ['PROJECT_BRIEF.md', 'AGENTS.md']"
                    ),
                    "default": [],
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of constraints the generated code must follow. "
                        "Example: ['Use Pydantic v2', 'No shell=True', 'Type hints required']"
                    ),
                    "default": [],
                },
                "task_type": {
                    "type": "string",
                    "enum": ["schema", "tests", "template", "boilerplate"],
                    "description": (
                        "Type of generation task. "
                        "schema: Pydantic models, "
                        "tests: pytest test code, "
                        "template: OpenFOAM config files, "
                        "boilerplate: General boilerplate code"
                    ),
                },
            },
            "required": ["task", "task_type"],
        },
    )
]


app = Server("codex-worker")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool calls from Claude Code.

    Args:
        name: Tool name (should be "codex_worker")
        arguments: Tool arguments

    Returns:
        Generated code or error message
    """
    if name != "codex_worker":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        # Extract arguments
        task = arguments.get("task", "")
        context_files = arguments.get("context_files", [])
        constraints = arguments.get("constraints", [])
        task_type = arguments.get("task_type", "boilerplate")

        if not task:
            return [TextContent(type="text", text="Error: 'task' parameter is required")]

        # Read context files
        context_data = {}
        for file_path in context_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    context_data[file_path] = f.read()
            except FileNotFoundError:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Context file not found: {file_path}",
                    )
                ]
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text=f"Error reading context file {file_path}: {str(e)}",
                    )
                ]

        # Dispatch to appropriate handler
        if task_type == "schema":
            generated_code = await handle_generate_schema(task, context_data, constraints)
        elif task_type == "tests":
            generated_code = await handle_generate_tests(task, context_data, constraints)
        elif task_type == "template":
            generated_code = await handle_generate_template(task, context_data, constraints)
        elif task_type == "boilerplate":
            generated_code = await handle_generate_boilerplate(task, context_data, constraints)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Error: Unknown task_type: {task_type}",
                )
            ]

        # Validate generated code
        validation_result = validate_generated_code(generated_code, task_type, constraints)

        if not validation_result["valid"]:
            error_msg = (
                f"Generated code failed validation:\n"
                f"{json.dumps(validation_result['errors'], indent=2)}\n\n"
                f"Generated code:\n{generated_code}"
            )
            return [TextContent(type="text", text=error_msg)]

        # Return validated code
        success_msg = (
            f"✓ Code generated and validated successfully\n\n"
            f"Task: {task}\n"
            f"Type: {task_type}\n\n"
            f"Generated code:\n\n{generated_code}\n\n"
            f"Validation passed: {', '.join(validation_result['checks_passed'])}"
        )

        return [TextContent(type="text", text=success_msg)]

    except Exception as e:
        error_msg = f"Error in codex_worker: {str(e)}\n\nTask: {task}\nType: {task_type}"
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
