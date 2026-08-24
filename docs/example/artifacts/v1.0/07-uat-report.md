# 07 — UAT report

**Date:** 2026-08-24 · **Build reviewed:** `05-build.html` (204 KB, self-contained)
**Gate 2 state:** `pending` — closes at the design review + Codex final review.

## Mechanical pre-pass

`static-lint` slot unfilled and the linter is network-dependent, so it was **skipped**.
Recorded rather than silently omitted. The manual checks below all ran.

## Hard floor — PASS

Measured, not asserted. Colours resolved through a canvas so `oklch()` values were read as
real sRGB; ratios computed with the standard relative-luminance formula.

| Check | Result | Evidence |
| --- | --- | --- |
| Body ≥14px | PASS | body 17px · lead 16px · card 14.5px |
| Labels/captions ≥12px | **PASS after 6 fixes** | every measured label now 12px+ |
| Text contrast ≥4.5:1 | **PASS after 2 fixes** | 14/14 pairs pass; lowest is 4.94:1 |
| Focus visible, full keyboard walk | PASS | 10 stops, `outline=solid` on every one, order matches the components contract |
| Dialogs | n/a | none on the page |
| `prefers-reduced-motion` | PASS | 0 of 16 animated elements remain hidden or transformed |
| Declared UI states exist | PASS | `placeholder` and `language` both implemented; the other six declared unreachable in `components.md` |
| No horizontal overflow | **PASS after 1 fix** | desktop 1440=1440 · mobile 390=390 |
| Console errors | PASS | none |
| No dead controls | PASS | install commands stamped `PLACEHOLDER` rather than faked |
| Real logos / no CSS silhouettes | n/a | no brand depicted; page has no logo and does not pretend otherwise |
| Meaning never by colour alone | PASS | gates carry a `GATE` stamp *and* a field tint; language toggle carries `aria-pressed` *and* an inverted fill |
| Images have alt text | PASS | 3/3 |
| Landmarks / single h1 | PASS | `header,nav,main,footer` · one `h1` |
| Works with JavaScript disabled | PASS | content visible; hidden states are armed only under a `.js` class |

### Full contrast measurements

| Element | Size | Ratio |
| --- | --- | --- |
| body copy | 17px | 8.45 |
| lead | 16px | 8.45 |
| cell body | 13.5px | 8.45 |
| cell label (drafting red) | 12px | 4.94 |
| mono label | 12px | 5.05 |
| figure caption | 12px | 5.55 |
| nav link | 12px | 5.05 |
| button, primary | 13px | 15.32 |
| file trail | 12.5px | 5.05 |
| card body | 14.5px | 7.44 |
| gallery figcaption | 12px | 5.05 |
| footer acknowledgement | 13.5px | 8.00 |
| gate stamp | 12px | 13.81 |
| placeholder pill | 12px | 5.90 |

### Viewport evidence

`screens/07-desktop.png` (1440) · `screens/07-tablet.png` (768) · `screens/07-mobile.png`
(390) · `screens/07-vi-desktop.png` · `screens/07-reduced-motion.png` · `screens/07-nojs.png`

Mobile is composed rather than squeezed: the figure grid becomes 2-across, install panes
stack, the index rail and nav links drop out, and the grid ground steps from 64px to 44px
so it stays proportional to the narrower sheet.

### Bilingual evidence

Toggling to Vietnamese sets `documentElement.lang="vi"`, moves `aria-pressed` to
`[false, true]`, and renders `Agent của bạn đã biết viết UI. Đây là thứ dạy nó thiết kế.`
Diacritics render correctly in the system stack; no font download required.

## Scores

| Dimension | Score | Evidence |
| --- | --- | --- |
| **Concept** | **8** | A process specification drawn as an engineering specimen sheet. Figure rules, captions on the rule, and `GATE` stamps encode something true about the content. Not a 9: the metaphor lives mostly in the chrome — a 9 would draw the seven steps as an actual annotated assembly rather than a bordered grid |
| Direction consistency | 8 | Delivers direction A faithfully — sheet frame, index rail, figure numbering, one drafting-red mark. Honest tension: raising every label to the 12px floor softened the fine-technical character the direction implied |
| Visual hierarchy | 8 | Squint test passes: display → section heading → figure label → body reads in four clear levels. Heading-to-body ratio 3.6× at desktop |
| Craft | 7 | One 8px scale throughout, two type families, controlled colour count. Held back by residual rhythm issues (below) and by the fact that six floor violations shipped into review rather than being caught at build |
| Function | 8 | Every element earns its place; no filler, no invented social proof; the placeholder state is modelled honestly instead of faked |
| Originality | 8 | A drafting-sheet direction with gate stamps is genuinely uncommon for a developer-tool page, and it deliberately inverts the dark-neon genre the reference site sits in |
| **Overall** | **7.8** | **Good**, upper end. Concept is 8 so no veto applies |

```
            Concept 8
                |
 Original 8 ----+---- Direction 8
         \      |      /
          \     |     /
 Function 8 ----+---- Hierarchy 8
                |
             Craft 7
```

## Keep

- The figure-caption-on-a-rule device. It is the identity, it is cheap, and it repeats
  without becoming wallpaper.
- Gate cells reading differently from step cells via tint **plus** stamp. The page's one
  structural claim is the one thing the eye catches.
- The refusal list in `06-motion-spec.md` being visible in the product's own argument —
  eight accepted, eight refused.
- Honest placeholder handling on install. It builds more trust than a fake command.
- Vietnamese as a real second language rather than a degraded one.

## Fix

Ordered by severity. All **blocking** items were fixed and verified during this loop.

