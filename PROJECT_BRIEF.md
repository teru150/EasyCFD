# EasyCFD Project Brief for Coding Agents

日本語名: やさしいCFD  
English name: EasyCFD

## One-line summary

EasyCFD is a desktop GUI assistant that helps CFD beginners run their first OpenFOAM simulations through natural language, guided workflow explanations, safe command execution, and visual feedback.

## Project motivation

This project comes from a real beginner pain point: when first learning CFD, the exciting part is fluid motion and simulation, but OpenFOAM introduces many barriers before a simple simulation can run.

Beginners must understand:

- OpenFOAM case directory structure
- dictionary files such as `controlDict`, `fvSchemes`, `fvSolution`, and `blockMeshDict`
- meshing commands
- solver selection
- boundary conditions
- terminal commands
- residual logs
- mesh and solver errors

EasyCFD is intended to make the first encounter with CFD more approachable. It should not hide CFD completely. Instead, it should translate the workflow into understandable steps so beginners can learn what is happening.

## Target user

Primary target:

- Students or self-learners curious about CFD
- OpenFOAM beginners
- People who want to run their first simple simulation but feel overwhelmed by command-line workflow and case files

Not the target:

- Professional CFD engineers needing industrial-grade accuracy
- Full CAD-to-mesh automation users
- Commercial CAE replacement users

## Research / portfolio framing

Possible project title:

> EasyCFD: A Natural-Language GUI Assistant for Beginner OpenFOAM Learners

Possible Japanese project title:

> やさしいCFD：OpenFOAM初学者のための自然言語GUIアシスタント

Possible JSEC-style research question:

> Can a natural-language GUI assistant reduce the initial workflow barrier for students learning OpenFOAM-based CFD?

Japanese research question:

> 自然言語GUIアシスタントは、OpenFOAMを用いたCFD学習における初期ワークフローの障壁を下げられるか？

Core hypothesis:

> If beginners can describe simple CFD cases in natural language and see the generated workflow, commands, logs, residuals, and results in a GUI, they can complete first simulations more successfully and understand the OpenFOAM workflow better than with command-line tutorials alone.

## Core design principle

Do not let the LLM directly execute arbitrary shell commands.

The LLM should produce a structured plan. The application should validate the plan. Only a safe runner should execute whitelisted OpenFOAM commands.

Correct flow:

```text
User prompt
  -> LLM
  -> structured JSON case plan
  -> validator
  -> template-based OpenFOAM case generation
  -> whitelisted OpenFOAM command runner
  -> log parser / residual monitor
  -> visualization
  -> explanation back to user
```

Incorrect flow:

```text
User prompt
  -> LLM
  -> arbitrary shell command
```

## MVP scope

The first MVP should be narrow and reliable.

Supported cases:

1. 2D lid-driven cavity flow
2. 2D channel flow

Supported physics:

- incompressible flow
- simple laminar cases first
- basic steady or transient workflows depending on template

Initial OpenFOAM commands:

- `blockMesh`
- `checkMesh`
- `icoFoam`
- `simpleFoam`
- `postProcess`

Initial features:

- Select or create a case from a template
- Run OpenFOAM commands safely
- Stream logs to the GUI
- Parse residuals from solver logs
- Show residual plot
- Show basic result visualization or generated image output
- Explain each step in beginner-friendly language
- Run without an API key in sample mode
- Optional LLM mode using OpenAI API or local Ollama

Out of scope for early MVP:

- arbitrary CAD import
- snappyHexMesh automation
- high-Reynolds-number validation
- industrial accuracy claims
- commercial solver replacement
- remote compute clusters
- unrestricted shell access

## Recommended development environment

Main development should happen on Ubuntu because OpenFOAM, Python tooling, command execution, logs, and local LLM tools are easier to integrate there.

Windows should be used later for:

- desktop app packaging
- installer testing
- UI checks
- GitHub Release builds

## Planned tech stack

Preferred architecture:

