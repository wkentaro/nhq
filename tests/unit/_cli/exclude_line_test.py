import pytest

from ihq._cli import _exclude_line
from ihq._cli import _managed_from_exclude_line


@pytest.mark.parametrize(
    "managed",
    [
        "scratch",
        "backend/.env",
        "a*b",
        "build[1]",
        "what?",
        "back\\slash",
        "a\\*b",
        "packages/foo/note[s]/*.log",
    ],
)
def test_round_trips_through_exclude_line(managed: str) -> None:
    assert _managed_from_exclude_line(_exclude_line(managed)) == managed


def test_foreign_lines_are_not_managed_paths() -> None:
    assert _managed_from_exclude_line("# a comment") is None
    assert _managed_from_exclude_line("") is None
    assert _managed_from_exclude_line("relative/path") is None
