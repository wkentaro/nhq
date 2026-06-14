from pathlib import Path

from ihq._store import MANIFEST_NAME
from ihq._store import add_to_manifest
from ihq._store import read_manifest


def test_read_missing_is_empty(tmp_path: Path) -> None:
    assert read_manifest(tmp_path) == []


def test_add_writes_sorted(tmp_path: Path) -> None:
    add_to_manifest(tmp_path, "scratch")
    add_to_manifest(tmp_path, "backend/.env")

    assert read_manifest(tmp_path) == ["backend/.env", "scratch"]
    assert (tmp_path / MANIFEST_NAME).read_text() == "backend/.env\nscratch\n"


def test_add_is_idempotent(tmp_path: Path) -> None:
    add_to_manifest(tmp_path, "scratch")
    add_to_manifest(tmp_path, "scratch")

    assert read_manifest(tmp_path) == ["scratch"]


def test_read_strips_blanks_and_sorts(tmp_path: Path) -> None:
    (tmp_path / MANIFEST_NAME).write_text("b\n\n  a  \n")

    assert read_manifest(tmp_path) == ["a", "b"]


def test_add_creates_store_dir(tmp_path: Path) -> None:
    store = tmp_path / "new" / "store"

    add_to_manifest(store, "x")

    assert (store / MANIFEST_NAME).is_file()
