from pathlib import Path

import pytest

from tests.conftest import GitRepo

from .conftest import NhqCLI


def test_not_a_git_repo(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    repo = GitRepo(str(tmp_path))
    cli = NhqCLI(repo, tmp_path_factory.mktemp("nhq_root"))

    result = cli.run("init")

    assert result.returncode == 1
    assert "not a git repository" in result.stderr


def test_no_origin_remote(cli: NhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("init")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr


def test_unparsable_origin(cli: NhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "set-url", "origin", "https://github.com/../../etc")

    result = cli.run("init")

    assert result.returncode == 1
    assert "invalid path" in result.stderr


def test_store_creation_failure(cli: NhqCLI, tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("")  # a file where the store's parent dir is expected
    cli.nhq_root = blocker

    result = cli.run("init")

    assert result.returncode == 1
    assert "cannot create store" in result.stderr


def test_git_not_found(
    cli: NhqCLI,
    git_repo: GitRepo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))  # a dir with no git binary

    result = cli.run("init")

    assert result.returncode == 1
    assert "git not found" in result.stderr


def test_unknown_command(cli: NhqCLI) -> None:
    result = cli.run("bogus")

    assert result.returncode == 2
    assert "unrecognized subcommand 'bogus'" in result.stderr


def test_bare_invocation_prints_help(cli: NhqCLI) -> None:
    result = cli.run()

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "init" in result.stdout
    assert result.stderr == ""


def test_help_flag(cli: NhqCLI) -> None:
    result = cli.run("--help")

    assert result.returncode == 0
    assert "Commands:" in result.stdout
    assert "nhq init" in result.stdout
    assert result.stderr == ""


def test_version_flag(cli: NhqCLI) -> None:
    result = cli.run("--version")

    assert result.returncode == 0
    assert "nhq" in result.stdout
    assert result.stderr == ""
