import contextlib
import os
import re
import shutil
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
from ._git import get_toplevel
from ._git import is_excluded
from ._git import is_git_repo
from ._git import is_tracked
from ._git import list_others
from ._git import remove_excluded
from ._store import add_to_manifest
from ._store import parse_remote_url
from ._store import read_manifest
from ._store import resolve_root
from ._store import store_path
from ._store import to_managed_path


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
    env_root = os.environ.get("IHQ_ROOT")
    config_root = None if env_root else get_config("ihq.root")
    return resolve_root(env_root=env_root, config_root=config_root)


def _resolve_identity() -> str:
    if not is_git_repo():
        raise CliError("not a git repository")

    origin = get_origin_url()
    if origin is None:
        raise CliError(
            "ihq requires an 'origin' remote",
            tip="add one with: git remote add origin <url>",
        )
    try:
        return parse_remote_url(origin)
    except ValueError as exc:
        raise CliError(str(exc)) from exc


def _resolve_store() -> Path:
    return store_path(root=_resolve_root(), identity=_resolve_identity())


def _resolve_managed(arg: str, toplevel: Path) -> str:
    try:
        return to_managed_path(arg=arg, toplevel=toplevel, cwd=Path.cwd())
    except ValueError as exc:
        raise CliError(str(exc)) from exc


def _overlaps(path: str, other: str) -> bool:
    return path == other or path.startswith(other + "/") or other.startswith(path + "/")


def _exclude_line(managed: str) -> str:
    # Escape gitignore metacharacters so the literal path is matched: an
    # unescaped '*', '?', '[' or '\' would make git read the line as a glob and
    # fail to exclude the symlink, leaking it into `git status`.
    escaped = re.sub(r"([\\*?\[])", r"\\\1", managed)
    return "/" + escaped


def _link_one(store: Path, managed: str, toplevel: Path) -> None:
    slot = store / managed
    link = toplevel / managed
    try:
        if link.is_symlink():
            current = link.readlink()
            if current != slot.absolute():
                raise CliError(
                    f"'{managed}' already links to {current}",
                    tip=f"remove {managed}, then re-run",
                )
            verb = "already linked"
        elif link.exists():
            raise CliError(
                f"'{managed}' exists and is not an ihq symlink",
                tip=f"remove {managed}, then re-run",
            )
        else:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(slot.absolute())
            verb = "linked"
        ensure_excluded(_exclude_line(managed))
    except OSError as exc:
        raise CliError(f"cannot link {managed}: {exc}") from exc

    print_status(verb, link, slot)


def _is_linked_here(store: Path, managed: str, toplevel: Path) -> bool:
    link = toplevel / managed
    return link.is_symlink() and link.readlink() == (store / managed).absolute()


def _unlink_one(store: Path, managed: str, toplevel: Path) -> None:
    slot = store / managed
    link = toplevel / managed
    if link.is_symlink():
        if link.readlink() != slot.absolute():
            raise CliError(
                f"'{managed}' links to {link.readlink()}, not this repo's store",
                tip=f"remove {managed} manually if you meant to",
            )
        remove_link = True
    elif link.exists():
        raise CliError(
            f"'{managed}' exists and is not an ihq symlink",
            tip=f"remove {managed} manually if you meant to",
        )
    else:
        remove_link = False

    # Scrub the exclude entry before removing the symlink: if it fails, the link
    # is still intact and the user can retry cleanly, rather than being left with
    # a removed symlink and a lingering exclude entry.
    exclude_line = _exclude_line(managed)
    try:
        scrubbed = remove_excluded(exclude_line)
    except OSError as exc:
        raise CliError(f"cannot unlink {managed}: {exc}") from exc

    if remove_link:
        try:
            link.unlink()
        except OSError as exc:
            # The symlink survives, so restore the exclude entry we just scrubbed
            # to keep it ignored and leave a clean state to retry from. Best-effort:
            # a restore failure must never mask the original error raised below.
            if scrubbed:
                with contextlib.suppress(Exception):
                    ensure_excluded(exclude_line)
            raise CliError(f"cannot unlink {managed}: {exc}") from exc

    verb = "unlinked" if remove_link or scrubbed else "nothing to unlink"
    print_status(verb, link)


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


