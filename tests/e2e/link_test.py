from pathlib import Path

from ihq._store import MANIFEST_NAME
from tests.conftest import GitRepo

from .conftest import IhqCLI
from .conftest import exclude_lines
from .conftest import seed


def test_link_creates_symlink_and_exclude(cli: IhqCLI, git_repo: GitRepo) -> None:
    slot = seed(cli, "scratch")

    result = cli.run_ok("link", "scratch")

    link = Path(git_repo.path) / "scratch"
    assert link.is_symlink()
    assert link.readlink() == slot
    assert "/scratch" in exclude_lines(git_repo)
    assert "linked" in result.stderr


def test_link_requires_store(cli: IhqCLI) -> None:
    result = cli.run("link", "scratch")

    assert result.returncode == 1
    assert "nothing in the store for 'scratch'" in result.stderr


def test_link_all_links_every_managed_path(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    seed(cli, "backend/.env")

    cli.run_ok("link")

    assert (Path(git_repo.path) / "scratch").is_symlink()
    assert (Path(git_repo.path) / "backend/.env").is_symlink()


def test_link_all_skips_missing_from_store(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    manifest = cli.store / MANIFEST_NAME
    manifest.write_text(manifest.read_text() + "ghost\n")

    cli.run_ok("link")

    assert (Path(git_repo.path) / "scratch").is_symlink()
    assert not (Path(git_repo.path) / "ghost").exists()


def test_link_is_idempotent(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    cli.run_ok("link", "scratch")

    result = cli.run_ok("link", "scratch")

    assert "already linked" in result.stderr
    assert exclude_lines(git_repo).count("/scratch") == 1


def test_link_creates_parent_dir_for_nested_path(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    seed(cli, "backend/.env")

    cli.run_ok("link", "backend/.env")

    assert (Path(git_repo.path) / "backend").is_dir()
    assert (Path(git_repo.path) / "backend/.env").is_symlink()


def test_link_refuses_foreign_symlink(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    (Path(git_repo.path) / "scratch").symlink_to("/somewhere/else")

    result = cli.run("link", "scratch")

    assert result.returncode == 1
    assert "already links to" in result.stderr


def test_link_refuses_regular_file(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    (Path(git_repo.path) / "scratch").write_text("not a link")

    result = cli.run("link", "scratch")

    assert result.returncode == 1
    assert "not an ihq symlink" in result.stderr


def test_link_help(cli: IhqCLI) -> None:
    result = cli.run_ok("link", "--help")

    assert "ihq link" in result.stdout
    assert result.stderr == ""


def test_link_requires_origin_remote(cli: IhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("link")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr
