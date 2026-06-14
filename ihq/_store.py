import os
import re
import urllib.parse
from pathlib import Path
from typing import Final

MANIFEST_NAME: Final = ".ihq"


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
    if managed == MANIFEST_NAME:
        raise ValueError(f"{MANIFEST_NAME!r} is reserved for the manifest")
    return managed


def read_manifest(store: Path) -> list[str]:
    manifest = store / MANIFEST_NAME
    if not manifest.is_file():
        return []
    paths = [line.strip() for line in manifest.read_text().splitlines()]
    return sorted(path for path in paths if path)


def add_to_manifest(store: Path, managed_path: str) -> None:
    paths = read_manifest(store)
    if managed_path in paths:
        return
    paths = sorted([*paths, managed_path])
    store.mkdir(parents=True, exist_ok=True)
    (store / MANIFEST_NAME).write_text("".join(path + "\n" for path in paths))
