from pathlib import Path

from nhq._store import store_path
from tests.conftest import GitRepo

from .conftest import NhqCLI

_IDENTITY = "github.com/wkentaro/labelme"


def _make_store(cli: NhqCLI, subpath: str) -> Path:
    store = store_path(root=cli.nhq_root, identity=_IDENTITY, subpath=subpath)
    store.mkdir(parents=True)
    return store


def _parse(stdout: str) -> list[tuple[bool, str, str]]:
    rows: list[tuple[bool, str, str]] = []
    for line in stdout.splitlines():
        marked = line[0] == "*"
        label, path = line[2:].split(None, 1)
        rows.append((marked, label, path))
    return rows


def test_list_no_stores_is_empty(cli: NhqCLI) -> None:
    result = cli.run_ok("list")

    assert result.stdout == ""
    assert result.stderr == ""


def test_list_root_only(cli: NhqCLI) -> None:
    root_store = _make_store(cli, "")

    result = cli.run_ok("list")

    assert _parse(result.stdout) == [(True, ".", str(root_store))]


def test_list_root_and_subtrees_sorted(cli: NhqCLI) -> None:
    root_store = _make_store(cli, "")
    tests_store = _make_store(cli, "tests")
    widgets_store = _make_store(cli, "labelme/widgets")

    result = cli.run_ok("list")

    assert _parse(result.stdout) == [
        (True, ".", str(root_store)),
        (False, "labelme/widgets/", str(widgets_store)),
        (False, "tests/", str(tests_store)),
    ]


def test_list_is_cwd_independent(cli: NhqCLI, git_repo: GitRepo) -> None:
    _make_store(cli, "")
    _make_store(cli, "tests")
    subdir = git_repo.mkdir("docs")

    from_root = cli.run_ok("list")
    from_subdir = cli.run_ok("list", cwd=subdir)

    def labels_and_paths(rows: list[tuple[bool, str, str]]) -> list[tuple[str, str]]:
        return [(label, path) for _, label, path in rows]

    assert labels_and_paths(_parse(from_root.stdout)) == labels_and_paths(
        _parse(from_subdir.stdout)
    )


def test_list_marks_current_subtree(cli: NhqCLI, git_repo: GitRepo) -> None:
    _make_store(cli, "")
    _make_store(cli, "tests")
    subdir = git_repo.mkdir("tests")

    result = cli.run_ok("list", cwd=subdir)

    marked = [label for is_marked, label, _ in _parse(result.stdout) if is_marked]
    assert marked == ["tests/"]


def test_list_ignores_sibling_repos_and_files(cli: NhqCLI) -> None:
    root_store = _make_store(cli, "")
    (root_store.parent / "labelme2").mkdir()
    (root_store.parent / "labelme%2Fa_file").write_text("")

    result = cli.run_ok("list")

    assert _parse(result.stdout) == [(True, ".", str(root_store))]


def test_list_requires_origin_remote(cli: NhqCLI, git_repo: GitRepo) -> None:
    git_repo.git("remote", "remove", "origin")

    result = cli.run("list")

    assert result.returncode == 1
    assert "requires an 'origin' remote" in result.stderr


def test_list_help(cli: NhqCLI) -> None:
    result = cli.run_ok("list", "--help")

    assert "Root resolution:" in result.stdout
    assert result.stderr == ""
