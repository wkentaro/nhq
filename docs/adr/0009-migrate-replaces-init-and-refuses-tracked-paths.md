# `migrate` replaces `init`; `link` stays attach-only; tracked paths refused

Supersedes the create-safety half of ADR-0004. The "exclude-only, no hooks" half
of ADR-0004 stands unchanged.

There is no `init`. The verb that creates store content is **`migrate <path>`**:
it moves existing working-tree content into the store, leaves a symlink behind,
adds a `.git/info/exclude` line, and records the path in the manifest. Its
precondition is **working-tree content exists AND the path is not tracked by
git**. `link` is unchanged in spirit: it only *attaches* a path the store
already has and **never creates store content**; on a fresh path it errors
("nothing in store; use `migrate`"). `migrate` **hard-refuses a git-tracked
path**, with no `--force`. There is no `new` verb: to externalize fresh content,
create it first (`mkdir` or `touch`) and `migrate` it.

## Why `migrate` replaces `init`

`init` existed to perform the one consequential act — creating store content —
once per repo. With arbitrary managed paths that act is per-path, so `migrate`
*is* the consequential creator and `init` has nothing left to do. The
load-bearing safety property of ADR-0004 survives intact: **`link` never creates
store content; only the deliberate `migrate` does.** The asymmetry simply moves
from `init`-vs-`link` to `migrate`-vs-`link`.

## Why tracked paths are refused

`.git/info/exclude` has no effect on tracked files, so migrating a *tracked* path
would hide nothing: git would show the file-to-symlink swap as a modification and
the content leaving the tree as a change to a committed file, which would then be
committed and pushed to the team. That is the exact opposite of "never in git."
Refusing tracked paths keeps the privacy promise load-bearing. A `--force` was
rejected: there is no safe automatic version of "rewrite a committed file for
everyone," so the user must `git rm --cached` deliberately first.

## Why no `new` verb

Creating fresh empty content is exactly `mkdir` (directory) and `touch` (file),
which already declare the type the filesystem would otherwise have to be told.
A `new` verb would re-import that file-vs-directory choice into the tool for no
gain; `migrate` auto-detects type from disk, so `mkdir x && ihq migrate x`
covers the fresh case with zero new surface.

## Consequence

A user looking for `init` will not find it; `migrate` is the first command. A
reviewer expecting a commit-time guard still finds none (ADR-0004's exclude-only
stance is unchanged); the guard is `migrate`'s refusal to touch tracked paths or
to fabricate content from a typo.