**1. Content hidden behind entrances that never fired** — *blocking · FIXED*
- Now: the figure grid, gallery, and all five figure captions rendered **invisible** in the
  first full-page capture. Two causes: `IntersectionObserver` never firing for a captured
  page, and `transform: scaleX(0)` on `.figrule` scaling its own caption child to nothing.
- Why it matters: an entrance animation was gating *content availability*. Any screenshot
  tool, print, or throttled environment would show a broken page.
- Fix: the rule became its own `<i class="ln">` element so the caption is never transformed;
  a failsafe reveals everything on `load` + 1200ms regardless of the observer; reduced-motion
  and no-observer paths reveal immediately; a `@media print` rule forces the final state.
- Verified: `screens/07-desktop.png`, `07-nojs.png`, `07-reduced-motion.png`.

**2. Horizontal overflow at 390px** — *blocking · FIXED*
- Now: `scrollWidth` 455 vs `clientWidth` 390.
- Cause: grid items default to `min-width: auto`, so the long install command inside `<pre>`
  forced its column wider than the viewport.
- Fix: `min-width: 0` on every grid child. Verified 390 = 390.

**3. Six labels below the 12px floor; two pairs below 4.5:1** — *blocking · FIXED*
- Now: gate stamp 9px, gallery caption 10.5px, placeholder pill 10px (4.45:1), mono label
  11px, rail label 10px, language buttons 11px; figure caption 3.59:1.
- Fix: all raised to 12px with letter-spacing compensated; two text-safe colour tokens added
  (`--mark-text`, `--rule-text`) so the decorative red and blueprint blue keep their
  character while clearing 4.5:1. Re-measured: **0 violations of 14**.

**4. `h2` inheriting `line-height: 1.6`** — *important · FIXED*
- Section headings read as two loosely stacked lines. Set to 1.16.

**5. Compounding section rhythm** — *important · FIXED*
- `section` padding plus `.figrule` margin produced 128px voids reading as absence rather
  than composition. Reduced to 104px.

**6. Uneven gap below the two-column artifact trail** — *polish · NOT FIXED*
- The right-hand card is shorter than the file list, leaving a soft void beneath it at
  desktop. Cosmetic, contained, and left deliberately so the report reflects reality.

**7. Hero-to-Fig.1 void still reads large at 1440** — *polish · NOT FIXED*
- Defensible on a drawing sheet, but worth a second opinion at final review.

## Quick wins

If there are only five minutes before publishing:
- [ ] Tighten the hero-to-Fig.1 gap by one step (`--s5` → `--s4` on the first `.figrule`).
- [ ] Give the trail card `height: 100%` so the two columns bottom out together.
- [ ] Add a favicon — currently absent, so the browser tab is anonymous.

## Motion review

Run against the motion playbook's own bar. **Approve.**

No automatic blocks present: no `transition: all`, no `scale(0)` entrance, no `ease-in`, no
layout-property animation, no keyframes on rapidly-fired elements, no ungated hover, no
missing reduced-motion path. Everything animates `transform`/`opacity` only. Every UI
response is ≤220ms; the single 520ms value is a rare-tier scroll entrance with a written
justification and nothing waiting on it.

One finding, non-blocking: the 60ms stagger across eight figure cells totals 420ms for the
last cell, which on a fast scroll may still be arriving as it leaves the viewport. Capped at
6 steps in the implementation to bound it. Flagged in the spec as needing a feel check on a
real scroll, which is not something this environment can judge.

## Unverified

- **Feel.** Everything about timing here is judged from values and still frames. The
  rule-then-caption sequencing (260ms delay) and the stagger cadence need a human watching a
  real scroll.
- **Real devices.** No physical device testing; touch targets are sized by rule, not tried.
- **Cross-browser.** Chromium only. `oklch()`, `color-mix()`, and `backdrop-filter` are the
  three features worth checking elsewhere; all have graceful-enough degradation but none was
  observed failing over.
- **Static lint.** Skipped, offline.

## Gate 2

`pending` — awaiting the design review + Codex final review.

---

## Process feedback — I was the user of my own pack

Five things the pipeline got wrong or left ambiguous while running it for real. This is
the most valuable output of the run.

1. **`choosing-fidelity.md` reads as if the chosen fidelity replaces the other artifacts.**
   It does not say that Steps 3 and 4 still run regardless — I had to decide that mid-run.
   One sentence fixes it. *(Recorded in `01-fidelity.md`.)*
2. **The `style-knowledge` slot fallback points at a section that does not exist.**
   `SKILL.md` promises "style axes in `references/direction-gate.md`"; there is no such
   catalogue. A student installing only this pack cannot run direction A as written. I built
   a 20-entry list for the run and recorded it. *(Recorded in `03-direction-decision.md`.)*
3. **Step 6 lands after Step 5, which forces either a rebuild or motion planned during the
   build.** Doing it honestly meant building the page, then adding motion as a genuine
   second pass — which is correct, but the router never says so, and the naive reading
   invites writing the CSS twice.
4. **Nothing in the pack warns that entrance animations can gate content availability.**
   The motion playbook covers reduced-motion thoroughly but never says *content must render
   without the animation ever playing*. That gap produced the single worst defect in this
   run — an invisible page. This belongs in `motion-playbook.md` as a hard rule.
5. **The 12px label floor is in genuine tension with fine-technical directions.** The
   specimen-sheet aesthetic wants 9–10px mono labels; the floor forbids them. The floor is
   right and I kept it, but the pack should say so explicitly — that some directions cost
   more to make accessible, and that is a reason to pick them knowingly, not a reason to
   bend the floor.
