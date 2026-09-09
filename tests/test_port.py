from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor" / "cursor-plugins" / "pstack"
DESTINATION = ROOT / "plugins" / "pstack-codex"


def snapshot(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


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

    def test_manifest_is_codex_shaped(self) -> None:
        manifest = json.loads((DESTINATION / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "pstack-codex")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("agents", manifest)
        self.assertEqual(manifest["version"], "0.14.8")

    def test_marketplace_points_at_generated_plugin(self) -> None:
        marketplace = json.loads((ROOT / "marketplace.json").read_text())
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/pstack-codex")

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
            if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
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
