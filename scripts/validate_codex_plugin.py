#!/usr/bin/env python3
"""Small dependency-free validator for the Codex plugin ingestion contract.

The official workspace validator is preferred by run_plugin_validator.py when
it is available. This fallback keeps CI meaningful on machines that do not
ship the Codex runtime.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
MANIFEST_KEYS = {
    "id",
    "name",
    "version",
    "description",
    "skills",
    "apps",
    "mcpServers",
    "interface",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
}
INTERFACE_KEYS = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
    "brandColor",
    "composerIcon",
    "logo",
    "logoDark",
    "screenshots",
    "defaultPrompt",
    "default_prompt",
}


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def safe_asset(root: Path, raw: Any) -> bool:
    if not isinstance(raw, str) or not raw.startswith("./"):
        return False
    target = (root / raw[2:]).resolve()
    return target.is_file() and root.resolve() in target.parents


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str] | None:
    contents = path.read_text(encoding="utf-8")
    if not contents.startswith("---\n"):
        error(errors, f"skill `{path.parent.name}` must start with YAML frontmatter")
        return None
    end = contents.find("\n---", 4)
    if end == -1:
        error(errors, f"skill `{path.parent.name}` frontmatter is not closed")
        return None
    fields: dict[str, str] = {}
    for line in contents[4:end].splitlines():
        if not line.strip() or line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def validate(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return ["missing .codex-plugin/plugin.json"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid plugin.json: {exc}"]
    if not isinstance(manifest, dict):
        return ["plugin.json must be an object"]

    for key in sorted(set(manifest) - MANIFEST_KEYS):
        error(errors, f"unsupported manifest field: {key}")
    for key in ("name", "version", "description"):
        if not non_empty(manifest.get(key)):
            error(errors, f"manifest field {key} must be non-empty")
    if non_empty(manifest.get("version")) and SEMVER.fullmatch(manifest["version"]) is None:
        error(errors, "manifest version must be strict semver")
    if not isinstance(manifest.get("author"), dict) or not non_empty(manifest["author"].get("name")):
        error(errors, "manifest author.name must be non-empty")
    if manifest.get("skills") != "./skills/":
        error(errors, "manifest skills must be ./skills/")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        error(errors, "manifest interface must be an object")
    else:
        for key in sorted(set(interface) - INTERFACE_KEYS):
            error(errors, f"unsupported interface field: {key}")
        for key in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
            if not non_empty(interface.get(key)):
                error(errors, f"interface.{key} must be non-empty")
        if "defaultPrompt" not in interface and "default_prompt" not in interface:
            error(errors, "interface.defaultPrompt is required")
        if not isinstance(interface.get("capabilities"), list) or not all(
            non_empty(value) for value in interface["capabilities"]
        ):
            error(errors, "interface.capabilities must be an array of strings")
        prompts = interface.get("defaultPrompt", interface.get("default_prompt"))
        if not isinstance(prompts, list) or not prompts or not all(non_empty(value) for value in prompts[:3]):
            error(errors, "interface.defaultPrompt must contain non-empty strings")
        for field in ("logo", "logoDark", "composerIcon"):
            if field in interface and not safe_asset(plugin_root, interface[field]):
                error(errors, f"interface.{field} must point to a local asset")
        if not isinstance(interface.get("brandColor"), str) or not re.fullmatch(
            r"#[0-9A-Fa-f]{6}", interface.get("brandColor", "")
        ):
            error(errors, "interface.brandColor must use #RRGGBB")

    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        error(errors, "missing skills directory")
    else:
        for skill_root in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            skill_path = skill_root / "SKILL.md"
            if not skill_path.is_file():
                error(errors, f"skill {skill_root.name} is missing SKILL.md")
                continue
            fields = parse_frontmatter(skill_path, errors)
            if fields is None:
                continue
            if not fields.get("name", "").strip():
                error(errors, f"skill {skill_root.name} has no name")
            if not fields.get("description", "").strip():
                error(errors, f"skill {skill_root.name} has no description")
            disabled = fields.get("disable-model-invocation", fields.get("disable_model_invocation"))
            if disabled is not None and disabled.lower() != "false":
                error(errors, f"skill {skill_root.name} disables model invocation")
    return errors


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_codex_plugin.py PLUGIN_PATH")
    errors = validate(Path(sys.argv[1]).expanduser().resolve())
    if errors:
        print("Compatible plugin validation failed:")
        for item in errors:
            print(f"- {item}")
        raise SystemExit(1)
    print("Compatible plugin validation passed")


if __name__ == "__main__":
    main()
