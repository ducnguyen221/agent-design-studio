# Typography for English and Vietnamese interfaces

Use at Step 4 to test a direction's type hypothesis, at Step 5 to make the token and font decision, and at Step 7 to review the rendered result. This is a decision aid, not a universal font league table. The rank below is an editorial starting order for a stated job; it is not a reading-speed experiment or an accessibility score. Keep the existing product's type tokens unless the brief and a rendered comparison justify a change.

## Decide in this order

1. **Name the job.** Record audience, EN/VI content mix, interface versus long reading versus editorial voice, available brand type, devices, and acceptable font transfer. Keep a system stack if consistent custom shapes add little value.
2. **Apply hard gates before ranking.** Check the exact files and styles to ship: redistribution and embedding rights; glyphs for the real EN/VI copy and weights/italics used; browser loading and fallback; and an acceptable transfer budget. Repository metadata naming a Vietnamese subset is a lead, not proof about a particular binary or its rendering. A candidate failing a gate is excluded, even if it ranks first below.
3. **Compare in context.** Set the same real copy, width, size, line height, contrast, and content hierarchy in each candidate. Judge accents, density, rhythm, numbers, and the first viewport. Record why the chosen face fits the subject and what it costs. Do not add families merely to reach a fashionable pairing.
4. **Verify the actual build.** Inspect the loaded font in browser devtools, fallback and delayed/blocked loads, the transferred bytes, the license file, and the rendered EN/VI pages. Review with user text resizing and spacing overrides. State any unverified case.

### Scenario shortlists

Ranks order *fit for the named scenario after hard gates*, not universal quality. The system stack is a valid no-download comparator in every scenario. These are design judgments based on intended roles and the cited upstream metadata, not measured legibility outcomes.

| Scenario | Editorial order to try | Reason and trade-off |
| --- | --- | --- |
| UI or technical landing page | 1. Inter; 2. Source Sans 3; 3. Be Vietnam Pro | Inter offers a restrained UI voice and variable weights; Source Sans 3 suits denser explanatory copy; Be Vietnam Pro changes the voice toward Vietnamese identity. Test Vietnamese accents at display sizes before committing. |
| Vietnamese-first brand or service | 1. Be Vietnam Pro; 2. Inter; 3. Noto Sans | Start with a face designed around Vietnamese brand use; Inter is a quieter UI direction; Noto Sans favors a broader language system. Name the actual audience and brand before choosing. |
| Long-form reading and documentation | 1. Source Sans 3; 2. Noto Sans; 3. Inter | Compare paragraph texture and line wrapping with real copy. A broad language set may make Noto Sans useful, but that does not prove it is more readable. |
| Editorial feature | 1. Source Serif 4 for display/body where appropriate, paired with Source Sans 3 for controls; 2. a single Source Sans 3 family | A serif can carry an editorial voice; the extra family adds transfer and pairing work. Keep a sans face for UI labels if the serif makes controls harder to scan. |
| Code, identifiers, or technical numerals | 1. JetBrains Mono; 2. system monospace | Use mono only where fixed-width alignment or code distinction serves a purpose. Do not rank it against proportional body faces or set long prose in it by default. |

