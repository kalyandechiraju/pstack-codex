#!/usr/bin/env python3
"""Build the Codex package from the immutable vendored Cursor snapshot.

The port is deliberately a generator. A reviewer can compare the generated
tree with vendor/cursor-plugins/pstack and rerun this file after an upstream
refresh without hand-editing dozens of skills.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor" / "cursor-plugins" / "pstack"
DESTINATION = ROOT / "plugins" / "pstack-codex"
ALLOWLIST = ROOT / "config" / "compatibility-allowlist.json"

TEXT_SUFFIXES = {
    ".md",
    ".mdc",
    ".mjs",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

SETUP_PSTACK_PATH = Path("skills/setup-pstack/SKILL.md")

MODEL_CONFIG_EXAMPLE = """# Copy this file to ~/.codex/pstack-models.toml or .codex/pstack-models.toml.
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
"""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def transform_text(
    value: str,
    skill_names: list[str],
    rules: dict[str, Any],
    *,
    prose: bool = False,
    relative_path: Path | None = None,
) -> str:
    """Apply the checked-in ordered compatibility allowlist."""

    for rule in rules["literal_replacements"]:
        value = value.replace(rule["from"], rule["to"])
    for rule in rules["regex_replacements"]:
        value = re.sub(rule["pattern"], rule["to"], value)

    # Skill invocations are the one context-sensitive transform. File links
    # such as ./skills/how/SKILL.md do not match because the slash is preceded
    # by a word character; command forms such as /how do.
    names = "|".join(re.escape(name) for name in sorted(skill_names, key=len, reverse=True))
    if names:
        dynamic_rule = next(
            rule
            for rule in rules["dynamic_transforms"]
            if rule["name"] == "skill-invocation"
        )
        value = re.sub(
            dynamic_rule["pattern"].format(skill_names=names),
            dynamic_rule["replacement"],
            value,
        )
    if prose:
        for rule in rules["prose_regex_replacements"]:
            value = re.sub(rule["pattern"], rule["to"], value)
    if relative_path == SETUP_PSTACK_PATH:
        value = rewrite_setup_pstack_example(value)
    # Whitespace normalization keeps the generated package reviewable without
    # rewriting the immutable upstream archive.
    lines = [line.rstrip() for line in value.splitlines()]
    normalized = "\n".join(lines)
    return normalized + ("\n" if value.endswith("\n") else "")


def rewrite_setup_pstack_example(value: str) -> str:
    """Replace the upstream rule-frontmatter sample with valid Codex TOML."""

    start_marker = "### 5. Write the rule"
    end_marker = "### 6. Confirm"
    start = value.find(start_marker)
    end = value.find(end_marker, start + len(start_marker))
    if start == -1 or end == -1:
        raise ValueError("setup-pstack example markers are missing")
    replacement = (
        "### 5. Write the rule\n\n"
        "Write `~/.codex/pstack-models.toml` as a valid TOML file. Each semantic role\n"
        "has a table under `[roles]`; single-model roles use `model` and\n"
        "`reasoning_effort`, while panel roles use a `models` array of inline tables.\n"
        "Use `inherit-parent` or `auto` as a model value when the role should run on\n"
        "the parent chat model. Overwrite the whole file so reruns stay idempotent.\n\n"
        "The default role-to-model mapping is:\n\n"
        "```toml\n"
        + MODEL_CONFIG_EXAMPLE
        + "```\n\n"
    )
    return value[:start] + replacement + value[end:]


def parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown
    end = markdown.find("\n---\n", 4)
    if end == -1:
        raise ValueError("agent markdown has an unterminated frontmatter block")
    frontmatter: dict[str, str] = {}
    for line in markdown[4:end].splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    body = markdown[end + len("\n---\n") :].lstrip()
    return frontmatter, body


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_agent(source: Path, destination: Path, skill_names: list[str], rules: dict[str, Any]) -> None:
    frontmatter, body = parse_frontmatter(source.read_text(encoding="utf-8"))
    source_name = frontmatter.get("name", source.stem)
    agent_name = re.sub(r"[^a-z0-9]+", "-", source_name.lower()).strip("-")
    description = transform_text(
        frontmatter.get("description", f"Ported agent: {source_name}"),
        skill_names,
        rules,
        prose=True,
    )
    body = transform_text(body, skill_names, rules, prose=True)
    sandbox_mode = "read-only" if agent_name == "comment-sicko" else "workspace-write"
    rendered = "\n".join(
        [
            f"name = {toml_string(agent_name)}",
            f"description = {toml_string(description)}",
            f"sandbox_mode = {toml_string(sandbox_mode)}",
            f"developer_instructions = {toml_string(body)}",
            "",
        ]
    )
    destination.write_text(rendered, encoding="utf-8")


def copy_source_tree(skill_names: list[str], rules: dict[str, Any]) -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"missing vendored source tree: {SOURCE}")
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    DESTINATION.mkdir(parents=True)

    for source in sorted(SOURCE.rglob("*")):
        relative = source.relative_to(SOURCE)
        if relative == Path(".cursor-plugin/plugin.json"):
            continue
        if relative.parts[:1] == ("agents",) and source.suffix == ".md":
            continue
        target = DESTINATION / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if is_text(source):
            target.write_text(
                transform_text(
                    source.read_text(encoding="utf-8"),
                    skill_names,
                    rules,
                    prose=source.suffix.lower() in {".md", ".mdc"},
                    relative_path=relative,
                ),
                encoding="utf-8",
            )
        else:
            shutil.copy2(source, target)


def write_manifest(source_manifest: dict[str, Any]) -> None:
    manifest = {
        "name": "pstack-codex",
        "version": source_manifest["version"],
        "description": "Rigorous, parallelizable engineering workflows for Codex.",
        "author": source_manifest["author"],
        "homepage": "https://github.com/kalyandechiraju/pstack-codex",
        "repository": "https://github.com/kalyandechiraju/pstack-codex",
        "license": source_manifest["license"],
        "keywords": source_manifest["keywords"],
        "skills": "./skills/",
        "interface": {
            "displayName": "pstack for Codex",
            "shortDescription": "Rigorous, parallelizable engineering workflows for Codex.",
            "longDescription": (
                "Pstack brings deliberate planning, parallel review, and evidence-driven "
                "verification to Codex."
            ),
            "developerName": source_manifest["author"]["name"],
            "category": "Developer tools",
            "capabilities": ["Workflow", "Planning", "Review", "Subagents"],
            "defaultPrompt": [
                "Use $poteto-mode for this task.",
                "Review this change with pstack's rigorous workflow.",
                "Plan and verify this work before shipping.",
            ],
            "brandColor": "#6B4EFF",
            "logo": "./assets/logo.png",
        },
    }
    path = DESTINATION / ".codex-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_agents(skill_names: list[str], rules: dict[str, Any]) -> None:
    destination = DESTINATION / "agents"
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted((SOURCE / "agents").glob("*.md")):
        write_agent(source, destination / f"{source.stem}.toml", skill_names, rules)
    (destination / "README.md").write_text(
        """# Codex custom agents

