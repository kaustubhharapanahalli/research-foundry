"""Read and render the templates shipped by research-foundry.

Examples:
    >>> {item.name for item in list_templates()} == set(TEMPLATE_NAMES)
    True
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path

from cookiecutter.exceptions import FailedHookException
from cookiecutter.generate import generate_context
from cookiecutter.main import cookiecutter
from cookiecutter.prompt import prompt_for_config
from research_foundry import __version__
from research_foundry.constants import (
    PUBLIC_REPOSITORY,
    REPOSITORY_ENV,
    TEMPLATE_NAMES,
)


class FoundryError(RuntimeError):
    """A requested operation was refused with a corrective message.

    Examples:
        >>> str(FoundryError("Choose a known template."))
        'Choose a known template.'
    """


class HookRefusal(FoundryError):
    """A template hook refused the selected answers.

    Examples:
        >>> str(HookRefusal("Choose a compatible component set."))
        'Choose a compatible component set.'
    """


def write_cookiecutter_config(workdir: Path) -> Path:
    """Write a Cookiecutter config whose mutable paths stay inside ``workdir``.

    Args:
        workdir: The temporary directory containing this Cookiecutter run.

    Returns:
        The config file path for Cookiecutter or cruft.

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as work:
        ...     config = write_cookiecutter_config(Path(work))
        ...     settings = json.loads(config.read_text())
        ...     Path(settings["replay_dir"]).parent == Path(work).resolve()
        True
    """
    root = workdir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = root / "cookiecutter-config.json"
    config.write_text(
        json.dumps(
            {
                "default_context": {},
                "cookiecutters_dir": str(root / "cookiecutters"),
                "replay_dir": str(root / "replay"),
            }
        ),
        encoding="utf-8",
    )
    return config


@dataclass(frozen=True)
class Template:
    """One public project template.

    Args:
        name: The command-line template name.
        title: The human-readable title.
        description: A short explanation of the generated project.

    Examples:
        >>> Template("paper", "Paper", "A paper.").name
        'paper'
    """

    name: str
    title: str
    description: str

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-compatible representation.

        Returns:
            The template's three public fields.

        Examples:
            >>> Template("paper", "Paper", "A paper.").as_dict()["title"]
            'Paper'
        """
        return asdict(self)


@dataclass(frozen=True)
class Question:
    """One answer accepted by a template.

    Args:
        name: The context key.
        prompt: The text shown to a person.
        default: The non-interactive default.
        choices: Allowed values, or an empty tuple for free text.

    Examples:
        >>> Question("venue", "Venue", "iclr", ("iclr",)).default
        'iclr'
    """

    name: str
    prompt: str
    default: str
    choices: tuple[str, ...]

    def as_dict(self) -> dict[str, str | list[str]]:
        """Return a JSON-compatible representation.

        Returns:
            The question fields with choices represented as a list.

        Examples:
            >>> Question("x", "X", "a", ("a",)).as_dict()["choices"]
            ['a']
        """
        return {
            "name": self.name,
            "prompt": self.prompt,
            "default": self.default,
            "choices": list(self.choices),
        }


def template_root() -> Path:
    """Return the installed template tree or source-checkout fallback.

    Returns:
        A directory containing the root ``cookiecutter.json``.

    Raises:
        FoundryError: If neither packaged nor source templates exist.

    Examples:
        >>> (template_root() / "cookiecutter.json").is_file()
        True
    """
    packaged = Path(__file__).resolve().parent / "templates"
    if (packaged / "cookiecutter.json").is_file():
        return packaged
    checkout = Path(__file__).resolve().parents[2]
    if (checkout / "cookiecutter.json").is_file():
        return checkout
    raise FoundryError(
        "The packaged templates are missing; reinstall research-foundry."
    )


def _mapping(path: Path) -> dict[str, object]:
    """Read a JSON object and reject any other top-level value."""
    loaded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise FoundryError(
            f"{path} is not a JSON object; reinstall the package."
        )
    return {str(key): value for key, value in loaded.items()}