@cli.command("migrate", add_help_option=False)
@click.argument("path", required=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_migrate(path: str | None, show_help: bool) -> None:
    if show_help or path is None:
        print_help(HELP_MIGRATE)
        return
    store = _resolve_store()
    toplevel = get_toplevel()
    managed = _resolve_managed(path, toplevel)

    for other in read_manifest(store):
        if _overlaps(managed, other):
            raise CliError(f"'{managed}' overlaps already-managed '{other}'")

    source = toplevel / managed
    if source.is_symlink():
        raise CliError(f"'{managed}' is a symlink, not content to migrate")
    if not source.exists():
        raise CliError(f"nothing to migrate at '{managed}'")
    if is_tracked(source):
        raise CliError(
            f"'{managed}' is tracked by git",
            tip=f"externalizing it would change a committed file; run "
            f"'git rm --cached {managed}' first if you really mean to",
        )

    slot = store / managed
    if slot.exists():
        raise CliError(
            f"'{managed}' is already in the store",
            tip="attach it instead with: ihq link",
        )

    try:
        slot.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(slot))
    except OSError as exc:
        raise CliError(f"cannot migrate {managed}: {exc}") from exc
    add_to_manifest(store, managed)
    _link_one(store, managed, toplevel)


@cli.command("migratable", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_migratable(show_help: bool) -> None:
    if show_help:
        print_help(HELP_MIGRATABLE)
        return
    store = _resolve_store()
    toplevel = get_toplevel()
    managed_paths = read_manifest(store)

    # A directory whose contents are all ignored (e.g. by a nested .gitignore) but
    # which is not itself ignored appears in both passes: the ignored pass collapses
    # it to 'dir/', and the untracked pass also emits 'dir/' since the directory
    # itself is untracked-not-ignored. The untracked '?' is the right mark, so it
    # must win; apply it last.
    mark_by_path = {path: " " for path in list_others(toplevel, ignored=True)}
    for path in list_others(toplevel, ignored=False):
        mark_by_path[path] = "?"

    # That same ignored pass also lists the directory's ignored contents
    # individually. Migrating the directory covers them, so keep the directory and
    # drop the entries nested under it.
    listed_dirs = [path for path in mark_by_path if path.endswith("/")]

    for path in sorted(mark_by_path):
        # --directory appends a trailing slash to directories; managed paths carry
        # none, so strip it before testing overlap.
        if any(_overlaps(path.rstrip("/"), managed) for managed in managed_paths):
            continue
        if any(path != parent and path.startswith(parent) for parent in listed_dirs):
            continue
        click.echo(f"{mark_by_path[path]} {path}")


@cli.command("link", add_help_option=False)
@click.argument("path", required=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_link(path: str | None, show_help: bool) -> None:
    if show_help:
        print_help(HELP_LINK)
        return
    store = _resolve_store()
    toplevel = get_toplevel()

    if path is None:
        for managed in read_manifest(store):
            if (store / managed).exists():
                _link_one(store, managed, toplevel)
        return

    managed = _resolve_managed(path, toplevel)
    if not (store / managed).exists():
        raise CliError(
            f"nothing in the store for '{managed}'",
            tip="create it with: ihq migrate",
        )
    _link_one(store, managed, toplevel)


@cli.command("unlink", add_help_option=False)
@click.argument("path", required=False)
@click.option("--all", "unlink_all", is_flag=True)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_unlink(path: str | None, unlink_all: bool, show_help: bool) -> None:
    if show_help:
        print_help(HELP_UNLINK)
        return
    if path is not None and unlink_all:
        raise CliError("give a path or --all, not both")
    if path is None and not unlink_all:
        raise CliError("specify a path or --all", usage=USAGE_UNLINK)

    store = _resolve_store()
    toplevel = get_toplevel()

    if unlink_all:
        for managed in read_manifest(store):
            link = toplevel / managed
            lingering = (
                not link.exists()
                and not link.is_symlink()
                and is_excluded(_exclude_line(managed))
            )
            if _is_linked_here(store, managed, toplevel) or lingering:
                _unlink_one(store, managed, toplevel)
        return

    assert path is not None
    _unlink_one(store, _resolve_managed(path, toplevel), toplevel)


@cli.command("list", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_list(show_help: bool) -> None:
    if show_help:
        print_help(HELP_LIST)
        return
    store = _resolve_store()
    toplevel = get_toplevel()
    managed_paths = read_manifest(store)
    if not managed_paths:
        return
    width = max(len(managed) for managed in managed_paths)
    for managed in managed_paths:
        slot = store / managed
        if not slot.exists():
            mark = "!"
        elif _is_linked_here(store, managed, toplevel):
            mark = "*"
        else:
            mark = " "
        click.echo(f"{mark} {managed:<{width}} {slot}")


@cli.command("root", add_help_option=False)
@click.option("-h", "--help", "show_help", is_flag=True)
def cmd_root(show_help: bool) -> None:
    if show_help:
        print_help(HELP_ROOT)
        return
    click.echo(str(_resolve_root()))


def _out() -> Console:
    return Console(highlight=False)


def _err() -> Console:
    return Console(stderr=True, highlight=False)


def print_help(text: str) -> None:
    _out().print(text)


def print_version(version: str) -> None:
    _out().print(f"ihq [dim]{version}[/dim]")


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
    "[bold green]Usage:[/bold green] [bold cyan]ihq[/bold cyan] [cyan]<COMMAND>[/cyan]"
)

USAGE_UNLINK: Final = (
    "[bold green]Usage:[/bold green] [bold cyan]ihq unlink[/bold cyan] "
    "[cyan]<PATH>[/cyan] | [cyan]--all[/cyan]"
)

EXAMPLES_MIGRATE: Final = [
    ("ihq migrate scratch", "Externalize an existing ./scratch"),
    ("touch .env && ihq migrate .env", "Create a fresh file, then externalize"),
    ("mkdir notes && ihq migrate notes", "Create a fresh directory, then externalize"),
]
EXAMPLES_MIGRATABLE: Final = [("ihq migratable", "List paths you could externalize")]
EXAMPLES_LINK: Final = [("ihq link", "Link all the store has (2nd machine)")]
EXAMPLES_UNLINK: Final = [("ihq unlink scratch", "Drop one link on this checkout")]
EXAMPLES_LIST: Final = [("ihq list", "Show this repo's managed paths")]
EXAMPLES_ROOT: Final = [("ihq root", "Print the resolved root directory")]


def render_examples(examples: list[tuple[str, str]]) -> str:
    width = max(len(command) for command, _ in examples)
    return "\n".join(
        f"  [cyan]{command}[/cyan]{' ' * (width - len(command) + 2)}[dim]# {note}[/dim]"
        for command, note in examples
    )


ALL_EXAMPLES: Final = (
    render_examples(EXAMPLES_MIGRATE)
    + "\n\n"
    + render_examples(
        EXAMPLES_MIGRATABLE
        + EXAMPLES_LINK
        + EXAMPLES_UNLINK
        + EXAMPLES_LIST
        + EXAMPLES_ROOT
    )
)

HELP: Final = f"""\
Externalize git-ignored files and directories to a synced, identity-derived
store, kept out of git.

{USAGE}

[bold green]Commands:[/bold green]
  [bold cyan]migrate[/bold cyan]     Move a path into the store and link it
  [bold cyan]migratable[/bold cyan]  List paths eligible for migrate
  [bold cyan]link[/bold cyan]        Link a path the store already has (per checkout)
  [bold cyan]unlink[/bold cyan]      Remove a link and its exclude entry
  [bold cyan]list[/bold cyan]        List this repo's managed paths and their status
  [bold cyan]root[/bold cyan]        Print the resolved root directory

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]     Print help
  [bold cyan]-V[/bold cyan], [bold cyan]--version[/bold cyan]  Print version

[bold green]Examples:[/bold green]
{ALL_EXAMPLES}"""

ROOT_RESOLUTION: Final = """\
[bold green]Root resolution:[/bold green]
  [cyan]IHQ_ROOT[/cyan] env -> [cyan]git config ihq.root[/cyan] -> [cyan]~/ihq[/cyan]"""

HELP_MIGRATE: Final = f"""\
Move an existing working-tree path into this repo's store (path derived from the
origin remote, ghq-style), leave an ihq symlink behind, add it to
.git/info/exclude, and record it in the manifest. The path must exist and must
not be tracked by git. To externalize fresh content, create it first with mkdir
or touch, then migrate it. This is the only verb that creates store content.

[bold green]Usage:[/bold green] [bold cyan]ihq migrate[/bold cyan] [cyan]<PATH>[/cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Examples:[/bold green]
{render_examples(EXAMPLES_MIGRATE)}

{ROOT_RESOLUTION}"""

HELP_MIGRATABLE: Final = f"""\
List every path you could externalize with migrate: working-tree paths that are
not tracked by git and not already managed, one per line, identically wherever in
the repo you run it. A wholly-ignored directory is collapsed to a single entry.
Each line is marked: [bold cyan] [/bold cyan] git-ignored,
[bold cyan]?[/bold cyan] untracked but not ignored (likely headed for a commit,
so check before you migrate it). Read-only: creates and links nothing.

[bold green]Usage:[/bold green] [bold cyan]ihq migratable[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Examples:[/bold green]
{render_examples(EXAMPLES_MIGRATABLE)}

{ROOT_RESOLUTION}"""

HELP_LINK: Final = f"""\
Link a path the store already has into this checkout and add it to
.git/info/exclude so git ignores it. With no PATH, link every managed path the
store has that is not yet linked here (the second-machine flow). Per checkout and
per machine; never creates store content (use migrate for that).

[bold green]Usage:[/bold green] [bold cyan]ihq link[/bold cyan] [cyan][PATH][/cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Examples:[/bold green]
{render_examples(EXAMPLES_LINK)}

{ROOT_RESOLUTION}"""

HELP_UNLINK: Final = f"""\
Remove an ihq symlink on this checkout and scrub its .git/info/exclude entry, the
inverse of ihq link. With --all, do this for every managed path linked here.
Link-only: it never touches the store or the manifest, and only removes a symlink
that points at this repo's store.

{USAGE_UNLINK}

[bold green]Options:[/bold green]
      [bold cyan]--all[/bold cyan]   Unlink every managed path on this checkout
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Examples:[/bold green]
{render_examples(EXAMPLES_UNLINK)}

{ROOT_RESOLUTION}"""

HELP_LIST: Final = f"""\
List every managed path for this repo (from the manifest), one per line,
identically wherever in the repo you run it. Each line is marked with its status
on this checkout: [bold cyan]*[/bold cyan] linked here, [bold cyan] [/bold cyan]
in the store but not linked here, [bold cyan]![/bold cyan] missing from the
store. Read-only: creates and links nothing.

[bold green]Usage:[/bold green] [bold cyan]ihq list[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Examples:[/bold green]
{render_examples(EXAMPLES_LIST)}

{ROOT_RESOLUTION}"""

HELP_ROOT: Final = f"""\
Print the resolved root directory, the base under which every store lives. Use
it to locate or cd into your stores. Works anywhere; a git repo is not required.

[bold green]Usage:[/bold green] [bold cyan]ihq root[/bold cyan]

[bold green]Options:[/bold green]
  [bold cyan]-h[/bold cyan], [bold cyan]--help[/bold cyan]  Print help

[bold green]Examples:[/bold green]
{render_examples(EXAMPLES_ROOT)}

{ROOT_RESOLUTION}"""
