---
name: design-system
description: "Creates, extracts, audits, documents and extends a reusable design system kept as files that import into Claude Design (format v3), with a DESIGN.md entry file any agent can read and an offline viewer.html. Use when building a design system or brand kit from brand material or a codebase, auditing tokens and components for naming drift, hardcoded values or missing states, documenting a component's variants, states and accessibility, or designing a new component, pattern or token that fits the existing system. Not for designing a whole new page or screen (use design-routing), picking only a palette or font, or generating brand-kit images."
---

# Design System

One folder, `design-system/`, that Claude Design imports (format v3) and any agent can read: `tokens.json` is the data root, `DESIGN.md` the file agents open first, `viewer.html` a generated offline page. A run yields a draft, an as-is system, a report or a delta; canonical files change only after promotion (owner confirms, reviewer checks).

## Choose a mode

| Mode | Use when | Needs | Writes | Read first |
|---|---|---|---|---|
| `create` | brand material or references exist, or nothing does | goal, surface, sources and your right to use them, target folder | a `draft` package; no source: `minimal` | `templates/brand-v3/`, `system-contract.md`, `token-contract.md`, `design-md-spec.md` |
| `extract` | a codebase holds the system | repo, commit, allowlist, surface, run folder | `as-is` system, inventory, trace, drift | `source-code-audit.md`, `system-contract.md`, `audit-report.md` |
| `audit` | naming drift, hardcoded values, components missing states | the system and the source in scope | read-only six-part report | `source-code-audit.md`, `audit-report.md` |
| `document` | one component needs a README | its source, story or spec | `components/<Comp>/README.md`, `preview.html` | `templates/component-v3/`, `system-contract.md` (Conditional entries) |
| `extend` | a component, pattern or token must fit | the system and the requested change | proposal with delta, migration, promotion `pending` | `extend-proposal.md`, `system-contract.md` |

Touching `tokens.json`: read [token-contract.md](references/token-contract.md) first. A host design-tool MCP server is a traced source (`Server:tool`).

## What every run returns

In this order: `mode`, `baseline/scope/output`, `owner/status`, `canonical map`, `inventory/trace`, `drift/decisions`, `evidence/coverage/unknown`, `adapters`, `next step`.

- Status is `draft`, `pending` or `as-is`, never `approved`; only the owner approves. An unnamed owner is `unknown`.
- No output folder given: hand the proposal over in chat and report `output: not-written`, since a guessed place can overwrite a canonical file.
- Label values `declared` (read in a file), `computed` (measured), `inferred` or `unverified`. Coverage needs a denominator inside the scope you read ("14 of 40 components"); a sample says nothing about the rest.
- Report `adapters: written`, `adapters: skipped` or `adapters: not-requested`.
- Ask only when the next step cannot be undone, changes the scope or needs input only the user has.

## create

1. Ask which sources the user chose, whether each may be used, and where the folder goes.
2. Copy `templates/brand-v3/` (start at [design-system.json](templates/brand-v3/design-system.json)) to the target as `design-system/` and replace every placeholder name, value and usage. The copy is profile `minimal`.
3. No brand source: stay on `minimal` (one theme, one-paragraph README, only `Cover`) and say it is a starter, since an invented brand would read as a decision. With brand sources, or before the first component, set `profile` to `full` in `canonical-map.json` and give the README its three headings.
4. `<plugin>` is the folder that holds `scripts/`, two folders above this file; pass `<dir>` as an absolute path. Generate, then check:

```
python <plugin>/scripts/build-design-system.py --package <dir> --design-md --viewer
python <plugin>/scripts/verify-design-system.py --package <dir>
```

5. Only if the user asks for harness files, add `--adapters <root>` (the folder that holds `design-system/`) to the build line. It fills [AGENTS.md.tmpl](templates/agent-adapters/AGENTS.md.tmpl) and two siblings and never overwrites: an existing file prints a proposal and counts as skipped. Report `adapters: written`, `skipped` or `not-requested`.

