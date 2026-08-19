#!/usr/bin/env python
"""Test that Sphinx documentation builds correctly.

This script performs a test build of the documentation to verify that:
1. The documentation builds without errors
2. All cross-references are working
3. Inheritance information is properly displayed

Usage:
    python test_build.py

Returns:
    0 if the build succeeded, non-zero otherwise
"""

import os
import subprocess
import sys
import pytest
from pathlib import Path

try:
    import sphinx  # noqa: F401

    sphinx_available = True
except ImportError:
    sphinx_available = False


def _sphinx_command(docs_dir, build_dir):
    return [
        sys.executable,
        "-m",
        "sphinx",
        "-W",  # Treat warnings as errors
        "--keep-going",
        "-b",
        "html",
        "-d",
        str(build_dir / "doctrees"),
        str(docs_dir),
        str(build_dir / "html"),
    ]


def _run_sphinx():
    docs_dir = Path(__file__).parent
    build_dir = docs_dir / "_build" / "test"
    os.makedirs(build_dir, exist_ok=True)
    return subprocess.run(
        _sphinx_command(docs_dir, build_dir),
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(not sphinx_available, reason="sphinx is not installed")
def test_sphinx_build():
    """Test that the Sphinx documentation builds correctly."""
    result = _run_sphinx()
    if result.returncode != 0:
        pytest.fail(
            "sphinx-build failed with return code "
            f"{result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


if __name__ == "__main__":
    if not sphinx_available:
        print("sphinx is not installed in this Python environment")
        sys.exit(1)
    result = _run_sphinx()
    if result.returncode == 0:
        print("Documentation build succeeded!")
    else:
        print(f"Documentation build failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    sys.exit(result.returncode)
