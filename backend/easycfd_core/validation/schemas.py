"""
Pydantic v2 schemas for EasyCFD backend validation.

These schemas define the structure and validation rules for:
- Case plans (simulation configurations)
- Mesh configurations
- Solver configurations
- Simulation results

All schemas use Pydantic v2 syntax with type hints and validation rules.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class MeshConfig(BaseModel):
    """
    Configuration for OpenFOAM blockMesh.

    Defines the 3D mesh dimensions and spatial extent.
    All spatial coordinates are in meters.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    nx: int = Field(..., gt=0, description="Number of cells in x direction")
    ny: int = Field(..., gt=0, description="Number of cells in y direction")
    nz: int = Field(..., gt=0, description="Number of cells in z direction")

    x_min: float = Field(..., description="Minimum x coordinate (meters)")
    x_max: float = Field(..., description="Maximum x coordinate (meters)")
    y_min: float = Field(..., description="Minimum y coordinate (meters)")
    y_max: float = Field(..., description="Maximum y coordinate (meters)")
    z_min: float = Field(..., description="Minimum z coordinate (meters)")
    z_max: float = Field(..., description="Maximum z coordinate (meters)")

    @field_validator("nx", "ny", "nz")
    @classmethod
    def validate_positive_cells(cls, v: int) -> int:
        """Ensure mesh cell counts are positive integers."""
        if v <= 0:
            raise ValueError(f"Mesh cell count must be positive, got {v}")
        if v > 1000:
            raise ValueError(f"Mesh cell count {v} exceeds safety limit of 1000 (MVP)")
        return v

    @model_validator(mode="after")
    def validate_spatial_extent(self) -> "MeshConfig":
        """Ensure spatial coordinates form valid domains."""
        if self.x_min >= self.x_max:
            raise ValueError(
                f"x_min ({self.x_min}) must be less than x_max ({self.x_max})"
            )
        if self.y_min >= self.y_max:
            raise ValueError(
                f"y_min ({self.y_min}) must be less than y_max ({self.y_max})"
            )
        if self.z_min >= self.z_max:
            raise ValueError(
                f"z_min ({self.z_min}) must be less than z_max ({self.z_max})"
            )
        return self


