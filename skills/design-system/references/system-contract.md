# System contract: the design-system package

One folder, `design-system/`, serves two readers: Claude Design (package format `v:3`, read on 2026-10-22, research preview) and any coding agent. This file is the folder tree and the rules around it. Token grammar: `token-contract.md`. `DESIGN.md` shape: `design-md-spec.md`. Why this shape: ADR 0001 and ADR 0002 under `docs/architecture/adr/`.

Size limits are bytes on the raw file, decimal units: 64 KB = 64 000, 256 KB = 256 000, 512 KB = 512 000, 1 MB = 1 000 000, 2 MB = 2 000 000, 12 MB = 12 000 000. Errors print as `<code>: <path>[: detail]` on stderr; warnings print as `WARN <code>: <path>[: detail]` on stdout; paths are relative to the package root with `/` separators.

## Package tree

```
design-system/                          ← = project/ của Claude Design; KHÔNG SKILL.md/AGENTS.md/CLAUDE.md/package.json/dot-*
├─ DESIGN.md              MUST   gốc đọc mọi agent: front matter YAML (sinh từ tokens.json) + 8 mục ## theo Google alpha;
│                                 Overview chứa hợp đồng ADS (thứ tự đọc · owner/version/status · canonical theo domain)
├─ README.md              MUST   brand book cho Claude Design (3 tiêu đề ở hồ sơ full) — không chép DESIGN.md
├─ tokens.json            MUST   GỐC DỮ LIỆU token, danh sách v3 {name,value,usage}
├─ design-system.json     MUST   chỉ mục v3, ghi cuối
├─ canonical-map.json     MUST   schemaVersion 1; profile; canonical; components.<C>.source; checks.contrast; decisions
├─ viewer.html            MUST   trang xem tự chứa, SINH bằng build-design-system.py, ≤512 KB (trần nền tảng), mục tiêu ≤300 KB
├─ provenance.md          TUỲ    sổ nguồn observed/inferred/unknown (hiện thành mục phụ)
├─ CHANGELOG.md           TUỲ    chỉ thêm
├─ components/
│  ├─ Cover/preview.html  MUST   dòng 1 marker @dsCard; 1 SVG inline + 2 phần tử chữ (theo cover.md — TK3 kiểm)
│  ├─ <Comp>/README.md    MUST-nếu  câu đầu = tóm tắt
│  ├─ <Comp>/preview.html MUST-nếu  marker dòng 1; không iframe/object/embed; CDN ghim version
│  └─ <Template>/preview.html TUỲ  marker page + group="Templates"
├─ assets/<Group>/README.md  MUST-nếu  liệt từng file, nguồn, quyền; không bịa logo (FR4.2)
├─ assets/<Group>/<file>  TUỲ    ≤12 MB; viewer nhúng inline chỉ file ≤64 KB
├─ fonts/<file>           TUỲ    woff2/woff/ttf/otf ≤1 MB, có quyền, khai type.fonts[].file
├─ patterns/<Pattern>.md  TUỲ    mục phụ
├─ surfaces/<s>/{rules.md, screens/<route>.md}  TUỲ  mục phụ
└─ (KHÔNG ghi tay: tokens.css, manifest.json, api/**, migration-map.json, publish-progress.json, archived/**)
```

The package root is `project/` of a Claude Design system. Harness wrapper files live one level up (see "Agent adapters live in the parent folder"). Only create the branches that have a real object behind them; never add empty folders.

## Required, conditional, optional

The tree marks each entry. `MUST` means the verifier reports an error when it is missing or wrong (exit 1). `MUST-nếu` is the conditional form: an error only when the object exists (a component folder, an asset group). `TUỲ` means optional: only the name and the section budget are checked, never the content.

### Required files

| Entry | What is checked | Codes |
|---|---|---|
| `design-system.json` | version 3, `layout` is `"files"`, non-empty `title`, `namespace` is an ASCII JavaScript identifier; `createdOnFiles` should be present | `missing_required_file`, `unsupported_format_version`, `missing_index_key`, `invalid_index_value`; warning `index_marker_missing` |
| `README.md` | exists, at most 200 000 bytes, no level-1 heading that repeats `title`, no "Provenance" or "Next steps" section; profile `full` needs the three headings "Content fundamentals", "Visual foundations", "Iconography" | `readme_missing_section`, `readme_too_large`, `readme_forbidden_section`; warning `readme_unknown_token` |
| `tokens.json` | grammar in `token-contract.md` | `token-contract.md`, section "Error codes" |
| `DESIGN.md` | front matter regenerated and checked for string equality, eight sections in order, references resolve | `design-md-spec.md`, section "What the verifier checks" |
| `canonical-map.json` | schema in "Canonical map" below | `invalid_manifest`, `invalid_canonical`, `invalid_external`, `invalid_status`, `invalid_id`, `invalid_path`, `missing_path` (names kept from the earlier manifest check) |
| `viewer.html` | exists, equals the regenerated page, at most 512 000 bytes (target 300 000), no outside resources, no event-handler attributes, content-security meta present | `viewer_missing`, `viewer_stale`, `viewer_too_large`, `viewer_external_ref`, `viewer_forbidden_tag`, `viewer_inline_handler`, `viewer_forbidden_api`, `viewer_missing_csp`, `viewer_a11y`, `viewer_coverage`, `viewer_leak`; warning `viewer_large` |
| `components/Cover/preview.html` | line 1 is the `@dsCard` marker, at most 256 000 bytes, one inline `<svg>`, no embedding tags, CDN URLs pinned to an exact version | `cover_missing`, `card_marker_missing`, `preview_too_large`, `forbidden_tag`, `unpinned_cdn`, `cover_shape` |

