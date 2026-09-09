# pstack for Codex

This repository ports Lauren Tan's `pstack` plugin from the pinned Cursor
snapshot at commit `7314f723a487ec406b6369fe5865ba034cfed166` (`0.14.8`) to
Codex. It carries the upstream skills and reference material, adapts the
invocation syntax and workspace paths, maps model names to configurable roles,
and converts the two upstream agent manifests to Codex custom-agent TOML.

## Install

In Codex, add this repository's `marketplace.json` as a local marketplace and
install `pstack-codex`. The installable package is
[`plugins/pstack-codex`](plugins/pstack-codex). After installation, invoke the
main workflow with `$poteto-mode` and configure model roles with `$setup-pstack`.

Custom agents are separate Codex configuration files because the plugin
manifest does not register them. Copy the generated files from
[`plugins/pstack-codex/agents`](plugins/pstack-codex/agents) to `.codex/agents/`
for a project or `~/.codex/agents/` for user-level use.

## Repository layout

- `vendor/cursor-plugins/pstack/` is the exact upstream archive. Do not edit it.
- `plugins/pstack-codex/` is generated and is the distributable plugin.
- `scripts/port.py` performs the deterministic source-to-Codex transformation.
- `scripts/sync_upstream.py` verifies the vendor hash manifest and can refresh a
  deliberately changed upstream pin.
- `config/compatibility-allowlist.json` records every mechanical compatibility
  transform.
- `docs/` explains the port boundary and the refresh process.

## Development

```bash
python3 scripts/port.py
python3 scripts/sync_upstream.py --check
python3 -m unittest discover -s tests -v
```

The generator is the source of truth for `plugins/pstack-codex`; changes to a
generated file should be made in the generator or allowlist and regenerated.

## Attribution and license

The upstream pstack content is MIT-licensed and remains attributed to Lauren
Tan. See [`NOTICE`](NOTICE), [`LICENSE`](LICENSE), and the vendored
[`LICENSE`](vendor/cursor-plugins/pstack/LICENSE).
