import os
from pathlib import Path
from typing import Final

import click
from rich.console import Console
from rich.text import Text
from typing_extensions import override

from . import __version__
from ._git import ensure_excluded
from ._git import get_config
from ._git import get_origin_url
from ._git import get_show_prefix
from ._git import is_git_repo
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
        except KeyboardInterrupt:
            ctx.exit(130)


def _resolve_store() -> Path:
    if not is_git_repo():
        raise CliError("not a git repository")

    origin = get_origin_url()
    if origin is None:
        raise CliError(
            "nhq requires an 'origin' remote",
            tip="add one with: git remote add origin <url>",
        )
    try:
        identity = parse_remote_url(origin)
    except ValueError as exc:
        raise CliError(str(exc)) from exc

    root = resolve_root(
        env_root=os.environ.get("NHQ_ROOT"),
        config_root=get_config("nhq.root"),
    )
    return store_path(root=root, identity=identity, subpath=get_show_prefix())


def _link_store(store: Path) -> None:
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
        ensure_excluded("/" + get_show_prefix() + "nhq")
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
    store = _resolve_store()
    existed = store.exists()
    try:
        store.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CliError(f"cannot create store: {exc}") from exc
    print_status("store exists" if existed else "created store", store)
    _link_store(store)


@cli.command("link", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_link(show_help: bool) -> None:
    if show_help:
        print_help(HELP_LINK)
        return
    store = _resolve_store()
    if not store.exists():
        raise CliError(
            "no store for this repo",
            tip="create it first with: nhq init",
        )
    _link_store(store)


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

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]     Print help
  [bold cyan]-V[/bold cyan], [bold cyan]--version[/bold cyan]  Print version

[bold green]Examples:[/bold green]
  [cyan]nhq init[/cyan]  [dim]# Set up the store and link ./nhq (first machine)[/dim]
  [cyan]nhq link[/cyan]  [dim]# Link ./nhq on another machine or checkout[/dim]"""

HELP_INIT: Final = """\
Create this repo's store under the resolved root (path derived from the origin
remote, ghq-style) and link ./nhq to it. Idempotent. Run this once, on the
machine where you first start; on other machines use nhq link.

[bold green]Usage:[/bold green] [bold cyan]nhq init[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Root resolution:[/bold green]
  [cyan]NHQ_ROOT[/cyan] env -> [cyan]git config nhq.root[/cyan] -> [cyan]~/nhq[/cyan]"""

HELP_LINK: Final = """\
Link ./nhq in the current directory to this repo's store and add it to
.git/info/exclude so git ignores it. Per checkout and per machine; the link
is never committed. Requires the store to exist (run nhq init first).

[bold green]Usage:[/bold green] [bold cyan]nhq link[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Root resolution:[/bold green]
  [cyan]NHQ_ROOT[/cyan] env -> [cyan]git config nhq.root[/cyan] -> [cyan]~/nhq[/cyan]"""
