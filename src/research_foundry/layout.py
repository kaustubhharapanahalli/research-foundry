"""Check a workspace against the shipped path contract.

Examples:
    >>> callable(check_layout) and callable(parse_local_rules)
    True
"""

from __future__ import annotations

import json
import posixpath
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

_LOCAL_RULES_HEADING = re.compile(
    r"^## Local rules(?:\s+.*)?\s*$", re.IGNORECASE
)
_LAYOUT_RULE = re.compile(
    r"^\s*[-*+]\s+(?:\*\*(Moved|Dropped):\*\*|(Moved|Dropped):)\s*(.*)$",
    re.IGNORECASE,
)
_BACKTICK = re.compile(r"`([^`\n]+)`")
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


@dataclass(frozen=True)
class LayoutRule:
    """An explicit change to a required workspace path.

    Args:
        action: Either ``Moved`` or ``Dropped``.
        target: The normalized contract path being changed.
        new_path: The destination of a moved path, if applicable.

    Examples:
        >>> LayoutRule("Dropped", "baselines", None).action
        'Dropped'
    """

    action: str
    target: str
    new_path: str | None


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


def _git_paths(project: Path) -> set[str]:
    """List indexed and visible untracked paths, excluding ignored paths."""
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
        PurePosixPath(name.decode("utf-8")).as_posix()
        for name in completed.stdout.split(b"\0")
        if name
    }


def _top_level_names(paths: set[str]) -> set[str]:
    """Return each root item represented by a Git-listed path."""
    return {PurePosixPath(path).parts[0] for path in paths}


def _entry_is_present(entry: Mapping[str, str], git_paths: set[str]) -> bool:
    """Check a contract entry using only paths visible to Git."""
    target = entry["target"]
    if entry["kind"] == "file":
        return target in git_paths
    if entry["kind"] == "dir":
        return any(path.startswith(target + "/") for path in git_paths)
    return True


def _require_workspace(
    project: Path,
    entries: list[dict[str, str]],
    git_paths: set[str],
) -> Mapping[str, object] | None:
    """Refuse unrelated repositories and parse optional render metadata."""
    record_path = project / ".cruft.json"
    if not record_path.is_file():
        required = [entry for entry in entries if entry["kind"] != "runtime"]
        present_count = sum(
            _entry_is_present(entry, git_paths) for entry in required
        )
        if "AGENTS.md" not in git_paths or present_count <= len(required) / 2:
            raise FoundryError(
                f"{project} does not look like a workspace; run this command "
                "at the root of a rendered workspace or restore its required "
                "paths."
            )
        return None
    try:
        value: object = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FoundryError(
            f"{record_path} is unreadable; repair or remove it and retry."
        ) from error
    if not isinstance(value, dict):
        raise FoundryError(
            f"{project} is not a workspace; run this command at the root "
            "of a rendered workspace."
        )
    directory = value.get("directory")
    context = value.get("context")
    if context is not None and not isinstance(context, dict):
        raise FoundryError(
            f"{record_path} has invalid answers; repair its context and retry."
        )
    cookiecutter_context = (
        context.get("cookiecutter") if isinstance(context, dict) else None
    )
    if cookiecutter_context is not None and not isinstance(
        cookiecutter_context, dict
    ):
        raise FoundryError(
            f"{record_path} has invalid answers; repair its context and retry."
        )
    template_kind = (
        cookiecutter_context.get("_template_kind")
        if isinstance(cookiecutter_context, dict)
        else None
    )
    if template_kind is not None and template_kind != "workspace":
        raise FoundryError(
            f"{project} is not a workspace; run this command at the root "
            "of a rendered workspace."
        )
    if "directory" in value:
        recognized = directory == "workspace"
    else:
        recognized = template_kind == "workspace"
    if not recognized:
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


def _local_rule_target(token: str) -> str | None:
    """Normalize a valid workspace-relative backticked path."""
    if (
        token.startswith("/")
        or any(character.isspace() for character in token)
        or "://" in token
    ):
        return None
    normalized_path = posixpath.normpath(token)
    if normalized_path in {"..", "."} or normalized_path.startswith("../"):
        return None
    components = normalized_path.removeprefix("./").strip("/").split("/")
    for index, component in enumerate(components):
        if "<" in component or "*" in component:
            components = components[:index]
            break
    path = "/".join(components)
    return path.rstrip("/") or None


def _local_rules_section(text: str) -> str | None:
    """Return the Local rules body, excluding fenced code blocks."""
    lines = text.splitlines()
    in_section = False
    fence: str | None = None
    section_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            continue
        if not in_section:
            if _LOCAL_RULES_HEADING.match(line):
                in_section = True
            continue
        if line.startswith("## "):
            break
        section_lines.append(line)
    return "\n".join(section_lines) if in_section else None


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
    section = _local_rules_section(text)
    if section is None:
        return set()
    present = top_level_names or set()
    result: set[str] = set()
    for line in section.splitlines():
        if _LAYOUT_RULE.match(line):
            continue
        for match in _BACKTICK.finditer(line):
            token = match.group(1)
            if (
                "/" in token
                or token in present
                or PurePosixPath(token).suffix in _KNOWN_EXTENSIONS
            ):
                normalized = _local_rule_target(token)
                if normalized is not None:
                    result.add(normalized)
    return result


