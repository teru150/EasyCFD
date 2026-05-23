# EasyCFD Validation Schemas

This module provides Pydantic v2 schemas for validating all data structures in the EasyCFD backend.

## Overview

All schemas implement comprehensive validation rules to ensure:
1. **Type safety**: Strict typing with Python type hints
2. **Value constraints**: Range checking, positive values, etc.
3. **Security**: Path traversal prevention, shell injection prevention
4. **Business logic**: Whitelisting of allowed commands, templates, and solvers

## Schemas

### MeshConfig

Defines OpenFOAM blockMesh parameters for 3D mesh generation.

**Fields:**
- `nx`, `ny`, `nz`: Cell counts in each direction (positive integers, max 1000 for MVP)
- `x_min`, `x_max`: X-axis domain extent (meters)
- `y_min`, `y_max`: Y-axis domain extent (meters)
- `z_min`, `z_max`: Z-axis domain extent (meters)

**Validation:**
- Cell counts must be positive and ≤ 1000
- `min` values must be less than `max` values for all axes

**Example:**
```python
mesh = MeshConfig(
    nx=20, ny=20, nz=1,
    x_min=0.0, x_max=1.0,
    y_min=0.0, y_max=1.0,
    z_min=0.0, z_max=0.1,
)
```

---

### SolverConfig

Defines OpenFOAM solver execution parameters.

**Fields:**
- `solver_name`: Solver executable name (whitelisted: `icoFoam`, `simpleFoam`)
- `end_time`: Simulation end time in seconds (positive, max 1000s for MVP)
- `delta_t`: Time step size in seconds (positive)
- `write_interval`: Output write interval in seconds (positive)

**Validation:**
- Solver must be in whitelist (MVP: `icoFoam`, `simpleFoam`)
- All time values must be positive
- `delta_t` and `write_interval` cannot exceed `end_time`
- `end_time` limited to 1000s for MVP safety

**Example:**
```python
solver = SolverConfig(
    solver_name="icoFoam",
    end_time=0.5,
    delta_t=0.005,
    write_interval=0.1,
)
```

---

### CasePlan

Complete validated simulation case configuration.

**Fields:**
- `case_name`: Case directory name (alphanumeric, underscore, hyphen only)
- `template_type`: Template identifier (whitelisted: `cavity_2d`, `channel_2d`)
- `mesh_config`: MeshConfig instance
- `solver_config`: SolverConfig instance

**Validation:**
- Case name must be safe for filesystem use:
  - No path traversal (`..`)
  - No absolute paths (starting with `/`)
  - No hidden files (starting with `.`)
  - No shell metacharacters (`;`, `&`, `|`, `$`, etc.)
- Template type must be in whitelist
- Nested mesh and solver configs are validated recursively

**Example:**
```python
case = CasePlan(
    case_name="cavity_demo_01",
    template_type="cavity_2d",
    mesh_config=mesh,
    solver_config=solver,
)
```

**Security Note:** This is the primary defense against path traversal and command injection attacks. All case names from LLM output must pass through this validator.

---

### SimulationResult

Result of a single OpenFOAM command execution.

**Fields:**
- `success`: Boolean success flag (must match `return_code == 0`)
- `stdout`: Standard output text (default: empty string)
- `stderr`: Standard error text (default: empty string)
- `return_code`: Process exit code (0 = success)
- `elapsed_time`: Execution time in seconds (non-negative)
- `command`: Optional command name that was executed
- `case_dir`: Optional case directory path

**Validation:**
- `elapsed_time` must be non-negative
- `success` flag must be consistent with `return_code` (0 = success)
- Extra fields are forbidden

**Example:**
```python
result = SimulationResult(
    success=True,
    stdout="Mesh created successfully",
    stderr="",
    return_code=0,
    elapsed_time=1.23,
    command="blockMesh",
    case_dir="/home/user/runs/cavity_01",
)
```

---

## Configuration

All schemas use Pydantic v2 ConfigDict:
```python
model_config = ConfigDict(frozen=False, extra="forbid")
```

- `frozen=False`: Schemas are mutable (can be updated during workflow)
- `extra="forbid"`: Extra fields are rejected (strict validation)

---

## Usage

### Import schemas:
```python
from backend.easycfd_core.validation.schemas import (
    CasePlan,
    MeshConfig,
    SolverConfig,
    SimulationResult,
)
```

### Validate LLM output:
```python
try:
    case_plan = CasePlan(**llm_output)
    # Safe to use: all validations passed
except ValidationError as e:
    # Reject: invalid or dangerous input
    log_error(f"LLM produced invalid case plan: {e}")
```

### JSON serialization:
```python
# Export to JSON
json_str = case_plan.model_dump_json(indent=2)

# Import from JSON
case_plan = CasePlan.model_validate_json(json_str)
```

### Dictionary conversion:
```python
# Export to dict
data = case_plan.model_dump()

# Import from dict
case_plan = CasePlan(**data)
```

---

## Testing

Comprehensive tests are in `backend/tests/test_schemas.py`:
- Valid configuration tests
- Boundary value tests
- Security constraint tests (path traversal, shell injection)
- Consistency validation tests

Run tests:
```bash
poetry run pytest backend/tests/test_schemas.py -v
```

---

## Demo

See `examples/schemas_demo.py` for a complete demonstration:
```bash
poetry run python examples/schemas_demo.py
```

---

## Security Constraints

These schemas enforce the following security rules from PROJECT_BRIEF.md:

### Command Whitelist
Only approved OpenFOAM commands are allowed:
- `blockMesh`
- `checkMesh`
- `icoFoam`
- `simpleFoam`
- `postProcess`

### Path Safety
Case names are validated to prevent:
- Path traversal attacks (`..`, `/`, `.`)
- Shell injection (`;`, `&`, `|`, `$`, `` ` ``, etc.)
- Arbitrary file access

### Template Whitelist
Only approved templates are allowed (MVP):
- `cavity_2d`
- `channel_2d`

### Resource Limits
MVP safety limits:
- Mesh cells: max 1000 per direction
- Simulation time: max 1000 seconds

---

## Design Philosophy

1. **Fail fast**: Invalid inputs are rejected immediately at the validation boundary
2. **Never trust LLM output**: All structured data from LLMs must pass through these schemas
3. **Defense in depth**: Multiple layers of validation (type, range, whitelist, consistency)
4. **Clear error messages**: Validation errors explain exactly what went wrong
5. **Type safety**: Comprehensive type hints for IDE support and mypy checking

---

## Future Extensions

When adding new features, follow these principles:

1. **Add to whitelist, don't bypass**: New solvers/templates should be added to whitelist constants
2. **Validate aggressively**: When in doubt, reject
3. **Test security constraints**: Every new validation rule needs a security test
4. **Document rationale**: Explain why each constraint exists
5. **Never weaken validation**: Security rules should never be relaxed without review

---

## Related Files

- Implementation: `backend/easycfd_core/validation/schemas.py`
- Tests: `backend/tests/test_schemas.py`
- Demo: `examples/schemas_demo.py`
- Project requirements: `PROJECT_BRIEF.md`
- Security policy: `CLAUDE.md`
