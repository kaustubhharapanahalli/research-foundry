"""The paper template builds the way Overleaf and arXiv expect."""

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.conftest import LEFTOVER

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


@pytest.mark.parametrize("venue", ["iclr", "neurips", "icml", "article"])
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


def test_icml_render_uses_official_style_macros(render: Render) -> None:
    project = render("paper", venue="icml", venue_year="2026")
    main = (project / "main.tex").read_text()
    for path in project.rglob("*"):
        if path.is_file():
            assert not LEFTOVER.search(path.read_text()), path.relative_to(
                project
            )
    # ICML's example: no option is the blind submission, [accepted] is
    # camera-ready, and [preprint] is a non-anonymous arXiv copy.
    assert "\\else\n  % No option is ICML's blind submission" in main
    assert "  \\usepackage{icml2026}\n\\fi" in main
    assert "[preprint]{icml" not in main
    assert "\\usepackage[accepted]{icml2026}" in main
    assert "\\icmltitle{My Project}" in main
    assert "\\begin{icmlauthorlist}" in main
    assert "\\icmlaffiliation{" in main
    assert "\\icmlkeywords{" in main
    assert "\\bibliographystyle{icml2026}" in main


def test_icml_venue_target_uses_the_rendered_year(render: Render) -> None:
    makefile = (
        render("paper", venue="icml", venue_year="2026") / "Makefile"
    ).read_text()
    assert (
        "https://media.icml.cc/Conferences/ICML$(YEAR)/Styles/"
        "icml$(YEAR).zip"
    ) in makefile
    assert (
        "unzip -o -j icml$(YEAR).zip '*.sty' '*.bst' " "-d venue/icml$(YEAR)"
    ) in makefile


@pytest.mark.parametrize("venue", ["iclr", "neurips", "article"])
def test_non_icml_makefiles_have_no_icml_fetch_settings(
    venue: str, render: Render
) -> None:
    makefile = (render("paper", venue=venue) / "Makefile").read_text()
    assert "ICML_URL" not in makefile
    assert "media.icml.cc" not in makefile


def test_icml_unpublished_year_fails_without_partial_kit(
    render: Render, tmp_path: Path
) -> None:
    project = render("paper", venue="icml", venue_year="2027")
    missing_zip = tmp_path / "not-published.zip"
    done = subprocess.run(
        ["make", "venue", f"ICML_URL={missing_zip.as_uri()}"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    output = done.stdout + done.stderr
    assert done.returncode != 0
    assert "ICML 2027 style kit is not published" in output
    assert "https://icml.cc" in output
    assert "venue_year" in output
    assert not (project / "venue" / "icml2027").exists()


def test_icml_corrupt_kit_fails_without_partial_kit(
    render: Render, tmp_path: Path
) -> None:
    project = render("paper", venue="icml", venue_year="2026")
    corrupt_zip = tmp_path / "truncated.zip"
    corrupt_zip.write_bytes(b"PK\x03\x04 not a whole archive")
    done = subprocess.run(
        ["make", "venue", f"ICML_URL={corrupt_zip.as_uri()}"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode != 0
    assert not (project / "venue" / "icml2026").exists()
    assert not (project / "icml2026.zip").exists()


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
