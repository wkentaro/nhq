from pathlib import Path

from ihq._store import store_path


def test_store_path() -> None:
    result = store_path(root=Path("/r"), identity="github.com/wkentaro/labelme")
    assert result == Path("/r/github.com/wkentaro/labelme")
