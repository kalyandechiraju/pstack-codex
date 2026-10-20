# pstack-codex

A permanent, independent Codex edition of Lauren Tan's pstack, kept current by syncing from upstream.

## Language

### Editions

**Upstream**:
The pstack plugin as published in `cursor/plugins`, the single source of workflow content.
_Avoid_: source repo, original

**Harness**:
An agent product that runs pstack skills, such as Cursor, Claude Code, or Codex.
_Avoid_: platform, host, IDE

**Port**:
The Codex edition of pstack this repository produces. Codex is its only harness.
_Avoid_: fork, Codex harness tree, plugin (when the whole edition is meant)

**Sync**:
A deliberate, manually started move of the port to a newer upstream version.
_Avoid_: refresh, update, upgrade

**Rewrite**:
A Codex-specific change to upstream text baked into the port when it is built.
_Avoid_: adapter (upstream's runtime lookup, which the port does not use)

### Models

**Role**:
A named job in a pstack workflow that gets its own model and reasoning effort.
_Avoid_: slot, tier

**Fast role**:
A role for well-specified or mechanical work, such as code delegates, explorers, and swarm workers.

**Judgment role**:
A role for prose, design judgment, and the hardest changes.

**Panel**:
A role that runs one subagent per listed model so their results can be compared.
_Avoid_: council, committee

**Budget**:
The user's overall reasoning level for the port. It sets the effort of judgment roles and panels; fast roles sit two steps lower.
_Avoid_: effort (that is per role)
