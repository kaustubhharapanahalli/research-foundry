import subprocess
import sys

IMPORT = "import {{ cookiecutter.package_name }}"


def test_package_imports_in_a_fresh_interpreter() -> None:
    # Without [build-system], `uv sync` does not install the project and
    # this import fails with ModuleNotFoundError.
    done = subprocess.run(
        [sys.executable, "-c", IMPORT],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
