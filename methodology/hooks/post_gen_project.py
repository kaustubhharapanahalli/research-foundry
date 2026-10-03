"""Remove the files of components the project did not choose.

Cookiecutter runs this inside the generated project, without asking. It
only deletes files inside that project: no network, nothing outside it.
"""

# Each template hook is a standalone entrypoint, so guards cannot be shared.
# pylint: disable=duplicate-code

import shutil
import sys
from pathlib import Path

# Rendered by cookiecutter before it runs; typed as str so a type checker
# reading the unrendered file does not see two unequal literals.
ANSWERS: dict[str, str] = {
    "ml_pytorch": "{{ cookiecutter.ml_pytorch }}",
    "license": "{{ cookiecutter.license }}",
    "public_docs": "{{ cookiecutter.public_docs }}",
    "contact_email": "{{ cookiecutter.contact_email }}",
    "dataset_registry": "{{ cookiecutter.dataset_registry }}",
    "run_records": "{{ cookiecutter.run_records }}",
}
PYTHON_VERSION = "{{ cookiecutter.python_version }}"
PYTHON_FLOOR = "{{ cookiecutter._python_floor }}"
PACKAGE = Path("src") / "{{ cookiecutter.package_name }}"

ML_ONLY = [
    PACKAGE / "seeding.py",
    PACKAGE / "device.py",
    PACKAGE / "threads.py",
    PACKAGE / "runrecord.py",
    Path("tests") / "unit" / "test_seeding.py",
    Path("tests") / "unit" / "test_device.py",
    Path("tests") / "unit" / "test_threads.py",
    Path("tests") / "unit" / "test_runrecord.py",
    Path("tests") / "functional" / "test_determinism.py",
    Path("docs_src") / "repeat_a_run.py",
    Path("docs") / "how-to" / "repeat-a-run.md",
    Path("docs") / "explanation",
]
STORE_ONLY = [
    PACKAGE / "sidecars.py",
    Path("tests") / "unit" / "test_sidecars.py",
    Path("tests") / "functional" / "test_dispatched_run.py",
]
DOCS_ONLY = [
    Path("docs") / "conf.py",
    Path("docs") / "index.md",
    Path("docs") / "_templates",
    Path("docs") / "api",
    Path("docs") / "how-to",
    Path("docs") / "explanation",
    Path("docs_src"),
    Path("make") / "docs.mk",
    Path(".readthedocs.yaml"),
    Path("CODE_OF_CONDUCT.md"),
    Path("CONTRIBUTING.md"),
    Path("SECURITY.md"),
    Path("CITATION.cff"),
    Path("tests") / "functional" / "test_docs_src.py",
    Path("tests") / "functional" / "test_project_files.py",
]


def remove(path: Path) -> None:
    """Delete a file or folder, if an earlier removal has not already."""
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def main() -> None:
    """Refuse an incomplete public project, then delete what is unused."""
    if tuple(map(int, PYTHON_VERSION.split("."))) < tuple(
        map(int, PYTHON_FLOOR.split("."))
    ):
        sys.exit("python_version must be 3.12 or newer.")
    if ANSWERS["public_docs"] == "yes" and ANSWERS["license"] == "none":
        # Public documentation standard, PD14: a public repository has a
        # licence. Without one, nobody may use the code it documents.
        sys.exit("public_docs=yes needs a licence: choose Apache-2.0 or MIT.")
    if ANSWERS["public_docs"] == "yes" and "@" not in ANSWERS["contact_email"]:
        # Conduct and security reports need somewhere to go. The address is
        # typed at generation; it is never a default or taken from a profile.
        sys.exit("public_docs=yes needs contact_email: type the address.")
    records = ANSWERS["run_records"] == "yes"
    if records and ANSWERS["ml_pytorch"] != "yes":
        # The witness records the device and its memory, which only a
        # PyTorch run has.
        sys.exit("run_records=yes needs ml_pytorch=yes.")
    if not records:
        for path in STORE_ONLY:
            remove(path)
    if ANSWERS["ml_pytorch"] != "yes":
        for path in ML_ONLY:
            remove(path)
    if ANSWERS["public_docs"] != "yes":
        for path in DOCS_ONLY:
            remove(path)
    if ANSWERS["license"] == "none":
        Path("LICENSE").unlink()
    if ANSWERS["dataset_registry"] != "yes":
        # Only the project's root holds one: a paper project's workspace
        # does, so its methodology repository must not hold a second.
        remove(Path("datasets"))


if __name__ == "__main__":
    main()
