# pstack → Codex port plan

## Objective

Ship a reviewable Codex plugin that preserves the behavior and organization of
the pinned upstream pstack skills while replacing product-specific packaging,
commands, paths, model identifiers, and agent manifests with Codex equivalents.

## Source of truth

The source snapshot is the `pstack` directory from
`cursor/plugins@7314f723a487ec406b6369fe5865ba034cfed166`. The archive is
vendored byte-for-byte under `vendor/cursor-plugins/pstack`; the commit, source
URL, and version are recorded in [`config/upstream.json`](../config/upstream.json).

## Phases

1. **Pin and preserve.** Vendor the exact upstream tree and record a sorted
   SHA-256 manifest.
2. **Generate the package.** Copy all source content except the Cursor manifest
   and Markdown agent wrappers; write a Codex plugin manifest and Codex agent
   TOML files.
3. **Apply compatibility-only transforms.** Use the ordered allowlist for
   commands, paths, model roles, product prose, and agent vocabulary. Do not
   rewrite behavior or upstream source files.
4. **Document boundaries.** Explain the custom-agent installation path, dormant
   Benny pack, model-role configuration, and unsupported Cursor-only endpoints.
5. **Verify.** Check source hashes, generated determinism, manifest validity,
   skill parity, agent syntax, and forbidden source-only tokens.

## Non-goals

- Reimplementing Codex features that are outside a plugin package.
- Registering the dormant `automations/benny` source pack as an active
  automation.
- Preserving Cursor-specific webhooks, slash commands, or model slugs.
- Hand-editing a generated skill to conceal a compatibility gap.

## Acceptance criteria

- The vendored tree matches the pinned archive and its hash manifest.
- The generated plugin has the same 45 skill directories as upstream.
- `plugin.json` is Codex-shaped and points at `./skills/`.
- Both upstream agents are available as valid Codex custom-agent TOML.
- Running the generator twice produces identical bytes.
- Tests and the CI workflow pass without network access.