## extract

Declare the inputs above and the dirty state before reading; follow [source-code-audit.md](references/source-code-audit.md) and fill [audit-report.md](templates/audit-report.md). Result: an `as-is` system, an inventory, a trace `path:line → token → component → route`, a drift entry per conflict. An allowlist grants reading, not running: no repo scripts, installs or sending source out.

## audit

Read-only. Fill the six parts of [audit-report.md](templates/audit-report.md), ending with at most three priorities. Score only when the denominator lies inside what you read.

## document

Write `components/<Comp>/README.md` from [component-v3/README.md](templates/component-v3/README.md); its first line is the one-sentence summary the viewer and Claude Design show. Profile `full` needs `preview.html` ([template](templates/component-v3/preview.html)) for every component; with no renderable source keep its `@dsCard` marker card and say so. A `minimal` package holds only `Cover`: set `profile` to `full` in `canonical-map.json` first (the README's three headings, a `components.<Comp>.source` per component). Then build with `--viewer` and verify.

## extend

Fill the seven parts of [extend-proposal.md](templates/extend-proposal.md). Reuse existing tokens; one you must add is marked `candidate`, because the owner decides whether it exists. After a token reaches `tokens.json`, build with `--design-md --viewer`, then verify, so nothing goes stale. Migration notes and CHANGELOG entries are only appended.

## Package format

Contracts: [system-contract.md](references/system-contract.md) (tree, codes, caps), [token-contract.md](references/token-contract.md), [design-md-spec.md](references/design-md-spec.md) ([template](templates/DESIGN.md)), [source-code-audit.md](references/source-code-audit.md). `agents/openai.yaml` is the Codex adapter.

## Boundaries

- `design-routing` owns UI briefs, shortlists, wireframes, direction choices, builds and motion, and is not called back from here; a new page or screen with no settled direction goes there. Palette candidates come from its colour protocol; token authority stays here.
- A system that already owns CSS, TypeScript or Figma tokens keeps that authority (record it under `decisions`).

## Gotchas

- The Claude Design page generates `manifest.json`, `tokens.css`, `api/**` and more (list in system-contract.md) and overwrites a hand-written copy (`generated_file_present`).
- The page ignores DTCG files and has no `motion` family (`unsupported_family`): `tokens.json` in the v3 list grammar is the source, DTCG only derived, motion stays in prose.
- Component folder names become code: ASCII JavaScript identifiers only.
- Every `*.md` outside `components/` and `archived/` (root `README.md` aside) becomes a brand-book section, at most 24.
- The page refuses `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `package.json`, lockfiles, dot-folders and a root `index.html`; harness files go in the parent folder.
- The `DESIGN.md` front matter and `viewer.html` are derived: edit `tokens.json`, then build, or the verifier says `design_md_stale` or `viewer_stale`. The viewer prints cleaned text and does not render components; open `preview.html` for that.
- `components/Cover/` holds only `preview.html`; a sibling is `cover_not_bare` and the system loses its cover.
- Never invent a logo, because the owner decides the mark and rights may not allow a copy; use a text wordmark and say why in `assets/<Group>/README.md`.
- `WARN contrast_unchecked` is not a pass: declare pairs under `checks.contrast`, then run again.
- A bare `input_error: <ExceptionName>` is a generator fault, not your input; keep the package that reproduces it.

## Commands

Python 3.12+, no install, no network; `<plugin>` as in `create`.

```
python <plugin>/scripts/verify-design-system.py
```

Alone it checks this skill's own files; with `--package <dir>`, a package (`--profile full|minimal` overrides the map). The build line takes `--check`: it writes nothing and exits 1 when a generated file is stale. Errors print as `<code>: <path>[: detail]` and exit 1. A PASS is structural only: live render, browser display and real import stay unchecked.
