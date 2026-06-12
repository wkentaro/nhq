import subprocess


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def is_git_repo() -> bool:
    return _run("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"


def get_origin_url() -> str | None:
    result = _run("remote", "get-url", "origin")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def get_show_prefix() -> str:
    return _run("rev-parse", "--show-prefix").stdout.strip()


def get_config(key: str) -> str | None:
    result = _run("config", key)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
