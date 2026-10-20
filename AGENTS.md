# AGENTS.md

Codex-native port of Lauren Tan's pstack plugin (Cursor). The repo is a
**generator**: an immutable upstream snapshot goes in, a Codex plugin package
comes out through an ordered, allowlisted set of mechanical transforms.

## Layout

| Path | Role |
| --- | --- |
| `vendor/cursor-plugins/pstack/` | Byte-exact upstream archive at the pinned commit. **Never edit.** |
| `config/upstream.json` | Upstream repo, commit, version, paths. |
| `config/hashes/upstream.sha256` | SHA-256 manifest of the vendor tree. |
| `config/compatibility-allowlist.json` | Ordered literal/regex/prose transforms applied to generated text. |
| `config/pstack-models.toml.example` | Default model-role mapping; must match the TOML block `port.py` injects into `setup-pstack`. |
| `plugins/pstack-codex/` | **Generated** Codex plugin (skills, agent TOML, manifest). Never hand-edit. |
| `.agents/plugins/marketplace.json`, `marketplace.json` | Codex marketplace entries; must stay identical. |
| `scripts/port.py` | Generator: vendor → `plugins/pstack-codex`. Skips upstream `plugin.json` and `docs/harness/`. |
| `scripts/sync_upstream.py` | `--check` vendor hashes; `--refresh` re-archive pin; `--write-hashes` only after a reviewed refresh. |
| `scripts/run_plugin_validator.py` | Official Codex validator if present, then `validate_codex_plugin.py` fallback. |
| `scripts/render_upstream_report.py` | Writes `docs/UPSTREAM_REPORT.md` for upstream-sync PRs. |
| `tests/test_port.py` | Parity, determinism, allowlist-coverage, forbidden-token, and manifest tests. |
| `docs/` | Porting plan, compatibility boundary, upstream sync, field guide (`pstack-guide.html`). |

## Commands

Run everything with Python 3.11+ (tests use `tomllib`); no network needed.

```bash
python3 scripts/sync_upstream.py --check
python3 scripts/port.py
python3 scripts/run_plugin_validator.py plugins/pstack-codex
python3 -m unittest discover -s tests -v
```

CI (`.github/workflows/validate.yml`) runs the same four steps. A weekly
workflow (`upstream-update.yml`) refreshes from upstream and opens a review PR;
it must never auto-merge.

## Rules

- Change behavior of the port only via `config/compatibility-allowlist.json` or
  `scripts/port.py`, then regenerate. Commit the regenerated package with it.
- `tests/test_port.py` contains an independent reference implementation of the
  transforms (`allowlisted_transform`). Changes to transform logic in
  `port.py` must be mirrored there.
- Transform order matters: literals, then regexes, then the skill-invocation
  rewrite (`/skill` → `$skill`), then prose-only rules (`.md`/`.mdc`).
- The generated package must not contain Cursor-only tokens (see
  `test_generated_package_has_no_cursor_only_tokens`).
- Skill parity is exact: same 56 skill directories as upstream.
- Generation must be deterministic; running `port.py` twice yields identical
  bytes.
- Use real Codex model slugs (`gpt-5.6-luna` fast, `gpt-6-astra` judgment), not
  synthetic `pstack.*` aliases. Reasoning effort lives in `reasoning_effort`,
  never in the slug.
- `automations/benny/` is shipped dormant; do not register it.
- Bump the upstream pin only by editing `config/upstream.json` and running
  `sync_upstream.py --refresh`; review the full vendor diff.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `kalyandechiraju/pstack-codex` (via `gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` + `docs/adr/`. See `docs/agents/domain.md`.
