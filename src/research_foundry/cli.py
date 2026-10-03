"""Command-line interface for packaged research-foundry templates.

Examples:
    >>> callable(main)
    True
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from research_foundry.cruft import check_project, update_project
from research_foundry.skills import main as install_skills_main
from research_foundry.templates import (
    FoundryError,
    create_project,
    describe_questions,
    list_templates,
)


def _parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(prog="research-foundry")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("templates", help="list available templates")
    questions = commands.add_parser(
        "questions", help="describe a template's questions"
    )
    questions.add_argument("template")
    questions.add_argument("--json", action="store_true", dest="as_json")
    new = commands.add_parser("new", help="create a project offline")
    new.add_argument("template")
    new.add_argument("-o", "--output-dir", type=Path, default=Path("."))
    new.add_argument(
        "--answer", action="append", default=[], metavar="KEY=VALUE"
    )
    check = commands.add_parser("check", help="check for template updates")
    check.add_argument("path", nargs="?", type=Path, default=Path("."))
    update = commands.add_parser("update", help="apply template updates")
    update.add_argument("path", nargs="?", type=Path, default=Path("."))
    update.add_argument("--yes", action="store_true")
    install = commands.add_parser(
        "install-skills", help="install the maintained agent skills"
    )
    install_modes = install.add_mutually_exclusive_group()
    install_modes.add_argument("--check", action="store_true")
    install_modes.add_argument("--adopt", action="store_true")
    install_modes.add_argument("--force", action="store_true")
    commands.add_parser("mcp", help="run the MCP server on standard I/O")
    return parser


def _answers(pairs: Sequence[str]) -> dict[str, str]:
    """Parse repeated ``KEY=VALUE`` command-line answers."""
    result: dict[str, str] = {}
    for pair in pairs:
        name, separator, value = pair.partition("=")
        if not separator or not name:
            raise FoundryError(
                f"Answer {pair!r} is not KEY=VALUE; pass --answer KEY=VALUE."
            )
        result[name] = value
    return result


def main(  # pylint: disable=too-many-return-statements
    argv: Sequence[str] | None = None,
) -> int:
    """Run the research-foundry command-line interface.

    Args:
        argv: Arguments without the executable name, or ``None`` for
            :data:`sys.argv`.

    Returns:
        The process exit status.

    Examples:
        >>> callable(main)
        True
    """
    args = _parser().parse_args(argv)
    try:
        if args.command == "templates":
            for item in list_templates():
                print(f"{item.name}\t{item.title}\t{item.description}")
            return 0
        if args.command == "questions":
            questions = describe_questions(str(args.template))
            if args.as_json:
                print(
                    json.dumps([question.as_dict() for question in questions])
                )
            else:
                for question in questions:
                    choices = ", ".join(question.choices) or "free text"
                    print(
                        f"{question.name}: {question.prompt} "
                        f"[default: {question.default}; choices: {choices}]"
                    )
            return 0
        if args.command == "new":
            project = create_project(
                str(args.template),
                _answers(args.answer),
                args.output_dir,
            )
            print(project)
            return 0
        if args.command == "check":
            return 0 if check_project(args.path) else 1
        if args.command == "update":
            return 0 if update_project(args.path, yes=args.yes) else 1
        if args.command == "install-skills":
            modes = [
                flag
                for flag in ("check", "adopt", "force")
                if getattr(args, flag)
            ]
            return install_skills_main([f"--{modes[0]}"] if modes else [])
        if args.command == "mcp":
            # Import lazily so non-server commands have no MCP startup cost.
            # pylint: disable-next=import-outside-toplevel
            from research_foundry.server import run

            run()
            return 0
    except (FoundryError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 2
