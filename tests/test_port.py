from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor" / "cursor-plugins" / "pstack"
DESTINATION = ROOT / "plugins" / "pstack-codex"
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


def snapshot(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def allowlisted_transform(
    value: str,
    skill_names: set[str],
    rules: dict[str, object],
    *,
    prose: bool,
    relative_path: Path | None = None,
) -> str:
    """Independent reference implementation for generated text changes."""

    for rule in rules["literal_replacements"]:  # type: ignore[index]
        value = value.replace(rule["from"], rule["to"])  # type: ignore[index]
    for rule in rules["regex_replacements"]:  # type: ignore[index]
        value = re.sub(rule["pattern"], rule["to"], value)  # type: ignore[index]
    names = "|".join(re.escape(name) for name in sorted(skill_names, key=len, reverse=True))
    dynamic = next(
        rule for rule in rules["dynamic_transforms"]  # type: ignore[index]
        if rule["name"] == "skill-invocation"  # type: ignore[index]
    )
    value = re.sub(
        dynamic["pattern"].format(skill_names=names),  # type: ignore[index]
        dynamic["replacement"],  # type: ignore[index]
        value,
    )
    if prose:
        for rule in rules["prose_regex_replacements"]:  # type: ignore[index]
            value = re.sub(rule["pattern"], rule["to"], value)  # type: ignore[index]
    if relative_path == Path("skills/setup-pstack/SKILL.md"):
        start_marker = "### 5. Write the rule"
        end_marker = "### 6. Confirm"
        start = value.find(start_marker)
        end = value.find(end_marker, start + len(start_marker))
        if start == -1 or end == -1:
            raise AssertionError("setup-pstack example markers are missing")
        example = (ROOT / "config/pstack-models.toml.example").read_text(encoding="utf-8")
        replacement = (
            "### 5. Write the rule\n\n"
            "Write `~/.codex/pstack-models.toml` as a valid TOML file. Each semantic role\n"
            "has a table under `[roles]`; single-model roles use `model` and\n"
            "`reasoning_effort`, while panel roles use a `models` array of inline tables.\n"
            "Use `inherit-parent` or `auto` as a model value when the role should run on\n"
            "the parent chat model. Overwrite the whole file so reruns stay idempotent.\n\n"
            "The default role-to-model mapping is:\n\n"
            "```toml\n"
            + example
            + "```\n\n"
        )
        value = value[:start] + replacement + value[end:]
    lines = [line.rstrip() for line in value.splitlines()]
    normalized = "\n".join(lines)
    return normalized + ("\n" if value.endswith("\n") else "")


def markdown_links(path: Path) -> list[str]:
    return re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class PortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [sys.executable, "scripts/port.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_upstream_hash_manifest_is_clean(self) -> None:
        subprocess.run(
            [sys.executable, "scripts/sync_upstream.py", "--check"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_upstream_config_version_matches_vendored_manifest(self) -> None:
        config = json.loads((ROOT / "config/upstream.json").read_text(encoding="utf-8"))
        manifest = json.loads((SOURCE / ".cursor-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(config["version"], manifest["version"])

    def test_model_role_example_is_complete_valid_toml(self) -> None:
        starter = (ROOT / "config/pstack-models.toml.example").read_text(encoding="utf-8")
        config = tomllib.loads(starter)
        roles = config["roles"]
        expected_roles = {
            "feature",
            "refactoring",
            "bug_fix",
            "perf_issue",
            "hillclimb",
            "judgment_and_prose",
            "hardest_tasks",
            "how_explorer",
            "how_explainer",
            "how_critics",
            "why_investigators",
            "why_synthesizer",
            "reflect_tooling",
            "reflect_judgment",
            "reflect_divergent",
            "reflect_synthesizer",
            "arena_runners",
            "arena_cross_judge_pool",
            "swarm_workers",
            "architect_runners",
            "interrogate_reviewers",
        }
        self.assertEqual(set(roles), expected_roles)
        self.assertEqual(roles["feature"]["model"], "gpt-5.6-luna")
        self.assertEqual(roles["reflect_tooling"]["model"], "gpt-5.6-sol")
        self.assertEqual(roles["judgment_and_prose"]["model"], "gpt-6-astra")
        for panel_name in (
            "how_critics",
            "arena_runners",
            "arena_cross_judge_pool",
            "architect_runners",
            "interrogate_reviewers",
        ):
            panel = roles[panel_name]["models"]
            self.assertEqual(len(panel), 4, panel_name)
            self.assertEqual(panel[-1]["model"], "gpt-5.6-terra")

        setup = (DESTINATION / "skills/setup-pstack/SKILL.md").read_text(encoding="utf-8")
        match = re.search(r"```toml\n(.*?)```", setup, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), starter)
        self.assertEqual(tomllib.loads(match.group(1)), config)

    def test_generated_defaults_use_real_model_slugs(self) -> None:
        forbidden = re.compile(r"pstack\.(?:fast|review|judgment|deep-judgment)\b")
        generated_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in DESTINATION.rglob("*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )
        self.assertIsNone(forbidden.search(generated_text))
        self.assertNotIn("always-applied", generated_text)
        for slug in ("gpt-5.6-luna", "gpt-5.6-sol", "gpt-6-astra", "gpt-5.6-terra"):
            self.assertIn(slug, generated_text)

    def test_manifest_is_codex_shaped(self) -> None:
        manifest = json.loads((DESTINATION / ".codex-plugin/plugin.json").read_text())
        upstream = json.loads((ROOT / "config/upstream.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "pstack-codex")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("agents", manifest)
        self.assertEqual(manifest["version"], upstream["version"])

    def test_marketplace_points_at_generated_plugin(self) -> None:
        marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/pstack-codex")
        self.assertEqual(marketplace, json.loads((ROOT / "marketplace.json").read_text()))

    def test_ci_is_pinned_and_upstream_job_only_opens_prs(self) -> None:
        validate_workflow = (ROOT / ".github/workflows/validate.yml").read_text()
        update_workflow = (ROOT / ".github/workflows/upstream-update.yml").read_text()
        for workflow in (validate_workflow, update_workflow):
            self.assertNotRegex(workflow, r"actions/(checkout|setup-python)@v")
            self.assertRegex(
                workflow,
                r"actions/(checkout|setup-python)@[0-9a-f]{40}",
            )
        self.assertIn("schedule:", update_workflow)
        self.assertIn("pull-requests: write", update_workflow)
        self.assertIn("gh pr create", update_workflow)
        self.assertIn("render_upstream_report.py", update_workflow)
        self.assertIn("docs/UPSTREAM_REPORT.md", update_workflow)
        self.assertNotIn("gh pr merge", update_workflow)
        self.assertNotIn("enable-auto-merge", update_workflow)

    def test_official_or_compatible_plugin_validator_passes(self) -> None:
        subprocess.run(
            [sys.executable, "scripts/run_plugin_validator.py", "plugins/pstack-codex"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_skill_directory_parity(self) -> None:
        source_skills = {path.name for path in (SOURCE / "skills").iterdir() if path.is_dir()}
        generated_skills = {path.name for path in (DESTINATION / "skills").iterdir() if path.is_dir()}
        self.assertEqual(generated_skills, source_skills)
        self.assertEqual(len(generated_skills), 45)

    def test_custom_agents_are_valid_toml(self) -> None:
        expected = {
            "comment-sicko.toml": ("comment-sicko", "read-only"),
            "poteto-agent.toml": ("poteto-agent", "workspace-write"),
        }
        for filename, (name, sandbox_mode) in expected.items():
            with self.subTest(filename=filename):
                config = tomllib.loads((DESTINATION / "agents" / filename).read_text())
                self.assertEqual(config["name"], name)
                self.assertEqual(config["sandbox_mode"], sandbox_mode)
                self.assertTrue(config["description"])
                self.assertTrue(config["developer_instructions"])

    def test_skill_invocation_metadata_is_codex_compatible(self) -> None:
        skill_dirs = [path for path in (DESTINATION / "skills").iterdir() if path.is_dir()]
        self.assertEqual(len(skill_dirs), 45)
        explicit_values = 0
        for skill_root in skill_dirs:
            contents = (skill_root / "SKILL.md").read_text(encoding="utf-8")
            match = re.search(r"^disable-model-invocation:\s*(\w+)\s*$", contents, re.MULTILINE)
            if match:
                explicit_values += 1
                self.assertEqual(match.group(1), "false", skill_root.name)
        self.assertEqual(explicit_values, 44)

    def test_internal_relative_markdown_links_resolve(self) -> None:
        broken: list[tuple[str, str]] = []
        for path in DESTINATION.rglob("*.md"):
            for raw in markdown_links(path):
                target = raw.strip().split("#", 1)[0].split("?", 1)[0].strip("<>")
                if not target or target.startswith(("http://", "https://", "mailto:", "tel:")):
                    continue
                if target in {"url", "URL"} or any(marker in target for marker in ("<", ">", "{", "}")):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    broken.append((str(path.relative_to(ROOT)), raw))
        self.assertEqual(broken, [])

    def test_generated_copy_changes_match_allowlist(self) -> None:
        rules = json.loads((ROOT / "config/compatibility-allowlist.json").read_text())
        source_skills = {path.name for path in (SOURCE / "skills").iterdir() if path.is_dir()}
        skipped = {Path(".cursor-plugin/plugin.json"), Path("agents/comment-sicko.md"), Path("agents/poteto-agent.md")}
        for source_path in sorted(SOURCE.rglob("*")):
            if not source_path.is_file():
                continue
            relative = source_path.relative_to(SOURCE)
            if relative in skipped:
                continue
            generated_path = DESTINATION / relative
            with self.subTest(path=relative):
                self.assertTrue(generated_path.is_file())
                if source_path.suffix.lower() not in TEXT_SUFFIXES:
                    self.assertEqual(generated_path.read_bytes(), source_path.read_bytes())
                    continue
                expected = allowlisted_transform(
                    source_path.read_text(encoding="utf-8"),
                    source_skills,
                    rules,
                    prose=source_path.suffix.lower() in {".md", ".mdc"},
                    relative_path=relative,
                )
                self.assertEqual(generated_path.read_text(encoding="utf-8"), expected)

    def test_generated_package_has_no_cursor_only_tokens(self) -> None:
        forbidden = (
            ".cursor",
            "Cursor",
            "/add-plugin",
            "subagent_type",
            "run_in_background",
            "AskQuestion",
            "generalPurpose",
            "claude-fable-5-1-thinking-max",
            "gpt-5.6-sol-max",
            "grok-4.6-fast-xhigh",
            "claude-opus-5-thinking-xhigh",
            "pstack-models.mdc",
            "/loop",
            "api2.cursor.sh",
        )
        for path in sorted(DESTINATION.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {
                ".json",
                ".md",
                ".mdc",
                ".toml",
                ".yaml",
                ".yml",
            }:
                continue
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=path.relative_to(ROOT), token=token):
                    self.assertNotIn(token, text)

    def test_generation_is_deterministic(self) -> None:
        before = snapshot(DESTINATION)
        subprocess.run(
            [sys.executable, "scripts/port.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(before, snapshot(DESTINATION))


if __name__ == "__main__":
    unittest.main()
