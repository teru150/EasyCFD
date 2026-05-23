"""
Tests for Pydantic v2 validation schemas.

Tests all validation rules, edge cases, and security constraints
for CasePlan, MeshConfig, SolverConfig, and SimulationResult.
"""

import pytest
from pydantic import ValidationError
from backend.easycfd_core.validation.schemas import (
    CasePlan,
    MeshConfig,
    SolverConfig,
    SimulationResult,
)


class TestMeshConfig:
    """Tests for MeshConfig validation."""

    def test_valid_mesh_config(self):
        """Test valid mesh configuration."""
        config = MeshConfig(
            nx=20,
            ny=20,
            nz=1,
            x_min=0.0,
            x_max=1.0,
            y_min=0.0,
            y_max=1.0,
            z_min=0.0,
            z_max=0.1,
        )
        assert config.nx == 20
        assert config.ny == 20
        assert config.nz == 1
        assert config.x_max > config.x_min
        assert config.y_max > config.y_min
        assert config.z_max > config.z_min

    def test_negative_cell_count_rejected(self):
        """Test that negative cell counts are rejected."""
        with pytest.raises(ValidationError, match="greater than 0"):
            MeshConfig(
                nx=-10,
                ny=20,
                nz=1,
                x_min=0.0,
                x_max=1.0,
                y_min=0.0,
                y_max=1.0,
                z_min=0.0,
                z_max=0.1,
            )

    def test_zero_cell_count_rejected(self):
        """Test that zero cell counts are rejected."""
        with pytest.raises(ValidationError, match="greater than 0"):
            MeshConfig(
                nx=0,
                ny=20,
                nz=1,
                x_min=0.0,
                x_max=1.0,
                y_min=0.0,
                y_max=1.0,
                z_min=0.0,
                z_max=0.1,
            )

    def test_excessive_cell_count_rejected(self):
        """Test that excessively large cell counts are rejected (MVP safety limit)."""
        with pytest.raises(ValidationError, match="exceeds safety limit"):
            MeshConfig(
                nx=2000,
                ny=20,
                nz=1,
                x_min=0.0,
                x_max=1.0,
                y_min=0.0,
                y_max=1.0,
                z_min=0.0,
                z_max=0.1,
            )

    def test_invalid_x_extent_rejected(self):
        """Test that x_min >= x_max is rejected."""
        with pytest.raises(ValidationError, match="x_min.*must be less than x_max"):
            MeshConfig(
                nx=20,
                ny=20,
                nz=1,
                x_min=1.0,
                x_max=0.0,
                y_min=0.0,
                y_max=1.0,
                z_min=0.0,
                z_max=0.1,
            )

    def test_invalid_y_extent_rejected(self):
        """Test that y_min >= y_max is rejected."""
        with pytest.raises(ValidationError, match="y_min.*must be less than y_max"):
            MeshConfig(
                nx=20,
                ny=20,
                nz=1,
                x_min=0.0,
                x_max=1.0,
                y_min=1.0,
                y_max=0.0,
                z_min=0.0,
                z_max=0.1,
            )

    def test_invalid_z_extent_rejected(self):
        """Test that z_min >= z_max is rejected."""
        with pytest.raises(ValidationError, match="z_min.*must be less than z_max"):
            MeshConfig(
                nx=20,
                ny=20,
                nz=1,
                x_min=0.0,
                x_max=1.0,
                y_min=0.0,
                y_max=1.0,
                z_min=0.1,
                z_max=0.0,
            )


