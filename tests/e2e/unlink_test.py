from pathlib import Path

import pytest

from tests.conftest import GitRepo

from .conftest import NhqCLI
from .conftest import exclude_lines
from .conftest import make_store


def test_unlink_removes_symlink_and_exclude(cli: NhqCLI, git_repo: GitRepo) -> None:
    store = make_store(cli)
    cli.run_ok("link")
    link = Path(git_repo.path) / "nhq"

    result = cli.run_ok("unlink")

    assert not link.is_symlink()
    assert not link.exists()
    assert "/nhq" not in exclude_lines(git_repo)
    assert "unlinked" in result.stderr
    assert store.is_dir()


def test_unlink_scrubs_lingering_exclude_when_link_already_gone(
    cli: NhqCLI, git_repo: GitRepo
) -> None:
    make_store(cli)
    cli.run_ok("link")
    (Path(git_repo.path) / "nhq").unlink()  # manual rm of the symlink

    result = cli.run_ok("unlink")

    assert "/nhq" not in exclude_lines(git_repo)
    assert "unlinked" in result.stderr


def test_unlink_noop_exits_zero(cli: NhqCLI, git_repo: GitRepo) -> None:
    make_store(cli)

    result = cli.run_ok("unlink")

    assert "nothing to unlink" in result.stderr
    assert not (Path(git_repo.path) / "nhq").exists()
    assert "/nhq" not in exclude_lines(git_repo)


def test_unlink_is_idempotent(cli: NhqCLI) -> None:
    make_store(cli)
    cli.run_ok("link")
    cli.run_ok("unlink")

    result = cli.run_ok("unlink")

    assert "nothing to unlink" in result.stderr


def test_unlink_subtree(cli: NhqCLI, git_repo: GitRepo) -> None:
    subdir = git_repo.mkdir("services/api")
    make_store(cli, "github.com/wkentaro/labelme%2Fservices%2Fapi")
    cli.run_ok("link", cwd=subdir)
    link = Path(subdir) / "nhq"

    cli.run_ok("unlink", cwd=subdir)

    assert not link.exists()
    assert "/services/api/nhq" not in exclude_lines(git_repo)


def test_unlink_refuses_foreign_symlink(cli: NhqCLI, git_repo: GitRepo) -> None:
    store = make_store(cli)
    link = Path(git_repo.path) / "nhq"
    link.symlink_to("/somewhere/else")

    result = cli.run("unlink")

    assert result.returncode == 1
    assert "not this repo's store" in result.stderr
    assert "remove ./nhq" in result.stderr
    assert link.readlink() == Path("/somewhere/else")
    assert store.is_dir()


def test_unlink_refuses_regular_file(cli: NhqCLI, git_repo: GitRepo) -> None:
    make_store(cli)
    link = Path(git_repo.path) / "nhq"
    link.write_text("not a link")

    result = cli.run("unlink")

    assert result.returncode == 1
    assert "not an nhq symlink" in result.stderr
    assert link.read_text() == "not a link"


def test_unlink_refuses_directory(cli: NhqCLI, git_repo: GitRepo) -> None:
    make_store(cli)
    link = Path(git_repo.path) / "nhq"
    link.mkdir()

    result = cli.run("unlink")

    assert result.returncode == 1
    assert "not an nhq symlink" in result.stderr
    assert link.is_dir()


def test_unlink_reports_filesystem_error_and_keeps_symlink(
    cli: NhqCLI, git_repo: GitRepo
) -> None:
    make_store(cli)
    cli.run_ok("link")
    link = Path(git_repo.path) / "nhq"
    exclude = Path(git_repo.path) / ".git/info/exclude"
    exclude.unlink()
    exclude.mkdir()  # a directory where the exclude file is expected

    result = cli.run("unlink")

    assert result.returncode == 1
    assert "cannot unlink" in result.stderr
    assert link.is_symlink()  # scrubbed-first: symlink left intact on failure


def test_unlink_restores_exclude_when_symlink_removal_fails(
    cli: NhqCLI, git_repo: GitRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_store(cli)
    cli.run_ok("link")
    link = Path(git_repo.path) / "nhq"

    def fail_unlink(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError("cannot remove symlink")

    monkeypatch.setattr(Path, "unlink", fail_unlink)
    result = cli.run("unlink")

    assert result.returncode == 1
    assert "cannot unlink" in result.stderr
    assert link.is_symlink()  # symlink survives the failed removal
    assert "/nhq" in exclude_lines(git_repo)  # exclude restored: state stays consistent


def test_unlink_help(cli: NhqCLI) -> None:
    result = cli.run_ok("unlink", "--help")

    assert "nhq unlink" in result.stdout
    assert result.stderr == ""


def test_unlink_requires_origin_remote(cli: NhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("unlink")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr
