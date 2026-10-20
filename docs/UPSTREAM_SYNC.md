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
python3 scripts/check_cursor_terms.py
python3 scripts/run_plugin_validator.py plugins/pstack-codex
python3 -m unittest discover -s tests -v
```

The check compares every vendored file against
`config/hashes/upstream.sha256`. It is intentionally independent of the
generated package, so a hand-edited port cannot make a changed source archive
look clean.

## Sync to a newer upstream

Syncs are manual; there is no scheduled workflow. Start one when you want the
port on a newer upstream version:

```bash
git switch -c chore/sync-upstream
python3 scripts/sync_upstream.py --latest
python3 scripts/render_upstream_report.py --base main
python3 -m unittest discover -s tests -v
```

`--latest` pins the head of the configured upstream branch and runs the refresh
below. To pin a specific reviewed commit instead, edit `config/upstream.json`
and run `python3 scripts/sync_upstream.py --refresh`.

The refresh clones the configured repository and archives only the pinned
commit's `pstack/` tree plus upstream's `scripts/generate-pstack-harness-trees.mjs`,
whose `TERMS` list names every Cursor-only term upstream skills use. It replaces
the vendor directory, writes the new hash manifest, regenerates the Codex
package, and runs `scripts/check_cursor_terms.py`.

When the coverage check fails, it names each new upstream Cursor name or each
translated name that leaked into the package. Add rewrite rules to
`config/compatibility-allowlist.json`, record the name in
`config/cursor-terms.json`, and rerun `python3 scripts/port.py` and the check.
Its "known gap" lines list upstream usage the port still leaves untranslated.

Then review the vendor diff, the generated diff, and `docs/UPSTREAM_REPORT.md`,
and grep the generated package for new Cursor product wording the `TERMS` list
does not cover, such as feature names or `cursor.com` links.

Do not run `--write-hashes` as a shortcut for accepting an unexplained vendor
diff. It is for recording a reviewed archive after a pin refresh.
