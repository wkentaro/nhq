# Store is a per-repo mirror tree of arbitrary managed paths

Supersedes ADR-0003 (subtree stores flattened, not nested).

The store for a repo is a single directory at the derived path
`<root>/<host>/<user>/<repo>/` (ADR-0001 unchanged). It is a **mirror tree**:
every externalized path lives inside it at the *same repo-root-relative
location* it has in the checkout. `./scratch` maps to `<store>/scratch`;
`./backend/.env` maps to `<store>/backend/.env`. A repo has one store holding
arbitrarily many managed paths, instead of one fixed `./ihq` symlink to the
whole store directory.

Managed paths are recorded **repo-root-relative**, never cwd-relative: running
`ihq migrate scratch` inside `packages/foo` externalizes `packages/foo/scratch`,
mirrored at `<store>/packages/foo/scratch`, regardless of where the verb runs.

## Why

The original design symlinked the entire store directory as a single `./ihq`, so
a monorepo subtree needed a *separate* store keyed by subpath and flattened with
`%2F` encoding to sit as a sibling (ADR-0003). Once paths are arbitrary and the
store mirrors them, that machinery is redundant: a subtree's paths simply nest
naturally as `packages/foo/...` inside the one store. Keying everything off the
repo-root-relative path keeps a managed path identical on every machine and lets
`ihq list` print the same thing from anywhere in the repo.

## Considered and rejected

- **Keep subtree stores (ADR-0003).** A separate flattened store per subtree
  duplicated the store concept and existed only to work around the single fixed
  `./ihq` link name. Removing that constraint removes the need; nesting in one
  mirror tree is simpler and loses nothing.
- **User-named store slots (both sides chosen).** Letting the caller name the
  store location as well as the source path discards the ghq-derived-path
  identity (ADR-0001) and turns the tool into a generic symlink farm. The store
  *location* stays derived; only the *set of paths* inside it is user-chosen.

This is hard to reverse: the mirror layout and the `%2F` removal orphan every
store created under ADR-0003.