These agents are distributed as standalone Codex custom-agent TOML files. Copy
them to `.codex/agents/` in a project or to `~/.codex/agents/` for user-level
use. The plugin manifest cannot register custom agents.

- `poteto-agent.toml` is the full pstack workflow agent.
- `comment-sicko.toml` is a read-only comment reviewer.
""",
        encoding="utf-8",
    )


def write_porting_notice() -> None:
    (DESTINATION / "PORTING-NOTES.md").write_text(
        """# pstack Codex port

This package is generated from the pinned upstream pstack tree. The generated
skills retain the upstream workflow content while adapting commands, paths,
model references, skill invocation metadata, and agent definitions to Codex.

The `automations/benny/` directory is preserved as a dormant source pack for
users who want to adapt it. It is not registered as an active Codex automation
by the plugin manifest.

Do not edit generated files by hand. Update the allowlist or generator, then
rerun `python scripts/port.py`.
""",
        encoding="utf-8",
    )


def generate() -> None:
    source_manifest = load_json(SOURCE / ".cursor-plugin" / "plugin.json")
    rules = load_json(ALLOWLIST)
    skill_names = sorted(path.name for path in (SOURCE / "skills").iterdir() if path.is_dir())
    copy_source_tree(skill_names, rules)
    write_manifest(source_manifest)
    write_agents(skill_names, rules)
    write_porting_notice()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="generate and exit successfully")
    args = parser.parse_args()
    generate()
    if args.check:
        print(f"generated {DESTINATION.relative_to(ROOT)}")
    else:
        print(f"generated {DESTINATION.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
