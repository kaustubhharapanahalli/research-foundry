"""Dependabot manifest directories use the syntax their keys accept."""

from pathlib import Path
from typing import cast

import pytest
import yaml
from tests.conftest import ROOT
from tools import check_pins

DIRECTORY_GLOB_CHARACTERS = "*?[]{}"


def _load_config(path: Path) -> dict[str, object]:
    """Load a Dependabot YAML configuration.

    Args:
        path: Path to the Dependabot configuration.

    Returns:
        The parsed configuration mapping.
    """
    config: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(config, dict)
    return cast(dict[str, object], config)


def _check_dependabot_directories(
    config: dict[str, object], repository_root: Path
) -> None:
    """Check directory values against Dependabot's accepted syntax.

    Args:
        config: Parsed Dependabot configuration.
        repository_root: Root used to resolve plural-directory globs.

    Raises:
        AssertionError: If a directory value is invalid or matches nothing.
    """
    updates = config["updates"]
    assert isinstance(updates, list)

    for update in updates:
        assert isinstance(update, dict)

        directory = update.get("directory")
        if directory is not None:
            assert isinstance(directory, str)
            assert not any(
                character in directory
                for character in DIRECTORY_GLOB_CHARACTERS
            ), f"directory must be literal: {directory}"

        directories = update.get("directories")
        if directories is not None:
            assert isinstance(directories, list)
            for pattern in directories:
                assert isinstance(pattern, str)
                assert (
                    "{" not in pattern and "}" not in pattern
                ), f"directories does not accept brace globs: {pattern}"
                matches = repository_root.glob(pattern.removeprefix("/"))
                assert any(
                    path.is_dir() for path in matches
                ), f"directories glob matches no directory: {pattern}"


def _check_dependabot_npm_holds(config: dict[str, object]) -> None:
    """Check that npm major ignores match the recorded frontend holds.

    Args:
        config: Parsed Dependabot configuration.

    Raises:
        AssertionError: If the npm ignores and recorded holds differ.
    """
    expected = {
        package for hold in check_pins.HOLDS for package in hold.held_packages
    }
    updates = config["updates"]
    assert isinstance(updates, list)
    npm_updates = [
        update
        for update in updates
        if isinstance(update, dict)
        and update.get("package-ecosystem") == "npm"
    ]
    assert len(npm_updates) == 1
    ignores = npm_updates[0].get("ignore")
    assert isinstance(ignores, list)
    actual: list[str] = []
    for rule in ignores:
        assert isinstance(rule, dict)
        dependency = rule.get("dependency-name")
        update_types = rule.get("update-types")
        assert isinstance(dependency, str)
        assert update_types == ["version-update:semver-major"]
        actual.append(dependency)
    assert len(actual) == len(expected) and set(actual) == expected, (
        f"npm major holds differ: expected {sorted(expected)}, "
        f"got {sorted(actual)}"
    )


@pytest.mark.unit
def test_dependabot_directories_are_valid() -> None:
    """Repository directory entries obey Dependabot's path rules."""
    config = _load_config(ROOT / ".github" / "dependabot.yml")

    _check_dependabot_directories(config, ROOT)


@pytest.mark.unit
def test_dependabot_npm_major_ignores_match_recorded_holds() -> None:
    """The npm major ignores stay synchronized with the pin report."""
    config = _load_config(ROOT / ".github" / "dependabot.yml")

    _check_dependabot_npm_holds(config)


@pytest.mark.unit
def test_dependabot_npm_hold_guard_refuses_a_missing_package() -> None:
    """The npm hold guard refuses a config missing a recorded package."""
    config = _load_config(ROOT / ".github" / "dependabot.yml")
    updates = config["updates"]
    assert isinstance(updates, list)
    npm_update = next(
        update
        for update in updates
        if isinstance(update, dict)
        and update.get("package-ecosystem") == "npm"
    )
    ignores = npm_update.get("ignore")
    assert isinstance(ignores, list)
    del ignores[0]

    with pytest.raises(AssertionError, match="npm major holds differ"):
        _check_dependabot_npm_holds(config)


@pytest.mark.unit
def test_dependabot_directory_guard_refuses_brace_globs(
    tmp_path: Path,
) -> None:
    """The singular directory key refuses a templated brace path."""
    config: dict[str, object] = {"updates": [{"directory": "/software/{{x}}"}]}

    with pytest.raises(AssertionError, match="directory must be literal"):
        _check_dependabot_directories(config, tmp_path)


@pytest.mark.unit
def test_dependabot_holds_the_python_image_to_its_minor_line() -> None:
    """The docker entry offers Python patch tags only, never a new minor."""
    config = _load_config(ROOT / ".github" / "dependabot.yml")
    updates = config["updates"]
    assert isinstance(updates, list)
    docker = [
        update
        for update in updates
        if isinstance(update, dict)
        and update.get("package-ecosystem") == "docker"
    ]
    assert len(docker) == 1
    ignores = docker[0].get("ignore")
    assert isinstance(ignores, list)
    python = [
        rule
        for rule in ignores
        if isinstance(rule, dict) and rule.get("dependency-name") == "python"
    ]
    assert len(python) == 1
    assert set(python[0].get("update-types", [])) == {
        "version-update:semver-minor",
        "version-update:semver-major",
    }
