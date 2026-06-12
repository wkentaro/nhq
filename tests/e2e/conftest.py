import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from nhq._cli import cli as nhq_cli
from tests.conftest import GitRepo


class NhqCLI:
    def __init__(self, repo: GitRepo, nhq_root: Path) -> None:
        self.repo = repo
        self.nhq_root = nhq_root
        self.pass_env_root = True

    def run(
        self, *args: str, cwd: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = {"NHQ_ROOT": str(self.nhq_root) if self.pass_env_root else None}
        runner = CliRunner()
        old_cwd = os.getcwd()
        try:
            os.chdir(cwd or self.repo.path)
            result = runner.invoke(nhq_cli, list(args), env=env)
        finally:
            os.chdir(old_cwd)

        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception

        return subprocess.CompletedProcess(
            args=["nhq", *args],
            returncode=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def run_ok(
        self, *args: str, cwd: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        result = self.run(*args, cwd=cwd)
        assert result.returncode == 0, f"nhq {' '.join(args)} failed: {result.stderr}"
        return result


@pytest.fixture
def cli(git_repo: GitRepo, tmp_path_factory: pytest.TempPathFactory) -> NhqCLI:
    nhq_root = tmp_path_factory.mktemp("nhq_root")
    return NhqCLI(git_repo, nhq_root)
