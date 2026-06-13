# Global store enumeration (`list --all`)

nhq does not support enumerating every store under the root from disk (the
proposed `nhq list --all`). Listing is scoped to the current repo (`nhq list`),
and `nhq root` is the entry point for browsing all stores by hand.

## Why this is out of scope

A rootwalk that discovers "every store" cannot be well-defined under the current
store layout. Two deliberate design choices collide:

- **ADR-0001**: a store's identity is `host/path` of *arbitrary depth* (2-level
  self-hosted remotes, 4-level GitLab subgroups).
- **ADR-0003**: stores hold *free-form notes at the store root with no marker
  file*, and flatten subtree stores as `%2F`-encoded siblings.

Together these make store directories structurally indistinguishable from
container directories (`host`, `user`) and from note subdirectories. A depth-3
dir could be a `host/user/repo` store or a subgroup container whose real store
sits at depth 4; a note subdir is shaped exactly like a subtree store. Scoped
`nhq list` sidesteps this entirely because it is handed the exact identity from
the origin remote and only ever inspects one known parent directory, decoding
`%2F` siblings of a known leaf. It never walks blind.

Making `--all` well-defined would require one of:

1. Fixing the layout at depth 3 (`host/user/repo`). Silently misreports any
   non-depth-3 store and contradicts ADR-0001's arbitrary depth.
2. A per-store marker file written by `nhq init`. Contradicts ADR-0003's
   no-marker property and changes the store contract.
3. A persistent store registry/index under the root. Adds mutable state that
   drifts from disk truth, undermining the "stores are just directories you
   sync" property the whole tool rests on.

None of these is worth it. nhq is deliberately repo-centric (ADR-0006: `list`
defaults to the current repo *because* nhq always has a current-repo context
that ghq lacks), so a global, repo-independent enumeration is not a core need.
`nhq root` already gives you the base path to cd into and browse.

## Prior requests

- #15 — "Add nhq list --all to enumerate every store under the root"
