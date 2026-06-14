from pathlib import Path

import pytest

from ihq._git import ensure_excluded
from ihq._git import is_excluded
from tests.conftest import GitRepo


@pytest.fixture
def in_repo(git_repo: GitRepo, monkeypatch: pytest.MonkeyPatch) -> GitRepo:
    monkeypatch.chdir(git_repo.path)
    return git_repo


def _exclude(git_repo: GitRepo) -> Path:
    return Path(git_repo.path) / ".git/info/exclude"


def test_returns_true_when_line_present(in_repo: GitRepo) -> None:
    ensure_excluded("/ihq")

    assert is_excluded("/ihq") is True


def test_returns_false_when_line_absent(in_repo: GitRepo) -> None:
    ensure_excluded("manual-entry")

    assert is_excluded("/ihq") is False


def test_returns_false_when_exclude_missing(in_repo: GitRepo) -> None:
    _exclude(in_repo).unlink()

    assert is_excluded("/ihq") is False
