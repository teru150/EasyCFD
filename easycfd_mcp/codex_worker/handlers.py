"""
Task handlers for Codex MCP Worker

Each handler is responsible for generating specific types of code:
- Schema: Pydantic models and data structures
- Tests: pytest test cases
- Template: OpenFOAM configuration files
- Boilerplate: General repetitive code

All handlers use LOCAL Codex CLI for code generation.

Architecture:
  Claude Code (Sonnet 4.5) = Commander (design, review, security)
  Codex CLI (local) = Worker (code generation, implementation)

Codex CLI: /home/teru_26_2/.nvm/versions/node/v22.19.0/bin/codex
Version: codex-cli 0.130.0
"""

import subprocess
from typing import Any


def call_codex(task: str, working_dir: str = None) -> str:
    """
    Call local Codex CLI to generate code.

    Args:
        task: Task description/prompt for Codex
        working_dir: Optional working directory for Codex

    Returns:
        Generated code from Codex

    Raises:
        RuntimeError: If Codex execution fails
    """
    cmd = [
        "codex", "exec",
        "-s", "workspace-write",
        task,
    ]

    if working_dir:
        cmd.extend(["-C", working_dir])

    # stdin=DEVNULL is critical: without it Codex waits for stdin forever
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Codex execution failed (exit code {result.returncode})\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

    return result.stdout.strip()


async def handle_generate_schema(
    task: str,
    context_data: dict[str, str],
    constraints: list[str],
) -> str:
    """
    Generate Pydantic schema code using Codex CLI.

    Args:
        task: Task description
        context_data: Dictionary of {file_path: content}
        constraints: List of constraints

    Returns:
        Generated Python code with Pydantic models
    """
    # Build context section
    context_section = ""
    if context_data:
        context_section = "\n\n## Context Files\n\n"
        for file_path, content in context_data.items():
            context_section += f"### {file_path}\n\n```\n{content}\n```\n\n"

    # Build constraints section
    constraints_section = ""
    if constraints:
        constraints_section = "\n\n## Constraints\n\n"
        for constraint in constraints:
            constraints_section += f"- {constraint}\n"

    prompt = f"""You are a Python code generator specializing in Pydantic v2 schemas.

## Task

{task}

{context_section}{constraints_section}

## Requirements

1. Use Pydantic v2 syntax (Field, ConfigDict, model_validator)
2. Include complete type hints
3. Add docstrings for all models and fields
4. Include validation where appropriate
5. Follow Python best practices
6. Output ONLY the Python code, no explanations

Generate the Pydantic schema code now:"""

    # Call Codex CLI
    generated_code = call_codex(prompt, working_dir="/home/teru_26_2/webapp/EasyCFD")

    # Remove markdown code blocks if present
    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()

    return generated_code


async def handle_generate_tests(
    task: str,
    context_data: dict[str, str],
    constraints: list[str],
) -> str:
    """
    Generate pytest test code using Codex CLI.

    Args:
        task: Task description
        context_data: Dictionary of {file_path: content}
        constraints: List of constraints

    Returns:
        Generated Python test code
    """
    context_section = ""
    if context_data:
        context_section = "\n\n## Context Files\n\n"
        for file_path, content in context_data.items():
            context_section += f"### {file_path}\n\n```\n{content}\n```\n\n"

    constraints_section = ""
    if constraints:
        constraints_section = "\n\n## Constraints\n\n"
        for constraint in constraints:
            constraints_section += f"- {constraint}\n"

    prompt = f"""You are a Python test code generator specializing in pytest.

## Task

{task}

{context_section}{constraints_section}

## Requirements

1. Use pytest framework
2. Include both positive and negative test cases
3. Test edge cases and error conditions
4. Use descriptive test function names (test_description_of_what_is_tested)
5. Include docstrings explaining what each test validates
6. Use assert statements with clear failure messages
7. Follow AAA pattern (Arrange, Act, Assert) where appropriate
8. Output ONLY the Python test code, no explanations

Generate the pytest test code now:"""

    generated_code = call_codex(prompt, working_dir="/home/teru_26_2/webapp/EasyCFD")

    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()

    return generated_code


async def handle_generate_template(
    task: str,
    context_data: dict[str, str],
    constraints: list[str],
) -> str:
    """
    Generate OpenFOAM template configuration files using Codex CLI.

    Args:
        task: Task description
        context_data: Dictionary of {file_path: content}
        constraints: List of constraints

    Returns:
        Generated OpenFOAM configuration content
    """
    context_section = ""
    if context_data:
        context_section = "\n\n## Context Files\n\n"
        for file_path, content in context_data.items():
            context_section += f"### {file_path}\n\n```\n{content}\n```\n\n"

    constraints_section = ""
    if constraints:
        constraints_section = "\n\n## Constraints\n\n"
        for constraint in constraints:
            constraints_section += f"- {constraint}\n"

    prompt = f"""You are an OpenFOAM configuration file generator.

## Task

{task}

{context_section}{constraints_section}

## Requirements

1. Follow OpenFOAM dictionary format
2. Include comments explaining key parameters
3. Use appropriate default values for beginner-friendly simulations
4. Ensure compatibility with OpenFOAM 9
5. Include FoamFile header if needed
6. Output ONLY the configuration content, no explanations

Generate the OpenFOAM template now:"""

    generated_code = call_codex(prompt, working_dir="/home/teru_26_2/webapp/EasyCFD")

    # For OpenFOAM files, we might not have markdown code blocks
    if "```" in generated_code:
        # Try to extract from code blocks
        if "```openfoam" in generated_code or "```cpp" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
            # Remove language identifier if present
            if "\n" in generated_code:
                lines = generated_code.split("\n")
                if lines[0] in ["openfoam", "cpp", "c++"]:
                    generated_code = "\n".join(lines[1:])
        else:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()

    return generated_code


async def handle_generate_boilerplate(
    task: str,
    context_data: dict[str, str],
    constraints: list[str],
) -> str:
    """
    Generate general boilerplate code using Codex CLI.

    Args:
        task: Task description
        context_data: Dictionary of {file_path: content}
        constraints: List of constraints

    Returns:
        Generated boilerplate code
    """
    context_section = ""
    if context_data:
        context_section = "\n\n## Context Files\n\n"
        for file_path, content in context_data.items():
            context_section += f"### {file_path}\n\n```\n{content}\n```\n\n"

    constraints_section = ""
    if constraints:
        constraints_section = "\n\n## Constraints\n\n"
        for constraint in constraints:
            constraints_section += f"- {constraint}\n"

    prompt = f"""You are a code generator for Python boilerplate.

## Task

{task}

{context_section}{constraints_section}

## Requirements

1. Write clean, readable Python code
2. Include type hints
3. Add docstrings for functions and classes
4. Follow PEP 8 style guidelines
5. Include error handling where appropriate
6. Output ONLY the code, no explanations

Generate the boilerplate code now:"""

    generated_code = call_codex(prompt, working_dir="/home/teru_26_2/webapp/EasyCFD")

    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()

    return generated_code
