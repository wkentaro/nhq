from pathlib import Path

import pytest

from tests.conftest import GitRepo

from .conftest import IhqCLI


def test_not_a_git_repo(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    repo = GitRepo(str(tmp_path))
    cli = IhqCLI(repo, tmp_path_factory.mktemp("ihq_root"))

    result = cli.run("list")

    assert result.returncode == 1
    assert "not a git repository" in result.stderr


def test_no_origin_remote(cli: IhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("list")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr


def test_unparsable_origin(cli: IhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "set-url", "origin", "https://github.com/../../etc")

    result = cli.run("list")

    assert result.returncode == 1
    assert "invalid path" in result.stderr


def test_migrate_store_write_failure(cli: IhqCLI, git_repo: GitRepo) -> None:
    blocker = cli.ihq_root / "blocker"
    blocker.write_text("")  # a file where the store dir is expected
    cli.ihq_root = blocker
    (Path(git_repo.path) / "scratch").write_text("x\n")

    result = cli.run("migrate", "scratch")

    assert result.returncode == 1
    assert "cannot migrate" in result.stderr


def test_git_not_found(
    cli: IhqCLI,
    git_repo: GitRepo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))  # a dir with no git binary

    result = cli.run("list")

    assert result.returncode == 1
    assert "git not found" in result.stderr


def test_unknown_command(cli: IhqCLI) -> None:
    result = cli.run("bogus")

    assert result.returncode == 2
    assert "unrecognized subcommand 'bogus'" in result.stderr


def test_bare_invocation_prints_help(cli: IhqCLI) -> None:
    result = cli.run()

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "migrate" in result.stdout
    assert result.stderr == ""


def test_help_flag(cli: IhqCLI) -> None:
    result = cli.run("--help")

    assert result.returncode == 0
    assert "Commands:" in result.stdout
    assert "migrate" in result.stdout
    assert result.stderr == ""


def test_version_flag(cli: IhqCLI) -> None:
    result = cli.run("--version")

    assert result.returncode == 0
    assert "ihq" in result.stdout
    assert result.stderr == ""