```text
Frontend:
  Tauri + React + TypeScript

Backend:
  Python FastAPI or Tauri Rust command layer
  Start with Python if speed is more important than packaging simplicity.

CFD:
  Native OpenFOAM on Ubuntu first
  Later add Docker or WSL backend for Windows

LLM:
  Provider abstraction
  - OpenAI API
  - Ollama local models
  - No-LLM sample mode

Visualization:
  Start simple:
  - residual plots generated from logs
  - PNG outputs from post-processing
  Later:
  - VTK / PyVista / ParaView integration
```

## Repository structure

Use this initial structure:

```text
easycfd/
  AGENTS.md
  CLAUDE.md
  README.md
  PROJECT_BRIEF.md
  apps/
    desktop/
      # Tauri + React app
  backend/
    easycfd_core/
      __init__.py
      api/
      cfd/
      llm/
      validation/
      visualization/
    tests/
  templates/
    cavity_2d/
    channel_2d/
  examples/
    prompts/
    cases/
  docs/
    architecture.md
    research-plan.md
    user-study.md
  scripts/
    dev.sh
    check_openfoam.sh
```

## Important abstractions

### OpenFOAM runner

Create an interface like:

```python
class OpenFOAMRunner:
    def run_command(self, case_dir: str, command: str) -> dict:
        raise NotImplementedError
```

Implement first:

```python
class NativeLinuxRunner(OpenFOAMRunner):
    ...
```

Plan later:

```python
class DockerRunner(OpenFOAMRunner):
    ...

class WSLRunner(OpenFOAMRunner):
    ...
```

### LLM provider

Create an interface like:

```python
class LLMProvider:
    def generate_case_plan(self, user_prompt: str) -> dict:
        raise NotImplementedError

    def explain_log(self, log_text: str) -> str:
        raise NotImplementedError
```

Implement providers:

```python
class MockProvider(LLMProvider):
    ...

class OpenAIProvider(LLMProvider):
    ...

class OllamaProvider(LLMProvider):
    ...
```

`MockProvider` is important. It allows development and testing without any API key or local LLM.

### Case plan schema

The LLM should output structured JSON similar to:

```json
{
  "case_type": "cavity_2d",
  "physics": {
    "flow": "incompressible",
    "state": "transient",
    "turbulence": "laminar"
  },
  "solver": "icoFoam",
  "geometry": {
    "width": 1.0,
    "height": 1.0,
    "depth": 0.1
  },
  "mesh": {
    "nx": 20,
    "ny": 20,
    "nz": 1
  },
  "fluid": {
    "kinematic_viscosity": 0.01
  },
  "boundary_conditions": {
    "movingWall": {
      "U": [1.0, 0.0, 0.0],
      "p": "zeroGradient"
    },
    "fixedWalls": {
      "U": "noSlip",
      "p": "zeroGradient"
    },
    "frontAndBack": {
      "type": "empty"
    }
  },
  "commands": [
    {"name": "blockMesh"},
    {"name": "checkMesh"},
    {"name": "icoFoam"}
  ]
}
```

## Safety constraints

These are mandatory.

Allowed OpenFOAM commands for MVP:

```python
ALLOWED_COMMANDS = {
    "blockMesh",
    "checkMesh",
    "icoFoam",
    "simpleFoam",
    "postProcess"
}
```

Never allow arbitrary commands from LLM output.

Explicitly reject:

- `rm`
- `mv`
- `chmod`
- `chown`
- `curl`
- `wget`
- `sudo`
- `python -c`
- shell pipes
- shell redirects
- `;`
- `&&`
- `|`
- path traversal outside the project workspace

All case generation should happen inside a controlled workspace directory such as:

```text
~/.easycfd/workspaces/
```

or a repo-local development workspace:

```text
./runs/
```

The app must never write outside the configured workspace unless the user explicitly selects an export path.

## API key and local LLM policy

Never commit API keys.

Use:

```text
.env.example
```

Do not commit:

```text
.env
.env.local
```

The app should support:

1. No-LLM sample mode
2. OpenAI API mode with user-provided key
3. Ollama local mode

API keys should be stored in OS credential storage, not plain text JSON, once the app reaches packaging stage.

For early development, `.env` is acceptable if it is ignored by git.

## Initial implementation milestones

### Milestone 0: Repository bootstrap

