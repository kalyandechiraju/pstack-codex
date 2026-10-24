#!/usr/bin/env python3
"""Fail when an upstream Cursor-only name is unhandled by the port.

Upstream's harness generator keeps a TERMS list of every Cursor name its skills
use, and its CI forces that list to stay complete. This check reads the vendored
copy so a sync surfaces new names instead of shipping them untranslated.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TERMS_SOURCE = ROOT / "vendor" / "cursor-plugins" / "scripts" / "generate-pstack-harness-trees.mjs"
CONFIG = ROOT / "config" / "cursor-terms.json"
GENERATED = ROOT / "plugins" / "pstack-codex"
TERM = re.compile(r'\{ key: ("(?:[^"\\]|\\.)*"), re: /((?:[^/\\\n]|\\.)+)/([a-z]*) \}')
STATUSES = {"translated", "kept", "gap"}


def upstream_terms() -> dict[str, re.Pattern[str]]:
    source = TERMS_SOURCE.read_text(encoding="utf-8")
    start = source.find("const TERMS = [")
    end = source.find("];", start)
    if start == -1 or end == -1:
        raise SystemExit(f"TERMS list not found in {TERMS_SOURCE.relative_to(ROOT)}")
    block = source[start:end]
    terms = {
        json.loads(key): re.compile(pattern, re.IGNORECASE if "i" in flags else 0)
        for key, pattern, flags in TERM.findall(block)
    }
    if len(terms) != block.count("key:"):
        raise SystemExit("could not parse every TERMS entry; update check_cursor_terms.py")
    return terms


def check() -> tuple[list[str], list[str]]:
    terms = upstream_terms()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))["terms"]
    errors: list[str] = []
    gaps: list[str] = []
    for key in sorted(set(terms) - set(config)):
        errors.append(f"new upstream Cursor name {key!r}: add a rewrite and an entry in config/cursor-terms.json")
    for key in sorted(set(config) - set(terms)):
        errors.append(f"config/cursor-terms.json lists {key!r}, which upstream TERMS no longer has")
    for key, entry in sorted(config.items()):
        if entry.get("status") not in STATUSES:
            errors.append(f"{key!r} has status {entry.get('status')!r}; use one of {sorted(STATUSES)}")
    documents = sorted(GENERATED.rglob("*.md"))
    for key, pattern in sorted(terms.items()):
        status = config.get(key, {}).get("status")
        if status not in {"translated", "gap"}:
            continue
        hits = sorted(
            {
                path.relative_to(GENERATED).as_posix()
                for path in documents
                if pattern.search(path.read_text(encoding="utf-8"))
            }
        )
        if not hits:
            continue
        if status == "translated":
            errors.append(f"{key!r} is marked translated but appears in {', '.join(hits)}")
        else:
            gaps.append(f"{key!r}: {', '.join(hits)}")
    return errors, gaps


def main() -> None:
    errors, gaps = check()
    for gap in gaps:
        print(f"known gap {gap}")
    if errors:
        print("Cursor name coverage failed:")
        for item in errors:
            print(f"- {item}")
        sys.exit(1)
    print("Cursor name coverage passed")


if __name__ == "__main__":
    main()
