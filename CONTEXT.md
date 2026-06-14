# ihq

`ihq` ("ignored headquarters") keeps gitignored files and directories alongside
a git repo without ever committing them. For each externalized path in a
checkout it manages a symlink to a store that lives outside git, in a folder the
user already syncs. The layout is modeled on `ghq`: a configurable root, with a
fixed `host/user/repo` layout derived beneath it, and each externalized path
mirrored at its repo-relative location inside. Private notes are the motivating
case, not the limit.

## Language

**Store**:
The per-repo directory under the root, outside git, shared across all of a
user's machines, that holds every externalized path for one repo at its own
repo-relative location (a mirror tree). The "headquarters" of the model.
_Avoid_: notes folder, backup dir.

**Managed path**:
A repo-root-relative path that has been externalized into the store and recorded
in the manifest. The unit every ihq verb operates on. It is identical on every
machine because it is repo-relative, not tied to where the repo is checked out.
_Avoid_: file, entry, target.

**Migratable**:
An unmanaged, untracked working-tree path that `migrate` would accept: it
exists, is not git-tracked, is not an `ihq` link, and is not already a managed
path. The candidate set the `migratable` command lists.
_Avoid_: candidate, untracked file.

**Link**:
An `ihq` symlink inside a checkout that points at a managed path's slot in the
store. Per-checkout and per-machine, never committed (it lives only in the
working tree and is hidden via `.git/info/exclude`). A repo can have many.
_Avoid_: alias, shortcut.

**Manifest**:
The record, kept in the store as the reserved file `.ihq`, of every managed path
for the repo. Canonical and machine-shared (it syncs with the store), so any
checkout knows the full set to link. Written only by `migrate`; `link` and
`unlink` never touch it.
_Avoid_: index, database, lockfile.

**Root**:
The configurable base directory under which every store lives (resolved from
`IHQ_ROOT`, then `git config ihq.root`, then the default `~/ihq`). Points at a
folder some other tool already syncs; `ihq` itself never syncs.
_Avoid_: base, home, IHQ_ROOT (that is the env var, not the concept).
