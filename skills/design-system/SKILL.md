---
name: design-system
description: "Creates, extracts, audits, documents and extends a reusable design system kept as files that import into Claude Design (format v3), with a DESIGN.md entry file any agent can read and an offline viewer.html. Use when building a design system or brand kit from brand material or a codebase, auditing tokens and components for naming drift, hardcoded values or missing states, documenting a component's variants, states and accessibility, or designing a new component, pattern or token that fits the existing system. Not for designing a whole new page or screen (use design-routing), picking only a palette or font, or generating brand-kit images."
---

# Design System

One folder, `design-system/`, that Claude Design imports (format v3) and any agent can read: `tokens.json` is the data root, `DESIGN.md` the file agents open first, `viewer.html` a generated offline page. A run yields a draft, an as-is system, a report or a delta; canonical files change only after promotion (owner confirms, reviewer checks).

## Choose a mode

| Mode | Use when | Writes |
|---|---|---|
| `create` | brand material or chosen references exist, or nothing does | a `draft` package; no source means profile `minimal` |
| `extract` | a codebase already holds the system | an `as-is` system with inventory, trace, drift; source untouched |
| `audit` | naming drift, hardcoded values, components missing states or docs | a read-only report in six parts |
| `document` | one component needs a README | `components/<Comp>/README.md`, `preview.html` if it renders |
| `extend` | a component, pattern or token must fit the system | a proposal with delta and migration, promotion `pending` |

Touching `tokens.json` in any mode: read [token-contract.md](references/token-contract.md) first. A design-tool MCP server on the host is a traced source; call it by its full name, `Server:tool`.

## What every run returns

Answer in this order: `mode` → `baseline/scope/output` → `owner/status` → `canonical map` → `inventory/trace` → `drift/decisions` → `evidence/coverage/unknown` → `adapters` → `next step`.

- Status is `draft`, `pending` or `as-is`, never `approved`; only the owner approves. An owner you cannot name is `unknown`.
- Name the output folder before writing. Nobody gave one: hand the proposal over in chat and report `output: not-written`, since a guessed place can overwrite a canonical file.
- Label values `declared` (read in a file), `computed` (measured in a render), `inferred` or `unverified`.
- Coverage needs a denominator inside the scope you read ("14 of 40 components"); a sample says nothing about the rest.
- Report `adapters: written`, `adapters: skipped` or `adapters: not-requested`.
- Ask only when the next step cannot be undone, changes the scope, or needs input only the user has.

## create

1. Copy `templates/brand-v3/` (start at [design-system.json](templates/brand-v3/design-system.json)) to the target as `design-system/`; replace every placeholder name, value and usage.
2. No brand source: use profile `minimal` (6 to 10 colours in one theme, 5 to 7 text styles, 4 spacing and 3 radius tokens, one-paragraph README, only `Cover`) and say it is a starter system, since inventing a brand would read as a decision.
3. Generate, then check, with these two commands in this order:

```
python scripts/build-design-system.py --package <dir> --design-md --viewer
python scripts/verify-design-system.py --package <dir>
```

4. Report `adapters: not-requested` unless the user asked for harness files.

## extract

Declare repo, commit and dirty state, allowlist, surface and run folder before reading. Follow [source-code-audit.md](references/source-code-audit.md) and fill [audit-report.md](templates/audit-report.md). Result: an `as-is` system, an inventory, a trace `path:line/symbol → token or alias → component → route`, and drift entries (domain → source A → source B → impact → proposal → owner decision). Never run the repo's scripts, install packages or send source out: an allowlist grants reading, not running.

## audit

Read-only. Fill the six parts of [audit-report.md](templates/audit-report.md): naming, token coverage and hardcoded values, component completeness, drift between system and code, verifier result, at most three priorities. Score only when the denominator lies inside what you read.

## document

Write `components/<Comp>/README.md` from [component-v3/README.md](templates/component-v3/README.md); its first line is the summary the viewer and Claude Design show, so make it one sentence. Add `preview.html` ([template](templates/component-v3/preview.html)) only for a component that renders from real source. Profile `full` also needs `components.<Comp>.source` in `canonical-map.json`. Then build with `--viewer` and run the verifier.

## extend

Fill the seven parts of [extend-proposal.md](templates/extend-proposal.md). Reuse existing tokens; one you must add is marked `candidate`, because the owner decides whether it exists. After a token reaches `tokens.json`, build with `--design-md --viewer`, then verify, so nothing goes stale. Migration notes and CHANGELOG entries are appended, never rewritten.

## Package format

- [system-contract.md](references/system-contract.md) — tree, error codes, size caps; read when building or changing the tree.
- [token-contract.md](references/token-contract.md) — v3 grammar and limits; read when touching `tokens.json`.
- [design-md-spec.md](references/design-md-spec.md) — generated front matter, eight sections; read when writing `DESIGN.md` ([template](templates/DESIGN.md)).
- [source-code-audit.md](references/source-code-audit.md) — read before `extract` or `audit`.

## Boundaries

- `design-routing` owns UI briefs, shortlists, wireframes, direction choices, builds and motion. This skill takes its distilled handoff and does not call it back; a new page or screen with no settled direction goes there.
- New palette: take candidates from the router's colour protocol; token authority stays here.
- A system that already owns CSS, TypeScript or Figma tokens keeps that authority; record the winner under `decisions` in `canonical-map.json`.

## Gotchas

- `manifest.json`, `tokens.css`, `api/**`, `migration-map.json`, `publish-progress.json`, `archived/**` come from the Claude Design page; a hand-written copy is `generated_file_present` and gets overwritten.
- The page ignores DTCG files, so `tokens.json` in the v3 list grammar is the source and DTCG is only derived from it.
- v3 has no `motion` family (`unsupported_family`); keep motion in prose.
- The page turns a component folder name into code, so it must be an ASCII JavaScript identifier.
- Every `*.md` outside `components/` and `archived/` except the root `README.md` becomes a brand-book section, at most 24; loose notes show up in the page.
- No `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `package.json`, lockfile or dot-folder in the package, and no root `index.html`: the page refuses them. Harness files go in the parent folder; the offline page is `viewer.html`.
- `viewer.html` prints cleaned README and preview text and does not render components live; open `preview.html` or Claude Design for that.
- The `DESIGN.md` front matter and `viewer.html` are derived: edit `tokens.json`, then build. A hand edit shows as `design_md_stale` or `viewer_stale`.
- `components/Cover/` holds only `preview.html`; a README beside it is `cover_not_bare` and the system loses its cover.
- Never invent a logo: without a licensed one, use a text wordmark and say why in `assets/<Group>/README.md`.
- `WARN contrast_unchecked` is not a pass; declare pairs under `checks.contrast` in `canonical-map.json`, then run again.
- A bare `input_error: <ExceptionName>` comes from inside a generator, not from your input; report it with the package that reproduces it.

## Commands

Run from the plugin root with Python 3.12 or later; nothing is installed and nothing touches the network.

```
python scripts/verify-design-system.py                 # this skill's own files
python scripts/verify-design-system.py --package <dir> [--profile full|minimal]
python scripts/build-design-system.py --package <dir> --design-md --viewer [--check]
```

`--check` writes nothing and exits 1 when a generated file is out of date. Exit 0 passes (warnings allowed), 1 means errors; errors go to stderr as `<code>: <path>[: detail]`, warnings to stdout as `WARN <code>: ...`. The PASS line lists what is not checked (live render, browser display, real import): a pass is structural only. Other flags: `--help`.
