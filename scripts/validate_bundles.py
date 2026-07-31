#!/usr/bin/env python3
"""Validate every command-catalog-seed bundle against the schema + cross-cutting rules.

Each bundle (bundles/**/*.json) must match schema/command_manifest.schema.json AND:
  - manifest.behavior.kind == "prompt" with a non-empty promptTemplate
  - manifest.actionSafety in {read-only, writes}
  - manifest.name is a slug ([a-z0-9] groups joined by '-'), unique across the repo,
    and NOT a reserved first-party name (roadmap / grill-me / migrate)
  - provenance.source and provenance.license (SPDX) are present

This is the same validation the platform seed loader expects (maestro-microservices
#165 C1-C4a / #232a): the manifest is published as a PUBLIC tier=community kind:command
bundle via upsert_command_bundle. There is no store-service / /publish endpoint.

Exit 0 if all bundles pass, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RESERVED_NAMES = {"roadmap", "grill-me", "migrate"}  # first-party, reserved/unshadowable
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "command_manifest.schema.json"
BUNDLES_DIR = REPO_ROOT / "bundles"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _schema_validate(bundle: dict, schema: dict) -> list[str]:
    """Validate against the JSON Schema. Uses jsonschema if available; otherwise a
    minimal structural fallback so the script runs with only the stdlib."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        m = bundle.get("manifest")
        p = bundle.get("provenance")
        if not isinstance(m, dict) or not isinstance(p, dict):
            return ["missing 'manifest' or 'provenance' object"]
        errs = []
        for k in ("name", "description", "behavior", "toolScope", "actionSafety"):
            if k not in m:
                errs.append(f"manifest missing '{k}'")
        return errs
    v = jsonschema.Draft7Validator(schema)
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
            for e in v.iter_errors(bundle)]


def _rule_checks(bundle: dict, seen: dict[str, str], rel: str) -> list[str]:
    errs: list[str] = []
    m = bundle.get("manifest", {})
    name = m.get("name", "")
    beh = m.get("behavior", {}) or {}
    if beh.get("kind") != "prompt":
        errs.append("behavior.kind must be 'prompt'")
    if not str(beh.get("promptTemplate", "")).strip():
        errs.append("behavior.promptTemplate must be non-empty")
    if m.get("actionSafety") not in ("read-only", "writes"):
        errs.append("actionSafety must be 'read-only' or 'writes'")
    if not SLUG_RE.match(str(name)):
        errs.append(f"name '{name}' is not a valid slug ([a-z0-9-])")
    if name in RESERVED_NAMES:
        errs.append(f"name '{name}' is a reserved first-party command name")
    if name in seen:
        errs.append(f"duplicate name '{name}' (also in {seen[name]})")
    prov = bundle.get("provenance", {}) or {}
    if not str(prov.get("source", "")).strip():
        errs.append("provenance.source is required")
    if not str(prov.get("license", "")).strip():
        errs.append("provenance.license (SPDX) is required")
    if name and not errs:
        seen[name] = rel
    return errs


def validate_all() -> tuple[int, int]:
    schema = _load_schema()
    files = sorted(BUNDLES_DIR.rglob("*.json"))
    seen: dict[str, str] = {}
    failed = 0
    for f in files:
        rel = str(f.relative_to(REPO_ROOT))
        try:
            bundle = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            print(f"FAIL  {rel}\n      invalid JSON: {e}")
            failed += 1
            continue
        errs = _schema_validate(bundle, schema) + _rule_checks(bundle, seen, rel)
        if errs:
            failed += 1
            print(f"FAIL  {rel}")
            for e in errs:
                print(f"      - {e}")
        else:
            print(f"ok    {rel}")
    return len(files), failed


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate command-catalog-seed bundles.")
    ap.parse_args()
    total, failed = validate_all()
    print(f"\n{total - failed}/{total} bundles valid.")
    if total == 0:
        print("WARNING: no bundles found under bundles/.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
