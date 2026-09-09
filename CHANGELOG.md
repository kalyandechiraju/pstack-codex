# Changelog

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
