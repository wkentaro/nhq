import pytest

from ihq._store import parse_remote_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("git@github.com:wkentaro/labelme.git", "github.com/wkentaro/labelme"),
        ("git@github.com:wkentaro/labelme", "github.com/wkentaro/labelme"),
        ("github.com:wkentaro/labelme.git", "github.com/wkentaro/labelme"),
        ("https://github.com/wkentaro/labelme.git", "github.com/wkentaro/labelme"),
        ("https://github.com/wkentaro/labelme", "github.com/wkentaro/labelme"),
        ("ssh://git@github.com/wkentaro/labelme.git", "github.com/wkentaro/labelme"),
        ("ssh://git@github.com:22/wkentaro/labelme.git", "github.com/wkentaro/labelme"),
        ("git://github.com/wkentaro/labelme.git", "github.com/wkentaro/labelme"),
        ("https://user@github.com/wkentaro/labelme.git", "github.com/wkentaro/labelme"),
        (
            "https://user:token@github.com/wkentaro/labelme.git",
            "github.com/wkentaro/labelme",
        ),
        (
            "git@gitlab.com:group/subgroup/project.git",
            "gitlab.com/group/subgroup/project",
        ),
        (
            "https://gitlab.com/group/subgroup/project.git",
            "gitlab.com/group/subgroup/project",
        ),
        ("git@gitlab.com:a/b/c/d/e.git", "gitlab.com/a/b/c/d/e"),
        ("https://github.com/wkentaro/labelme.git/", "github.com/wkentaro/labelme"),
        ("https://github.com//wkentaro//labelme.git", "github.com/wkentaro/labelme"),
        ("git@GitHub.com:wkentaro/labelme.git", "github.com/wkentaro/labelme"),
    ],
)
def test_parse_remote_url(url: str, expected: str) -> None:
    assert parse_remote_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://github.com/",
        "github.com",
        "https://github.com/../../etc/passwd",
        "https://github.com/%2E%2E/%2E%2E/etc/passwd",
    ],
)
def test_parse_remote_url_invalid(url: str) -> None:
    with pytest.raises(ValueError):
        parse_remote_url(url)
