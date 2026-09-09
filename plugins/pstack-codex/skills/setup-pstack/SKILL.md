---
name: setup-pstack
description: Configure which models pstack uses per role. Detects your available models and writes an always-applied rule that overrides the skill defaults. Use for $setup-pstack, "configure pstack models", or changing pstack's model choices.
---

# Setup pstack

Write `~/.codex/pstack-models.toml`, an always-applied configuration file that sets pstack's model per role. The skills read it and fall back to their inline defaults when a line is absent, so this is an override layer, not a requirement.

## Steps

### 1. Detect available models

Enumerate the model slugs you can pass to a `task` subagent in this session; that is the dependable source. If Codex also exposes a models API or CLI that lists the user's entitled models, prefer it for completeness. If you cannot detect any, ask the user to paste the slugs they have access to. Never write a real slug you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not detected slugs.

### 2. Load current state

The default role-to-model mapping is the rule shape shown in step 5 below. If `~/.codex/pstack-models.toml` already exists, read it and treat its values as the current choices. Otherwise start from those defaults.

### 3. Map and confirm

Show every role with its current model, marking any real slug not in the detected set as needing a choice. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model, which is how Auto users stay on Auto) as the options. Prefer request user input over free text. For panel roles (how critics, arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose model family differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real slug written must be in the detected set; `inherit-parent` and `auto` always pass. If a chosen real slug is not available, stop and ask again. A rule pointing at a model the user cannot use breaks every delegation that reads it.

### 5. Write the rule

Write `~/.codex/pstack-models.toml` as a valid TOML file. Each semantic role
has a table under `[roles]`; single-model roles use `model` and
`reasoning_effort`, while panel roles use a `models` array of inline tables.
Use `inherit-parent` or `auto` as a model value when the role should run on
the parent chat model. Overwrite the whole file so reruns stay idempotent.

The default role-to-model mapping is:

```toml
# Copy this file to ~/.codex/pstack-models.toml or .codex/pstack-models.toml.
# Each role is a semantic name used by pstack. Single-model roles use model and
# reasoning_effort; panel roles use a models array of inline tables.
# Use inherit-parent or auto as a model value to keep the parent chat model.

[roles.feature]
model = "gpt-5.6-luna"
reasoning_effort = "medium"

[roles.refactoring]
model = "gpt-5.6-luna"
reasoning_effort = "medium"

[roles.bug_fix]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.perf_issue]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.hillclimb]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.judgment_and_prose]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.hardest_tasks]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.how_explorer]
model = "gpt-5.6-luna"
reasoning_effort = "medium"

[roles.how_explainer]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.how_critics]
models = [
  { model = "gpt-6-astra", reasoning_effort = "high" },
  { model = "gpt-5.6-sol", reasoning_effort = "medium" },
  { model = "gpt-5.6-luna", reasoning_effort = "medium" },
  { model = "gpt-5.6-terra", reasoning_effort = "xhigh" }
]

[roles.why_investigators]
model = "gpt-5.6-luna"
reasoning_effort = "medium"

[roles.why_synthesizer]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.reflect_tooling]
model = "gpt-5.6-sol"
reasoning_effort = "medium"

[roles.reflect_judgment]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.reflect_divergent]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.reflect_synthesizer]
model = "gpt-6-astra"
reasoning_effort = "high"

[roles.arena_runners]
models = [
  { model = "gpt-6-astra", reasoning_effort = "high" },
  { model = "gpt-5.6-sol", reasoning_effort = "medium" },
  { model = "gpt-5.6-luna", reasoning_effort = "medium" },
  { model = "gpt-5.6-terra", reasoning_effort = "xhigh" }
]

[roles.arena_cross_judge_pool]
models = [
  { model = "gpt-6-astra", reasoning_effort = "high" },
  { model = "gpt-5.6-sol", reasoning_effort = "medium" },
  { model = "gpt-5.6-luna", reasoning_effort = "medium" },
  { model = "gpt-5.6-terra", reasoning_effort = "xhigh" }
]

[roles.swarm_workers]
model = "gpt-5.6-luna"
reasoning_effort = "medium"

[roles.architect_runners]
models = [
  { model = "gpt-6-astra", reasoning_effort = "high" },
  { model = "gpt-5.6-sol", reasoning_effort = "medium" },
  { model = "gpt-5.6-luna", reasoning_effort = "medium" },
  { model = "gpt-5.6-terra", reasoning_effort = "xhigh" }
]

[roles.interrogate_reviewers]
models = [
  { model = "gpt-6-astra", reasoning_effort = "high" },
  { model = "gpt-5.6-sol", reasoning_effort = "medium" },
  { model = "gpt-5.6-luna", reasoning_effort = "medium" },
  { model = "gpt-5.6-terra", reasoning_effort = "xhigh" }
]
```

### 6. Confirm

Tell the user the rule was written and that it applies to new sessions. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with $create-verification-skill." On yes, invoke `$create-verification-skill` (resolves wherever pstack is installed — workspace, user, or plugin). On no, move on without pushing.