class SolverConfig(BaseModel):
    """
    Configuration for OpenFOAM solver execution.

    Defines solver type and time-stepping parameters.
    MVP supports only whitelisted solvers: icoFoam, simpleFoam.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    solver_name: str = Field(
        ...,
        description="OpenFOAM solver name (must be in whitelist)"
    )
    end_time: float = Field(
        ...,
        gt=0,
        description="Simulation end time (seconds)"
    )
    delta_t: float = Field(
        ...,
        gt=0,
        description="Time step size (seconds)"
    )
    write_interval: float = Field(
        ...,
        gt=0,
        description="Output write interval (seconds)"
    )

    @field_validator("solver_name")
    @classmethod
    def validate_solver_whitelist(cls, v: str) -> str:
        """Ensure solver is in the MVP whitelist."""
        ALLOWED_SOLVERS = {"icoFoam", "simpleFoam"}
        if v not in ALLOWED_SOLVERS:
            raise ValueError(
                f"Solver '{v}' not in whitelist. Allowed: {ALLOWED_SOLVERS}"
            )
        return v

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: float) -> float:
        """Ensure end time is reasonable for MVP."""
        if v <= 0:
            raise ValueError(f"end_time must be positive, got {v}")
        if v > 1000:
            raise ValueError(f"end_time {v} exceeds safety limit of 1000s (MVP)")
        return v

    @field_validator("delta_t")
    @classmethod
    def validate_delta_t(cls, v: float) -> float:
        """Ensure time step is positive."""
        if v <= 0:
            raise ValueError(f"delta_t must be positive, got {v}")
        return v

    @field_validator("write_interval")
    @classmethod
    def validate_write_interval(cls, v: float) -> float:
        """Ensure write interval is positive."""
        if v <= 0:
            raise ValueError(f"write_interval must be positive, got {v}")
        return v

    @model_validator(mode="after")
    def validate_time_consistency(self) -> "SolverConfig":
        """Ensure time step and write interval are consistent with end time."""
        if self.delta_t > self.end_time:
            raise ValueError(
                f"delta_t ({self.delta_t}) cannot exceed end_time ({self.end_time})"
            )
        if self.write_interval > self.end_time:
            raise ValueError(
                f"write_interval ({self.write_interval}) cannot exceed end_time ({self.end_time})"
            )
        return self


class CasePlan(BaseModel):
    """
    Complete simulation case plan.

    Represents a validated OpenFOAM case configuration including:
    - Case identification
    - Template type selection
    - Mesh parameters
    - Solver parameters

    This is the primary output from LLM-based case planning.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    case_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Case directory name (alphanumeric, underscore, hyphen only)"
    )
    template_type: str = Field(
        ...,
        description="Template identifier (e.g., 'cavity_2d', 'channel_2d')"
    )
    mesh_config: MeshConfig = Field(
        ...,
        description="Mesh generation parameters"
    )
    solver_config: SolverConfig = Field(
        ...,
        description="Solver execution parameters"
    )

    @field_validator("case_name")
    @classmethod
    def validate_case_name_safety(cls, v: str) -> str:
        """
        Ensure case name is safe for filesystem use.

        Prevents path traversal and shell injection.
        """
        if not v:
            raise ValueError("case_name cannot be empty")

        # Check for path traversal attempts
        if ".." in v:
            raise ValueError("case_name cannot contain '..'")
        if v.startswith("/"):
            raise ValueError("case_name cannot be absolute path")
        if v.startswith("."):
            raise ValueError("case_name cannot start with '.'")

        # Check for shell metacharacters
        forbidden_chars = {";", "&", "|", "$", "`", "(", ")", "<", ">", "\\", "'", '"'}
        if any(char in v for char in forbidden_chars):
            raise ValueError(f"case_name contains forbidden characters: {forbidden_chars}")

        return v

    @field_validator("template_type")
    @classmethod
    def validate_template_whitelist(cls, v: str) -> str:
        """Ensure template type is in the MVP whitelist."""
        ALLOWED_TEMPLATES = {"cavity_2d", "channel_2d"}
        if v not in ALLOWED_TEMPLATES:
            raise ValueError(
                f"Template '{v}' not in whitelist. Allowed: {ALLOWED_TEMPLATES}"
            )
        return v


class SimulationResult(BaseModel):
    """
    Result of a single OpenFOAM command execution.

    Captures all outputs and metadata from running an OpenFOAM command
    (e.g., blockMesh, checkMesh, icoFoam).
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    success: bool = Field(
        ...,
        description="Whether the command completed successfully (return_code == 0)"
    )
    stdout: str = Field(
        default="",
        description="Standard output from the command"
    )
    stderr: str = Field(
        default="",
        description="Standard error from the command"
    )
    return_code: int = Field(
        ...,
        description="Process exit code (0 = success)"
    )
    elapsed_time: float = Field(
        ...,
        ge=0,
        description="Execution time in seconds"
    )
    command: Optional[str] = Field(
        default=None,
        description="The command that was executed"
    )
    case_dir: Optional[str] = Field(
        default=None,
        description="The case directory where command was executed"
    )

    @field_validator("elapsed_time")
    @classmethod
    def validate_elapsed_time(cls, v: float) -> float:
        """Ensure elapsed time is non-negative."""
        if v < 0:
            raise ValueError(f"elapsed_time cannot be negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_success_consistency(self) -> "SimulationResult":
        """Ensure success flag matches return code."""
        expected_success = (self.return_code == 0)
        if self.success != expected_success:
            raise ValueError(
                f"success={self.success} inconsistent with return_code={self.return_code}"
            )
        return self
