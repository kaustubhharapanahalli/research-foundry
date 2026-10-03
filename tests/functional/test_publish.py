"""The shared public export (`make publish`), tested where it is defined.

Each test builds a small private repository in a temporary directory and
publishes to a local bare repository, so no network is touched and no real
remote is ever pushed to.
"""

import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
from tests.conftest import GIT_ENV, SHARED


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "publish", SHARED / "publish" / "publish.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Dataclasses look their module up in sys.modules while being defined.
    sys.modules["publish"] = module
    spec.loader.exec_module(module)
    return module


pub = _load()

FILES = {
    "README.md": "# Tidal\n",
    "pyproject.toml": '[project]\nname = "tidal"\nversion = "0.3.0"\n',
    "src/tidal/__init__.py": '"""Tidal."""\n',
    "AGENTS.md": "# Agent rules\n",
    "CLAUDE.md": "@AGENTS.md\n",
    "docs/AGENTS.md": "# Nested agent rules\n",
    ".claude/settings.json": "{}\n",
    ".publish-deny": "# private names\nmpslab-private\n",
}


def git(cwd: Path, *argv: str) -> str:
    done = subprocess.run(
        ["git", *argv],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **GIT_ENV},
    )
    return done.stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str) -> None:
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)


@pytest.fixture(name="private")
def private_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name, value in GIT_ENV.items():
        monkeypatch.setenv(name, value)
    repo = tmp_path / "private"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    commit(repo, FILES, "first private commit")
    commit(repo, {"notes.txt": "a private draft\n"}, "second private commit")
    return repo


@pytest.fixture(name="public")
def public_fixture(tmp_path: Path) -> Path:
    remote = tmp_path / "public.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    return remote


def _published(remote: Path) -> set[str]:
    return set(git(remote, "ls-tree", "-r", "--name-only", "main").split())