### Conditional entries

- `components/<Comp>/README.md` and `components/<Comp>/preview.html`: profile `full` requires both for every component folder except `Cover` and folders whose preview carries the `page` marker, plus a `components.<Comp>.source` entry in `canonical-map.json`. The folder name must be an ASCII JavaScript identifier. The first sentence of the README is the summary. A README over 64 000 bytes gives `WARN component_readme_large`. Codes: `component_name_invalid`, `component_incomplete`, `component_without_source`.
- A preview may not use `iframe`, `frame`, `object`, `embed`, `portal` or `noscript` (`forbidden_tag`), may not exceed 256 000 bytes (`preview_too_large`), and every CDN URL pins an exact version (`unpinned_cdn`). A marker `height` outside 40 to 4000 gives `WARN card_marker_height`.
- `assets/<Group>/README.md`: every direct subfolder of `assets/` has one; it names each file in the group, its source and its usage right, and says which ink a one-colour SVG uses. Never invent a logo: with no real logo, use a text wordmark and say why in this README. Codes: `asset_group_readme_missing`, `asset_unlisted`. A single asset over 12 000 000 bytes (an SVG over 2 000 000) is an error: `asset_too_large`.
- `fonts/<file>`: listed in `type.fonts[].file`, woff2, woff, ttf or otf, at most 1 000 000 bytes, with usage right. Codes: `font_file_missing`, `font_file_invalid`.

### Optional entries

`provenance.md`, `CHANGELOG.md` (append only), `patterns/<Pattern>.md`, `surfaces/<s>/rules.md`, `surfaces/<s>/screens/<route>.md`, `components/<Template>/preview.html` (marker `page` with `group="Templates"`). Only names and the section budget are checked.

Advisory checklist for a pattern, template or screen file (not machine-checked): the user task; information order and hierarchy; grid, widths and breakpoints; data formats; loading, empty, error and permission states; interaction and recovery; keyboard, focus and accessibility; links to the components and patterns used. Unknown fields say `unknown` and how to find out; fields that do not apply say `N/A` with a reason.

### Profiles

| Profile | How selected | Rules |
|---|---|---|
| `full` | default, or `profile: "full"` | everything above |
| `minimal` | `--profile minimal` or `profile: "minimal"` in `canonical-map.json` | 6 to 10 colours in exactly one theme; 5 to 7 text styles; exactly 4 spacing tokens; exactly 3 radius tokens; README is one paragraph of at least 80 characters (the three headings are not required); no component other than `Cover`. Code: `minimal_profile_violation` |

### Contrast

Text and surface pairs are declared in `canonical-map.json` under `checks.contrast`, not in `tokens.json`. Each pair is measured in every theme against its `min` (default 4.5; 3.0 for large text, borders, focus rings and icons). No declared pair gives `WARN contrast_unchecked` and the PASS line says so; a colour that cannot be converted to sRGB gives `WARN contrast_unsupported_space`; a failing pair is `contrast_below_min`.

### Cover folder is bare

`components/Cover/` holds `preview.html` and nothing else. Any sibling (`README.md`, `Cover.d.ts`, `index.html`), or a `@ds-bundle` header in `components/bundle.js` that lists `Cover`, turns the cover into an ordinary component and the system loses its cover. The verifier reports `cover_not_bare: components/Cover/<file>` (detail `bundle header lists Cover` for the bundle case).

Cover rule: line 1 is `<!-- @dsCard height=N -->` with N from 240 to 360 (outside it: `WARN card_marker_height`); the frame is a fixed 960 by N; exactly one inline `<svg>` (any other count: `cover_shape: components/Cover/preview.html: <n> svg`) plus two text elements, the name and a one-line tagline (not machine-checked); no gradient, shadow or motion; every `fill`, `stroke` and `rx` goes through a class bound to a token.

### Recognised, never generated

The verifier recognises, and the PASS line then adds `bundle`, when it finds `components/bundle.js`, `components/bundle.css`, `components/index.d.ts`, `components/<Comp>/<Comp>.d.ts`, `components/lib/**` or `components/src/**`. This skill never writes them; Claude Design owns their limits.

### Legacy folders

`ui-kit/`, `specimens/`, `integrations/` and, from the earlier layout of this skill, `brand/` and `foundations/` give `WARN legacy_layout_dir: <folder>`. Markdown inside them would silently become brand-book sections, so move the content before importing.

## Read order

`DESIGN.md` Overview states both branches; every package repeats them there.

