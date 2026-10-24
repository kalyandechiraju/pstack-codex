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
SOURCE_MANIFEST = VENDOR / ".cursor-plugin" / "plugin.json"
# Upstream's harness generator holds its maintained list of Cursor-only names.
# check_cursor_terms.py reads it, so new upstream names fail the sync.
TERMS_SOURCE = "scripts/generate-pstack-harness-trees.mjs"
TERMS_VENDOR = ROOT / "vendor" / "cursor-plugins" / TERMS_SOURCE


def tracked_files() -> list[Path]:
    return [path for path in sorted(VENDOR.rglob("*")) if path.is_file()] + [TERMS_VENDOR]


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


def source_version() -> str:
    if not SOURCE_MANIFEST.is_file():
        raise SystemExit(f"missing upstream manifest: {SOURCE_MANIFEST}")
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit(f"upstream manifest has no usable version: {SOURCE_MANIFEST}")
    return version


def check_manifest_version(config: dict[str, object]) -> None:
    expected = source_version()
    actual = config.get("version")
    if actual != expected:
        raise SystemExit(
            f"upstream version mismatch: config/upstream.json has {actual!r}, "
            f"but the vendored manifest has {expected!r}"
        )
    print(f"verified upstream version {expected}")


def refresh(config: dict[str, object]) -> None:
    commit = str(config["commit"])
    repository = str(config["repository"])
    with tempfile.TemporaryDirectory(prefix="pstack-upstream-") as temporary:
        checkout = Path(temporary) / "checkout"
        subprocess.run(["git", "clone", "--filter=blob:none", repository, str(checkout)], check=True)
        subprocess.run(["git", "-C", str(checkout), "fetch", "--depth", "1", "origin", commit], check=True)
        archive = subprocess.run(
            ["git", "-C", str(checkout), "archive", "--format=tar", commit, "pstack", TERMS_SOURCE],
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
        TERMS_VENDOR.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(unpacked / TERMS_SOURCE, TERMS_VENDOR)
    config["version"] = source_version()
    CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    write_hashes()


def latest_commit(repository: str, branch: str) -> str:
    result = subprocess.run(
        ["git", "ls-remote", repository, f"refs/heads/{branch}"],
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.split()[0] if result.stdout.split() else ""
    if not commit:
        raise SystemExit(f"could not resolve {repository} branch {branch!r}")
    return commit


def write_pinned_config(config: dict[str, object], commit: str) -> None:
    repository = str(config["repository"])
    source_root = repository[:-4] if repository.endswith(".git") else repository
    config["commit"] = commit
    config["source"] = f"{source_root}/tree/{commit}/pstack"
    CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the vendored hash manifest")
    parser.add_argument("--write-hashes", action="store_true", help="write hashes for the current vendor tree")
    parser.add_argument("--refresh", action="store_true", help="clone and archive the configured pinned commit")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="resolve the configured branch head, update the pin, refresh, and regenerate",
    )
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if args.latest and not args.refresh:
        args.refresh = True
    if args.latest:
        commit = latest_commit(config["repository"], config.get("branch", "main"))
        write_pinned_config(config, commit)
    if args.refresh:
        refresh(config)
    if args.write_hashes:
        write_hashes()
    if args.check or not (args.write_hashes or args.refresh):
        check_hashes()
        check_manifest_version(config)
    if args.refresh:
        subprocess.run(["python3", str(ROOT / "scripts" / "port.py")], check=True)
        subprocess.run(["python3", str(ROOT / "scripts" / "check_cursor_terms.py")], check=True)


if __name__ == "__main__":
    main()
