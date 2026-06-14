# `migratable` includes untracked-not-ignored paths, but the tool stays `ihq`

`migratable` lists everything `migrate` accepts: git-ignored paths **and**
untracked-not-ignored ones. This follows from `migrate`'s real precondition,
which was always "exists AND not tracked" (ADR-0009), never "ignored." We
considered renaming `ihq` -> `uhq` ("untracked HQ") to match the broader set,
and rejected it: the untracked-not-ignored case is rare and risky (such a file
is usually code headed for a commit), so it is surfaced with a distinct `?` mark
rather than promoted to the tool's identity.

## Why keep the `ihq` name

The `ihq` ("ignored HQ") name keeps steering users toward the safe mental model:
externalize the junk git already ignores. The everyday candidate is an ignored
path; the untracked-not-ignored path is the exception. Naming the tool after the
exception would invite the exact foot-gun we want to avoid, where a new file
destined for a commit gets externalized and silently excluded for everyone.
There is also churn: `nhq` was renamed to `ihq` one day prior (ADR-0010), so a
second rename inside 48 hours would read as thrash, not conviction.

## Why surface untracked paths at all, with a mark

Hiding them would make `migratable` lie by omission: `migrate` *will* accept an
untracked-not-ignored path, so a candidate list that silently dropped it would
not match what the next command does. Instead the listing shows it with a `?`
prefix (blank means ignored), making the sharp case visible without blessing it.
The mark deliberately avoids `!`, which `list` already uses for a problem state
(missing from store), to keep the two sibling listers readable side by side.

## Consequence

A reader who notices that an "ignored HQ" tool also lists untracked files will
wonder why it was not renamed; this records that the omission was deliberate.
The load-bearing safety property is that the dangerous case is *flagged*, not
*normalized*: `migratable` reports the full eligible set, and the `?` mark plus
the unchanged `ihq` name keep pushing users toward the ignored-file default.
