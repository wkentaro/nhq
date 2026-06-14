from pathlib import Path

from ihq._store import MANIFEST_NAME
from tests.conftest import GitRepo

from .conftest import IhqCLI
from .conftest import exclude_lines


def _manifest(cli: IhqCLI) -> list[str]:
    return (cli.store / MANIFEST_NAME).read_text().splitlines()


def test_migrate_file(cli: IhqCLI, git_repo: GitRepo) -> None:
    src = Path(git_repo.path) / "scratch.txt"
    src.write_text("notes\n")

    result = cli.run_ok("migrate", "scratch.txt")

    slot = cli.store / "scratch.txt"
    assert slot.read_text() == "notes\n"
    assert src.is_symlink()
    assert src.readlink() == slot
    assert "/scratch.txt" in exclude_lines(git_repo)
    assert _manifest(cli) == ["scratch.txt"]
    assert "linked" in result.stderr


def test_migrate_escapes_glob_metacharacters_in_exclude(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    (Path(git_repo.path) / "build[1]").write_text("x\n")

    cli.run_ok("migrate", "build[1]")

    assert "/build\\[1]" in exclude_lines(git_repo)
    # The escape is load-bearing: an unescaped /build[1] is a glob and would not
    # exclude the symlink, so prove git actually ignores it.
    assert git_repo.git("status", "--porcelain") == ""


def test_migrate_directory_preserves_content(cli: IhqCLI, git_repo: GitRepo) -> None:
    src = Path(git_repo.mkdir("scratch"))
    (src / "a.txt").write_text("a\n")

    cli.run_ok("migrate", "scratch")

    slot = cli.store / "scratch"
    assert (slot / "a.txt").read_text() == "a\n"
    assert src.is_symlink()
    assert src.readlink() == slot


def test_migrate_nested_path(cli: IhqCLI, git_repo: GitRepo) -> None:
    backend = Path(git_repo.mkdir("backend"))
    (backend / ".env").write_text("SECRET=1\n")

    cli.run_ok("migrate", "backend/.env")

    assert (cli.store / "backend/.env").read_text() == "SECRET=1\n"
    assert (backend / ".env").is_symlink()
    assert "/backend/.env" in exclude_lines(git_repo)
    assert _manifest(cli) == ["backend/.env"]


def test_migrate_from_subdir_uses_repo_relative_path(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    subdir = git_repo.mkdir("packages/foo")
    (Path(subdir) / "scratch").write_text("x\n")

    cli.run_ok("migrate", "scratch", cwd=subdir)

    assert (cli.store / "packages/foo/scratch").read_text() == "x\n"
    assert _manifest(cli) == ["packages/foo/scratch"]


def test_migrate_refuses_tracked_path(cli: IhqCLI, git_repo: GitRepo) -> None:
    src = Path(git_repo.path) / "tracked.txt"
    src.write_text("committed\n")
    git_repo.git("add", "tracked.txt")
    git_repo.git("commit", "-m", "add tracked")

    result = cli.run("migrate", "tracked.txt")

    assert result.returncode == 1
    assert "tracked by git" in result.stderr
    assert not src.is_symlink()
    assert not (cli.store / "tracked.txt").exists()


def test_migrate_refuses_missing_path(cli: IhqCLI) -> None:
    result = cli.run("migrate", "absent")

    assert result.returncode == 1
    assert "nothing to migrate" in result.stderr


def test_migrate_refuses_symlink_source(cli: IhqCLI, git_repo: GitRepo) -> None:
    link = Path(git_repo.path) / "alias"
    link.symlink_to("/somewhere")

    result = cli.run("migrate", "alias")

    assert result.returncode == 1
    assert "is a symlink" in result.stderr


def test_migrate_refuses_when_already_in_store(cli: IhqCLI, git_repo: GitRepo) -> None:
    (cli.store / "scratch").mkdir(parents=True)
    Path(git_repo.mkdir("scratch"))

    result = cli.run("migrate", "scratch")

    assert result.returncode == 1
    assert "already in the store" in result.stderr


def test_migrate_refuses_reserved_name(cli: IhqCLI, git_repo: GitRepo) -> None:
    (Path(git_repo.path) / MANIFEST_NAME).write_text("x\n")

    result = cli.run("migrate", MANIFEST_NAME)

    assert result.returncode == 1
    assert "reserved" in result.stderr


def test_migrate_refuses_overlap_with_managed_parent(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    notes = Path(git_repo.mkdir("notes"))
    cli.run_ok("migrate", "notes")
    (notes / "sub").mkdir()  # notes is now a symlink into the store; write via it

    result = cli.run("migrate", "notes/sub")

    assert result.returncode == 1
    assert "overlaps already-managed" in result.stderr


def test_migrate_refuses_path_outside_repo(cli: IhqCLI) -> None:
    result = cli.run("migrate", "../outside")

    assert result.returncode == 1
    assert "outside the repository" in result.stderr


def test_migrate_no_arg_prints_help(cli: IhqCLI) -> None:
    result = cli.run_ok("migrate")

    assert "ihq migrate" in result.stdout
    assert result.stderr == ""


def test_migrate_help(cli: IhqCLI) -> None:
    result = cli.run_ok("migrate", "--help")

    assert "Root resolution:" in result.stdout
    assert result.stderr == ""
