import os
import subprocess
from pathlib import Path

import pytest


class GitRepo:
    def __init__(self, path: str) -> None:
        self.path = path

    def run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(list(args), capture_output=True, text=True, cwd=self.path)

    def git(self, *args: str) -> str:
        result = self.run("git", *args)
        assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"
        return result.stdout

    def mkdir(self, name: str) -> str:
        path = os.path.join(self.path, name)
        os.makedirs(path, exist_ok=True)
        return path


@pytest.fixture
def git_repo(tmp_path: Path) -> GitRepo:
    repo = GitRepo(str(tmp_path))
    repo.git("init")
    repo.git("config", "user.email", "test@test.com")
    repo.git("config", "user.name", "Test")
    repo.git("remote", "add", "origin", "git@github.com:wkentaro/labelme.git")
    return repo
