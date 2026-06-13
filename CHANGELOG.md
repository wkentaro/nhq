# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `nhq init` to create this repo's store under
  `$NHQ_ROOT/<host>/<user>/<repo>/` and link it in one step (run once per repo).
- `nhq link` to connect `./nhq` to an existing store on additional checkouts or
  machines, creating the symlink and the `.git/info/exclude` entry.
- `nhq unlink` to remove the symlink and exclude entry, leaving the store
  untouched.
- `nhq root` to print the absolute store-root path for the current repo.
- `nhq list` to show the stores under the current repo's identity, marking the
  one linked to the current checkout.
- `--version` and `--help` output on stdout, with Examples sections in each
  subcommand's help.
