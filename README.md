# ihq

[![PyPI](https://img.shields.io/pypi/v/ihq.svg)](https://pypi.org/project/ihq/)
[![Python](https://img.shields.io/pypi/pyversions/ihq.svg)](https://pypi.org/project/ihq/)
[![Build](https://github.com/wkentaro/ihq/actions/workflows/test.yml/badge.svg)](https://github.com/wkentaro/ihq/actions/workflows/test.yml)
[![License](https://img.shields.io/pypi/l/ihq.svg)](https://pypi.org/project/ihq/)

ghq for the files git shouldn't see: externalize any git-ignored path to storage
you already sync, never to git. A capture tool, not a config-distribution tool.

`ihq` ("ignored headquarters") moves git-ignored files and directories out of a
checkout into a store kept outside git, leaving a symlink behind. While working
in a repo (often with an AI agent) you accumulate notes, scratch, `.env` files,
and artifacts you want beside the code but never committed, not for the team and
not on GitHub. `ihq` keeps them in a store whose path is derived from the repo's
identity, the same way [ghq](https://github.com/x-motemen/ghq) derives a checkout
path from a remote URL.

## How it works

Two planes:

- **The store** is `$IHQ_ROOT/<host>/<user>/<repo>/`: a mirror tree holding your
  externalized paths, each at its own repo-relative location. Lives in your
  synced folder, shared across machines. A `.ihq` manifest at its root records
  the managed set.
- **The links** are the `ihq` symlinks plus their `.git/info/exclude` entries.
  Per-checkout and per-machine, never committed.

`ihq migrate` externalizes a path on the first machine; `ihq link` re-attaches it
on every other.

`ihq` does not sync. Point the root at a folder something already syncs (Dropbox,
iCloud, Syncthing, a NAS mount) and backup comes for free.

## Install

```bash
pip install ihq
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ihq
```

Requires POSIX (macOS, Linux); it relies on symlinks.

## Usage

### Externalize a path

`ihq migrate <path>` moves an existing file or directory into the store and drops
a symlink in its place, added to `.git/info/exclude` so git never sees it:

```console
$ echo "scratch notes" > scratch.md
$ ihq migrate scratch.md
linked /home/you/code/labelme/scratch.md -> /home/you/ihq/github.com/wkentaro/labelme/scratch.md
```

The path keeps working in place; its bytes now live in your synced store. Nested
paths work too (`ihq migrate backend/.env`). The path must not be tracked by git:
externalizing a committed file would change it for the whole team, so `ihq`
refuses.

`migrate` only moves content that already exists. To start something fresh,
create it first, then migrate:

```console
$ mkdir notes && ihq migrate notes
```

### Link on another machine

The store syncs over, so other checkouts just re-attach. `ihq link` with no
argument links every path the store has but this checkout does not:

```console
$ ihq link
linked /home/you/code/labelme/scratch.md -> /home/you/ihq/github.com/wkentaro/labelme/scratch.md
linked /home/you/code/labelme/notes -> /home/you/ihq/github.com/wkentaro/labelme/notes
```

Or link one path: `ihq link scratch.md`. `link` never creates store content; if
the store does not have the path it errors (run `ihq migrate` first). This is the
guard that catches a typo'd remote or an un-synced store instead of producing
junk.

### Unlink

`ihq unlink <path>` removes one symlink and its exclude entry; `ihq unlink --all`
does every path on this checkout. It never touches the store or the manifest, so
your content stays safe in the synced root:

```console
$ ihq unlink scratch.md
unlinked /home/you/code/labelme/scratch.md
```

### List

`ihq list` shows every managed path for this repo and its status on this
checkout, the same wherever in the repo you run it. `*` is linked here, a space
is in the store but not linked here, `!` is missing from the store. Read-only:

```console
$ ihq list
* scratch.md   /home/you/ihq/github.com/wkentaro/labelme/scratch.md
  backend/.env /home/you/ihq/github.com/wkentaro/labelme/backend/.env
```

### Root resolution

The root is resolved like ghq, in order:

```
IHQ_ROOT env  ->  git config ihq.root  ->  ~/ihq
```

`ihq root` prints it, the same way `ghq root` does. It needs no repo, so it works
anywhere:

```console
$ ihq root
/home/you/ihq

$ cd "$(ihq root)"
```

## vs repoverlay

[repoverlay](https://github.com/tylerbutler/repoverlay) uses the same mechanism
(a symlink plus `.git/info/exclude`) but the opposite data model. It distributes
one shared bundle of files into many repos; `ihq` captures each repo's own unique
git-ignored paths out to a synced store.

- **Capture, not distribute**: content flows out of the repo, not config in.
- **Zero config**: the store path is derived from repo identity, not named.
- **Few verbs**: `migrate`, `link`, and `unlink` are all that change anything; `root` and `list` only print.

## Scope

`ihq` manages links and the derived store; it never syncs, clones, or touches the
network. Backup is delegated entirely to whatever already syncs your root.

## License

MIT. Modeled on and crediting [ghq](https://github.com/x-motemen/ghq).
