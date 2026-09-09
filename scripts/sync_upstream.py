#!/usr/bin/env python3
"""Verify or refresh the pinned upstream archive and regenerate the port."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "upstream.json"
VENDOR = ROOT / "vendor" / "cursor-plugins" / "pstack"
HASHES = ROOT / "config" / "hashes" / "upstream.sha256"


def tracked_files() -> list[Path]:
    return [path for path in sorted(VENDOR.rglob("*")) if path.is_file()]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def hash_lines() -> list[str]:
    return [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in tracked_files()]


def write_hashes() -> None:
    HASHES.parent.mkdir(parents=True, exist_ok=True)
    HASHES.write_text("\n".join(hash_lines()) + "\n", encoding="utf-8")


def check_hashes() -> None:
    if not HASHES.exists():
        raise SystemExit(f"missing hash manifest: {HASHES}")
    expected = HASHES.read_text(encoding="utf-8").splitlines()
    actual = hash_lines()
    if expected != actual:
        missing = sorted(set(expected) - set(actual))
        detail = "\n".join(
            [
                *(f"unexpected: {line}" for line in sorted(set(actual) - set(expected))),
                *(f"missing: {line}" for line in missing),
            ]
        )
        raise SystemExit(f"vendor hash mismatch; refresh hashes only after reviewing the pinned tree\n{detail}")
    print(f"verified {len(actual)} vendored files against {CONFIG.relative_to(ROOT)}")


def refresh(commit: str, repository: str) -> None:
    with tempfile.TemporaryDirectory(prefix="pstack-upstream-") as temporary:
        checkout = Path(temporary) / "checkout"
        subprocess.run(["git", "clone", "--filter=blob:none", repository, str(checkout)], check=True)
        subprocess.run(["git", "-C", str(checkout), "fetch", "--depth", "1", "origin", commit], check=True)
        archive = subprocess.run(
            ["git", "-C", str(checkout), "archive", "--format=tar", commit, "pstack"],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        archive_path = Path(temporary) / "pstack.tar"
        archive_path.write_bytes(archive)
        unpacked = Path(temporary) / "unpacked"
        unpacked.mkdir()
        subprocess.run(["tar", "-xf", str(archive_path), "-C", str(unpacked)], check=True)
        source = unpacked / "pstack"
        if not source.is_dir():
            raise SystemExit("the pinned archive did not contain pstack/")
        if VENDOR.exists():
            shutil.rmtree(VENDOR)
        shutil.copytree(source, VENDOR)
    write_hashes()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the vendored hash manifest")
    parser.add_argument("--write-hashes", action="store_true", help="write hashes for the current vendor tree")
    parser.add_argument("--refresh", action="store_true", help="clone and archive the configured pinned commit")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if args.refresh:
        refresh(config["commit"], config["repository"])
    if args.write_hashes:
        write_hashes()
    if args.check or not (args.write_hashes or args.refresh):
        check_hashes()
    if args.refresh:
        subprocess.run(["python3", str(ROOT / "scripts" / "port.py")], check=True)


if __name__ == "__main__":
    main()
