import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from ihq._cli import cli as ihq_cli
from ihq._store import MANIFEST_NAME
from tests.conftest import GitRepo

IDENTITY = "github.com/wkentaro/labelme"


class IhqCLI:
    def __init__(self, repo: GitRepo, ihq_root: Path) -> None:
        self.repo = repo
        self.ihq_root = ihq_root
        self.pass_env_root = True

    @property
    def store(self) -> Path:
        return self.ihq_root / IDENTITY

    def run(
        self, *args: str, cwd: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = {"IHQ_ROOT": str(self.ihq_root) if self.pass_env_root else None}
        runner = CliRunner()
        old_cwd = os.getcwd()
        try:
            os.chdir(cwd or self.repo.path)
            result = runner.invoke(ihq_cli, list(args), env=env)
        finally:
            os.chdir(old_cwd)

        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception

        return subprocess.CompletedProcess(
            args=["ihq", *args],
            returncode=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def run_ok(
        self, *args: str, cwd: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        result = self.run(*args, cwd=cwd)
        assert result.returncode == 0, f"ihq {' '.join(args)} failed: {result.stderr}"
        return result


@pytest.fixture
def cli(git_repo: GitRepo, tmp_path_factory: pytest.TempPathFactory) -> IhqCLI:
    ihq_root = tmp_path_factory.mktemp("ihq_root")
    return IhqCLI(git_repo, ihq_root)


def exclude_lines(git_repo: GitRepo) -> list[str]:
    return (Path(git_repo.path) / ".git/info/exclude").read_text().splitlines()


def seed(cli: IhqCLI, managed: str, *, is_dir: bool = False) -> Path:
    """Populate a store slot and manifest entry, as if migrated on another machine."""
    slot = cli.store / managed
    slot.parent.mkdir(parents=True, exist_ok=True)
    if is_dir:
        slot.mkdir()
    else:
        slot.write_text(f"{managed} content\n")

    manifest = cli.store / MANIFEST_NAME
    entries = manifest.read_text().splitlines() if manifest.exists() else []
    if managed not in entries:
        entries = sorted([*entries, managed])
        manifest.write_text("".join(entry + "\n" for entry in entries))
    return slot
