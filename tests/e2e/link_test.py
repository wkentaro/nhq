from pathlib import Path

from tests.conftest import GitRepo

from .conftest import NhqCLI
from .conftest import exclude_lines


def _make_store(cli: NhqCLI, name: str = "github.com/wkentaro/labelme") -> Path:
    store = cli.nhq_root / name
    store.mkdir(parents=True)
    return store


def test_link_creates_symlink_and_exclude(cli: NhqCLI, git_repo: GitRepo) -> None:
    store = _make_store(cli)

    result = cli.run_ok("link")

    link = Path(git_repo.path) / "nhq"
    assert link.is_symlink()
    assert link.readlink() == store
    assert "/nhq" in exclude_lines(git_repo)
    assert "already linked" not in result.stderr
    assert "linked" in result.stderr


def test_link_is_idempotent(cli: NhqCLI, git_repo: GitRepo) -> None:
    _make_store(cli)
    cli.run_ok("link")

    result = cli.run_ok("link")

    assert "already linked" in result.stderr
    assert exclude_lines(git_repo).count("/nhq") == 1


def test_link_subtree(cli: NhqCLI, git_repo: GitRepo) -> None:
    subdir = git_repo.mkdir("services/api")
    store = _make_store(cli, "github.com/wkentaro/labelme%2Fservices%2Fapi")

    cli.run_ok("link", cwd=subdir)

    link = Path(subdir) / "nhq"
    assert link.is_symlink()
    assert link.readlink() == store
    assert "/services/api/nhq" in exclude_lines(git_repo)


def test_link_appends_after_file_without_trailing_newline(
    cli: NhqCLI, git_repo: GitRepo
) -> None:
    _make_store(cli)
    exclude = Path(git_repo.path) / ".git/info/exclude"
    exclude.write_text("manual-entry")  # no trailing newline

    cli.run_ok("link")

    lines = exclude_lines(git_repo)
    assert "manual-entry" in lines
    assert "/nhq" in lines


def test_link_help(cli: NhqCLI) -> None:
    result = cli.run_ok("link", "--help")

    assert "nhq link" in result.stderr


def test_link_requires_store(cli: NhqCLI) -> None:
    result = cli.run("link")

    assert result.returncode == 1
    assert "no store for this repo" in result.stderr


def test_link_refuses_foreign_symlink(cli: NhqCLI, git_repo: GitRepo) -> None:
    _make_store(cli)
    (Path(git_repo.path) / "nhq").symlink_to("/somewhere/else")

    result = cli.run("link")

    assert result.returncode == 1
    assert "already links to" in result.stderr
    assert "remove ./nhq" in result.stderr


def test_link_refuses_regular_file(cli: NhqCLI, git_repo: GitRepo) -> None:
    _make_store(cli)
    (Path(git_repo.path) / "nhq").write_text("not a link")

    result = cli.run("link")

    assert result.returncode == 1
    assert "not an nhq symlink" in result.stderr
    assert "remove ./nhq" in result.stderr


def test_link_reports_filesystem_error(cli: NhqCLI, git_repo: GitRepo) -> None:
    _make_store(cli)
    exclude = Path(git_repo.path) / ".git/info/exclude"
    exclude.unlink()
    exclude.mkdir()  # a directory where the exclude file is expected

    result = cli.run("link")

    assert result.returncode == 1
    assert "cannot link" in result.stderr


def test_link_store_missing_wins_over_existing_link(
    cli: NhqCLI, git_repo: GitRepo
) -> None:
    # No store created; an unrelated ./nhq is also present.
    (Path(git_repo.path) / "nhq").symlink_to("/somewhere/else")

    result = cli.run("link")

    assert result.returncode == 1
    assert "no store for this repo" in result.stderr