- Create repo structure
- Add README
- Add AGENTS.md
- Add CLAUDE.md
- Add `.gitignore`
- Add `.env.example`
- Add basic Python package layout
- Add simple test setup

### Milestone 1: OpenFOAM runner

Goal: run a fixed existing template without LLM.

Tasks:

- Add `NativeLinuxRunner`
- Add command whitelist
- Add case workspace creation
- Add subprocess execution
- Capture stdout/stderr
- Save logs to file
- Add tests for command validation

Success criteria:

- App/backend can run `blockMesh` on a cavity template
- Unsafe commands are rejected

### Milestone 2: Template-based case generation

Goal: generate a simple cavity case from parameters.

Tasks:

- Add `cavity_2d` template
- Add simple renderer for OpenFOAM dictionary files
- Generate `system`, `constant`, and `0` directories
- Validate required parameters

Success criteria:

- Generated case passes `blockMesh`
- Generated case passes `checkMesh`

### Milestone 3: Solver run and residual parsing

Goal: run solver and extract residual-like data.

Tasks:

- Run `icoFoam` or `simpleFoam`
- Stream or save solver logs
- Parse residuals from logs
- Return structured residual history

Success criteria:

- Backend returns command status and parsed residual data

### Milestone 4: Minimal GUI

Goal: desktop UI can run a sample case.

Tasks:

- Tauri + React setup
- Case selection screen
- Run button
- Log panel
- Residual chart
- Case summary panel

Success criteria:

- User can run a sample cavity case without touching terminal

### Milestone 5: LLM structured planning

Goal: natural language creates a case plan, but still through validation.

Tasks:

- Add `MockProvider`
- Add `OpenAIProvider`
- Add `OllamaProvider`
- Add JSON schema validation
- Add repair/retry only for JSON format errors
- Add UI settings for provider choice

Success criteria:

- User can type a simple prompt and get a validated case plan
- Invalid or unsafe plans are rejected with clear errors

### Milestone 6: Beginner explanations

Goal: explain workflow without pretending results are guaranteed.

Tasks:

- Explain selected solver
- Explain generated boundary conditions
- Explain each OpenFOAM command
- Explain common errors from logs
- Explain residual plot

Success criteria:

- Beginner can understand what happened in the run

## Suggested first Codex / Claude task

Start with this task:

> Create the initial EasyCFD repository scaffold. Add a Python backend package under `backend/easycfd_core`, define `OpenFOAMRunner`, implement `NativeLinuxRunner` with a strict command whitelist, create a minimal `.gitignore`, `.env.example`, README, AGENTS.md, and CLAUDE.md. Do not implement the GUI yet. Add tests that verify unsafe commands are rejected.

## Coding style preferences

- Prefer simple, readable code over clever abstractions.
- Keep the first version boring and reliable.
- Use type hints in Python.
- Use Pydantic for schemas if FastAPI is used.
- Validate external inputs aggressively.
- Add tests for safety-critical behavior.
- Keep OpenFOAM-specific logic isolated from GUI code.
- Do not let frontend code directly execute shell commands.
- Keep LLM prompts and schemas versioned in files.

## Testing priorities

Test these first:

- command whitelist
- workspace path validation
- case plan schema validation
- template parameter validation
- log parser behavior on sample logs
- runner behavior when command fails

## Security reminders

- Do not commit secrets.
- Do not expose API keys in logs.
- Do not display full API keys in the UI.
- Do not trust LLM output.
- Do not run arbitrary shell strings.
- Do not allow writes outside the workspace.
- Do not claim CFD accuracy without validation.

## README positioning

Suggested README opening:

```markdown
# EasyCFD / やさしいCFD

EasyCFD is a desktop GUI assistant that helps CFD beginners run their first OpenFOAM simulations through natural language.

It is designed for students who are curious about fluid dynamics but feel overwhelmed by OpenFOAM's initial workflow: case directories, dictionary files, meshing commands, solver selection, and log interpretation.

EasyCFD does not attempt to replace CFD knowledge or professional simulation tools. Instead, it provides a guided first step into CFD by generating simple template-based OpenFOAM cases, running validated commands, visualizing logs and residuals, and explaining each step.
```
