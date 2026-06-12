from pathlib import Path

from tests.conftest import GitRepo

from .conftest import NhqCLI
from .conftest import exclude_lines


def test_init_creates_store_and_links(cli: NhqCLI, git_repo: GitRepo) -> None:
    store = cli.nhq_root / "github.com/wkentaro/labelme"
    assert not store.exists()

    result = cli.run_ok("init")

    assert store.is_dir()
    link = Path(git_repo.path) / "nhq"
    assert link.is_symlink()
    assert link.readlink() == store
    assert "/nhq" in exclude_lines(git_repo)
    assert "created store" in result.stderr
    assert "linked" in result.stderr
    assert "already linked" not in result.stderr


def test_init_help(cli: NhqCLI) -> None:
    result = cli.run_ok("init", "--help")

    assert "Root resolution:" in result.stderr


def test_init_is_idempotent(cli: NhqCLI, git_repo: GitRepo) -> None:
    cli.run_ok("init")

    result = cli.run_ok("init")

    assert "store exists" in result.stderr
    assert "already linked" in result.stderr
    assert exclude_lines(git_repo).count("/nhq") == 1


def test_init_subtree_store(cli: NhqCLI, git_repo: GitRepo) -> None:
    subdir = git_repo.mkdir("services/api")

    cli.run_ok("init", cwd=subdir)

    store = cli.nhq_root / "github.com/wkentaro/labelme%2Fservices%2Fapi"
    assert store.is_dir()
    link = Path(subdir) / "nhq"
    assert link.is_symlink()
    assert link.readlink() == store
    assert "/services/api/nhq" in exclude_lines(git_repo)


def test_init_reports_link_conflict_but_keeps_store(
    cli: NhqCLI, git_repo: GitRepo
) -> None:
    (Path(git_repo.path) / "nhq").symlink_to("/somewhere/else")

    result = cli.run("init")

    assert result.returncode == 1
    assert "already links to" in result.stderr
    assert "created store" in result.stderr  # store created before the link failed
    assert (cli.nhq_root / "github.com/wkentaro/labelme").is_dir()


def test_init_root_uses_git_config_when_no_env(
    cli: NhqCLI, git_repo: GitRepo, tmp_path: Path
) -> None:
    config_root = tmp_path / "config-root"
    git_repo.git("config", "nhq.root", str(config_root))
    cli.pass_env_root = False  # leaves NHQ_ROOT unset so git config wins

    cli.run_ok("init")

    assert (config_root / "github.com/wkentaro/labelme").is_dir()
