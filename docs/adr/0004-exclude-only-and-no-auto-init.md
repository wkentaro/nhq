# Hide via `.git/info/exclude` only; `link` never auto-creates the store

The link is hidden from git using a single anchored line in
`.git/info/exclude` (per-repo, untracked, invisible to the team). There are
**no git hooks and no pre-commit guard** ("trust the ignore").

`nhq init` performs the full first-time setup: it creates the store **and** links
`./nhq` to it. `nhq link` only connects an existing store, and **errors if the
store does not exist** ("no store for this repo; run `nhq init`") rather than
creating it. So a store is only ever created by the deliberate `nhq init`.

## Why exclude-only

`.git/info/exclude` is the one ignore mechanism that is per-checkout and never
travels into the repo's history or to teammates, which is exactly the privacy
property wanted. Hooks would add a moving part, can be bypassed, and are
per-repo state that has to be installed and maintained. The ignore is trusted;
the tool does not police commits.

## Why `link` refuses to auto-init

Auto-creating a store on `link` would silently manufacture a store for a typo'd
or wrong-identity repo (for example a misconfigured remote), scattering junk
stores. `init` is run once, on the machine where you first start taking notes;
`link` is the routine per-machine command. Making `link` refuse to create a store
turns it into a safety guard: on a second machine where the store has not synced
yet, or where the remote is wrong, `link` errors instead of producing junk.

This is why `init` may also link but `link` may not also init. The two acts are
not symmetric: creating a store is consequential and must stay explicit, while
linking is cheap and safe to bundle into the deliberate `init`.

## Consequence

A reviewer may expect a commit-time guard and find none; that is deliberate. The
load-bearing safety property is that **`link` never creates a store**: `init` is
the full first-time setup (create store + link), and `link` is the per-checkout
command for every other machine, where its refusal catches a typo'd remote or an
un-synced store.
