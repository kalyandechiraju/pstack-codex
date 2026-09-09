# pstack for Codex

This repository ports Lauren Tan's `pstack` plugin from the pinned Cursor
snapshot at commit `7314f723a487ec406b6369fe5865ba034cfed166` (`0.14.8`) to
Codex. It carries the upstream skills and reference material, adapts the
invocation syntax and workspace paths, maps model names to configurable roles,
and converts the two upstream agent manifests to Codex custom-agent TOML.

The generated defaults use real Codex model slugs (`gpt-5.6-luna` for fast work,
`gpt-5.6-sol` for review, `gpt-6-astra` for judgment, and `gpt-5.6-terra` for
the fourth panel). `$setup-pstack` writes semantic role tables and panel arrays
as valid TOML; see [`config/pstack-models.toml.example`](config/pstack-models.toml.example).

## Install

Add the GitHub repository as a Codex marketplace, then install the plugin:

```bash
codex plugin marketplace add kalyandechiraju/pstack-codex --ref main
codex plugin add pstack-codex@pstack-codex
```

Start a new Codex task so it discovers the installed skills. Invoke the main
workflow with `$poteto-mode` and configure model roles with `$setup-pstack`.
The installable package is [`plugins/pstack-codex`](plugins/pstack-codex).

Verify the installation:

```bash
codex plugin list --marketplace pstack-codex
```

## Update

Refresh the Git marketplace snapshot and reinstall the plugin, then start a new
Codex task:

```bash
codex plugin marketplace upgrade pstack-codex
codex plugin add pstack-codex@pstack-codex
```

## Optional custom agents

Custom agents are separate Codex configuration files because the plugin
manifest does not register them. To add them to one project:

```bash
git clone https://github.com/kalyandechiraju/pstack-codex.git
mkdir -p /path/to/your-project/.codex/agents
cp pstack-codex/plugins/pstack-codex/agents/*.toml /path/to/your-project/.codex/agents/
```

Use `~/.codex/agents/` instead for user-level agents.

## Troubleshooting

- If the marketplace is missing, rerun the `codex plugin marketplace add`
  command and inspect `codex plugin marketplace list`.
- If the plugin is listed but its skills are absent, reinstall it and start a
  new Codex task; skill discovery happens at the task boundary.
- If `$setup-pstack` cannot write `~/.codex/pstack-models.toml`, grant Codex
  access to that file or copy `config/pstack-models.toml.example` there
  manually.
- The two custom agents are intentionally separate from plugin installation;
  copy their TOML files as shown above when you want them.

## Repository layout

- `vendor/cursor-plugins/pstack/` is the exact upstream archive. Do not edit it.
- `plugins/pstack-codex/` is generated and is the distributable plugin.
- `scripts/port.py` performs the deterministic source-to-Codex transformation.
- `scripts/sync_upstream.py` verifies the vendor hash manifest and can refresh a
  deliberately changed upstream pin.
- `config/compatibility-allowlist.json` records every mechanical compatibility
  transform.
- `.agents/plugins/marketplace.json` is the canonical repo/team marketplace;
  root `marketplace.json` is kept as an identical convenience copy.
- `docs/` explains the port boundary and the refresh process.

## Development

```bash
python3 scripts/port.py
python3 scripts/sync_upstream.py --check
python3 scripts/run_plugin_validator.py plugins/pstack-codex
python3 -m unittest discover -s tests -v
```

The generator is the source of truth for `plugins/pstack-codex`; changes to a
generated file should be made in the generator or allowlist and regenerated.
When the Codex runtime is installed locally, `run_plugin_validator.py` invokes
the official plugin validator first. CI uses the checked-in dependency-free
compatible validator when the runtime is unavailable.

## Attribution and license

The upstream pstack content is MIT-licensed and remains attributed to Lauren
Tan. See [`NOTICE`](NOTICE), [`LICENSE`](LICENSE), and the vendored
[`LICENSE`](vendor/cursor-plugins/pstack/LICENSE).
