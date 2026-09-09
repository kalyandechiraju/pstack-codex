#!/usr/bin/env python3
"""Run the official validator when present, then the dependency-free fallback."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OFFICIAL = Path(
    "/Users/kalyandechiraju/Developer/CodexRuntime/skills/.system/plugin-creator/scripts/validate_plugin.py"
)
FALLBACK = ROOT / "scripts" / "validate_codex_plugin.py"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_plugin_validator.py PLUGIN_PATH")
    plugin_path = sys.argv[1]
    official = Path(os.environ.get("CODEX_OFFICIAL_VALIDATOR", str(DEFAULT_OFFICIAL)))
    if official.is_file():
        print(f"running official validator: {official}")
        subprocess.run([sys.executable, str(official), plugin_path], check=True)
    else:
        print("official validator unavailable; using the checked-in compatible validator")
    subprocess.run([sys.executable, str(FALLBACK), plugin_path], check=True)


if __name__ == "__main__":
    main()
