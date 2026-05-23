import subprocess
from unittest.mock import patch
import pytest


class DockerOpenFOAMRunner:
    def __init__(self, container_name="easycfd-openfoam"):
        self.container_name = container_name

    def check_docker_running(self) -> bool:
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True, shell=False)
        except FileNotFoundError:
            return False
        return result.returncode == 0

    def run_command(self, cmd: str, workspace: str) -> dict:
        if not self.check_docker_running():
            return {"success": False, "stdout": "", "stderr": "Docker is not running or not installed", "returncode": 1}
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name, cmd, "-case", workspace],
                capture_output=True, text=True, shell=False,
            )
        except FileNotFoundError:
            return {"success": False, "stdout": "", "stderr": "Docker is not running or not installed", "returncode": 1}
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}


def test_default_container_name():
    assert DockerOpenFOAMRunner().container_name == "easycfd-openfoam"

@patch("subprocess.run")
def test_check_docker_running_returns_bool(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(args=["docker", "info"], returncode=0)
    assert DockerOpenFOAMRunner().check_docker_running() is True

@patch("subprocess.run")
def test_check_docker_running_returns_false_when_fails(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(args=["docker", "info"], returncode=1)
    assert DockerOpenFOAMRunner().check_docker_running() is False

@patch("subprocess.run")
def test_check_docker_running_missing_binary(mock_run):
    mock_run.side_effect = FileNotFoundError("docker")
    assert DockerOpenFOAMRunner().check_docker_running() is False

@patch("subprocess.run")
def test_run_command_returns_dict_keys(mock_run):
    mock_run.side_effect = [
        subprocess.CompletedProcess(args=["docker", "info"], returncode=0),
        subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr=""),
    ]
    result = DockerOpenFOAMRunner().run_command("checkMesh", "/tmp/ws")
    assert set(result.keys()) == {"success", "stdout", "stderr", "returncode"}

@patch("subprocess.run")
def test_run_command_docker_not_running(mock_run):
    mock_run.side_effect = FileNotFoundError("docker")
    result = DockerOpenFOAMRunner().run_command("blockMesh", "/tmp/ws")
    assert result["success"] is False
    assert "Docker" in result["stderr"]
