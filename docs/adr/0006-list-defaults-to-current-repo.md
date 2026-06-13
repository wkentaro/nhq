# `nhq list` defaults to the current repo, not all repos (unlike `ghq list`)

`nhq list` with no flag enumerates only the current repo's stores (the root
store plus its subtree stores). The global "every store under the root" view
lives behind `--all`. This inverts `ghq`, where a bare `ghq list` is the global
listing.

## Why

`nhq` always has a current-repo context that `ghq` lacks. `ghq` is a clone
manager invoked from anywhere with no notion of "the repo you are in," so its
only meaningful default is the global list. `nhq` is a notes-beside-this-code
tool: you are essentially always inside a repo when you run it, so "the stores
for the repo I'm in" is the useful default.

The dominant CLI convention is also narrow-default-then-widen, not the reverse:
`docker ps` shows the current context and `-a` widens it, `kubectl get` is the
current namespace and `-A` widens it, `git config` writes local and `--global`
widens it. Global-by-default with a *narrowing* flag is the rarer arrangement.
`nhq` follows the mainstream pattern and makes `--all` the widener.

## Considered and rejected

- **Bare `list` = global (literal ghq parity), local behind a flag.** Copies
  ghq's global default, which exists only because ghq has no current-repo
  context. Adopting it in a tool that *does* have that context fights the
  mainstream narrow-default convention and demotes the everyday case (the repo
  you are in) behind a flag.
- **`ls` = local, `list` = global as two distinct verbs.** `ls` is the
  near-universal *alias* of `list` (docker, gh, kubectl), so making the two
  differ in scope surprises anyone who reaches for `ls` as shorthand.

A reader who knows `ghq` will expect `nhq list` to be global; this records why
it is not. The default scope is a UX contract that users script against and
build muscle memory on, so changing it later would silently break them.
