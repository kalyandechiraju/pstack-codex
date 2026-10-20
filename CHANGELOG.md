# Changelog

## 0.15.29-codex.1 — 2026-10-20

- Synced upstream pstack `0.15.29` from commit
  `88d47514b82e7c44f00f2b2a72ff6dd12158038c` (11 new skills, 56 total).
- Followed upstream's two-model defaults: `gpt-5.6-luna` (fast) and
  `gpt-6-astra` (judgment) at `xhigh`; panels pair the two. Retired
  `how_critics`; added a top-level `budget` key to `pstack-models.toml`.
- Translated the new reasoning-budget ladder to `reasoning_effort`.
- Removed Cursor-only Custom Mode, cloud subagent, and Project wording, and the
  upstream Claude Code install path, from the generated package. Skipped the
  upstream root `plugin.json` and `docs/harness/`.
- Dropped allowlist rules for model slugs and URLs upstream no longer uses.

## 0.14.8-codex.3 — 2026-09-09

- Replaced synthetic model role IDs with real Codex model slugs and complete
  semantic TOML role mappings.
- Synced the upstream manifest version during refresh and added a deterministic
  compatibility report to scheduled update PRs.

## 0.14.8-codex.2 — 2026-09-09

- Corrected the Codex manifest interface and skill invocation metadata.
- Added the canonical repo marketplace, official-validator preflight, link and
  allowlist coverage tests, and SHA-pinned scheduled upstream PR workflow.

## 0.14.8-codex.1 — 2026-09-09

- Ported upstream pstack `0.14.8` from commit
  `7314f723a487ec406b6369fe5865ba034cfed166`.
- Added deterministic Codex plugin generation and upstream hash verification.
- Converted the two upstream agent manifests to Codex custom-agent TOML.
- Added role-based model configuration and documented the compatibility
  boundary.
