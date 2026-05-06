# AGENTS.md

Use `PROJECT_BRIEF.md` as the main project context.

## Project

Japanese name: やさしいCFD  
English name: EasyCFD

## Mission

Build EasyCFD: a desktop GUI assistant for CFD beginners learning OpenFOAM. It should help users run simple OpenFOAM simulations through guided workflows, safe command execution, logs, residuals, and explanations.

## Highest-priority rule

Never execute arbitrary shell commands produced by an LLM. LLM output must be structured, validated, and executed only through a whitelisted OpenFOAM runner.

## MVP

Start with backend only:

1. Python package under `backend/easycfd_core`
2. `OpenFOAMRunner` interface
3. `NativeLinuxRunner`
4. strict command whitelist
5. workspace path validation
6. `.gitignore`
7. `.env.example`
8. tests for unsafe command rejection

Do not implement the GUI until the backend runner and safety tests are working.

## Allowed OpenFOAM commands for MVP

- `blockMesh`
- `checkMesh`
- `icoFoam`
- `simpleFoam`
- `postProcess`

Reject all other commands.

## Code style

- Keep code simple and readable.
- Use Python type hints.
- Add tests for safety-critical behavior.
- Keep OpenFOAM execution logic isolated from UI code.
- Do not commit secrets.
- Do not write outside the configured workspace.