def list_templates(root: Path | None = None) -> list[Template]:
    """List the templates in the root catalog.

    Args:
        root: An alternate template tree, mainly for isolated tests.

    Returns:
        Templates in catalog order.

    Raises:
        FoundryError: If the installed catalog is malformed.

    Examples:
        >>> [item.name for item in list_templates()]
        ['methodology', 'workspace', 'paper', 'software']
    """
    source = root or template_root()
    catalog = _mapping(source / "cookiecutter.json")
    entries = catalog.get("templates")
    if not isinstance(entries, dict):
        raise FoundryError(
            "The template catalog has no templates mapping; reinstall the "
            "package."
        )
    result: list[Template] = []
    for name, value in entries.items():
        if not isinstance(name, str) or not isinstance(value, dict):
            raise FoundryError(
                "The template catalog is malformed; reinstall the package."
            )
        title = value.get("title")
        description = value.get("description")
        if not isinstance(title, str) or not isinstance(description, str):
            raise FoundryError(
                f"Template {name!r} lacks a title or description; fix the "
                "catalog."
            )
        result.append(Template(name, title, description))
    return result


def _known_template(template: str, root: Path) -> None:
    """Refuse a template absent from the public catalog."""
    known = {item.name for item in list_templates(root)}
    if template not in known:
        choices = ", ".join(sorted(known))
        raise FoundryError(
            f"Unknown template {template!r}; choose one of: {choices}."
        )


def describe_questions(
    template: str, root: Path | None = None
) -> list[Question]:
    """Describe every public answer a template accepts.

    Args:
        template: A name from :func:`list_templates`.
        root: An alternate template tree, mainly for isolated tests.

    Returns:
        Questions in Cookiecutter context order.

    Raises:
        FoundryError: If the template is unknown or its context is malformed.

    Examples:
        >>> describe_questions("paper")[0].name
        'project_name'
    """
    source = root or template_root()
    _known_template(template, source)
    context = _mapping(source / template / "cookiecutter.json")
    generated = generate_context(
        context_file=str(source / template / "cookiecutter.json")
    )
    # Cookiecutter's public prompt resolver computes dependent Jinja defaults.
    resolved: dict[str, object] = dict(
        prompt_for_config(generated, no_input=True)
    )
    raw_prompts = context.get("__prompts__", {})
    prompts = raw_prompts if isinstance(raw_prompts, dict) else {}
    result: list[Question] = []
    for name, value in context.items():
        if name.startswith("_"):
            continue
        choices = (
            tuple(str(item) for item in value)
            if isinstance(value, list)
            else ()
        )
        default = str(resolved[name])
        prompt = prompts.get(name, name)
        result.append(Question(name, str(prompt), default, choices))
    return result


def asked(template: str, root: Path | None = None) -> set[str]:
    """Return the public answer names accepted by a template.

    Args:
        template: A name from :func:`list_templates`.
        root: An alternate template tree, mainly for isolated tests.

    Returns:
        The template's non-private context keys.

    Raises:
        FoundryError: If the template is unknown or malformed.

    Examples:
        >>> "project_name" in asked("workspace")
        True
    """
    return {question.name for question in describe_questions(template, root)}


def asked_from_json(text: str) -> set[str]:
    """Return public answer names from Cookiecutter context JSON.

    Args:
        text: The complete ``cookiecutter.json`` text.

    Returns:
        Every non-private top-level key.

    Raises:
        FoundryError: If the text is not a JSON object.

    Examples:
        >>> asked_from_json('{"name": "Example", "_private": "x"}')
        {'name'}
    """
    loaded: object = json.loads(text)
    if not isinstance(loaded, dict):
        raise FoundryError(
            "The template context is not a JSON object; repair "
            "cookiecutter.json."
        )
    return {str(name) for name in loaded if not str(name).startswith("_")}


