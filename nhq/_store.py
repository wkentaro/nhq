import re
import urllib.parse
from pathlib import Path


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
    return Path.home() / "nhq"


def store_path(root: Path, identity: str, subpath: str) -> Path:
    base = root / identity
    subpath = subpath.strip("/")
    if not subpath:
        return base
    # Encode the joining "/" too, so the subtree store is a sibling of the repo
    # store, not a child of it (ADR-0003).
    encoded = urllib.parse.quote("/" + subpath, safe="")
    return base.parent / (base.name + encoded)


def decode_subpath(leaf: str, name: str) -> str | None:
    if name == leaf:
        return ""
    prefix = leaf + urllib.parse.quote("/", safe="")
    if not name.startswith(prefix):
        return None
    return urllib.parse.unquote(name[len(leaf) :]).strip("/")


def list_stores(root: Path, identity: str) -> list[tuple[str, Path]]:
    base = root / identity
    parent = base.parent
    if not parent.is_dir():
        return []
    stores: list[tuple[str, Path]] = []
    for entry in parent.iterdir():
        if not entry.is_dir():
            continue
        subpath = decode_subpath(leaf=base.name, name=entry.name)
        if subpath is None:
            continue
        stores.append((subpath, entry))
    stores.sort(key=lambda item: (item[0] != "", item[0]))
    return stores
