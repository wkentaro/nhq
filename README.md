# nhq

[![PyPI](https://img.shields.io/pypi/v/nhq.svg)](https://pypi.org/project/nhq/)
[![Python](https://img.shields.io/pypi/pyversions/nhq.svg)](https://pypi.org/project/nhq/)
[![Build](https://github.com/wkentaro/nhq/actions/workflows/test.yml/badge.svg)](https://github.com/wkentaro/nhq/actions/workflows/test.yml)
[![License](https://img.shields.io/pypi/l/nhq.svg)](https://pypi.org/project/nhq/)

ghq for your private per-repo notes: every repo gets a private folder that lives
in storage you already sync, never in git. A capture tool, not a
config-distribution tool.

`nhq` ("notes headquarters") manages a deterministic symlink from inside a git
repo to a notes directory kept outside git. While working in a repo (often with
an AI agent) you accumulate notes, scratch, and artifacts you want beside the
code but never committed, not for the team and not on GitHub. `nhq` keeps them
in a store whose path is derived from the repo's identity, the same way
[ghq](https://github.com/x-motemen/ghq) derives a checkout path from a remote
URL.

## How it works

Two planes:

- **The store** is `$NHQ_ROOT/<host>/<user>/<repo>/`: the actual notes. Created
  once, lives in your synced folder, shared across machines.
- **The link** is the `./nhq` symlink plus a `.git/info/exclude` entry.
  Per-checkout and per-machine, never committed.

`nhq init` sets up both on the first machine; `nhq link` connects the link plane
on every other machine.

`nhq` does not sync. Point the root at a folder something already syncs (Dropbox,
iCloud, Syncthing, a NAS mount) and backup comes for free.

## Install

```bash
pip install nhq
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install nhq
```

Verify it works:

```bash
nhq --help
```

Requires POSIX (macOS, Linux); it relies on symlinks.

## Usage

On the first machine, one command sets everything up. `nhq init` creates the
store and drops a `./nhq` symlink into your working tree, added to
`.git/info/exclude` so git never sees it:

```console
$ nhq init
created store /home/you/nhq/github.com/wkentaro/labelme
linked /home/you/code/labelme/nhq -> /home/you/nhq/github.com/wkentaro/labelme

$ ls -l nhq
nhq -> /home/you/nhq/github.com/wkentaro/labelme
```

Now write notes into `./nhq/`. They live in your synced storage and never touch
git.

On any other machine or checkout the store already exists (it synced over), so
just link to it:

```console
$ nhq link
linked /home/you/code/labelme/nhq -> /home/you/nhq/github.com/wkentaro/labelme
```

Your notes from the first machine are already under `./nhq/`, synced over.

Both commands also work from a subdirectory: a subtree gets its own separate
store, keyed by its path within the repo, so a monorepo subtree keeps its own
notes.

### Root resolution

The root is resolved like ghq, in order:

```
NHQ_ROOT env  ->  git config nhq.root  ->  ~/nhq
```

`nhq root` prints it, the same way `ghq root` does. It needs no repo, so it
works anywhere:

```console
$ nhq root
/home/you/nhq

$ cd "$(nhq root)"
```

## vs repoverlay

[repoverlay](https://github.com/tylerbutler/repoverlay) uses the same mechanism
(a symlink plus `.git/info/exclude`) but the opposite data model. It distributes
one shared bundle of files into many repos; `nhq` captures each repo's own unique
notes out to a synced store.

- **Capture, not distribute**: notes flow out of the repo, not config in.
- **Zero config**: the store path is derived from repo identity, not named.
- **Two verbs**: `init` and `link`, nothing else.

## Scope

v1 manages the link and the derived path; it never syncs, clones, or touches the
network. Backup is delegated entirely to whatever already syncs your root.

## License

MIT. Modeled on and crediting [ghq](https://github.com/x-motemen/ghq).
