# Compatibility boundary

The port is intentionally mechanical. The upstream tree remains available for
diffing; the generated package receives the transforms below.

| Upstream concept | Codex representation |
| --- | --- |
| Cursor plugin manifest | `.codex-plugin/plugin.json` |
| upstream presentation metadata | `plugin.json.interface` fields required by Codex |
| `/skill-name` invocation | `$skill-name` invocation |
| `.cursor/skills` | `.agents/skills` |
| Cursor user/project metadata | `~/.codex` / `.codex` |
| `pstack-models.mdc` | `pstack-models.toml` |
| hard-coded model slugs | real Codex model slugs in generated defaults, with semantic per-role overrides in TOML |
| `subagent_type` and `generalPurpose` | Codex agent names and standard Codex subagents |
| `run_in_background` | Background Codex task when available |
| `readonly` | Codex `sandbox_mode` language |
| Cursor agent Markdown | standalone Codex custom-agent TOML |
| Cursor `/loop` wake command | Codex heartbeat/automation wording |
| `disable-model-invocation: true` | `disable-model-invocation: false` so Codex can invoke copied skills |
| Cursor Custom Modes, cloud subagents, Projects | portable wording: start each task with `$poteto-mode`, use worktrees or Codex cloud tasks |
| upstream Claude Code install and `docs/harness/claude-code.md` | omitted from the Codex package |
| upstream root `plugin.json` | omitted; the package ships `.codex-plugin/plugin.json` |

## Cursor name coverage

Upstream keeps a `TERMS` list of every Cursor-only name its skills use, in
`scripts/generate-pstack-harness-trees.mjs`. A sync vendors that file, and
`scripts/check_cursor_terms.py` matches it against
[`config/cursor-terms.json`](../config/cursor-terms.json). Each name is
`translated` (must not appear in the generated package), `kept` (valid in Codex),
or `gap` (known untranslated usage, reported on every run). The check fails on a
name upstream adds that the config does not list, and on a `translated` name that
leaks into the package.

## Model roles

The generated skills use real Codex model slugs in their defaults: `gpt-6-luna`
for fast roles, `gpt-6-astra` for judgment roles, and `gpt-6.1-sol` for
`reflect_tooling` and as the second panel model beside `gpt-6-astra`. Fast roles
sit two reasoning steps below judgment roles and panels (`medium` versus `xhigh`
under the default `large` budget). Upstream encodes reasoning effort
in the model slug (`claude-opus-5-5-xhigh`); the port keeps the slug plain and
sets `reasoning_effort` per role instead, with the `$setup-pstack` budget
(`unlimited`, `large`, `medium`, `small`) recorded as a top-level `budget` key.
A user can override each semantic role and its reasoning effort in `~/.codex/pstack-models.toml` or
`.codex/pstack-models.toml`; panel roles use arrays of inline TOML tables. The
starter file is [`config/pstack-models.toml.example`](../config/pstack-models.toml.example),
and `$setup-pstack` writes the same valid TOML shape. There are no synthetic
`pstack.*` model aliases to resolve.

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

Every text change in the generated copy is checked against the ordered
[`config/compatibility-allowlist.json`](../config/compatibility-allowlist.json)
by the test suite. The manifest, agent, and setup-file conversions are the
documented structural transforms.
