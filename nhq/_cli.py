import os
from pathlib import Path
from typing import Final

import click
from rich.console import Console
from rich.text import Text
from typing_extensions import override

from . import __version__
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


def _err() -> Console:
    return Console(stderr=True, highlight=False)


def print_help(text: str) -> None:
    _err().print(text)


def print_version(version: str) -> None:
    _err().print(f"nhq [dim]{version}[/dim]")


def print_status(verb: str, path: Path) -> None:
    line = Text()
    line.append(f"{verb} ", style="bold green")
    line.append(str(path), style="cyan")
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
  [bold cyan]init[/bold cyan]  Create the notes store for this repo (run once)

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]     Print help
  [bold cyan]-V[/bold cyan], [bold cyan]--version[/bold cyan]  Print version

[bold green]Examples:[/bold green]
  [cyan]nhq init[/cyan]  [dim]# Create this repo's notes store under $NHQ_ROOT[/dim]"""

HELP_INIT: Final = """\
Create the notes store for this repo under the resolved root, deriving its
path from the origin remote (ghq-style host/user/repo). Idempotent. The store
is shared across machines via whatever syncs the root; run this once.

[bold green]Usage:[/bold green] [bold cyan]nhq init[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Root resolution:[/bold green]
  [cyan]NHQ_ROOT[/cyan] env -> [cyan]git config nhq.root[/cyan] -> [cyan]~/nhq[/cyan]"""
