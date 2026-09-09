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
        value = re.sub(
            rf"(?<![A-Za-z0-9_./-])/({names})(?![A-Za-z0-9_-])",
            r"$\1",
            value,
        )

    # A few source phrases contain the model role as a `Task` parameter
    # rather than in the exact forms covered by the allowlist.
    value = value.replace("Task model", "subagent role")
    value = value.replace("Task `model`", "subagent role")
    value = value.replace("Task", "task")
    if prose:
        value = re.sub(r"\bcursor\b", "Codex", value, flags=re.IGNORECASE)
    # Whitespace normalization keeps the generated package reviewable without
    # rewriting the immutable upstream archive.
    lines = [line.rstrip() for line in value.splitlines()]
    normalized = "\n".join(lines)
    return normalized + ("\n" if value.endswith("\n") else "")


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
                ),
                encoding="utf-8",
            )
        else:
            shutil.copy2(source, target)


def write_manifest(source_manifest: dict[str, Any]) -> None:
    manifest = {
        "name": "pstack-codex",
        "displayName": "pstack for Codex",
        "version": source_manifest["version"],
        "description": "Rigorous, parallelizable engineering workflows for Codex.",
        "author": source_manifest["author"],
        "homepage": "https://github.com/kalyandechiraju/pstack-codex",
        "repository": "https://github.com/kalyandechiraju/pstack-codex",
        "license": source_manifest["license"],
        "logo": source_manifest["logo"],
        "keywords": source_manifest["keywords"],
        "category": source_manifest["category"],
        "tags": source_manifest["tags"],
        "skills": "./skills/",
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
model references, and agent definitions to Codex.

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
