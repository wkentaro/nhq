from pathlib import Path

from tests.conftest import GitRepo

from .conftest import NhqCLI


def test_path_prints_store(cli: NhqCLI) -> None:
    store = cli.nhq_root / "github.com/wkentaro/labelme"

    result = cli.run_ok("path")

    assert result.stdout.strip() == str(store)
    assert result.stderr == ""


def test_path_does_not_create_or_link(cli: NhqCLI, git_repo: GitRepo) -> None:
    store = cli.nhq_root / "github.com/wkentaro/labelme"

    cli.run_ok("path")

    assert not store.exists()
    assert not (Path(git_repo.path) / "nhq").exists()


def test_path_subtree_store(cli: NhqCLI, git_repo: GitRepo) -> None:
    subdir = git_repo.mkdir("services/api")
    store = cli.nhq_root / "github.com/wkentaro/labelme%2Fservices%2Fapi"

    result = cli.run_ok("path", cwd=subdir)

    assert result.stdout.strip() == str(store)


def test_path_requires_origin_remote(cli: NhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("path")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr


def test_path_help(cli: NhqCLI) -> None:
    result = cli.run_ok("path", "--help")

    assert "Root resolution:" in result.stdout
    assert result.stderr == ""
