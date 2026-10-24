# Translate Cursor-isms with build-time rewrites, not a runtime adapter

Upstream added Claude Code support by shipping its skills nearly verbatim plus an adapter document the model reads at runtime to map Cursor names. The port keeps rewriting upstream text when it is built instead, so Codex users read native names (`$skill`, Codex paths and models, Codex-correct prose) and no run spends tokens translating. We accept that syncs cost more, because upstream rewording can break sentence-level rewrites, and offset that with a check driven by upstream's own list of Cursor names.

## Considered Options

- **Runtime adapter** (upstream's Claude Code approach): cheapest syncs, but skills keep Cursor names and every run depends on the model applying the lookup correctly.
- **Hybrid**: mechanical rewrites at build time, Cursor-only concepts in an adapter. Rejected to keep one translation mechanism and fully native output.
