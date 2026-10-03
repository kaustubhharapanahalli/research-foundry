"""The paper template builds the way Overleaf and arXiv expect."""

from collections.abc import Callable
from pathlib import Path

import pytest

Render = Callable[..., Path]
SECTIONS = [
    "introduction",
    "related_work",
    "method",
    "experiments",
    "results",
    "conclusion",
    "appendix",
]


def test_latexmkrc_has_no_leading_dot(render: Render) -> None:
    # Overleaf reads only "latexmkrc", and arXiv deletes hidden files.
    project = render("paper")
    assert (project / "latexmkrc").is_file()
    assert not (project / ".latexmkrc").exists()


def test_latexmkrc_uses_pdflatex(render: Render) -> None:
    # Venue kits require pdflatex, and arXiv does not accept LuaLaTeX.
    assert "$pdf_mode = 1;" in (render("paper") / "latexmkrc").read_text()


def test_paper_has_no_symlinks(render: Render) -> None:
    # Overleaf's git bridge turns a symlink into a plain file.
    project = render("paper")
    assert not [p for p in project.rglob("*") if p.is_symlink()]


@pytest.mark.parametrize("section", SECTIONS)
def test_every_section_is_input(section: str, render: Render) -> None:
    project = render("paper")
    assert (project / "sections" / f"{section}.tex").is_file()
    assert (
        f"\\input{{sections/{section}}}" in (project / "main.tex").read_text()
    )


def test_numbers_come_from_the_generated_file(render: Render) -> None:
    project = render("paper")
    assert "\\input{generated/numbers}" in (project / "main.tex").read_text()
    numbers = project / "generated" / "numbers.tex"
    assert numbers.is_file()
    assert "\\newcommand{\\rnum}" in numbers.read_text()


@pytest.mark.parametrize("venue", ["iclr", "neurips", "article"])
def test_submission_is_anonymous_by_default(
    venue: str, render: Render
) -> None:
    main = (render("paper", venue=venue) / "main.tex").read_text()
    assert "\\camerareadyfalse" in main
    assert "Anonymous authors" in main


def test_iclr_camera_ready_sets_final_copy(render: Render) -> None:
    main = (
        render("paper", venue="iclr", venue_year="2027") / "main.tex"
    ).read_text()
    assert "\\usepackage{iclr2027_conference,times}" in main
    assert "\\ifcameraready\n  \\iclrfinalcopy\n\\fi" in main


def test_neurips_camera_ready_uses_the_final_option(render: Render) -> None:
    main = (
        render("paper", venue="neurips", venue_year="2026") / "main.tex"
    ).read_text()
    assert "\\usepackage[final]{neurips_2026}" in main


def test_no_kit_is_shipped(render: Render) -> None:
    # Venues state no licence for redistributing their kits.
    venue = render("paper", venue="iclr") / "venue"
    assert [p.name for p in venue.iterdir()] == ["README.md"]


@pytest.mark.parametrize(("mirror", "has_ci"), [("no", False), ("yes", True)])
def test_ci_only_with_a_github_mirror(
    mirror: str, has_ci: bool, render: Render
) -> None:
    project = render("paper", github_mirror=mirror)
    assert (project / ".github" / "workflows" / "ci.yml").exists() is has_ci


def test_texlive_image_is_pinned_by_digest(render: Render) -> None:
    makefile = (render("paper") / "Makefile").read_text()
    assert "texlive/texlive:TL2025-historic@sha256:" in makefile
