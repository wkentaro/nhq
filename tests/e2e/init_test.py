from pathlib import Path

from tests.conftest import GitRepo

from .conftest import NhqCLI


def test_init_creates_store(cli: NhqCLI) -> None:
    store = cli.nhq_root / "github.com/wkentaro/labelme"
    assert not store.exists()

    result = cli.run_ok("init")

    assert store.is_dir()
    assert "created store" in result.stderr


def test_init_help(cli: NhqCLI) -> None:
    result = cli.run_ok("init", "--help")

    assert "Root resolution:" in result.stderr


def test_init_is_idempotent(cli: NhqCLI) -> None:
    cli.run_ok("init")
    result = cli.run_ok("init")

    assert "store exists" in result.stderr
    store = cli.nhq_root / "github.com/wkentaro/labelme"
    assert store.is_dir()


def test_init_subtree_store(cli: NhqCLI, git_repo: GitRepo) -> None:
    subdir = git_repo.mkdir("services/api")

    cli.run_ok("init", cwd=subdir)

    store = cli.nhq_root / "github.com/wkentaro/labelme%2Fservices%2Fapi"
    assert store.is_dir()


def test_init_root_uses_git_config_when_no_env(
    cli: NhqCLI, git_repo: GitRepo, tmp_path: Path
) -> None:
    config_root = tmp_path / "config-root"
    git_repo.git("config", "nhq.root", str(config_root))
    cli.pass_env_root = False  # leaves NHQ_ROOT unset so git config wins

    cli.run_ok("init")

    assert (config_root / "github.com/wkentaro/labelme").is_dir()