- Claude Design: `README.md` → `tokens.json` → `components/*/README.md`.
- Any other agent: `DESIGN.md` → `tokens.json` → `canonical-map.json` → `components/`.

Two roots, two roles. The reading root is `README.md` for Claude Design and `DESIGN.md` for everything else. The data root is always `tokens.json`; the `DESIGN.md` front matter and any DTCG file are derived from it and never edited by hand. The `DESIGN.md` Overview also gives owner, version, status and the canonical file for each domain (brand, tokens, components). `DESIGN.md` does not repeat the brand book, and the body names tokens without copying values.

## Section budget

Claude Design turns every Markdown file outside `components/` and `archived/` into a brand-book section, in path order, at most 24. The verifier counts statically: every `*.md` and `*.mdx` in the package except the root `README.md` and anything under `components/` or `archived/`. That includes `DESIGN.md`, `provenance.md`, `CHANGELOG.md`, `patterns/**`, `surfaces/**` and `assets/<Group>/README.md`. More than 24 gives `WARN sections_over_limit: <n> > 24: <paths in path order>`; it is a warning because the files stay in the package.

Keep the profile `full` fixture at 10 or fewer. For `surfaces/`, use one `rules.md` per surface and put approved screens into few files (`screens/<route>.md` only for screens that are signed off). Other size warnings: `file_count_high` above 1 000 files, `kept_file_large` for any file kept without UI over 512 000 bytes.

## Canonical map

`canonical-map.json` replaces the earlier `manifest.json`; that name is generated by the Claude Design page, so a hand-written file with it is refused as `generated_file_present`.

```json
{
  "schemaVersion": "1",
  "system": {"id": "sample-studio", "version": "0.1.0", "status": "draft"},
  "profile": "minimal",
  "canonical": {
    "brand": {"kind": "file", "path": "README.md"},
    "tokens": {"kind": "file", "path": "tokens.json"},
    "components": {"kind": "external", "url": "https://example.com/storybook"}
  },
  "components": {"Button": {"source": "src/Button.tsx"}},
  "checks": {"contrast": [{"fg": "text", "bg": "bg", "min": 4.5, "large": false}]},
  "decisions": []
}
```

- `status` is one of `draft`, `pending`, `as-is`, `proposed`, `approved`, `deprecated`.
- `canonical.<domain>` is `{"kind": "file", "path"}` (relative to the package root), `{"kind": "repo-path", "path"}` (relative to the parent folder of the package, the project root) or `{"kind": "external", "url"}` (an `https` pointer with no credentials; never fetched, so it proves nothing about availability or rights). A local source has no `url`; an external one has no `path`. One domain has one canonical source.
- `components.<Comp>.source` is a path or an external URL under the same rules.
- `checks.contrast[]` entries name token names for `fg` and `bg`.
- `decisions[]` records owner decisions as data (pending or quoted). A partial map is allowed for a draft; do not invent paths.
- Every path goes through the safe-path check before any read: no absolute path, no `..`, no backslash or drive letter, no sensitive name, no link.

Authority: brand guidance confirmed by the owner describes the target; code at the baseline describes the present. A README, an export or an image never wins by default. Record drift as domain → source A → source B → impact → proposal → owner decision.

## Agent adapters live in the parent folder

Harness wrappers belong to the project that uses the package, not to the package. They sit next to `design-system/`:

- `AGENTS.md`: the real instructions, pointing at `design-system/DESIGN.md`.
- `CLAUDE.md`: the single line `@AGENTS.md`.
- `GEMINI.md`: a short prose pointer.

Each is at most 30 lines. `build-design-system.py --package <root>/design-system --adapters <root>` writes them from the `.tmpl` templates of this skill and never overwrites: an existing file prints `WARN adapter_exists: <name>` and a proposal block. The templates carry a `.tmpl` suffix so that a harness does not load them as rules while they sit inside the plugin.

## Refused and generated paths

Claude Design refuses these inside a package; the verifier reports `refused_path: <path>` before opening anything:

- `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` at any depth.
- `package.json`, `tsconfig.json`, `deno.json`, `bunfig.toml`, and a `node_modules` folder, at any depth.
- Lockfiles: `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`, `bun.lockb`, `deno.lock`.
- Any path segment that starts with a dot, except exactly `.image-slots.state.json`.
- 8.3 short names: a segment matching `~` followed by a digit, such as `NAME~1`.
- `index.html` at the package root and `components/<Comp>/index.html` (an alias of `preview.html`). An `index.html` anywhere else gives `WARN index_html_nested`, because the refusal depth is not confirmed.
- `design-system.json` anywhere except the root (at the root it is the required index).
- An `artifact-type/` folder.

Files the page generates itself are `generated_file_present: <path>`: `manifest.json`, `tokens.css`, `api/**`, `migration-map.json`, `publish-progress.json`, `archived/**`. Do not write them by hand.

Sensitive or escaping paths (`.env*`, `*.pem`, `credentials`, a path leaving the package, a link) are refused with `refused_sensitive_path` and never opened. The refused-path check runs right after that one and before any read.
