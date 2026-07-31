#!/usr/bin/env python3
"""Repo → platform bridge (Issue #6, option a).

Concatenate every validated bundles/**/*.json into the exact list shape the platform
seed loader consumes — the `SEED_COMMANDS` list of `{"manifest": {...}, "provenance": {...}}`
entries used by maestro-microservices `platform/office-backend/app/commands/seed_catalog.py`
(#232a). The platform vendors this output and `sync_seed_commands` publishes each entry as a
PUBLIC tier=community kind:command bundle via `upsert_command_bundle` at startup — installable
via the C4a catalog. There is NO store-service / /publish call.

Validates first (reuses validate_bundles); refuses to emit if any bundle is invalid.

Usage:
  python scripts/build_seed_module.py                 # -> dist/seed_commands.generated.json
  python scripts/build_seed_module.py --out PATH
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import validate_bundles as vb  # sibling module

REPO_ROOT = Path(__file__).resolve().parent.parent


def build(out_path: Path) -> int:
    total, failed = vb.validate_all()
    if failed:
        print(f"\nrefusing to build: {failed}/{total} bundles invalid.", file=sys.stderr)
        return 1
    entries = []
    for f in sorted((REPO_ROOT / "bundles").rglob("*.json")):
        b = json.loads(f.read_text())
        entries.append({"manifest": b["manifest"], "provenance": b["provenance"]})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
    try:
        shown = out_path.relative_to(REPO_ROOT)
    except ValueError:
        shown = out_path
    print(f"\nwrote {len(entries)} seed commands -> {shown}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the platform seed_commands JSON from bundles/.")
    ap.add_argument("--out", default=str(REPO_ROOT / "dist" / "seed_commands.generated.json"),
                    help="output path (default: dist/seed_commands.generated.json)")
    args = ap.parse_args()
    return build(Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