def parse_layout_rules(text: str) -> tuple[LayoutRule, ...]:
    r"""Parse explicit Moved and Dropped rules from Local rules.

    Args:
        text: The full workspace instruction file.

    Returns:
        Valid layout rules in document order.

    Examples:
        >>> parse_layout_rules(
        ...     "## Local rules\n- Moved: `baselines/` to `vendor/`"
        ... )
        (LayoutRule(action='Moved', target='baselines', new_path='vendor'),)
    """
    section = _local_rules_section(text)
    if section is None:
        return ()
    result: list[LayoutRule] = []
    for line in section.splitlines():
        rule_match = _LAYOUT_RULE.match(line)
        if rule_match is None:
            continue
        action = (
            rule_match.group(1) or rule_match.group(2) or ""
        ).capitalize()
        paths = [
            path
            for match in _BACKTICK.finditer(rule_match.group(3))
            if (path := _local_rule_target(match.group(1))) is not None
        ]
        if not paths or action == "Moved" and len(paths) < 2:
            continue
        result.append(
            LayoutRule(
                action, paths[0], paths[1] if action == "Moved" else None
            )
        )
    return tuple(result)


def _workspace_rules(
    project: Path, present: set[str]
) -> tuple[bool, set[str], tuple[LayoutRule, ...]]:
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
    has_section = _local_rules_section(text) is not None
    return (
        has_section,
        parse_local_rules(text, present),
        parse_layout_rules(text),
    )


def _missing_contract_paths(
    entries: list[dict[str, str]],
    git_paths: set[str],
    rules: tuple[LayoutRule, ...],
) -> list[LayoutFinding]:
    """Find required contract paths absent from Git and moved destinations."""
    missing: list[LayoutFinding] = []
    contract_targets = {
        entry["target"] for entry in entries if entry["kind"] != "runtime"
    }
    applicable_rules = tuple(
        rule for rule in rules if rule.target in contract_targets
    )
    dropped_targets = {
        rule.target for rule in applicable_rules if rule.action == "Dropped"
    }
    moved_targets = {
        rule.target for rule in applicable_rules if rule.action == "Moved"
    }
    for entry in entries:
        if entry["kind"] == "runtime":
            continue
        target = entry["target"]
        if (
            target not in dropped_targets
            and target not in moved_targets
            and not _entry_is_present(entry, git_paths)
        ):
            missing.append(LayoutFinding("missing", target))
    for rule in applicable_rules:
        if (
            rule.action == "Moved"
            and rule.new_path is not None
            and not any(
                path == rule.new_path or path.startswith(rule.new_path + "/")
                for path in git_paths
            )
        ):
            missing.append(LayoutFinding("missing", rule.new_path))
    return missing


def _extra_top_level_paths(
    present: set[str],
    expected: set[str],
    declarations: set[str],
    rules: tuple[LayoutRule, ...],
    entries: list[dict[str, str]],
) -> list[LayoutFinding]:
    """Find undeclared top-level paths outside the rendered template."""
    contract_targets = {
        entry["target"] for entry in entries if entry["kind"] != "runtime"
    }
    applicable_rules = tuple(
        rule for rule in rules if rule.target in contract_targets
    )
    moved_destinations = {
        PurePosixPath(rule.new_path).parts[0]
        for rule in applicable_rules
        if rule.action == "Moved" and rule.new_path is not None
    }
    return [
        LayoutFinding("extra", name)
        for name in present - expected
        if not any(
            declaration == name or declaration.startswith(name + "/")
            for declaration in declarations
        )
        and name not in moved_destinations
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
    git_paths = _git_paths(project)
    cruft = _require_workspace(project, entries, git_paths)
    present = _top_level_names(git_paths)
    has_local_rules, declarations, rules = _workspace_rules(project, present)
    expected = _rendered_top_level(project, cruft)
    expected.update(generated)
    expected.update(
        PurePosixPath(entry["target"]).parts[0]
        for entry in entries
        if entry["kind"] == "runtime"
    )

    findings = _missing_contract_paths(entries, git_paths, rules)
    if "AGENTS.md" not in git_paths or not has_local_rules:
        findings.append(LayoutFinding("missing-local-rules", "AGENTS.md"))
    findings.extend(
        _extra_top_level_paths(present, expected, declarations, rules, entries)
    )
    return LayoutResult(
        tuple(sorted(findings, key=lambda item: (item.kind, item.path)))
    )


__all__ = [
    "LayoutFinding",
    "LayoutResult",
    "LayoutRule",
    "check_layout",
    "parse_layout_rules",
    "parse_local_rules",
]