def validate_answers(
    template: str,
    answers: Mapping[str, str],
    root: Path | None = None,
) -> None:
    """Refuse unknown templates and answers before generation writes files.

    Args:
        template: A name from :func:`list_templates`.
        answers: Explicit Cookiecutter context overrides.
        root: An alternate template tree, mainly for isolated tests.

    Raises:
        FoundryError: If the template or any answer is unknown.

    Examples:
        >>> validate_answers("workspace", {"project_name": "Example"})
    """
    accepted = asked(template, root)
    unknown = sorted(set(answers) - accepted)
    if unknown:
        names = ", ".join(unknown)
        raise FoundryError(
            f"Template {template!r} does not ask for {names}. "
            "Remove that --answer or run 'research-foundry questions "
            f"{template}'."
        )


@contextmanager
def prepared_templates(root: Path | None = None) -> Iterator[Path]:
    """Yield a work copy with each template's shared include restored.

    Args:
        root: The installed or source template tree.

    Yields:
        A temporary Cookiecutter repository layout.

    Raises:
        FoundryError: If the template catalog is malformed.

    Examples:
        >>> with prepared_templates() as work:
        ...     all((work / name / "templates").exists()
        ...         for name in TEMPLATE_NAMES)
        True
    """
    source = root or template_root()
    names = [item.name for item in list_templates(source)]
    with tempfile.TemporaryDirectory(prefix="research-foundry-") as temporary:
        work = Path(temporary)
        shutil.copy2(source / "cookiecutter.json", work / "cookiecutter.json")
        shutil.copytree(source / "_shared", work / "_shared")
        for name in names:
            target = work / name
            shutil.copytree(source / name, target, symlinks=True)
            include = target / "templates"
            if not include.exists():
                try:
                    include.symlink_to("../_shared", target_is_directory=True)
                except OSError:
                    shutil.copytree(work / "_shared", include)
        yield work


@contextmanager
def _captured_stderr(path: Path) -> Iterator[None]:
    """Redirect Python and child-process stderr to one UTF-8 file."""
    sys.stderr.flush()
    saved = os.dup(2)
    with path.open("w", encoding="utf-8") as sink:
        os.dup2(sink.fileno(), 2)
        try:
            yield
        finally:
            sys.stderr.flush()
            os.dup2(saved, 2)
            os.close(saved)


def hook_reason(text: str) -> str:
    r"""Extract a generation hook's own refusal reason.

    Args:
        text: Cookiecutter's captured standard error.

    Returns:
        Hook output before Cookiecutter's wrapper message.

    Examples:
        >>> hook_reason("choose another value\nStopping generation!")
        'choose another value'
    """
    said: list[str] = []
    for line in text.splitlines():
        if line.startswith("Stopping generation"):
            break
        if line.strip():
            said.append(line.strip())
    return " ".join(said) or "refused by a generation hook"


def repository_url(environ: Mapping[str, str] | None = None) -> str:
    """Return the update repository, honoring the test/user override.

    Args:
        environ: An alternate environment mapping.

    Returns:
        The configured repository URL or the public repository.

    Examples:
        >>> repository_url({REPOSITORY_ENV: "/tmp/foundry"})
        '/tmp/foundry'
    """
    environment = os.environ if environ is None else environ
    return environment.get(REPOSITORY_ENV, PUBLIC_REPOSITORY)


