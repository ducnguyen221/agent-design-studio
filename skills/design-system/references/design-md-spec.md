# DESIGN.md: what this skill emits and what the verifier checks

`DESIGN.md` is the package's entry file for agents (ADR 0002). Its front matter is generated from `tokens.json`; its body is written by hand. This file pins the shape the generator produces and the verifier checks. It is written in our own words; it is not a copy of the upstream specification.

## Source

- Shape: Google Labs "Design Markdown" specification, repository `https://github.com/google-labs-code/design.md`, file `docs/spec.md`, spec label `version: alpha`, read on 2026-10-22. Licence of that repository as read on 2026-10-22: Apache-2.0 (`LICENSE` at the repository root). No text from it is reproduced here; only section names and key names are reused, which are needed for interoperability.
- Token source: Claude Design format `v:3`, read on 2026-10-22 (`token-contract.md`). Both pins are printed by the verifier; a change in either source is handled by updating this file and `render_front_matter` together, then a new ADR.
- Package contract: `system-contract.md`.

## Sections in order

Exactly these eight level-2 headings, in this order, each spelled exactly like this:

1. `## Overview`
2. `## Colors`
3. `## Typography`
4. `## Layout`
5. `## Elevation & Depth`
6. `## Shapes`
7. `## Components`
8. `## Do's and Don'ts`

Rules we add on top of the upstream shape:

- No level-1 heading is emitted by the template. If a person adds one before `## Overview` the verifier ignores that single line.
- All eight sections must be present (upstream allows omissions; we do not, so that every agent finds the same map). Upstream aliases of section names are not accepted.
- `## Overview` must contain, as list items, a line starting with `- Read order:`, one starting with `- Owner:` and one starting with `- Status:`; `- Version:` and `- Canonical by domain:` are expected but not machine-checked.
- The body names tokens (as `{colors.<key>}`, `{typography.<key>}`, `{rounded.<key>}`, `{spacing.<key>}` or in back-ticks) and never copies values. Value copying is not machine-checked.
- `## Elevation & Depth` is where `shadow` tokens and other single-value families are named, because they have no front matter key.

Starting point: `templates/DESIGN.md`.

## Front matter keys we emit

The front matter starts on line 1 with `---` and ends with the next `---` line. Keys appear in this fixed order; a key whose source family is empty is omitted entirely (no empty maps):

| Key | Value | Source |
|---|---|---|
| `version` | `alpha` (bare word) | constant, the pinned spec label |
| `name` | `"<title>"` | `design-system.json` → `title` |
| `colors` | map `<name>: "<hex or reference>"` | `tokens.json` → `color.tokens[]`, first theme |
| `typography` | map `<style>: {fontFamily, fontSize, fontWeight, lineHeight}` | `tokens.json` → `type.groups[].styles[]` + `type.families` |
| `rounded` | map `<name>: "<value>"` | `tokens.json` → `radius.tokens[]` |
| `spacing` | map `<name>: "<value>"` | `tokens.json` → `spacing.tokens[]` |

Keys defined upstream that we do not emit: `description` (the Overview paragraph plays that role), `omitted` (we require all eight sections), `components` (the v3 grammar has no component property map). Families that do not enter the front matter: `shadow`, `type.fonts`, and any further single-value family.

Serialisation rules, so that regeneration is byte-stable and the verifier can check string equality:

- Two-space indentation; no blank lines, no comments, no timestamps inside the block.
- A key is written bare when it matches `^[A-Za-z_][A-Za-z0-9_-]*$` and is not, ignoring case, one of the YAML words `true`, `false`, `yes`, `no`, `on`, `off`, `y`, `n`, `null`, `~`; otherwise it is double-quoted (token names may start with a digit, contain `.`, or spell one of those words).
- String values are always double-quoted and escaped the JSON way: `\` becomes `\\`, `"` becomes `\"`, a control character becomes `\n`, `\t` or `\u00XX`; nothing else is escaped. A YAML double-quoted scalar reads exactly these escapes, so a reader with a YAML parser and the string-equality check of the verifier agree on the bytes. The same escaping applies to a quoted key. Numbers are bare. `version: alpha` is the only bare string.
- Within each group, entries keep the order of `tokens.json`; typography entries keep group order, then style order.
- Line endings are `\n`; the block ends with `---\n`.

## Mapping from tokens.json

