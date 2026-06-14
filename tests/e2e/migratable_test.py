from pathlib import Path

from tests.conftest import GitRepo

from .conftest import IhqCLI
from .conftest import seed


def _parse(stdout: str) -> list[tuple[str, str]]:
    return [(line[0], line[2:]) for line in stdout.splitlines()]


def _ignore(git_repo: GitRepo, *patterns: str) -> None:
    (Path(git_repo.path) / ".gitignore").write_text(
        "".join(pattern + "\n" for pattern in patterns)
    )
    git_repo.git("add", ".gitignore")
    git_repo.git("commit", "-m", "gitignore")


def test_migratable_empty_is_blank(cli: IhqCLI) -> None:
    result = cli.run_ok("migratable")

    assert result.stdout == ""
    assert result.stderr == ""


def test_migratable_marks_ignored_blank_and_untracked_question(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    _ignore(git_repo, "*.log", "secret.env")
    (Path(git_repo.path) / "app.log").write_text("log\n")
    (Path(git_repo.path) / "secret.env").write_text("SECRET=1\n")
    (Path(git_repo.path) / "newfeature.py").write_text("print()\n")

    result = cli.run_ok("migratable")

    assert _parse(result.stdout) == [
        (" ", "app.log"),
        ("?", "newfeature.py"),
        (" ", "secret.env"),
    ]


def test_migratable_collapses_wholly_ignored_directory(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    _ignore(git_repo, "build/")
    build = Path(git_repo.mkdir("build"))
    (build / "a.txt").write_text("a\n")
    (build / "b.txt").write_text("b\n")

    result = cli.run_ok("migratable")

    assert _parse(result.stdout) == [(" ", "build/")]


def test_migratable_marks_partially_ignored_directory_untracked(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    # The directory's own name is not ignored, but its contents are (nested
    # .gitignore '*'), so it surfaces in both git passes. The untracked '?' wins.
    vendor = Path(git_repo.mkdir("vendor"))
    (vendor / ".gitignore").write_text("*\n")
    (vendor / "blob.bin").write_text("x\n")

    result = cli.run_ok("migratable")

    assert _parse(result.stdout) == [("?", "vendor/")]


def test_migratable_excludes_managed_paths(cli: IhqCLI, git_repo: GitRepo) -> None:
    _ignore(git_repo, "*.log")
    (Path(git_repo.path) / "keep.log").write_text("keep\n")
    seed(cli, "scratch")
    cli.run_ok("link", "scratch")

    result = cli.run_ok("migratable")

    assert _parse(result.stdout) == [(" ", "keep.log")]


def test_migratable_excludes_paths_under_a_managed_directory(
    cli: IhqCLI, git_repo: GitRepo
) -> None:
    notes = Path(git_repo.mkdir("notes"))
    cli.run_ok("migrate", "notes")
    (notes / "loose.txt").write_text("x\n")  # notes is a symlink into the store

    result = cli.run_ok("migratable")

    assert result.stdout == ""


def test_migratable_is_cwd_independent(cli: IhqCLI, git_repo: GitRepo) -> None:
    _ignore(git_repo, "*.log")
    (Path(git_repo.path) / "a.log").write_text("x\n")
    subdir = git_repo.mkdir("docs")

    from_root = cli.run_ok("migratable")
    from_subdir = cli.run_ok("migratable", cwd=subdir)

    assert from_root.stdout != ""
    assert from_root.stdout == from_subdir.stdout


def test_migratable_help(cli: IhqCLI) -> None:
    result = cli.run_ok("migratable", "--help")

    assert "Root resolution:" in result.stdout
    assert result.stderr == ""


def test_migratable_requires_origin_remote(cli: IhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("migratable")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr
