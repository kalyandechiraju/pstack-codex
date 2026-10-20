# How the author uses pstack

This note records Lauren Tan's workflow from Parts 1 and 2 of *The Complete Guide to pstack*. Use it when advising someone how to adopt pstack in a project. It supplements the [practical field guide](./pstack-guide.html).

## Source posts

- [The Complete Guide to pstack, Part 1](https://x.com/poteto/status/2094457600259842065)
- [The Complete Guide to pstack, Part 2](https://x.com/poteto/status/2097732320606507506)

The posts describe upstream pstack 0.15.0 in Cursor and Grok Bot. This repository ports pstack 0.15.29 to Codex. Use `$skill-name` in Codex where the posts use `/skill-name`. Treat product-specific details such as Cursor cloud agents, routines, and `.cursor` paths as examples, not requirements.

## Start with verification

Create a project-specific verification skill before adding elaborate agent workflows. Run `$create-verification-skill`, then keep the result current with `$maintain-verification-skill`.

A useful verification skill lets an agent operate the real application and collect evidence. Its control tool should cover the actions the team uses to debug by hand, such as:

- starting the development environment and checking its health;
- navigating, typing, clicking, and using keyboard paths;
- reading accessibility state, console output, and network activity;
- taking screenshots, recordings, profiles, and performance traces;
- seeding test data, selecting test users, and changing development feature flags;
- resetting state and cleaning up after a run.

Prefer a small, tested CLI over instructions that make each agent rebuild throwaway scripts. Give destructive commands a `--dry-run` option. Use subcommands, useful `--help` text, actionable errors, and machine-readable output such as JSON.

Tests are part of verification, but they are not the finish line. The agent must run the changed behavior in the real artifact and show evidence that the requested outcome works.

## Keep a feature map

The verification skill should include a searchable feature map. Record each user-facing feature, how a user reaches it, how the control tool drives it, relevant account or entitlement conditions, and known recovery steps.

The feature map is compact project memory. It helps a fresh agent find and exercise behavior without rediscovering the application on every task. Run `$maintain-verification-skill` after product changes or on a regular schedule if the project changes daily.

## Build context before changing code

For a noisy or ambiguous report, ask the agent to restate the underlying problem in plain language before proposing a fix. This exposes misunderstandings without anchoring the agent on the user's first hypothesis.

Use the focused research skills when more context is needed:

- `$how` traces the current runtime mechanics.
- `$why` finds the evidence behind past design choices.
- `$teach` combines mechanics and rationale into an explanation the user can check.
- `$recall` restores useful context from earlier work and conversations.

Do not invoke all four by habit. Use the smallest set that closes the actual context gap.

## Design with executable evidence

Avoid treating a long abstract plan as proof. Use code and live behavior to answer design questions.

For a public package or shared API, start from the caller's experience. Write the tutorial or usage example first, then derive the API and implementation from it. Use `$technical-writing` so tutorials, how-to guides, reference material, and explanations do not collapse into one document.

For uncertain changes, ask `$poteto-mode` to prototype two or three options. Drive each option with the verification skill and compare screenshots, recordings, timings, or other direct evidence. Throw the prototypes away after they answer the question.

Use `$architect` for a consequential service boundary, shared package, or core data model. Start from desired call sites and type signatures. Let independent candidates compete when the design space warrants the cost. If implementation needs repeated workarounds, forced casts, or unexpected shared state, revisit the design instead of hiding the mismatch.

Write a multi-phase execution plan only after the design is credible. Each phase needs a runnable proof. Keep committed plans only while they coordinate active work, then remove them when they no longer describe the repository.

## Scale only after the loop closes

Parallel agents multiply a working development and verification loop. They also multiply setup failures and ambiguous checks. Make local setup reproducible first, then add isolated workers or cloud agents when the project and available tools support them.

Use `$swarm` when repeated independent verification adds evidence, such as performance samples, fuzz runs, or compatibility checks. Do not use parallelism as a substitute for a deterministic reproduction.

## Default guidance

Most work should start with one direct `$poteto-mode` prompt. State the outcome, the constraints, and the proof of completion. Let the mode select its playbook and supporting skills.

```text
$poteto-mode the export writes duplicate rows when a retry lands mid-run. Reproduce it first, fix the root cause, then run the export in the real app and show the before-and-after evidence.
```

Escalate the workflow only when the task needs it:

1. If the report is unclear, restate it before editing.
2. If the system is unfamiliar, use `$how`, `$why`, `$teach`, or `$recall`.
3. If the solution is uncertain, build and verify prototypes.
4. If the change defines a lasting boundary, use `$architect`.
5. If the implementation spans many reviewable units, create a proof-driven multi-phase plan.
6. If one verified worker is reliable, add parallel workers for independent work or repeated checks.

The user's main job is to supply intent, constraints, permission boundaries, and a checkable finish condition. The agent's job is to investigate, choose the workflow, implement, and prove the result.
