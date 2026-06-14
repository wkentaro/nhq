from collections.abc import Callable
from pathlib import Path

import pytest

from ihq._git import GitError
from ihq._git import get_exclude_path
from ihq._git import get_toplevel


@pytest.mark.parametrize("query", [get_toplevel, get_exclude_path])
def test_raises_outside_repo(
    query: Callable[[], object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(GitError):
        query()