Only the first theme (`color.themes[0]`) is emitted; a colour token with no value in the first theme borrows the first theme that has one (Claude Design does the same). A token with no valid value in any theme fails validation (`invalid_value`) before anything is generated.

| v3 source | Emitted as | Notes |
|---|---|---|
| `color.tokens[i].value` as a string or as `{<themeId>: value}` | `colors.<name>: "<value>"` | first-theme value after inheritance |
| `#rgb` / `#rgba` | `"#rrggbb"` / `"#rrggbbaa"` | expanded, lower-case |
| `#rrggbb` / `#rrggbbaa` | lower-cased, unchanged length | |
| `rgb()`, `rgba()`, `hsl()`, `hsla()`, `oklch()`, `oklab()` | `"#rrggbb"` via `parse_color` (gamut-clamped); alpha other than 1 → `"#rrggbbaa"` | |
| `lab()`, `lch()`, `color()` | the original string, unchanged | build prints `WARN design_md_color_passthrough: <name>` |
| alias `"{x}"` | `"{colors.x}"` | aliases are not resolved; the target must exist (verifier) |
| `type.groups[g].styles[s]` | `typography.<style.name>:` | one entry per style |
| `style.family` else `group.family` | `fontFamily: "<type.families[key]>"` | the whole CSS stack string, quoted and escaped as above: a stack `"Inter", sans-serif` is written `fontFamily: "\"Inter\", sans-serif"` |
| `style.fontSize` | `fontSize: "<value>"`; a bare number becomes `"<n>px"` | |
| `style.fontWeight` | `fontWeight: <number>`; `normal`/`bold` → `400`/`700`; a range such as `"300 800"` stays a quoted string | |
| `style.lineHeight` | `lineHeight: <number>` when unitless, otherwise `"<value>"` | |
| other style fields (`letterSpacing`, `fontStyle`, `opticalSize`, `sample`, `usage`) | not emitted | |
| `radius.tokens[i]` | `rounded.<name>: "<value>"`; a bare number becomes `"<n>px"` | `%` and `0` pass through unchanged |
| `spacing.tokens[i]` | `spacing.<name>: "<value>"`; a bare number becomes `"<n>px"` | |
| `shadow`, other families, `type.fonts` | nothing | name them in the body instead |

Worked example (three colour tokens): `bg` = `#ffffff`, `text` = `{ink}`, `ink` = `oklch(0 0 0)` produce

```yaml
colors:
  bg: "#ffffff"
  text: "{colors.ink}"
  ink: "#000000"
```

## What the verifier checks

Run by `verify-design-system.py` as part of `verify_package` (the `DESIGN.md` entry of `system-contract.md`, section "Required files"). Errors go to stderr as `<code>: DESIGN.md[: detail]` and exit 1.

| Code | Trigger |
|---|---|
| `design_md_missing` | no `DESIGN.md` at the package root |
| `design_md_stale` | the front matter block (line 1 up to the second `---`) is not string-equal to `render_front_matter(tokens, index)` |
| `design_md_section_missing` | one of the eight `##` headings is absent (exact spelling) |
| `design_md_section_order` | all eight present but out of order, or a heading repeated |
| `design_md_broken_ref` | a `{colors.x}`, `{typography.x}`, `{rounded.x}` or `{spacing.x}` in the body (outside fenced code) names a key that is not in the front matter |
| `design_md_overview_incomplete` | the Overview section lacks a `- Read order:`, `- Owner:` or `- Status:` line |

`build-design-system.py --design-md --check` reports the same `design_md_stale` and exits 1 without writing. `build-design-system.py --design-md` replaces only the front matter block and leaves the body untouched; on a file without a front matter block it prepends one.

## Not checked

- Google's own lint rules (required `primary` colour, dimension units `px|em|rem`, unknown component properties, duplicate YAML keys across code blocks). Running that lint is optional QA outside this skill.
- Whether the body copies token values, whether prose matches the tokens, the quality of the Overview paragraph.
- Headings of level 3 and deeper, extra text before `## Overview` other than one optional `#` line, and any section a person adds after the eighth one (allowed upstream; we neither require nor forbid it, but the eight pinned headings must still appear in order).
- How the Claude Design page renders `DESIGN.md` (it becomes one further brand-book section; front matter display not measured).
- Live render, browser display, real import: see the verifier's PASS line.