class TestSolverConfig:
    """Tests for SolverConfig validation."""

    def test_valid_solver_config_icofoam(self):
        """Test valid solver configuration with icoFoam."""
        config = SolverConfig(
            solver_name="icoFoam",
            end_time=0.5,
            delta_t=0.005,
            write_interval=0.1,
        )
        assert config.solver_name == "icoFoam"
        assert config.end_time == 0.5
        assert config.delta_t == 0.005
        assert config.write_interval == 0.1

    def test_valid_solver_config_simplefoam(self):
        """Test valid solver configuration with simpleFoam."""
        config = SolverConfig(
            solver_name="simpleFoam",
            end_time=1000,
            delta_t=1.0,
            write_interval=100,
        )
        assert config.solver_name == "simpleFoam"

    def test_invalid_solver_rejected(self):
        """Test that non-whitelisted solvers are rejected."""
        with pytest.raises(ValidationError, match="not in whitelist"):
            SolverConfig(
                solver_name="potentialFoam",
                end_time=0.5,
                delta_t=0.005,
                write_interval=0.1,
            )

    def test_negative_end_time_rejected(self):
        """Test that negative end_time is rejected."""
        with pytest.raises(ValidationError, match="greater than 0"):
            SolverConfig(
                solver_name="icoFoam",
                end_time=-1.0,
                delta_t=0.005,
                write_interval=0.1,
            )

    def test_excessive_end_time_rejected(self):
        """Test that excessively large end_time is rejected (MVP safety limit)."""
        with pytest.raises(ValidationError, match="exceeds safety limit"):
            SolverConfig(
                solver_name="icoFoam",
                end_time=2000,
                delta_t=0.005,
                write_interval=0.1,
            )

    def test_negative_delta_t_rejected(self):
        """Test that negative delta_t is rejected."""
        with pytest.raises(ValidationError, match="must be positive"):
            SolverConfig(
                solver_name="icoFoam",
                end_time=0.5,
                delta_t=-0.005,
                write_interval=0.1,
            )

    def test_delta_t_exceeds_end_time_rejected(self):
        """Test that delta_t > end_time is rejected."""
        with pytest.raises(ValidationError, match="cannot exceed end_time"):
            SolverConfig(
                solver_name="icoFoam",
                end_time=0.5,
                delta_t=1.0,
                write_interval=0.1,
            )

    def test_write_interval_exceeds_end_time_rejected(self):
        """Test that write_interval > end_time is rejected."""
        with pytest.raises(ValidationError, match="cannot exceed end_time"):
            SolverConfig(
                solver_name="icoFoam",
                end_time=0.5,
                delta_t=0.005,
                write_interval=1.0,
            )


class TestCasePlan:
    """Tests for CasePlan validation."""

    def test_valid_case_plan(self):
        """Test valid complete case plan."""
        mesh_config = MeshConfig(
            nx=20,
            ny=20,
            nz=1,
            x_min=0.0,
            x_max=1.0,
            y_min=0.0,
            y_max=1.0,
            z_min=0.0,
            z_max=0.1,
        )
        solver_config = SolverConfig(
            solver_name="icoFoam",
            end_time=0.5,
            delta_t=0.005,
            write_interval=0.1,
        )
        case_plan = CasePlan(
            case_name="cavity_test_01",
            template_type="cavity_2d",
            mesh_config=mesh_config,
            solver_config=solver_config,
        )
        assert case_plan.case_name == "cavity_test_01"
        assert case_plan.template_type == "cavity_2d"
        assert case_plan.mesh_config.nx == 20
        assert case_plan.solver_config.solver_name == "icoFoam"

    def test_case_name_with_path_traversal_rejected(self):
        """Test that case names with .. are rejected (path traversal attack)."""
        mesh_config = MeshConfig(
            nx=20, ny=20, nz=1, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0, z_min=0.0, z_max=0.1
        )
        solver_config = SolverConfig(
            solver_name="icoFoam", end_time=0.5, delta_t=0.005, write_interval=0.1
        )
        with pytest.raises(ValidationError, match="cannot contain '\\.\\.'"):
            CasePlan(
                case_name="../etc/passwd",
                template_type="cavity_2d",
                mesh_config=mesh_config,
                solver_config=solver_config,
            )

    def test_case_name_with_absolute_path_rejected(self):
        """Test that absolute paths in case_name are rejected."""
        mesh_config = MeshConfig(
            nx=20, ny=20, nz=1, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0, z_min=0.0, z_max=0.1
        )
        solver_config = SolverConfig(
            solver_name="icoFoam", end_time=0.5, delta_t=0.005, write_interval=0.1
        )
        with pytest.raises(ValidationError, match="cannot be absolute path"):
            CasePlan(
                case_name="/tmp/evil",
                template_type="cavity_2d",
                mesh_config=mesh_config,
                solver_config=solver_config,
            )

    def test_case_name_with_shell_metacharacters_rejected(self):
        """Test that shell metacharacters in case_name are rejected."""
        mesh_config = MeshConfig(
            nx=20, ny=20, nz=1, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0, z_min=0.0, z_max=0.1
        )
        solver_config = SolverConfig(
            solver_name="icoFoam", end_time=0.5, delta_t=0.005, write_interval=0.1
        )
        dangerous_names = [
            "case; rm -rf /",
            "case && evil",
            "case | grep secret",
            "case$(whoami)",
            "case`ls`",
        ]
        for name in dangerous_names:
            with pytest.raises(ValidationError, match="forbidden characters"):
                CasePlan(
                    case_name=name,
                    template_type="cavity_2d",
                    mesh_config=mesh_config,
                    solver_config=solver_config,
                )

    def test_case_name_starting_with_dot_rejected(self):
        """Test that case names starting with . are rejected."""
        mesh_config = MeshConfig(
            nx=20, ny=20, nz=1, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0, z_min=0.0, z_max=0.1
        )
        solver_config = SolverConfig(
            solver_name="icoFoam", end_time=0.5, delta_t=0.005, write_interval=0.1
        )
        with pytest.raises(ValidationError, match="cannot start with '\\.'"):
            CasePlan(
                case_name=".hidden",
                template_type="cavity_2d",
                mesh_config=mesh_config,
                solver_config=solver_config,
            )

    def test_invalid_template_rejected(self):
        """Test that non-whitelisted templates are rejected."""
        mesh_config = MeshConfig(
            nx=20, ny=20, nz=1, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0, z_min=0.0, z_max=0.1
        )
        solver_config = SolverConfig(
            solver_name="icoFoam", end_time=0.5, delta_t=0.005, write_interval=0.1
        )
        with pytest.raises(ValidationError, match="not in whitelist"):
            CasePlan(
                case_name="test",
                template_type="custom_evil_template",
                mesh_config=mesh_config,
                solver_config=solver_config,
            )


