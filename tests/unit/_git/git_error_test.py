from collections.abc import Callable
from pathlib import Path

import pytest

from nhq._git import GitError
from nhq._git import get_exclude_path
from nhq._git import get_show_prefix


@pytest.mark.parametrize("query", [get_show_prefix, get_exclude_path])
def test_raises_outside_repo(
    query: Callable[[], str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(GitError):
        query()
