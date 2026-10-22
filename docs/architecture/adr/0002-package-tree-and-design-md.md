# 0002. Ship one package tree with DESIGN.md as the agent entry file and generated front matter

Status: accepted · Sprint: SPR-32 · Related: ADR 0001, PLAN section "Hợp đồng bàn giao" (items 1, 2, 7), SPEC FR5, FR10, FR12
Format pin: Claude Design `v:3` and the Design Markdown spec `version: alpha`, both read on 2026-10-22

## Context

The owner asked on 2026-10-22 for one standard folder per design system, with a Design Markdown file as the root that any agent can read. Constraints found while checking that wish against the two consumers:

- Claude Design opens `README.md` first (the brand book), reads `tokens.json` as the data source (ADR 0001), and refuses a set of paths inside the package: `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `package.json` and other toolchain manifests at any depth, dot-prefixed segments, `node_modules`, lockfiles, 8.3 names, and `index.html` at the package root. Any other Markdown file outside `components/` and `archived/` becomes a further brand-book section, at most 24 of them. Full side-by-side review: TK3 evidence (kept outside this repository).
- Google Labs' Design Markdown spec (`alpha`, Apache-2.0) defines a YAML front matter with token groups (`colors`, `typography`, `rounded`, `spacing`, …) and eight `##` sections in a fixed order. It is a reading format for coding agents, not a token store: it has no themes and no `usage`.
- `tokens.json` must stay the only data source (`Q2`). The verifier and generator are stdlib-only, so there is no YAML parser; whatever is generated must be checkable by regenerating and checking string equality.
- Agent harnesses load `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` from the folder they work in. Those files cannot live inside the package (refused) and would be loaded as rules if they sat inside the plugin under their real names.

Affected: the `design-system` skill (five modes), `verify-design-system.py`, `build-design-system.py`, the brand template, the fixture, and every project that adopts a package.

## Options

| Option | How | Trade-off | When it fits |
|---|---|---|---|
| A. `DESIGN.md` is a short prose contract | Hand-written reading order, owner, status, canonical pointers; no front matter | Cheap, cannot drift from tokens because it carries none; but agents outside Claude Design still have to parse `tokens.json` themselves and nothing is lintable | Teams that never use a Design Markdown-aware agent |
| B. `DESIGN.md` follows the Google `alpha` shape; front matter generated one-way from `tokens.json`; body of eight sections written by hand; Overview carries the contract | Agents get tokens and prose in one file; staleness is detectable by regenerating; body stays human-owned | Front matter is lossy (first theme only, no `usage`); the Google spec is alpha and may move | The package must serve Claude Design and other agents at once |
| C. Front matter is the data source, `tokens.json` generated from it | One hand-edited file | Breaks `Q2`; loses themes, `usage`, fonts and the family caps Claude Design needs | Only if Claude Design were dropped as a consumer |
| Keep the status quo | The branch's `DESIGN.md` prose plus `manifest.json` | No generator work; but no shared entry file for agents and a manifest name that collides with the file Claude Design generates | Not viable: the manifest name alone forces a change |

## Decision

Option B, with the tree below as the package contract. Chosen because it is the only option that satisfies both consumers and `Q2` at the same time: Claude Design keeps `README.md` + `tokens.json`, other agents get `DESIGN.md`, and one generator keeps the two in step.

- **Tree**: the canonical tree is reproduced verbatim in `skills/design-system/references/system-contract.md` (section "Package tree"). Root files: `DESIGN.md`, `README.md`, `tokens.json`, `design-system.json`, `canonical-map.json`, `viewer.html` (all required); `provenance.md`, `CHANGELOG.md`, `components/`, `assets/`, `fonts/`, `patterns/`, `surfaces/` (conditional or optional). Nothing hand-written may use a name the page generates (`manifest.json`, `tokens.css`, `api/**`, `migration-map.json`, `publish-progress.json`, `archived/**`).
- **`canonical-map.json`** replaces the branch's `manifest.json` (same schema, new name) because Claude Design regenerates `manifest.json` on every build.
- **`viewer.html`** replaces `index.html` as the offline viewer, because `index.html` at the root is refused while any other file is kept without UI (≤ 512 000 bytes).
- **Two roots, two roles**: the *reading* root is `DESIGN.md` for agents and `README.md` for Claude Design; the *data* root is `tokens.json`. `DESIGN.md` Overview states the reading order for both harnesses, owner, version, status and the canonical file per domain. The body names tokens and never copies values.
- **Front matter** is emitted by `render_front_matter` from the first theme, in the fixed key order `version`, `name`, `colors`, `typography`, `rounded`, `spacing`; the mapping is specified in `skills/design-system/references/design-md-spec.md`. The verifier regenerates it and checks string equality (`design_md_stale`).
- **Cover folder is bare**: `components/Cover/` holds only `preview.html`; any sibling file demotes the cover to an ordinary component on the page, so the verifier reports `cover_not_bare`.
- **Harness adapters live in the parent folder** of the package (`AGENTS.md`, `CLAUDE.md` = `@AGENTS.md`, `GEMINI.md`), generated by `build-design-system.py --adapters <root>` from templates that carry a `.tmpl` suffix inside the plugin. Inside the package they are `refused_path`.

## Consequences

- Easier: one folder works for Claude Design import and for any agent that reads Markdown; a stale front matter is a verifier error, not a surprise; the template and fixture verify in place because `canonical-map.json` paths of kind `file` are package-relative.
- Harder: every token edit must be followed by `build-design-system.py --design-md --viewer` (the `extend` mode does this; `--check` catches omissions in CI); `DESIGN.md` itself spends one of the 24 brand-book section slots on the Claude Design page, as do `provenance.md`, `CHANGELOG.md`, `patterns/**`, `surfaces/**` and `assets/<Group>/README.md`; the front matter may be displayed as text on that page (not measured).
- Fixed from now on: the eight section names and their order, the six emitted front matter keys, and the rule that the body never carries values. Google's own lint is optional QA outside the verifier; the verifier checks only the structure pinned in `design-md-spec.md`.
- Not generated from the Google spec: `description`, `omitted`, `components` (no v3 source for them). Not emitted into front matter: per-theme values beyond the first, `shadow` and other families, `type.fonts`.
- When the Google spec changes: update `design-md-spec.md` and `render_front_matter` first, regenerate the fixture and template, then bump the pinned date; a renamed section or key is a new ADR.
- Way back: if `DESIGN.md` has to become prose-only (Option A), delete the front matter block, drop `design_md_stale` and the mapping section, keep the eight sections; cost is one task and no data loss because `tokens.json` was never derived from it.