class TestSimulationResult:
    """Tests for SimulationResult validation."""

    def test_valid_success_result(self):
        """Test valid successful simulation result."""
        result = SimulationResult(
            success=True,
            stdout="Mesh created successfully",
            stderr="",
            return_code=0,
            elapsed_time=1.5,
            command="blockMesh",
            case_dir="/home/user/runs/cavity_01",
        )
        assert result.success is True
        assert result.return_code == 0
        assert result.elapsed_time == 1.5

    def test_valid_failure_result(self):
        """Test valid failed simulation result."""
        result = SimulationResult(
            success=False,
            stdout="",
            stderr="Error: mesh quality check failed",
            return_code=1,
            elapsed_time=0.5,
            command="checkMesh",
            case_dir="/home/user/runs/cavity_01",
        )
        assert result.success is False
        assert result.return_code == 1

    def test_negative_elapsed_time_rejected(self):
        """Test that negative elapsed_time is rejected."""
        with pytest.raises(ValidationError, match="cannot be negative"):
            SimulationResult(
                success=True,
                return_code=0,
                elapsed_time=-1.0,
            )

    def test_inconsistent_success_flag_rejected(self):
        """Test that success=True with return_code != 0 is rejected."""
        with pytest.raises(ValidationError, match="inconsistent with return_code"):
            SimulationResult(
                success=True,
                return_code=1,
                elapsed_time=1.0,
            )

    def test_inconsistent_failure_flag_rejected(self):
        """Test that success=False with return_code == 0 is rejected."""
        with pytest.raises(ValidationError, match="inconsistent with return_code"):
            SimulationResult(
                success=False,
                return_code=0,
                elapsed_time=1.0,
            )

    def test_optional_fields_default_correctly(self):
        """Test that optional fields have correct defaults."""
        result = SimulationResult(
            success=True,
            return_code=0,
            elapsed_time=1.0,
        )
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.command is None
        assert result.case_dir is None

    def test_extra_fields_rejected(self):
        """Test that extra fields are rejected (extra='forbid')."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            SimulationResult(
                success=True,
                return_code=0,
                elapsed_time=1.0,
                extra_field="should be rejected",
            )
