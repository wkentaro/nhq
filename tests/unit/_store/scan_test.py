from pathlib import Path

from ihq._store import MARKER_NAME
from ihq._store import scan_store


def test_missing_store_is_empty(tmp_path: Path) -> None:
    assert scan_store(tmp_path / "absent") == []


def test_empty_store_is_empty(tmp_path: Path) -> None:
    assert scan_store(tmp_path) == []


def test_files_are_leaves_sorted(tmp_path: Path) -> None:
    (tmp_path / "scratch.md").write_text("x\n")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/.env").write_text("y\n")

    assert scan_store(tmp_path) == ["backend/.env", "scratch.md"]


def test_marked_directory_is_a_unit(tmp_path: Path) -> None:
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / MARKER_NAME).touch()
    (notes / "a.txt").write_text("a\n")
    (notes / "sub").mkdir()
    (notes / "sub/b.txt").write_text("b\n")

    assert scan_store(tmp_path) == ["notes"]


def test_nested_managed_directory(tmp_path: Path) -> None:
    deep = tmp_path / "packages/foo/notes"
    deep.mkdir(parents=True)
    (deep / MARKER_NAME).touch()

    assert scan_store(tmp_path) == ["packages/foo/notes"]


def test_marked_directory_may_be_empty(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / MARKER_NAME).touch()

    assert scan_store(tmp_path) == ["cache"]


def test_intermediate_holds_file_and_managed_subdir(tmp_path: Path) -> None:
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / ".env").write_text("x\n")
    sub = backend / "sub"
    sub.mkdir()
    (sub / MARKER_NAME).touch()

    assert scan_store(tmp_path) == ["backend/.env", "backend/sub"]


def test_stray_marker_file_is_ignored(tmp_path: Path) -> None:
    (tmp_path / MARKER_NAME).touch()
    (tmp_path / "scratch.md").write_text("x\n")

    assert scan_store(tmp_path) == ["scratch.md"]
