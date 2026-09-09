# Compatibility boundary

The port is intentionally mechanical. The upstream tree remains available for
diffing; the generated package receives the transforms below.

| Upstream concept | Codex representation |
| --- | --- |
| Cursor plugin manifest | `.codex-plugin/plugin.json` |
| `/skill-name` invocation | `$skill-name` invocation |
| `.cursor/skills` | `.agents/skills` |
| Cursor user/project metadata | `~/.codex` / `.codex` |
| `pstack-models.mdc` | `pstack-models.toml` |
| hard-coded model slugs | `pstack.fast`, `pstack.review`, `pstack.judgment`, and `pstack.deep-judgment` role IDs |
| `subagent_type` and `generalPurpose` | Codex agent names and standard Codex subagents |
| `run_in_background` | Background Codex task when available |
| `readonly` | Codex `sandbox_mode` language |
| Cursor agent Markdown | standalone Codex custom-agent TOML |
| Cursor `/loop` wake command | Codex heartbeat/automation wording |

## Model roles

The generated skills refer to stable role IDs rather than assuming a model
catalog. A user can define the concrete models and reasoning effort in
`~/.codex/pstack-models.toml` or `.codex/pstack-models.toml`; a starter file is
[`config/pstack-models.toml.example`](../config/pstack-models.toml.example).

## Custom agents

Codex custom agents are standalone TOML definitions. The plugin manifest
therefore exposes the skills only. Install the generated `agents/*.toml` files
under `.codex/agents/` or `~/.codex/agents/` as described in the generated
[`agents/README.md`](../plugins/pstack-codex/agents/README.md).

## Deliberately dormant material

`automations/benny/` is carried for source completeness and adaptation. It is
not registered by the plugin manifest. Its setup instructions describe Codex
automation editor flows, but enabling those automations remains an explicit
user action.

The upstream `make-bot-ui` material refers to a third-party automation webhook.
The port removes the hard-coded Cursor endpoint and tells the user to provide a
Codex-compatible service URL instead.

## What is not transformed

The generator does not alter source code semantics, image assets, or upstream
workflow sequencing. A compatibility change that needs semantic redesign must
be proposed as a separate change with tests and an explicit update to this
document.
