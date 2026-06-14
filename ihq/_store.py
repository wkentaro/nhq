import os
import re
import urllib.parse
from pathlib import Path
from typing import Final

MARKER_NAME: Final = ".ihqdir"


def parse_remote_url(url: str) -> str:
    url = url.strip().rstrip("/")

    scp = (
        re.match(r"^(?:[^@/]+@)?(?P<host>[^/:]+):(?P<path>.+)$", url)
        if "://" not in url
        else None
    )
    if scp:
        host, path = scp.group("host"), scp.group("path")
    else:
        parsed = urllib.parse.urlparse(url)
        host, path = parsed.hostname or "", parsed.path

    host = host.lower()
    path = re.sub(r"/+", "/", urllib.parse.unquote(path).strip("/"))
    path = path.removesuffix(".git").strip("/")

    if not host or not path:
        raise ValueError(f"cannot parse remote url: {url!r}")
    if any(segment in (".", "..") for segment in path.split("/")):
        raise ValueError(f"remote url has invalid path: {url!r}")
    return f"{host}/{path}"


def resolve_root(env_root: str | None, config_root: str | None) -> Path:
    raw = env_root or config_root
    if raw:
        return Path(raw).expanduser().absolute()
    return Path.home() / "ihq"


def store_path(root: Path, identity: str) -> Path:
    return root / identity


def to_managed_path(arg: str, toplevel: Path, cwd: Path) -> str:
    target = Path(os.path.normpath(os.path.join(str(cwd), arg)))
    try:
        relative = target.relative_to(toplevel)
    except ValueError:
        raise ValueError(f"path is outside the repository: {arg!r}") from None
    managed = relative.as_posix()
    if managed in (".", ""):
        raise ValueError("path is the repository root, not a file within it")
    if Path(managed).name == MARKER_NAME:
        raise ValueError(f"{MARKER_NAME!r} is reserved by ihq as a directory marker")
    return managed


def scan_store(store: Path) -> list[str]:
    if not store.is_dir():
        return []
    managed: list[str] = []
    _collect_managed(directory=store, store=store, managed=managed)
    return sorted(managed)


def _collect_managed(directory: Path, store: Path, managed: list[str]) -> None:
    for child in directory.iterdir():
        # The store holds real moved content; a stray symlink is never a unit.
        if child.is_symlink():
            continue
        relative = child.relative_to(store).as_posix()
        if not child.is_dir():
            if child.name != MARKER_NAME:
                managed.append(relative)
            continue
        if (child / MARKER_NAME).is_file():
            managed.append(relative)
            continue
        _collect_managed(directory=child, store=store, managed=managed)
