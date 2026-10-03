"""Print the installed version of {{ cookiecutter.package_name }}.

The "Check the install" guide includes this file, and a test runs it.
"""

import {{ cookiecutter.package_name }}


def main() -> None:
    """Import the package and print its version."""
    print({{ cookiecutter.package_name }}.__version__)


if __name__ == "__main__":
    main()
