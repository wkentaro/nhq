from pathlib import Path

import pytest

from ihq._store import MANIFEST_NAME
from tests.conftest import GitRepo

from .conftest import IhqCLI
from .conftest import exclude_lines
from .conftest import seed


def test_unlink_removes_symlink_but_keeps_store_and_manifest(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    slot = seed(cli, "scratch")
    cli.run_ok("link", "scratch")
    link = Path(git_repo.path) / "scratch"

    result = cli.run_ok("unlink", "scratch")

    assert not link.exists()
    assert "/scratch" not in exclude_lines(git_repo)
    assert "unlinked" in result.stderr
    assert slot.exists()
    assert (cli.store / MANIFEST_NAME).read_text().splitlines() == ["scratch"]


def test_unlink_all_removes_every_link(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    seed(cli, "backend/.env")
    cli.run_ok("link")

    cli.run_ok("unlink", "--all")

    assert not (Path(git_repo.path) / "scratch").exists()
    assert not (Path(git_repo.path) / "backend/.env").is_symlink()
    assert (cli.store / "scratch").exists()
    assert sorted((cli.store / MANIFEST_NAME).read_text().splitlines()) == [
        "backend/.env",
        "scratch",
    ]


def test_unlink_all_scrubs_lingering_exclude_when_link_already_gone(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    seed(cli, "scratch")
    cli.run_ok("link", "scratch")
    (Path(git_repo.path) / "scratch").unlink()  # manual rm of the symlink

    result = cli.run_ok("unlink", "--all")

    assert "/scratch" not in exclude_lines(git_repo)
    assert "unlinked" in result.stderr


def test_unlink_all_leaves_foreign_occupant_untouched(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    seed(cli, "scratch")
    foreign = Path(git_repo.path) / "scratch"
    foreign.symlink_to("/somewhere/else")

    cli.run_ok("unlink", "--all")

    assert foreign.readlink() == Path("/somewhere/else")


def test_unlink_bare_requires_path_or_all(cli: IhqCLI) -> None:
    result = cli.run("unlink")

    assert result.returncode == 2
    assert "specify a path or --all" in result.stderr


def test_unlink_rejects_path_and_all_together(cli: IhqCLI) -> None:
    result = cli.run("unlink", "scratch", "--all")

    assert result.returncode == 1
    assert "not both" in result.stderr


def test_unlink_scrubs_lingering_exclude_when_link_already_gone(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    seed(cli, "scratch")
    cli.run_ok("link", "scratch")
    (Path(git_repo.path) / "scratch").unlink()  # manual rm of the symlink

    result = cli.run_ok("unlink", "scratch")

    assert "/scratch" not in exclude_lines(git_repo)
    assert "unlinked" in result.stderr


def test_unlink_noop_exits_zero(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")

    result = cli.run_ok("unlink", "scratch")

    assert "nothing to unlink" in result.stderr
    assert not (Path(git_repo.path) / "scratch").exists()


def test_unlink_refuses_foreign_symlink(cli: IhqCLI, git_repo: GitRepo) -> None:
    slot = seed(cli, "scratch")
    link = Path(git_repo.path) / "scratch"
    link.symlink_to("/somewhere/else")

    result = cli.run("unlink", "scratch")

    assert result.returncode == 1
    assert "not this repo's store" in result.stderr
    assert link.readlink() == Path("/somewhere/else")
    assert slot.exists()


def test_unlink_refuses_regular_file(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    link = Path(git_repo.path) / "scratch"
    link.write_text("not a link")

    result = cli.run("unlink", "scratch")

    assert result.returncode == 1
    assert "not an ihq symlink" in result.stderr
    assert link.read_text() == "not a link"


def test_unlink_reports_filesystem_error_and_keeps_symlink(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    seed(cli, "scratch")
    cli.run_ok("link", "scratch")
    link = Path(git_repo.path) / "scratch"
    exclude = Path(git_repo.path) / ".git/info/exclude"
    exclude.unlink()
    exclude.mkdir()  # a directory where the exclude file is expected

    result = cli.run("unlink", "scratch")

    assert result.returncode == 1
    assert "cannot unlink" in result.stderr
    assert link.is_symlink()  # scrubbed-first: symlink left intact on failure


def test_unlink_restores_exclude_when_symlink_removal_fails(
    cli: IhqCLI, git_repo: GitRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed(cli, "scratch")
    cli.run_ok("link", "scratch")
    link = Path(git_repo.path) / "scratch"

    def fail_unlink(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError("cannot remove symlink")

    monkeypatch.setattr(Path, "unlink", fail_unlink)
    result = cli.run("unlink", "scratch")

    assert result.returncode == 1
    assert "cannot unlink" in result.stderr
    assert link.is_symlink()  # symlink survives the failed removal
    assert "/scratch" in exclude_lines(git_repo)  # exclude restored: state consistent


def test_unlink_help(cli: IhqCLI) -> None:
    result = cli.run_ok("unlink", "--help")

    assert "ihq unlink" in result.stdout
    assert result.stderr == ""


def test_unlink_requires_origin_remote(cli: IhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("unlink", "scratch")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr
