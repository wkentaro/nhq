# A manifest in the store records the managed set

Every managed path for a repo is recorded in a manifest: the reserved file
`.ihq` at the store root, holding one repo-root-relative path per line, sorted.
It is written **only by `migrate`** (the verb that creates store content);
`link` and `unlink` never touch it. Because it lives in the store, it syncs
across machines, so any checkout knows the full set of paths to link. `migrate`
refuses to externalize a repo path that would map onto the reserved `.ihq` name.

## Why

The original tool deliberately kept **no recorded state**: with exactly one
derived link, "what is linked here" was fully derivable from the `./ihq` symlink
plus its exclude line. Supporting arbitrary *nested* managed paths breaks that.
Walking the store cannot tell whether `backend` is the managed unit or
`backend/.env` is, so the set of managed paths must be recorded explicitly. It
must also live where it syncs (the store), so a second machine can re-link
without being told each path.

A plain sorted path list, not TOML or JSON, is chosen because the path *is* the
whole record: store presence and per-checkout link state are both derivable, so
there is no per-entry metadata to carry. It diffs and merges cleanly across
sync, like `.git/info/exclude` itself. If metadata is ever needed, the format is
migrated then, not pre-built now.

## Consequence

The manifest is append-only in normal use: only `migrate` adds, and reversing a
migrate is out of scope. A store slot deleted by hand leaves a dangling manifest
entry, which `ihq list` flags as "missing from store" rather than auto-pruning.
A reader expecting the old zero-state design will find one small synced file;
that is the price of arbitrary nested paths.
