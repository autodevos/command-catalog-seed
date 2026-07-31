# command-catalog-seed

Curated **slash-commands** for the AutoDevOS Command Catalog. Each bundle is one
command; the platform publishes them as **public, installable** catalog commands
that any org can add to its palette.

This repo is the **source-of-truth for seed content** (#232b). The platform code
lives in `autodevos/maestro-microservices` (Slash Command Catalog #165: C1–C4a).

## What a bundle is

One command = one JSON file under `bundles/<ecosystem>/`, shaped **exactly** like
the platform's seed manifest (see `schema/command_manifest.schema.json`):

```json
{
  "manifest": {
    "name": "review-diff",
    "description": "Review the current diff for bugs, security, and style",
    "argHint": "[focus]",
    "behavior": { "kind": "prompt", "promptTemplate": "…the command's instruction text…" },
    "toolScope": "*",
    "actionSafety": "read-only"
  },
  "provenance": {
    "source": "https://github.com/owner/repo/path (or \"original\")",
    "license": "CC0-1.0",
    "fetchedAt": "2026-07-31",
    "notes": "origin format / attribution"
  }
}
```

- **`manifest`** matches the shipped command manifest 1:1 (`name`, `description`,
  optional `argHint`, `behavior`, `toolScope`, `actionSafety`). Seed commands use
  `behavior.kind: "prompt"` — the whole instruction/rule text goes in
  `promptTemplate`.
- **`name`** is a slug and must be unique and **not** one of the reserved
  first-party names: `roadmap`, `grill-me`, `migrate`.
- **`provenance`** is the git-committed license record (SPDX in `license`). Only
  permissively-licensed sources (CC0/MIT/Apache-2.0) or original content.

## How it reaches the catalog

The platform's `sync_seed_commands` loader
(`platform/office-backend/app/commands/seed_catalog.py`) publishes each bundle's
`manifest` via `upsert_command_bundle` as a **PUBLIC, `tier="community"`,
`kind:command`** bundle at startup. Because it's `community` (not `first_party`),
it appears in the **C4a catalog** (`GET /commands/catalog`, the "Browse catalog"
page) as **installable** — it does not auto-appear in anyone's palette until an
org installs it. Commands are config-only (no artifact); install is C4a's
`POST /bundles/{id}/install`.

```
bundles/**/*.json  →  validate (schema)  →  seed loader (upsert_command_bundle, tier=community)
                   →  GET /commands/catalog  →  install per-org  →  palette
```

## Validation & the platform bridge

- **Validate** every bundle (schema + rules: `behavior.kind=="prompt"` with a
  non-empty `promptTemplate`, `actionSafety` enum, slug + unique + non-reserved
  `name`, `provenance.source`/`license`):
  ```bash
  python scripts/validate_bundles.py
  ```
  CI (`.github/workflows/validate.yml`) runs this on every PR + push to `master`.
- **Build the platform seed module** (repo → platform bridge): concatenate the
  validated bundles into the exact `SEED_COMMANDS` list shape
  (`[{manifest, provenance}, …]`) that the platform's
  `app/commands/seed_catalog.py` consumes:
  ```bash
  python scripts/build_seed_module.py   # -> dist/seed_commands.generated.json
  ```
  The platform vendors that output and `sync_seed_commands` publishes each entry
  as a PUBLIC `tier=community` `kind:command` bundle at startup. (Wiring
  `sync_seed_commands` to read the vendored file is a small follow-up PR on the
  platform side.)

## Layout

```
schema/command_manifest.schema.json   the bundle JSON Schema (source of truth)
bundles/cursor-rules/                  Cursor .mdc rules → commands   (Issue #2)
bundles/claude-commands/               Claude Code commands/skills     (Issue #3)
bundles/windsurf-rules/                Windsurf rules                  (Issue #4)
bundles/copilot-instructions/          Copilot instructions            (Issue #4)
bundles/aider-conventions/             Aider conventions               (Issue #4)
bundles/gemini-skills/                 Gemini/agent SKILL.md           (Issue #5)
scripts/                               validator + repo→platform bridge (Issue #6)
NOTICE.md                              third-party attribution roll-up
```

## Contributing a command

1. Pick or create the right `bundles/<ecosystem>/` dir.
2. Add `<name>.json` in the schema shape above. Keep extracted text **verbatim**
   in `behavior.promptTemplate`; write a short `description`; choose
   `actionSafety` (`read-only` unless the command tells the agent to make
   changes).
3. Fill `provenance` (permissive source + SPDX license + `fetchedAt`), and add a
   row to `NOTICE.md`.
4. Ensure the name is unique and not reserved; validate against the schema.
5. Open a PR — CI validates every bundle (Issue #6).

## License

Repo code + schema: MIT (`LICENSE`). Embedded third-party text: per-bundle,
tracked in `NOTICE.md` — permissive licenses only.
