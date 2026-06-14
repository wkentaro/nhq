from pathlib import Path

import pytest

from tests.conftest import GitRepo

from .conftest import IhqCLI


def test_root_prints_env_root(cli: IhqCLI) -> None:
    result = cli.run_ok("root")

    assert result.stdout.strip() == str(cli.ihq_root)
    assert result.stderr == ""


def test_root_uses_git_config_when_no_env(
    cli: IhqCLI, git_repo: GitRepo, tmp_path: Path
) -> None:
    config_root = tmp_path / "config-root"
    git_repo.git("config", "ihq.root", str(config_root))
    cli.pass_env_root = False

    result = cli.run_ok("root")

    assert result.stdout.strip() == str(config_root)


def test_root_absolutizes_relative_env_root(cli: IhqCLI) -> None:
    cli.ihq_root = Path("relative/dir")

    result = cli.run_ok("root")

    printed = Path(result.stdout.strip())
    assert printed.is_absolute()
    assert str(printed).endswith("/relative/dir")
    assert result.stderr == ""


def test_root_absolutizes_relative_git_config(cli: IhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("config", "ihq.root", "relative/dir")
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
    cli = IhqCLI(repo, tmp_path_factory.mktemp("ihq_root"))

    result = cli.run_ok("root")

    assert result.stdout.strip() == str(cli.ihq_root)


def test_root_with_env_root_skips_git(
    cli: IhqCLI, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # With IHQ_ROOT set, resolution must not shell out to git; PATH points at a
    # dir with no git binary, so any git call would fail with "git not found".
    monkeypatch.setenv("PATH", str(tmp_path))

    result = cli.run_ok("root")

    assert result.stdout.strip() == str(cli.ihq_root)


def test_root_help(cli: IhqCLI) -> None:
    result = cli.run_ok("root", "--help")

    assert "a git repo is not required" in result.stdout
    assert "Root resolution:" in result.stdout
    assert result.stderr == ""
