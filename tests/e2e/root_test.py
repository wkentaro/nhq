from pathlib import Path

import pytest

from tests.conftest import GitRepo

from .conftest import NhqCLI


def test_root_prints_env_root(cli: NhqCLI) -> None:
    result = cli.run_ok("root")

    assert result.stdout.strip() == str(cli.nhq_root)
    assert result.stderr == ""


def test_root_uses_git_config_when_no_env(
    cli: NhqCLI, git_repo: GitRepo, tmp_path: Path
) -> None:
    config_root = tmp_path / "config-root"
    git_repo.git("config", "nhq.root", str(config_root))
    cli.pass_env_root = False

    result = cli.run_ok("root")

    assert result.stdout.strip() == str(config_root)


def test_root_absolutizes_relative_env_root(cli: NhqCLI) -> None:
    cli.nhq_root = Path("relative/dir")

    result = cli.run_ok("root")

    printed = Path(result.stdout.strip())
    assert printed.is_absolute()
    assert str(printed).endswith("/relative/dir")
    assert result.stderr == ""


def test_root_absolutizes_relative_git_config(cli: NhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("config", "nhq.root", "relative/dir")
    cli.pass_env_root = False

    result = cli.run_ok("root")

    printed = Path(result.stdout.strip())
    assert printed.is_absolute()
    assert str(printed).endswith("/relative/dir")
    assert result.stderr == ""


def test_root_without_git_repo(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    repo = GitRepo(str(tmp_path))  # bare dir, never git init
    cli = NhqCLI(repo, tmp_path_factory.mktemp("nhq_root"))

    result = cli.run_ok("root")

    assert result.stdout.strip() == str(cli.nhq_root)


def test_root_with_env_root_skips_git(
    cli: NhqCLI, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # With NHQ_ROOT set, resolution must not shell out to git; PATH points at a
    # dir with no git binary, so any git call would fail with "git not found".
    monkeypatch.setenv("PATH", str(tmp_path))

    result = cli.run_ok("root")

    assert result.stdout.strip() == str(cli.nhq_root)


def test_root_help(cli: NhqCLI) -> None:
    result = cli.run_ok("root", "--help")

    assert "a git repo is not required" in result.stderr
    assert "Root resolution:" in result.stderr
