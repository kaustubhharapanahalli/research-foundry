"""Check a workspace against the shipped path contract.

Examples:
    >>> callable(check_layout) and callable(parse_local_rules)
    True
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from research_foundry.templates import (
    FoundryError,
    create_project,
    describe_questions,
    template_root,
)

_LOCAL_RULES = re.compile(
    r"^## Local rules\s*$\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
_BACKTICK = re.compile(r"`([^`]+)`")
_KNOWN_EXTENSIONS = {
    ".bib",
    ".cjs",
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".ipynb",
    ".lock",
    ".log",
    ".json",
    ".md",
    ".pdf",
    ".py",
    ".rst",
    ".sh",
    ".tex",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
_KINDS = {"file", "dir", "runtime"}


@dataclass(frozen=True)
class LayoutFinding:
    """One missing, extra, or incomplete workspace path.

    Args:
        kind: The finding category.
        path: A workspace-relative path.

    Examples:
        >>> LayoutFinding("extra", "archive").kind
        'extra'
    """

    kind: str
    path: str


@dataclass(frozen=True)
class LayoutResult:
    """The deterministic findings from one workspace check.

    Args:
        findings: Findings sorted by category and path.

    Examples:
        >>> LayoutResult(()).report
        'layout matches the template contract'
    """

    findings: tuple[LayoutFinding, ...]

    @property
    def report(self) -> str:
        """Return the plain-text report used by the command and tool.

        Returns:
            One line per finding, or the successful match message.

        Examples:
            >>> LayoutResult((LayoutFinding("extra", "archive"),)).report
            'extra: archive'
        """
        if not self.findings:
            return "layout matches the template contract"
        return "\n".join(
            f"{finding.kind}: {finding.path}" for finding in self.findings
        )


def _contract_target(path: str) -> str:
    """Resolve a placeholder or glob to the fixed path prefix."""
    components = path.strip("/").split("/")
    for index, component in enumerate(components):
        if "<" in component or "*" in component:
            components = components[:index]
            break
    path = "/".join(components)
    target = PurePosixPath(path.rstrip("/")).as_posix()
    if target in {"", "."} or target.startswith("../"):
        raise ValueError(f"invalid contract path {path!r}")
    return target


def _load_contract() -> tuple[set[str], list[dict[str, str]]]:
    """Load and validate the contract included with the workspace template."""
    path = template_root() / "workspace" / "contract.json"
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FoundryError(
            f"The workspace contract at {path} is unreadable; reinstall "
            "research-foundry."
        ) from error
    if not isinstance(value, dict):
        raise FoundryError(
            f"The workspace contract at {path} is invalid; reinstall "
            "research-foundry."
        )
    about = value.get("about")
    generated = value.get("generated")
    entries = value.get("entries")
    if (
        not isinstance(about, str)
        or not about.strip()
        or not isinstance(generated, list)
        or not all(isinstance(item, str) and item for item in generated)
        or not isinstance(entries, list)
    ):
        raise FoundryError(
            f"The workspace contract at {path} is invalid; reinstall "
            "research-foundry."
        )
    parsed: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("entry must be an object")
            entry_path = entry.get("path")
            kind = entry.get("kind")
            used_by = entry.get("used_by")
            if not isinstance(entry_path, str) or not entry_path:
                raise ValueError("entry path is invalid")
            if not isinstance(kind, str) or kind not in _KINDS:
                raise ValueError("entry kind is invalid")
            if not isinstance(used_by, str) or not used_by.strip():
                raise ValueError("entry fields are invalid")
            target = _contract_target(entry_path)
            if target in seen:
                raise ValueError(f"duplicate contract path {entry_path!r}")
            seen.add(target)
            parsed.append({"path": entry_path, "target": target, "kind": kind})
    except ValueError as error:
        raise FoundryError(
            f"The workspace contract at {path} is invalid; reinstall "
            "research-foundry."
        ) from error
    return set(generated), parsed


def _top_level_files(project: Path) -> set[str]:
    """List indexed and visible untracked files, excluding ignored paths."""
    try:
        completed = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=project,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise FoundryError(
            f"{project} is not a Git repository; initialize Git in the "
            "workspace root and retry."
        ) from error
    return {
        PurePosixPath(name.decode("utf-8")).parts[0]
        for name in completed.stdout.split(b"\0")
        if name
    }


def _require_workspace(project: Path) -> Mapping[str, object] | None:
    """Refuse unrelated repositories and parse optional render metadata."""
    record_path = project / ".cruft.json"
    if not record_path.is_file():
        if not any(
            (project / candidate).exists()
            for candidate in (
                "AGENTS.md",
                "datasets/registry.yaml",
                "experiments/configs",
                "methodology/theory",
                "advisor-logs",
            )
        ):
            raise FoundryError(
                f"{project} does not look like a workspace; run this command "
                "at the root of a rendered workspace."
            )
        return None
    try:
        value: object = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FoundryError(
            f"{record_path} is unreadable; repair or remove it and retry."
        ) from error
    if not isinstance(value, dict) or value.get("directory") not in (
        None,
        "workspace",
    ):
        raise FoundryError(
            f"{project} is not a workspace; run this command at the root "
            "of a rendered workspace."
        )
    return value


def _rendered_top_level(
    project: Path, cruft: Mapping[str, object] | None
) -> set[str]:
    """Render the template in a temporary directory to learn its top level."""
    answers: dict[str, str] = {}
    if cruft is not None:
        context = cruft.get("context")
        cookiecutter_context = (
            context.get("cookiecutter") if isinstance(context, dict) else None
        )
        if cookiecutter_context is not None and not isinstance(
            cookiecutter_context, dict
        ):
            raise FoundryError(
                f"{project / '.cruft.json'} has invalid answers; repair "
                "its context and retry."
            )
        allowed = {
            question.name for question in describe_questions("workspace")
        }
        if isinstance(cookiecutter_context, dict):
            answers = {
                name: value
                for name, value in cookiecutter_context.items()
                if name in allowed and isinstance(value, str)
            }
    answers.setdefault("repo_name", project.name)
    with tempfile.TemporaryDirectory(
        prefix="research-foundry-layout-"
    ) as temporary:
        rendered = create_project(
            "workspace",
            answers,
            Path(temporary),
            write_cruft=False,
        )
        return {item.name for item in rendered.iterdir()}


def _local_rule_target(token: str) -> str:
    """Normalize a backticked template path to its declared prefix."""
    components = (
        token.strip().removeprefix("./").lstrip("/").strip("/").split("/")
    )
    for index, component in enumerate(components):
        if "<" in component or "*" in component:
            components = components[:index]
            break
    path = "/".join(components)
    return path.rstrip("/")


def parse_local_rules(
    text: str, top_level_names: set[str] | None = None
) -> set[str]:
    """Extract normalized path declarations from the Local rules section.

    Args:
        text: The full workspace instruction file.
        top_level_names: Existing top-level names that make a bare token a
            recognizable path.

    Returns:
        Declared relative paths, with patterns reduced to their fixed prefix.

    Examples:
        >>> parse_local_rules(chr(10).join([
        ...     "## Local rules", "- `archive/` is allowed."
        ... ]))
        {'archive'}
    """
    section = _LOCAL_RULES.search(text)
    if section is None:
        return set()
    present = top_level_names or set()
    result: set[str] = set()
    for match in _BACKTICK.finditer(section.group(1)):
        token = match.group(1).strip()
        if (
            "/" in token
            or token in present
            or PurePosixPath(token).suffix in _KNOWN_EXTENSIONS
        ):
            normalized = _local_rule_target(token)
            if normalized:
                result.add(normalized)
    return result


def _is_declared(path: str, declarations: set[str]) -> bool:
    """Return whether an exact or more specific declaration covers a path."""
    return any(
        declaration == path or declaration.startswith(path + "/")
        for declaration in declarations
    )


def _workspace_rules(
    project: Path, present: set[str]
) -> tuple[Path, bool, set[str]]:
    """Read the Local rules section and normalize its declared paths."""
    agents_path = project / "AGENTS.md"
    try:
        text = (
            agents_path.read_text(encoding="utf-8")
            if agents_path.is_file()
            else ""
        )
    except (OSError, UnicodeError) as error:
        raise FoundryError(
            f"{agents_path} is unreadable; restore or repair it and retry."
        ) from error
    has_section = _LOCAL_RULES.search(text) is not None
    return agents_path, has_section, parse_local_rules(text, present)


def _missing_contract_paths(
    project: Path,
    entries: list[dict[str, str]],
    declarations: set[str],
) -> list[LayoutFinding]:
    """Find required contract paths absent from disk."""
    missing: list[LayoutFinding] = []
    for entry in entries:
        if entry["kind"] == "runtime":
            continue
        target = entry["target"]
        item = project / target
        exists = item.is_file() if entry["kind"] == "file" else item.is_dir()
        if not exists and not _is_declared(target, declarations):
            missing.append(LayoutFinding("missing", target))
    return missing


def _extra_top_level_paths(
    present: set[str], expected: set[str], declarations: set[str]
) -> list[LayoutFinding]:
    """Find undeclared top-level paths outside the rendered template."""
    return [
        LayoutFinding("extra", name)
        for name in present - expected
        if not _is_declared(name, declarations)
    ]


def check_layout(path: Path) -> LayoutResult:
    """Compare a Git workspace with its rendered template and path contract.

    Args:
        path: The workspace root.

    Returns:
        Findings in stable order; an empty result means the layout matches.

    Raises:
        FoundryError: If the path is not a workspace, Git root, or the
            packaged contract cannot be read.

    Examples:
        >>> callable(check_layout)
        True
    """
    project = path.expanduser().resolve()
    if not project.is_dir():
        raise FoundryError(
            f"{project} is not a directory; choose a workspace directory."
        )
    try:
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise FoundryError(
            f"{project} is not a Git repository; initialize Git in the "
            "workspace root and retry."
        ) from error
    if Path(git_root).resolve() != project:
        raise FoundryError(
            f"{project} is not the Git repository root; run the command at "
            "the workspace root."
        )

    generated, entries = _load_contract()
    cruft = _require_workspace(project)
    present = _top_level_files(project)
    entry_directories = {
        entry["target"]
        for entry in entries
        if entry["kind"] in {"dir", "runtime"}
        and (project / entry["target"]).is_dir()
    }
    present.update(
        PurePosixPath(directory).parts[0] for directory in entry_directories
    )
    agents_path, has_local_rules, declarations = _workspace_rules(
        project, present
    )
    expected = _rendered_top_level(project, cruft)
    expected.update(generated)
    expected.update(
        PurePosixPath(entry["target"]).parts[0]
        for entry in entries
        if entry["kind"] == "runtime"
    )

    findings = _missing_contract_paths(project, entries, declarations)
    if not agents_path.is_file() or not has_local_rules:
        findings.append(LayoutFinding("missing-local-rules", "AGENTS.md"))
    findings.extend(_extra_top_level_paths(present, expected, declarations))
    return LayoutResult(
        tuple(sorted(findings, key=lambda item: (item.kind, item.path)))
    )


__all__ = [
    "LayoutFinding",
    "LayoutResult",
    "check_layout",
    "parse_local_rules",
]
