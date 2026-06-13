import pytest

from nhq._store import decode_subpath

_LEAF = "labelme"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("labelme", ""),
        ("labelme%2Ftests", "tests"),
        ("labelme%2Flabelme%2Fwidgets", "labelme/widgets"),
        ("labelme%2Fservices%2Fapi", "services/api"),
        ("labelme%2Fa%25b", "a%b"),
        ("labelme%2Fweird%20dir", "weird dir"),
    ],
)
def test_decode_subpath(name: str, expected: str) -> None:
    assert decode_subpath(leaf=_LEAF, name=name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "labelme2",
        "labelme-io",
        "other",
        "labelmetests",
    ],
)
def test_decode_subpath_non_store(name: str) -> None:
    assert decode_subpath(leaf=_LEAF, name=name) is None
