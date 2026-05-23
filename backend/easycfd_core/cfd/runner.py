from __future__ import annotations

import subprocess
import time
from typing import Any

from easycfd_core.validation.schemas import SimulationResult


class OpenFOAMRunner:
    def __init__(self, workspace_root: str, case_dir: str) -> None:
        self.workspace_root = workspace_root
        self.case_dir = case_dir

    def run_command(
        self,
        command: str,
        additional_args: list[str] | None = None,
    ) -> SimulationResult:
        args: list[str] = [command, "-case", self.case_dir]

        if additional_args is not None:
            args.extend(additional_args)

        start_time = time.monotonic()
        completed_process = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            cwd=self.workspace_root,  # ensures relative case_dir resolves correctly
        )
        elapsed_time = time.monotonic() - start_time

        return SimulationResult(
            success=completed_process.returncode == 0,
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            return_code=completed_process.returncode,
            elapsed_time=elapsed_time,
            command=command,
            case_dir=self.case_dir,
        )


class DockerOpenFOAMRunner:
    """Runs OpenFOAM commands inside a Docker container.

    Callers MUST validate cmd against safety.py whitelist before calling run_command.
    """

    def __init__(self, container_name: str = "easycfd-openfoam") -> None:
        self.container_name = container_name

    def check_docker_running(self) -> bool:
        """Return True if Docker daemon is reachable."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def run_command(self, cmd: str, workspace: str) -> dict[str, Any]:
        """Run a prevalidated OpenFOAM command inside the Docker container.

        Args:
            cmd: Prevalidated command (must be in ALLOWED_COMMANDS).
            workspace: Working directory inside the container.

        Returns:
            {"success": bool, "stdout": str, "stderr": str, "returncode": int}
        """
        try:
            result = subprocess.run(
                ["docker", "exec", "-w", workspace, self.container_name, cmd],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=300,
                shell=False,
                check=False,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as exc:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "returncode": -1,
            }
