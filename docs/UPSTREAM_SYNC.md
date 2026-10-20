# Upstream synchronization

The repository is pinned to:

- repository: `https://github.com/cursor/plugins.git`
- path: `pstack`
- commit: `88d47514b82e7c44f00f2b2a72ff6dd12158038c`
- version: `0.15.29`

## Verify the current archive

Run:

```bash
python3 scripts/sync_upstream.py --check
python3 scripts/port.py
python3 scripts/run_plugin_validator.py plugins/pstack-codex
python3 -m unittest discover -s tests -v
```

The check compares every vendored file against
`config/hashes/upstream.sha256`. It is intentionally independent of the
generated package, so a hand-edited port cannot make a changed source archive
look clean.

## Refresh a pin

Refreshing is an explicit operation because it changes the source of truth:

```bash
# First edit config/upstream.json to the reviewed commit and source URL.
python3 scripts/sync_upstream.py --refresh
python3 -m unittest discover -s tests -v
```

The script clones the configured repository, archives only the configured
commit's `pstack/` tree, replaces the narrowly scoped vendor directory, writes
the new hash manifest, and regenerates the Codex package. Review the complete
vendor diff and update the compatibility allowlist only for real upstream
changes.

Do not run `--write-hashes` as a shortcut for accepting an unexplained vendor
diff. It is for recording a reviewed archive after a pin refresh.

The scheduled workflow `.github/workflows/upstream-update.yml` runs the same
refresh and validation path weekly. It also writes a deterministic
`docs/UPSTREAM_REPORT.md` into the review branch with the old/new pin and the
paths that changed. If the upstream branch changed, it pushes an update branch
and opens a review PR. It never enables auto-merge.
