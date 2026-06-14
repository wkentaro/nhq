from ihq._store import MANIFEST_NAME
from tests.conftest import GitRepo

from .conftest import IhqCLI
from .conftest import seed


def _parse(stdout: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in stdout.splitlines():
        mark = line[0]
        managed = line[2:].split(None, 1)[0]
        rows.append((mark, managed))
    return rows


def test_list_empty_is_blank(cli: IhqCLI) -> None:
    result = cli.run_ok("list")

    assert result.stdout == ""
    assert result.stderr == ""


def test_list_marks_status_per_path(cli: IhqCLI) -> None:
    seed(cli, "linked-here")
    seed(cli, "in-store-only")
    cli.run_ok("link", "linked-here")
    manifest = cli.store / MANIFEST_NAME
    manifest.write_text(manifest.read_text() + "missing\n")

    result = cli.run_ok("list")

    assert _parse(result.stdout) == [
        (" ", "in-store-only"),
        ("*", "linked-here"),
        ("!", "missing"),
    ]


def test_list_is_cwd_independent(cli: IhqCLI, git_repo: GitRepo) -> None:
    seed(cli, "scratch")
    seed(cli, "backend/.env")
    subdir = git_repo.mkdir("docs")

    from_root = cli.run_ok("list")
    from_subdir = cli.run_ok("list", cwd=subdir)

    assert from_root.stdout == from_subdir.stdout


def test_list_help(cli: IhqCLI) -> None:
    result = cli.run_ok("list", "--help")

    assert "Root resolution:" in result.stdout
    assert result.stderr == ""


def test_list_requires_origin_remote(cli: IhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("list")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr
