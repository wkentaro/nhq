import os
from pathlib import Path
from typing import Final

import click
from rich.console import Console
from rich.text import Text
from typing_extensions import override

from . import __version__
from ._git import GitError
from ._git import ensure_excluded
from ._git import get_config
from ._git import get_origin_url
from ._git import get_show_prefix
from ._git import is_git_repo
from ._store import list_stores
from ._store import parse_remote_url
from ._store import resolve_root
from ._store import store_path


class CliError(Exception):
    def __init__(
        self,
        message: str,
        *,
        tip: str | None = None,
        usage: str | None = None,
    ) -> None:
        super().__init__(message)
        self.tip = tip
        self.usage = usage


class CliGroup(click.Group):
    @override
    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            cmd_name = args[0] if args else ""
            raise CliError(
                f"unrecognized subcommand '{cmd_name}'", usage=USAGE
            ) from None

    @override
    def invoke(self, ctx: click.Context) -> None:
        try:
            super().invoke(ctx)
        except CliError as exc:
            print_error(str(exc), tip=exc.tip, usage=exc.usage)
            ctx.exit(2 if exc.usage else 1)
        except GitError as exc:
            print_error(str(exc))
            ctx.exit(1)
        except FileNotFoundError:
            print_error(
                "git not found",
                tip="install git and ensure it is on your PATH",
            )
            ctx.exit(1)
        except KeyboardInterrupt:
            ctx.exit(130)


def _resolve_root() -> Path:
    env_root = os.environ.get("NHQ_ROOT")
    config_root = None if env_root else get_config("nhq.root")
    return resolve_root(env_root=env_root, config_root=config_root)


def _resolve_identity() -> str:
    if not is_git_repo():
        raise CliError("not a git repository")

    origin = get_origin_url()
    if origin is None:
        raise CliError(
            "nhq requires an 'origin' remote",
            tip="add one with: git remote add origin <url>",
        )
    try:
        return parse_remote_url(origin)
    except ValueError as exc:
        raise CliError(str(exc)) from exc


def _resolve_store() -> tuple[Path, str]:
    identity = _resolve_identity()
    show_prefix = get_show_prefix()
    store = store_path(root=_resolve_root(), identity=identity, subpath=show_prefix)
    return store, show_prefix


def _link_store(store: Path, show_prefix: str) -> None:
    link = Path("nhq")
    try:
        if link.is_symlink():
            current = link.readlink()
            if current != store.absolute():
                raise CliError(
                    f"'./nhq' already links to {current}",
                    tip="remove ./nhq, then re-run",
                )
            verb = "already linked"
        elif link.exists():
            raise CliError(
                "'./nhq' exists and is not an nhq symlink",
                tip="remove ./nhq, then re-run",
            )
        else:
            link.symlink_to(store.absolute())
            verb = "linked"
        ensure_excluded("/" + show_prefix + "nhq")
    except OSError as exc:
        raise CliError(f"cannot link ./nhq: {exc}") from exc

    print_status(verb, link.absolute(), store)


@click.group(cls=CliGroup, invoke_without_command=True, add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
@click.option("-V", "--version", "show_version", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, show_help: bool, show_version: bool) -> None:
    if show_version:
        print_version(__version__)
        return
    if show_help or ctx.invoked_subcommand is None:
        print_help(HELP)


@cli.command("init", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_init(show_help: bool) -> None:
    if show_help:
        print_help(HELP_INIT)
        return
    store, show_prefix = _resolve_store()
    existed = store.exists()
    try:
        store.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CliError(f"cannot create store: {exc}") from exc
    print_status("store exists" if existed else "created store", store)
    _link_store(store, show_prefix)


@cli.command("link", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_link(show_help: bool) -> None:
    if show_help:
        print_help(HELP_LINK)
        return
    store, show_prefix = _resolve_store()
    if not store.exists():
        raise CliError(
            "no store for this repo",
            tip="create it first with: nhq init",
        )
    _link_store(store, show_prefix)


@cli.command("root", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_root(show_help: bool) -> None:
    if show_help:
        print_help(HELP_ROOT)
        return
    click.echo(str(_resolve_root()))


@cli.command("path", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_path(show_help: bool) -> None:
    if show_help:
        print_help(HELP_PATH)
        return
    store, _ = _resolve_store()
    click.echo(str(store))


@cli.command("list", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_list(show_help: bool) -> None:
    if show_help:
        print_help(HELP_LIST)
        return
    identity = _resolve_identity()
    root = _resolve_root()
    current = store_path(root=root, identity=identity, subpath=get_show_prefix())
    stores = list_stores(root=root, identity=identity)
    if not stores:
        return
    rows = [("." if subpath == "" else subpath + "/", path) for subpath, path in stores]
    width = max(len(label) for label, _ in rows)
    for label, path in rows:
        mark = "*" if path == current else " "
        click.echo(f"{mark} {label:<{width}} {path}")


def _err() -> Console:
    return Console(stderr=True, highlight=False)


def print_help(text: str) -> None:
    _err().print(text)


def print_version(version: str) -> None:
    _err().print(f"nhq [dim]{version}[/dim]")


def print_status(verb: str, path: Path, target: Path | None = None) -> None:
    line = Text()
    line.append(f"{verb} ", style="bold green")
    line.append(str(path), style="cyan")
    if target is not None:
        line.append(" -> ", style="dim")
        line.append(str(target), style="cyan")
    _err().print(line)


def print_error(
    msg: str,
    *,
    tip: str | None = None,
    usage: str | None = None,
) -> None:
    err = _err()
    err.print(f"[bold red]error[/bold red]: {msg}")
    if tip:
        err.print(f"\n  [green]tip[/green]: {tip}")
    if usage:
        err.print(f"\n{usage}")
        err.print("\nFor more information, try '[bold cyan]--help[/bold cyan]'.")


USAGE: Final = (
    "[bold green]Usage:[/bold green] [bold cyan]nhq[/bold cyan] [cyan]<COMMAND>[/cyan]"
)

HELP: Final = f"""\
Private per-repo notes alongside a git repo, kept out of git.

{USAGE}

[bold green]Commands:[/bold green]
  [bold cyan]init[/bold cyan]  Create this repo's store and link it (run once)
  [bold cyan]link[/bold cyan]  Link ./nhq to an existing store (per checkout)
  [bold cyan]root[/bold cyan]  Print the resolved root directory
  [bold cyan]path[/bold cyan]  Print this repo's store path
  [bold cyan]list[/bold cyan]  List this repo's stores (root and subtrees)

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]     Print help
  [bold cyan]-V[/bold cyan], [bold cyan]--version[/bold cyan]  Print version

[bold green]Examples:[/bold green]
  [cyan]nhq init[/cyan]  [dim]# Set up the store and link ./nhq (first machine)[/dim]
  [cyan]nhq link[/cyan]  [dim]# Link ./nhq on another machine or checkout[/dim]"""

ROOT_RESOLUTION: Final = """\
[bold green]Root resolution:[/bold green]
  [cyan]NHQ_ROOT[/cyan] env -> [cyan]git config nhq.root[/cyan] -> [cyan]~/nhq[/cyan]"""

HELP_INIT: Final = f"""\
Create this repo's store under the resolved root (path derived from the origin
remote, ghq-style) and link ./nhq to it. Idempotent. Run this once, on the
machine where you first start; on other machines use nhq link.

[bold green]Usage:[/bold green] [bold cyan]nhq init[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

{ROOT_RESOLUTION}"""

HELP_LINK: Final = f"""\
Link ./nhq in the current directory to this repo's store and add it to
.git/info/exclude so git ignores it. Per checkout and per machine; the link
is never committed. Requires the store to exist (run nhq init first).

[bold green]Usage:[/bold green] [bold cyan]nhq link[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

{ROOT_RESOLUTION}"""

HELP_ROOT: Final = f"""\
Print the resolved root directory, the base under which every store lives. Use
it to locate or cd into your stores. Works anywhere; a git repo is not required.

[bold green]Usage:[/bold green] [bold cyan]nhq root[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

{ROOT_RESOLUTION}"""

HELP_PATH: Final = f"""\
Print this repo's store path, derived from the origin remote (ghq-style) and the
subdirectory you run it in. Does not create or link anything; use it to locate or
cd into the store. Requires a git repo with an origin remote.

[bold green]Usage:[/bold green] [bold cyan]nhq path[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

{ROOT_RESOLUTION}"""

HELP_LIST: Final = f"""\
List every existing store for this repo, the root store plus any subtree stores,
one per line, identically wherever in the repo you run it. Each line shows the
decoded subpath (. for the repo root) and the store path; the store for the
current directory is marked with *. Read-only: creates and links nothing.
Requires a git repo with an origin remote.

[bold green]Usage:[/bold green] [bold cyan]nhq list[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

{ROOT_RESOLUTION}"""
