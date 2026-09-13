import subprocess
import sys
from pathlib import Path


def test_mock_portal_standalone_test_suite():
    """Verify that the isolated mock-portal backend passes its test suite on its own port/context."""
    repo_root = Path(__file__).resolve().parents[3]
    mock_portal_backend = repo_root / "mock-portal" / "backend"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd=str(mock_portal_backend),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Mock portal test suite failed:\n{result.stdout}\n{result.stderr}"
    assert "passed" in result.stdout
    assert "failed" not in result.stdout

