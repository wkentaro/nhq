from pathlib import Path

import pytest

from nhq._git import ensure_excluded
from nhq._git import remove_excluded
from tests.conftest import GitRepo


@pytest.fixture
def in_repo(git_repo: GitRepo, monkeypatch: pytest.MonkeyPatch) -> GitRepo:
    monkeypatch.chdir(git_repo.path)
    return git_repo


def _exclude(git_repo: GitRepo) -> Path:
    return Path(git_repo.path) / ".git/info/exclude"


def test_removes_matching_line_and_preserves_others(in_repo: GitRepo) -> None:
    ensure_excluded("manual-entry")
    ensure_excluded("/nhq")

    assert remove_excluded("/nhq") is True
    lines = _exclude(in_repo).read_text().splitlines()
    assert "/nhq" not in lines
    assert "manual-entry" in lines


def test_returns_false_when_line_absent(in_repo: GitRepo) -> None:
    ensure_excluded("manual-entry")

    assert remove_excluded("/nhq") is False
    assert "manual-entry" in _exclude(in_repo).read_text().splitlines()


def test_returns_false_when_exclude_missing(in_repo: GitRepo) -> None:
    _exclude(in_repo).unlink()

    assert remove_excluded("/nhq") is False