| Family | Useful role | Do not default to it when | Candidate metadata |
| --- | --- | --- | --- |
| Inter | UI, technical display/body | the brand needs a distinctive editorial voice or the real VI display test fails | [Inter metadata](https://raw.githubusercontent.com/google/fonts/main/ofl/inter/METADATA.pb) |
| Source Sans 3 | documentation, explanatory UI | the brief needs a more particular brand expression | [Source Sans 3 metadata](https://raw.githubusercontent.com/google/fonts/main/ofl/sourcesans3/METADATA.pb) |
| Be Vietnam Pro | VI-first identity and UI | a neutral existing product token system must stay consistent | [Be Vietnam Pro metadata](https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/METADATA.pb) |
| Noto Sans | multilingual product system | only EN/VI is needed and a narrower family meets the brief and budget | [Noto Sans metadata](https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/METADATA.pb) |
| Source Serif 4 | editorial heading or reading texture | dense controls, labels, or a strictly neutral UI dominate | [Source Serif 4 metadata](https://raw.githubusercontent.com/google/fonts/main/ofl/sourceserif4/METADATA.pb) |
| JetBrains Mono | code, aligned technical values | ordinary body copy or a heading merely needs to look technical | [JetBrains Mono metadata](https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/METADATA.pb) |

The linked Google Fonts records list OFL and Vietnamese subsets for these families. Verify the **specific version, binary, style and license** you distribute. A local system stack has no webfont transfer but varies by platform and may change line breaks; test it as its own candidate.

## Starting type tokens

These are starting ranges, not WCAG minimum sizes or experimentally optimal values. Pixel equivalents assume the browser's default root is 16px; a user's changed root changes the result. Choose one point per role, then adapt it in the browser. `title` is a visual role (for a card, for example), not an HTML heading level.

| Visual role | Starting size | Unitless line height | Weight | Tracking and measure to check |
| --- | --- | --- | --- | --- |
| Hero display | 3–5rem (48–80px) | 1.08–1.2 | 600–700 | Start at `0`; try `-0.01em` only after checking VI marks. Keep deliberate short lines; allow wrapping. |
| H1 | 2.5–4rem (40–64px) | 1.12–1.25 | 600–700 | Start at `0`; roughly 10–20ch for a display line if copy allows. |
| H2 | 1.875–2.75rem (30–44px) | 1.15–1.3 | 600–700 | Start at `0`; inspect stacked accents and multiline breaks. |
| H3 | 1.5–2rem (24–32px) | 1.2–1.35 | 600 | Start at `0`; do not squeeze a VI label into one line. |
| Title | 1.25–1.5rem (20–24px) | 1.25–1.4 | 500–600 | Start at `0`; match the card or panel width. |
| Body | 1–1.125rem (16–18px) | 1.5–1.7 | 400 | Start at `0`; try about 55–75ch for sustained reading, then judge real EN/VI copy. |
| Lead | 1.125–1.25rem (18–20px) | 1.4–1.6 | 400–500 | Start at `0`; use a shorter measure than body when it introduces a section. |
| Label | 0.875–0.9375rem (14–15px) | 1.3–1.5 | 500–600 | Avoid wide all-caps tracking for VI; let controls grow and wrap. |
| Caption | 0.875–0.9375rem (14–15px) | 1.35–1.55 | 400–500 | Keep contrast and surrounding space; do not hide meaning in tiny print. |
| Code | 0.875–1rem (14–16px) | 1.4–1.6 | 400–500 | Use mono for code only; allow code blocks to scroll when two-dimensional layout requires it. |

The pack's [quality floor](../SKILL.md#the-quality-floor) still applies: body at least 14px and labels/captions at least 12px, with text contrast at least 4.5:1. Those are **pack rules**, not a WCAG minimum-font-size claim. Test actual computed sizes and contrast; a chosen size does not excuse poor contrast. For unusually dense interfaces, preserve the floor and test the token in context.

HTML headings express document structure. Use `<h1>` for the page topic and descend by section, regardless of whether a hero is visually larger or an H2 is styled like a card title. Avoid skipping levels to get a CSS size. [W3C heading guidance](https://www.w3.org/WAI/tutorials/page-structure/headings/) addresses this structural role; the token table is presentation only.

### Small CSS starting point

```css
:root { font-size: 100%; }
body {
  font-family: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 1.0625rem;
  line-height: 1.6;
}
h1 { font-size: clamp(2.5rem, 1.8rem + 2vw, 4rem); line-height: 1.16; letter-spacing: 0; }
h2 { font-size: clamp(1.875rem, 1.5rem + 1vw, 2.75rem); line-height: 1.22; letter-spacing: 0; }
p { max-width: 70ch; }
```

Load `Inter` only if the chosen file and license gates pass; otherwise use the system stack without the missing first family. The `rem` terms make the scale responsive to root size, but `clamp()` with `vw` is **not automatically safe at zoom**: test 100%, 150%, and 200% text enlargement and actual browser zoom where available. Avoid fixed-height text boxes, `overflow: hidden`, and `white-space: nowrap` on essential prose or headings. Prefer natural height and wrapping.

## English/Vietnamese and font loading checks

- **Proof string:** `Typography preserves hierarchy, clarity, and orientation.` / `Tiếng Việt: Đường dẫn, tưởng tượng, Nguyễn, Ắ Ằ Ẳ Ẵ Ặ Ấ Ầ Ẩ Ẫ Ậ Ế Ề Ể Ễ Ệ Ố Ồ Ổ Ỗ Ộ Ớ Ờ Ở Ỡ Ợ Ứ Ừ Ử Ữ Ự.` Add actual names, product words, numbers, punctuation, and italic text. Compare NFC with canonically equivalent NFD input in the shipped browser. A short proof string never certifies a complete font.
- Test the exact 400/500/600/700 weights and italics used. Check combining marks above and below letters at heading and small-label sizes. Donny Trương's [design challenges](https://vietnamesetypography.com/design-challenges/) and [diacritical details](https://vietnamesetypography.com/diacritical-details/) explain why mark placement and spacing need visual review; they do not endorse a family here.
- Inspect local and network-loaded faces in the browser. Test delayed and blocked font requests, then compare fallback line wrapping and layout shifts. `font-display: swap` controls display timing; it does not guarantee zero shift. Use `size-adjust` or metric overrides only after measuring the **actual** face/fallback pair. [MDN font-display](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@font-face/font-display) · [MDN size-adjust](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@font-face/size-adjust).
- Load only needed styles and subsets; self-host when that improves control, keep the license and origin, and preload only a critical resource. Record shipped WOFF2 bytes and unexpected requests. [web.dev font loading](https://web.dev/articles/optimize-webfont-loading) explains the loading trade-offs. A candidate must meet the project's stated budget; this guide sets no universal byte cap.
- Test EN and VI at narrow, middle and wide widths; look for clipping, overlap, sudden breaks, and unintended horizontal scroll. Test [200% text resize](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) with no loss of content or function; test [320 CSS px reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) as reflow, not as a substitute for browser zoom. Apply the [text-spacing override](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html): line height 1.5, paragraph spacing 2em, letter spacing 0.12em, word spacing 0.16em. These are override test values, **not required design defaults**.

Record the chosen family, font files and license, measured bytes, fallback, token overrides, EN/VI visual evidence, and any failed or unverified checks in `04-design-system/` and `07-uat-report.md`. Step 7 should review what rendered, not only what the stylesheet declares.