@pytest.mark.functional
def test_the_export_leaves_every_agent_file_out(
    private: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    paths = pub.build(private, out)
    assert paths == [
        "README.md", "notes.txt", "pyproject.toml", "src/tidal/__init__.py",
    ]  # fmt: skip
    assert not (out / ".claude").exists()


@pytest.mark.functional
def test_the_same_tree_exports_the_same_files(
    private: Path, tmp_path: Path
) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    assert pub.build(private, tmp_path / "a") == pub.build(
        private, tmp_path / "b"
    )
    assert (tmp_path / "a" / "README.md").read_bytes() == (
        tmp_path / "b" / "README.md"
    ).read_bytes()


@pytest.mark.functional
def test_guard_a_dirty_tree_is_refused(private: Path, tmp_path: Path) -> None:
    (private / "README.md").write_text("# Changed\n")
    with pytest.raises(pub.PublishError, match="working tree"):
        pub.build(private, tmp_path)


@pytest.mark.functional
@pytest.mark.parametrize(
    ("text", "rule"),
    [
        ("see https://www.overleaf.com/project/0123456789abcdef01234567\n",
         "Overleaf project ID"),
        ("git clone https://git.overleaf.com/0123456789abcdef01234567\n",
         "Overleaf project ID"),
        ("data at /Users/someone/data/x\n", "home path"),
        ("data at /home/someone/data/x\n", "home path"),
        ("built at MPSLAB-PRIVATE\n", ".publish-deny line 2"),
    ],
)  # fmt: skip
def test_guard_a_private_item_is_refused_by_file_line_and_rule(
    private: Path, tmp_path: Path, text: str, rule: str
) -> None:
    commit(private, {"docs/setup.md": "# Setup\n\n" + text}, "leak")
    with pytest.raises(pub.PublishError) as refused:
        pub.build(private, tmp_path)
    message = str(refused.value)
    assert f"docs/setup.md:3: {rule}" in message
    # The matched text is not repeated.
    assert text.split()[-1] not in message


@pytest.mark.functional
def test_a_ci_runners_home_is_not_a_private_path(
    private: Path, tmp_path: Path
) -> None:
    commit(private, {"ci.txt": "cache at /home/runner/.cache\n"}, "ci")
    assert "ci.txt" in pub.build(private, tmp_path)


@pytest.mark.functional
def test_guard_a_deny_line_that_is_not_a_pattern_is_refused(
    private: Path, tmp_path: Path
) -> None:
    commit(private, {".publish-deny": "([unclosed\n"}, "bad pattern")
    with pytest.raises(pub.PublishError, match="line 1"):
        pub.build(private, tmp_path)


@pytest.mark.functional
def test_the_first_push_is_one_commit_with_no_private_history(
    private: Path, public: Path
) -> None:
    pub.push(private, str(public), "main", "Release 0.3.0")
    assert git(public, "rev-list", "--count", "main") == "1"
    assert git(public, "log", "-1", "--format=%s", "main") == "Release 0.3.0"
    assert _published(public) == {
        "README.md", "notes.txt", "pyproject.toml", "src/tidal/__init__.py",
    }  # fmt: skip
    private_head = git(private, "rev-parse", "HEAD")
    assert private_head not in git(public, "rev-list", "--all")


@pytest.mark.functional
def test_each_later_release_is_one_commit_on_the_last(
    private: Path, public: Path
) -> None:
    first = pub.push(private, str(public), "main", "Release 0.3.0")
    commit(private, {"README.md": "# Tidal, better\n"}, "private work")
    second = pub.push(private, str(public), "main", "Release 0.4.0")
    assert git(public, "rev-list", "--count", "main") == "2"
    assert git(public, "rev-parse", f"{second}^") == first


@pytest.mark.functional
def test_guard_an_unchanged_export_is_not_published_again(
    private: Path, public: Path
) -> None:
    pub.push(private, str(public), "main", "Release 0.3.0")
    commit(private, {"AGENTS.md": "# Rules, revised\n"}, "agent files only")
    with pytest.raises(pub.PublishError, match="nothing to publish"):
        pub.push(private, str(public), "main", "Release 0.3.1")
    assert git(public, "rev-list", "--count", "main") == "1"


@pytest.mark.functional
def test_guard_a_refused_export_pushes_nothing(
    private: Path, public: Path
) -> None:
    commit(private, {"x.md": "at /Users/someone/x\n"}, "leak")
    with pytest.raises(pub.PublishError):
        pub.push(private, str(public), "main", "Release 0.3.0")
    assert not git(public, "for-each-ref")


@pytest.mark.functional
def test_a_remote_is_named_or_given_as_a_url(
    private: Path, public: Path
) -> None:
    git(private, "remote", "add", "public", str(public))
    assert pub.main(["push", "public"], root=private) == 0
    assert git(public, "log", "-1", "--format=%s", "main") == "Release 0.3.0"


@pytest.mark.functional
def test_check_pushes_nothing_and_says_what_it_found(
    private: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert pub.main(["check"], root=private) == 0
    out = capsys.readouterr().out
    assert "4 files, no agent files, nothing private" in out


@pytest.mark.functional
def test_a_refusal_exits_1_with_the_reason(
    private: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (private / "README.md").write_text("# Changed\n")
    assert pub.main(["check"], root=private) == 1
    assert "publish refused" in capsys.readouterr().err


Render = Callable[..., Path]
PUBLIC_FACING = ("methodology", "software")


@pytest.mark.functional
@pytest.mark.parametrize("kind", PUBLIC_FACING)
def test_a_public_facing_template_ships_the_shared_publish(
    kind: str, render: Render
) -> None:
    project = render(kind)
    shared = SHARED / "publish"
    assert (project / "scripts" / "publish.py").read_bytes() == (
        shared / "publish.py"
    ).read_bytes()
    assert (project / ".publish-deny").read_bytes() == (
        shared / "publish-deny"
    ).read_bytes()
    assert "include make/publish.mk" in (project / "Makefile").read_text()


@pytest.mark.functional
@pytest.mark.parametrize("kind", ["workspace", "paper"])
def test_a_private_template_has_no_publish(kind: str, render: Render) -> None:
    project = render(kind)
    assert not (project / "scripts" / "publish.py").exists()
    assert not (project / ".publish-deny").exists()


@pytest.mark.functional
@pytest.mark.parametrize(
    ("kind", "answers"),
    [
        (
            "methodology",
            {
                "ml_pytorch": "yes",
                "public_docs": "yes",
                "contact_email": "maintainers@example.org",
            },
        ),
        ("software", {"gateway_litellm": "yes", "ml_pytorch": "yes"}),
    ],
)
def test_a_new_project_passes_its_own_publish_check(
    kind: str,
    answers: dict[str, str],
    render: Render,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The templates themselves carry nothing the scan refuses.
    for name, value in GIT_ENV.items():
        monkeypatch.setenv(name, value)
    project = render(kind, **answers)
    git(project, "init", "-q", "-b", "main")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "generated")
    assert pub.main(["check"], root=project) == 0
