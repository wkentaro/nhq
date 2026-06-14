import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _check_returncode(result: subprocess.CompletedProcess[str], *args: str) -> None:
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exited with {result.returncode}"
        raise GitError(f"git {' '.join(args)}: {detail}")


def _run_checked(*args: str) -> str:
    result = _run(*args)
    _check_returncode(result, *args)
    return result.stdout.strip()


def is_git_repo() -> bool:
    return _run("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"


def get_origin_url() -> str | None:
    result = _run("remote", "get-url", "origin")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def get_toplevel() -> Path:
    return Path(_run_checked("rev-parse", "--show-toplevel"))


def is_tracked(path: Path) -> bool:
    return _run("ls-files", "--error-unmatch", "--", str(path)).returncode == 0


def list_others(toplevel: Path, *, ignored: bool) -> list[str]:
    # Run from the toplevel so the listing is whole-repo and repo-relative
    # regardless of the caller's cwd. --directory collapses a wholly-ignored
    # directory to a single entry instead of dumping its contents. Without
    # --ignored the result is the untracked-but-not-ignored set; with it, the
    # ignored set.
    args = [
        "-C",
        str(toplevel),
        "ls-files",
        "--others",
        "--exclude-standard",
        "--directory",
        "-z",
    ]
    if ignored:
        args.append("--ignored")
    result = _run(*args)
    _check_returncode(result, *args)
    return [entry for entry in result.stdout.split("\0") if entry]


def get_config(key: str) -> str | None:
    result = _run("config", key)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def get_exclude_path() -> str:
    return _run_checked("rev-parse", "--git-path", "info/exclude")


def ensure_excluded(line: str) -> None:
    exclude = Path(get_exclude_path())
    content = exclude.read_text() if exclude.exists() else ""
    if line in content.splitlines():
        return
    prefix = "" if content == "" or content.endswith("\n") else "\n"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as file:
        file.write(prefix + line + "\n")


def is_excluded(line: str) -> bool:
    exclude = Path(get_exclude_path())
    if not exclude.exists():
        return False
    return line in exclude.read_text().splitlines()


def remove_excluded(line: str) -> bool:
    exclude = Path(get_exclude_path())
    if not exclude.exists():
        return False
    lines = exclude.read_text().splitlines()
    if line not in lines:
        return False
    kept = [existing for existing in lines if existing != line]
    exclude.write_text("".join(existing + "\n" for existing in kept))
    return True
