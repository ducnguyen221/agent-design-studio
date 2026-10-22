# 0001. Use the Claude Design v3 token list as the canonical token format

Status: accepted · Sprint: SPR-32 · Related: ADR 0002, PLAN section "Hợp đồng bàn giao" (items 4, 6), SPEC FR6
Format pin: `v:3`, read on 2026-10-22 (research preview; a format change supersedes this ADR with a new one)

## Context

Three token shapes coexist in this repository and in the systems it has produced:

1. The frozen example under `docs/example/` keeps a name-to-value map with a `_why` field per entry (Step 5 output of the routing skill). It must not change.
2. The unreleased branch `sprint/tk1-uiux-source-foundation` validated a DTCG 2025.10 subset (`$type`, `$value`, sRGB component arrays, same-file aliases).
3. Claude Design (the artifact type this skill targets) reads `tokens.json` as a list grammar: `color.themes[]` plus one flat `color.tokens[{name,value,usage}]`, `type.{fonts,families,groups[].styles[]}`, and list families for `spacing`, `radius`, optional `shadow` and other single-value families.

Constraints that matter: the Claude Design page cannot read a DTCG map at all (the family renders empty and its entries are dropped on the first in-page edit); the colour protocol used by the routing skill emits `oklch()`, which the DTCG subset rejects because it only accepts sRGB components; the verifier must stay Python 3.12 stdlib with no network; the owner decided on 2026-10-22 (`Q2`) that `tokens.json` is the single data source and that `DESIGN.md` front matter and any DTCG file are derived outputs. Affected parties: the `design-system` skill, its verifier and generator, the template and fixture, and every agent that opens a package.

## Options

| Option | How | Trade-off | When it fits |
|---|---|---|---|
| A. v3 list canonical, DTCG exporter, legacy map read-only | `tokens.json` follows the Claude Design list grammar; `export-dtcg.py` derives a DTCG subset and lists what it dropped; the `_why` map is accepted only behind `--legacy-tokens` | Import into Claude Design works unchanged; `oklch()` is valid at the source; DTCG consumers get a lossy export | The primary consumer is Claude Design and agents reading one file |
| B. DTCG canonical, v3 exporter | Author DTCG, generate the v3 list for import | Standards-aligned source, but every import needs a build step, the exporter must invent `usage` and theme ids, and `oklch()` cannot be stored | The primary consumer is a token pipeline (Style Dictionary and the like) |
| C. Keep both canonical | Maintain both files by hand, verifier checks parity | Two sources drift; parity checks are expensive and still miss intent | Never, beyond a short migration |
| Keep the status quo | Leave the `_why` map as the only shape | Nothing new to build, but nothing imports into Claude Design | Not viable for this release |

## Decision

Option A: `tokens.json` in the Claude Design v3 list grammar is the canonical token file; DTCG is an exporter output and the `_why` map is read-only legacy. The reason is the constraint set, not preference: the target page reads only the list grammar, the colour protocol needs `oklch()`, and `Q2` fixes a single data source.

Concretely:

- Verifier: `validate_tokens_v3` enforces the pinned grammar (names `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`, one namespace across all families except `type`, hex or numeric colour functions or `{alias}`, per-theme maps with first-theme inheritance, alias depth ≤ 16, the published caps). Error codes are listed in `skills/design-system/references/token-contract.md`.
- Generator: `render_front_matter` derives `DESIGN.md` front matter from the first theme (ADR 0002); `to_dtcg` derives the DTCG subset and returns the list of skipped tokens with reasons.
- Legacy: `--legacy-tokens` reads the map shape and never labels it valid v3; `docs/example/**` stays byte-identical.

## Consequences

- Easier: a package imports into Claude Design without a build step; `oklch()` colours are first-class; one file answers "what are the tokens" for every agent.
- Harder: DTCG consumers receive a lossy export (per-theme values beyond the first, `usage`, non-sRGB spaces that only round-trip as converted hex); motion has no v3 family and stays in prose (`06-motion-spec.md` of the routing skill); `shadow` is optional and never enters `DESIGN.md` front matter.
- Fixed from now on: `FORMAT_VERSION = 3` and `FORMAT_READ_ON = "2026-10-22"` live in `scripts/design_system_v3.py`, are printed on the PASS line, and the verifier refuses any other `--format-version`. Claude Design is a research preview; when its grammar changes, a new ADR replaces this one and the constants move together.
- The `_why` map stays readable until the owner decides to drop it; no deadline is set here.
- Way back: if DTCG must become canonical later, the exporter direction flips (write `to_v3` from DTCG), the verifier swaps `validate_tokens_v3` for the DTCG subset validator that already exists on the branch, and the fixture and template are regenerated. Estimated cost: one sprint, no data loss because the v3 list is a superset of what the DTCG subset carries except `oklch()` values, which would have to be converted to sRGB.