def release_commit(repository: str) -> str:
    """Resolve this release's tag to a full SHA when reachable.

    Args:
        repository: A Git URL or local repository path.

    Returns:
        The full tag SHA, or ``v<version>`` when Git cannot reach it.

    Examples:
        >>> release_commit("/path/that/does/not/exist") == f"v{__version__}"
        True
    """
    tag = f"v{__version__}"
    try:
        completed = subprocess.run(
            [
                "git",
                "ls-remote",
                "--tags",
                repository,
                f"refs/tags/{tag}",
                f"refs/tags/{tag}^{{}}",
            ],
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return tag
    if completed.returncode != 0:
        return tag
    lines = [line.split()[0] for line in completed.stdout.splitlines() if line]
    return lines[-1] if lines else tag


def _rendered_context(
    context_file: Path,
    answers: Mapping[str, str],
    repository: str,
    commit: str,
) -> dict[str, object]:
    """Build the complete context format cruft expects."""
    generated = generate_context(
        context_file=str(context_file), extra_context=dict(answers)
    )
    # Cookiecutter is intentionally untyped at this third-party boundary.
    rendered: dict[str, object] = dict(
        prompt_for_config(generated, no_input=True)
    )
    rendered["_template"] = repository
    rendered["_commit"] = commit
    return {"cookiecutter": rendered}


def _write_cruft(
    project: Path,
    template: str,
    answers: Mapping[str, str],
    source: Path,
) -> None:
    """Write the metadata consumed by later cruft checks and updates."""
    repository = repository_url()
    commit = release_commit(repository)
    state: dict[str, object] = {
        "template": repository,
        "commit": commit,
        "checkout": None,
        "context": _rendered_context(
            source / template / "cookiecutter.json",
            answers,
            repository,
            commit,
        ),
        "directory": template,
    }
    (project / ".cruft.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def create_project(
    template: str,
    answers: Mapping[str, str],
    output_dir: Path,
    *,
    source: Path | None = None,
    write_cruft: bool = True,
) -> Path:
    """Render one project offline from the packaged templates.

    Args:
        template: A name from :func:`list_templates`.
        answers: Explicit Cookiecutter context overrides.
        output_dir: Parent directory for the generated project.
        source: An alternate template tree, mainly for isolated tests.
        write_cruft: Whether to record update metadata.

    Returns:
        The generated project directory.

    Raises:
        FoundryError: If the template or an answer is unknown.
        HookRefusal: If the template's hook refuses the answer combination.

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as directory:
        ...     made = create_project("workspace", {}, Path(directory),
        ...                           write_cruft=False)
        ...     (made / "README.md").is_file()
        True
    """
    root = source or template_root()
    validate_answers(template, answers, root)
    output_dir.mkdir(parents=True, exist_ok=True)
    before = set(output_dir.iterdir())
    with prepared_templates(root) as work:
        captured = work / "hook-stderr.txt"
        try:
            config = write_cookiecutter_config(work)
            with _captured_stderr(captured):
                rendered = cookiecutter(
                    str(work),
                    directory=template,
                    no_input=True,
                    output_dir=str(output_dir),
                    extra_context=dict(answers),
                    config_file=str(config),
                )
        except FailedHookException as error:
            for path in set(output_dir.iterdir()) - before:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            raise HookRefusal(hook_reason(captured.read_text())) from error
        project = Path(rendered)
        if write_cruft:
            _write_cruft(project, template, answers, work)
    return project


def plan_project(
    template: str,
    answers: Mapping[str, str],
    *,
    source: Path | None = None,
) -> list[str]:
    """Validate a project by rendering it and return its file list.

    Args:
        template: A name from :func:`list_templates`.
        answers: Explicit Cookiecutter context overrides.
        source: An alternate template tree, mainly for isolated tests.

    Returns:
        Sorted file paths relative to the generated project.

    Raises:
        FoundryError: If the template or an answer is unknown.
        HookRefusal: If the template's hook refuses the answer combination.

    Examples:
        >>> "README.md" in plan_project("workspace", {})
        True
    """
    with tempfile.TemporaryDirectory(prefix="research-foundry-plan-") as temp:
        project = create_project(
            template,
            answers,
            Path(temp),
            source=source,
            write_cruft=False,
        )
        return sorted(
            str(path.relative_to(project))
            for path in project.rglob("*")
            if path.is_file()
        )


__all__ = [
    "FoundryError",
    "HookRefusal",
    "Question",
    "TEMPLATE_NAMES",
    "Template",
    "asked",
    "asked_from_json",
    "create_project",
    "describe_questions",
    "hook_reason",
    "list_templates",
    "plan_project",
    "prepared_templates",
    "release_commit",
    "repository_url",
    "template_root",
    "validate_answers",
    "write_cookiecutter_config",
]
