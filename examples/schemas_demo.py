#!/usr/bin/env python3
"""
Demonstration of EasyCFD Pydantic v2 schemas.

Shows how to create, validate, and use the validation schemas
for case plans, mesh configs, solver configs, and simulation results.
"""

from backend.easycfd_core.validation.schemas import (
    CasePlan,
    MeshConfig,
    SolverConfig,
    SimulationResult,
)


def demo_mesh_config():
    """Demonstrate MeshConfig creation and validation."""
    print("=" * 60)
    print("MeshConfig Demonstration")
    print("=" * 60)

    # Valid mesh configuration for 2D lid-driven cavity
    mesh = MeshConfig(
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

    print(f"Created valid mesh config:")
    print(f"  Grid: {mesh.nx} x {mesh.ny} x {mesh.nz}")
    print(f"  Domain: [{mesh.x_min}, {mesh.x_max}] x [{mesh.y_min}, {mesh.y_max}] x [{mesh.z_min}, {mesh.z_max}]")
    print()

    # Show JSON export
    print("JSON representation:")
    print(mesh.model_dump_json(indent=2))
    print()


def demo_solver_config():
    """Demonstrate SolverConfig creation and validation."""
    print("=" * 60)
    print("SolverConfig Demonstration")
    print("=" * 60)

    # Valid solver configuration for transient incompressible flow
    solver = SolverConfig(
        solver_name="icoFoam",
        end_time=0.5,
        delta_t=0.005,
        write_interval=0.1,
    )

    print(f"Created valid solver config:")
    print(f"  Solver: {solver.solver_name}")
    print(f"  End time: {solver.end_time} s")
    print(f"  Time step: {solver.delta_t} s")
    print(f"  Write interval: {solver.write_interval} s")
    print(f"  Total steps: {int(solver.end_time / solver.delta_t)}")
    print()

    # Show JSON export
    print("JSON representation:")
    print(solver.model_dump_json(indent=2))
    print()


def demo_case_plan():
    """Demonstrate CasePlan creation and validation."""
    print("=" * 60)
    print("CasePlan Demonstration")
    print("=" * 60)

    # Create complete case plan
    mesh = MeshConfig(
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

    solver = SolverConfig(
        solver_name="icoFoam",
        end_time=0.5,
        delta_t=0.005,
        write_interval=0.1,
    )

    case = CasePlan(
        case_name="cavity_demo_01",
        template_type="cavity_2d",
        mesh_config=mesh,
        solver_config=solver,
    )

    print(f"Created valid case plan:")
    print(f"  Case name: {case.case_name}")
    print(f"  Template: {case.template_type}")
    print(f"  Mesh cells: {case.mesh_config.nx * case.mesh_config.ny * case.mesh_config.nz}")
    print(f"  Solver: {case.solver_config.solver_name}")
    print()

    # Show JSON export
    print("JSON representation:")
    print(case.model_dump_json(indent=2))
    print()


def demo_simulation_result():
    """Demonstrate SimulationResult creation and validation."""
    print("=" * 60)
    print("SimulationResult Demonstration")
    print("=" * 60)

    # Successful blockMesh execution
    success_result = SimulationResult(
        success=True,
        stdout="Mesh created successfully\nWriting polyMesh\nEnd",
        stderr="",
        return_code=0,
        elapsed_time=1.23,
        command="blockMesh",
        case_dir="/home/user/runs/cavity_demo_01",
    )

    print(f"Successful result:")
    print(f"  Success: {success_result.success}")
    print(f"  Command: {success_result.command}")
    print(f"  Elapsed: {success_result.elapsed_time:.2f} s")
    print(f"  Return code: {success_result.return_code}")
    print()

    # Failed checkMesh execution
    failure_result = SimulationResult(
        success=False,
        stdout="Checking mesh...",
        stderr="***Error in mesh quality: negative volumes detected",
        return_code=1,
        elapsed_time=0.45,
        command="checkMesh",
        case_dir="/home/user/runs/cavity_demo_01",
    )

    print(f"Failed result:")
    print(f"  Success: {failure_result.success}")
    print(f"  Command: {failure_result.command}")
    print(f"  Elapsed: {failure_result.elapsed_time:.2f} s")
    print(f"  Return code: {failure_result.return_code}")
    print(f"  Error: {failure_result.stderr[:50]}...")
    print()


def demo_validation_errors():
    """Demonstrate validation error handling."""
    print("=" * 60)
    print("Validation Error Demonstration")
    print("=" * 60)

    # Test case name with path traversal
    print("Testing dangerous case name: '../etc/passwd'")
    try:
        mesh = MeshConfig(
            nx=20, ny=20, nz=1,
            x_min=0.0, x_max=1.0,
            y_min=0.0, y_max=1.0,
            z_min=0.0, z_max=0.1,
        )
        solver = SolverConfig(
            solver_name="icoFoam",
            end_time=0.5,
            delta_t=0.005,
            write_interval=0.1,
        )
        CasePlan(
            case_name="../etc/passwd",
            template_type="cavity_2d",
            mesh_config=mesh,
            solver_config=solver,
        )
    except Exception as e:
        print(f"  Correctly rejected: {e}")
    print()

    # Test invalid solver
    print("Testing invalid solver: 'potentialFoam'")
    try:
        SolverConfig(
            solver_name="potentialFoam",
            end_time=0.5,
            delta_t=0.005,
            write_interval=0.1,
        )
    except Exception as e:
        print(f"  Correctly rejected: {e}")
    print()

    # Test inconsistent success flag
    print("Testing inconsistent result: success=True with return_code=1")
    try:
        SimulationResult(
            success=True,
            return_code=1,
            elapsed_time=1.0,
        )
    except Exception as e:
        print(f"  Correctly rejected: {e}")
    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("#" * 60)
    print("# EasyCFD Pydantic v2 Schemas Demonstration")
    print("#" * 60)
    print()

    demo_mesh_config()
    demo_solver_config()
    demo_case_plan()
    demo_simulation_result()
    demo_validation_errors()

    print("=" * 60)
    print("Demonstration complete!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
