from {{ cookiecutter.package_name }} import (
    __version__,
)


def test_version_comes_from_the_installed_package() -> None:
    assert __version__ == "0.1.0"
