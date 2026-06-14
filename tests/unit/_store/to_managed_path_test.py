from pathlib import Path

import pytest

from ihq._store import to_managed_path

_TOP = Path("/repo")


def test_simple() -> None:
    assert to_managed_path(arg="scratch", toplevel=_TOP, cwd=_TOP) == "scratch"


def test_nested() -> None:
    assert (
        to_managed_path(arg="backend/.env", toplevel=_TOP, cwd=_TOP) == "backend/.env"
    )


def test_from_subdir_is_repo_relative() -> None:
    result = to_managed_path(arg="scratch", toplevel=_TOP, cwd=Path("/repo/pkg/foo"))
    assert result == "pkg/foo/scratch"


def test_absolute_arg() -> None:
    result = to_managed_path(arg="/repo/a/b", toplevel=_TOP, cwd=Path("/repo/x"))
    assert result == "a/b"


def test_dotdot_within_repo() -> None:
    result = to_managed_path(arg="../scratch", toplevel=_TOP, cwd=Path("/repo/sub"))
    assert result == "scratch"


@pytest.mark.parametrize("arg", ["../../outside", "../../../etc/passwd", "/elsewhere"])
def test_outside_repo_raises(arg: str) -> None:
    with pytest.raises(ValueError, match="outside the repository"):
        to_managed_path(arg=arg, toplevel=_TOP, cwd=Path("/repo/sub"))


@pytest.mark.parametrize("arg", [".", ""])
def test_repo_root_raises(arg: str) -> None:
    with pytest.raises(ValueError, match="repository root"):
        to_managed_path(arg=arg, toplevel=_TOP, cwd=_TOP)


def test_reserved_manifest_name_raises() -> None:
    with pytest.raises(ValueError, match="reserved"):
        to_managed_path(arg=".ihq", toplevel=_TOP, cwd=_TOP)
