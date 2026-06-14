# Rename `nhq` to `ihq`

The tool is renamed from `nhq` ("notes headquarters") to `ihq` ("ignored
headquarters"). The rename covers the PyPI package, the CLI command, the Python
module, the `IHQ_ROOT` env var, the `ihq.root` git config key, the default root
`~/ihq`, the reserved manifest file `.ihq`, and the GitHub repository.

## Why

The tool no longer manages only notes; it externalizes any git-ignored path
(ADR-0007). "Notes" named a single use case that the design outgrew. "Ignored
headquarters" names what the store actually holds — the repo's git-ignored
paths — which is both accurate and a closer homage to `ghq`, whose name also
describes *what* it stores (git repositories) rather than a purpose. The `-hq`
derived-from-identity layout that is the real homage is fully preserved.

## Why now

A rename is costly exactly once, and that cost only rises with adoption. The tool
is at 0.1.0, and the move to a mirror-tree store with a manifest (ADR-0007,
ADR-0008) is already a breaking store-layout change that forces a one-time
migration. Folding the rename into that single break means users migrate once.
`ihq` is unclaimed on PyPI.

## Considered and rejected

- **Keep `nhq`, broaden the tagline only.** Reinterpreting the "n" away from
  "notes" leaves a name that mismatches the tool, banking on a gloss to paper
  over it. The honest fix is to rename while it is still cheap.
- **A purpose-oriented name (capture, stash, and the like).** `ghq` names by
  *what* is stored; matching that convention keeps the homage legible.
  "Ignored" also precisely matches the mechanism: every managed path is
  git-ignored by construction (tracked paths are refused, ADR-0009).

This is hard to reverse: it is an outward-facing identity change across a
published package and repository.
