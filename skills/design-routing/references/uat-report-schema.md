# UAT report schema

Step 7. Review what was built, fix it, verify the fix, and close Gate 2.

Output: `07-uat-report.md` (and `.json` when a machine will read it).

## The loop

1. **Mechanical pre-pass.** If a static linter is available, run it first — it finds the
   boring class of defects for free. If it is unavailable or offline, skip it and note
   that in the report; the manual checks below still apply.
2. **Hard floor check.** The pass/fail list below. Any failure is a defect, not a
   suggestion.
3. **Six-dimension critique.** Scored, with evidence.
   For EN/VI pages, apply the font, scale, fallback, diacritic, resize, spacing, and
   reflow checks in [typography-en-vi.md](typography-en-vi.md). Record the shipped file
   and bytes, actual rendered evidence, and any unverified branch.
4. **Motion review.** Run the motion playbook's review bar against Step 6's output.
   For every accepted recipe, inspect the rendered result, not only source: reduced
   motion at load and after a preference change, keyboard/focus, print/full-page
   capture, and content/CTA when animation never runs or fails after starting.
   Exercise observer absence/no callback and cleanup/remount only when those branches
   exist. For scroll pin/scrub, inspect resize, teardown and focus in the pinned area.
   Separate intended state transitions from unexpected layout shifts or moving targets;
   a low CLS number alone does not prove the flow is usable. Record browser evidence
   per recipe and mark untested branches unverified.
5. **Fix, one issue at a time.** Each fix is its own commit with a before/after
   screenshot. Never batch unrelated fixes — when something regresses, you need to know
   which change caused it.
6. **Re-verify** the specific thing you fixed, at every viewport it affects.
7. **Close Gate 2.**

## The hard floor — pass or fail, no score

Declared at Step 3, verified here. Every row is checked at all three viewports.

- [ ] Body text ≥14px; labels and captions ≥12px.
- [ ] Text contrast ≥4.5:1, measured on **computed** colors on **every distinct surface**
      — including text inheriting the body color inside a dark or tinted region.
- [ ] Focus visible on every interactive element; the whole modeled flow is
      keyboard-operable; focus placed deliberately after each view change.
- [ ] Dialogs: accessible name, contained focus, Escape closes, focus returns to trigger.
- [ ] `prefers-reduced-motion` honored wherever motion exists.
- [ ] Every declared UI state exists and was exercised: loading, empty, error, validation,
      disabled, permission-denied — or is explicitly listed as out of scope.
- [ ] No accidental horizontal overflow at any viewport.
- [ ] No console errors.
- [ ] No dead controls. Anything the real system would own is labeled as a boundary.
- [ ] Every named brand's real logo is present; no product drawn as a CSS silhouette.
- [ ] Meaning never carried by color alone.
- [ ] Full-height sections use `100dvh` (or a `min-height` on it), not `100vh`, so a
      mobile browser's changing toolbar does not clip or jump the layout.
- [ ] Rendered and checked in **both** light and dark when the product supports both, not
      only the one the author looked at.
- [ ] Every imported package, font, and asset resolves: each import exists in the project
      manifest or is bundled, and no request fails.
- [ ] Forms and calls to action: every input has a visible label, helper text is in the
      markup, and an error shows beside its field; one label per intent across the page;
      ghost or outline buttons over imagery keep their contrast.
- [ ] Touch targets on touch layouts are at least 44×44 px with clear space between
      neighbours; a smaller icon gets a larger hit area.
- [ ] Layers follow one declared z-index scale of named tiers; no ad-hoc values.
- [ ] Hover and press states change no layout dimensions, so neighbours never shift.
- [ ] An async action disables its control or shows progress while it runs, and a second
      click cannot submit twice.
- [ ] Space is reserved for late content (image dimensions, skeletons), so nothing jumps
      when it arrives.
- [ ] Meaningful images have descriptive alt text, decorative ones an empty alt, and
      icon-only buttons an accessible name.
- [ ] The document declares a viewport meta tag and does not block zoom.
- [ ] Images are sized near their display size with explicit dimensions, and those below
      the first screen load lazily.
- [ ] A fixed or floating bar never covers content; the content carries a matching offset.
- [ ] Destructive or irreversible actions ask for confirmation or offer undo.

### Perceived finish — public and marketing deliverables only

One more floor row, and it is not measurable with a ruler. It applies whenever the
deliverable is **public-facing**: a marketing page, a landing page, a portfolio, a docs
home, anything a stranger will judge in the first second.

- [ ] **The three-second test.** Show the **first viewport only** — not the full-page
      capture — to a cold eye for three seconds, then take it away. Ask one question:
      *did that read as an invested, finished product page, or as a document, a spec, or
      an unfinished wireframe?* A "document" answer is a **fail**, and it blocks Gate 2
      exactly like a contrast failure does.

Capture the first-viewport frame at the real desktop height (roughly 1900×940, not a
tall stitched screenshot) and look at that frame, because that is the only frame most
visitors will ever see. A full-page render flatters a page: it shows the whole argument
at once and hides the fact that the opening screen was thin.

**A quiet direction must still pass this.** Restraint is not an exemption — see *"Quiet is
not bare"* in the taste calibration reference. The failure this row exists to catch is a
page that is correct on every measurable row, scores respectably, and still reads to its
own owner as an unfinished draft.

If you cannot get a cold eye, simulate one honestly: look at the first-viewport frame
after doing something else, describe out loud what it *is* before what it *says*, and
write the answer into the report verbatim — including when the answer is unflattering.

A failure here blocks Gate 2 regardless of how well the design scores below.

### Load and stability — public pages (recommended, not a floor)

Public pages also get a measured pass, with the tool and the conditions recorded, or the
check marked unverified. The commonly cited thresholds for a "good" result are a starting
point, not a pack rule: main content painted within about 2.5 s, response to input within
about 200 ms, and layout shift of about 0.1 or less. The cheapest fixes are layout-side:
reserve space for images, embeds, and late-loading fonts, and preload the hero image.

## Six dimensions, scored 0–10

Score with evidence, not adjectives. Every score cites something specific.

**0. Concept — weighted highest.**
Ask whether the design has an idea before asking how well it is executed. Execution is a
multiplier, and multiplying an empty concept only makes the emptiness bigger.

| Score | Standard |
| --- | --- |
| 9–10 | An idea grown from this content; the visual motif could not be swapped out |
| 7–8 | A clear intent; the motif relates to the content but would survive a neighboring topic |
| 5–6 | Style without concept: good-looking, saying nothing |
| 3–4 | A generic template wearing this content |
| 1–2 | Not even a style choice — decoration piled up |

Test it: *Can you state the idea in one sentence? Cover every word and logo — is the
subject still recognizable? Swap in a different client's name — does it still work?* If
the last answer is yes, it is a template, and this dimension caps at 5.

**Veto rule: concept ≤5 caps the overall score at 6.0.** Fix the concept before polishing
execution.

**1. Direction consistency.** Does the design actually deliver the direction chosen at
Gate 1, or has it drifted toward a house default? Check that the color, type, and layout
decisions trace back to `03-direction-decision.md`, and that no element contradicts the
stated intent.

**2. Visual hierarchy.** Does the eye move the way the designer intended? Heading-to-body
size contrast of at least 2.5× (3× is comfortable); three or four legible levels built
from size, weight, and color; white space guiding rather than merely existing. Squint at
it: if the hierarchy survives blurred, it is real.

**3. Craft.** One spacing system, used consistently (an 8-point scale is a safe default).
Equal spacing between equivalent elements. Controlled color count — one primary, one
secondary, one accent, plus a neutral ramp. At most two type families, with variation
carried by weight and size. Precise edge alignment.

**Craft floor for public deliverables: below 8 blocks shipping.** Craft is where "correct
but unfinished" shows up, and it is the dimension most easily waved through because
nothing on the hard floor is red. On a public-facing surface a 7 means *known rhythm,
spacing, or finish problems are going out the door where strangers will see them* — fix
them or do not ship. Internal artifacts, wireframes, and working prototypes are exempt.

**4. Function.** Every element earns its place: *remove it — is the design worse?* If not,
remove it. The primary action sits where the eye lands first. Information density matches
the medium and the viewing distance.

**5. Originality.** Avoided the known defaults (see the taste calibration reference).
Found a specific expression inside the chosen direction. Contains at least one decision
that is surprising and, on reflection, obviously right.

## Scoring guide

Overall is the weighted read, not a mean: **8.0+** excellent · **6.0–7.9** good ·
**4.0–5.9** needs work · **below 4.0** not acceptable. Concept ≤5 caps it at 6.0
regardless.

Two blocks sit on top of the bands, and both apply only to public-facing work: the
three-second test must pass, and **Craft must be 8 or higher**. A respectable overall
score does not buy passage past either. Passing a deliverable *because the total looked
fine* while its lowest dimension was the one a visitor sees first is the specific mistake
these two rules exist to stop.

## The report

```markdown
# 07 — UAT report
**Date:** YYYY-MM-DD · **Build reviewed:** <path or commit>
**Gate 2 state:** pending | human-approved | policy-auto-selected

## Hard floor
PASS / FAIL — <failing rows listed, each with file:line and viewport>

## Three-second test  (public/marketing deliverables only)
Frame judged: <first-viewport capture path, at the real desktop height>
Cold-eye verdict: <"invested product page" | "document" | "wireframe"> — <one honest line>
PASS / FAIL

## Scores
| Dimension | Score | One-line evidence |
|---|---|---|
| Concept | /10 | <the idea, in one sentence — or the absence of one> |
| Direction consistency | /10 | |
| Visual hierarchy | /10 | |
| Craft | /10 | <public deliverable? below 8 blocks shipping> |
| Function | /10 | |
| Originality | /10 | |
| **Overall** | **/10** | <band, and whether the concept cap applied> |

## Keep
- <what genuinely works, in design language — this calibrates the fixes>

## Fix
Ordered by severity: **blocking** / **important** / **polish**

**1. <name>** — blocking
- Now: <what it does today, with file:line>
- Problem: <why it is a problem>
- Fix: <the concrete change, with values>
- Verified: <before/after screenshot paths, commit>

## Quick wins
If there are only five minutes, do these three:
- [ ] <highest leverage>
- [ ] <second>
- [ ] <third>

## Motion review
<verdict from the motion playbook's review bar: block or approve, with findings>

## Unverified
<checks that could not be run — no browser, linter offline, device unavailable>

## Gate 2
Human-approved: "<their words>", YYYY-MM-DD
— or —
Policy-auto-selected: <criteria, decision, and the grant that permitted it>
```

## Reviewer discipline

- **Default to flagging. Approval is earned.** "It works" is not the bar.
- **Cite `file:line`.** A finding without a location is an opinion.
- **One fix per commit**, each with before/after evidence.
- **Say what you could not check.** Reading source is not a substitute for looking at the
  rendered result, and a report that hides its blind spots is worse than one that admits
  them.
- If a checker skill disagrees with the owner's decision, record both positions here
  rather than editing over the top of each other.

## Appendix — tells to scan for

A fast manual pass before scoring, alongside any static linter. Each hit becomes a Fix
item rated blocking, important, or polish. Items marked *advisory* are judgment calls
about density or context, never a blocker alone; the rest are defects when they appear.

**Hierarchy and type**
- Flat hierarchy: sizes too close together, one family carrying everything with no weight
  or size contrast.
- A rounded icon tile stacked above every feature heading.
- A tiny tracked label or pill chip above the hero headline that adds nothing the
  headline lacks.
- A full-sentence headline at display size that eats the whole first screenful.
- Letter-spacing tightened until the glyphs lose their shape.
- An italic serif display as the unexamined hero choice *(advisory; an editorial register
  can earn it)*.

**Color and effects**
- Gradient text on headings or metrics.
- Glowing colored shadows, chromatic halos, or a decorative radial spotlight behind a
  section.
- A thick accent border on one side of a card, or on a rounded card.
- A hairline border and a wide soft shadow on the same element *(advisory: commit to one)*.
- Stripe or grid-line background decoration with no job to do *(advisory)*.

**Layout and space**
- Cards nested inside cards.
- One spacing value everywhere, so the page has no rhythm.
- Numeric index labels on sections that are not a sequence *(advisory)*.
- A heading sitting as close to the block above as to its own content; body text flush
  against the viewport edge; cramped padding inside bordered containers.
- Body line length beyond roughly 80 characters; justified text without hyphenation; a
  skipped heading level.

**Motion**
- Bounce or elastic easing on interface elements.
- A pulsing status dot with no live data behind it.
- A decorative blinking caret *(advisory)*; scale or rotate on every image hover
  *(advisory)*.
- An auto-scrolling marquee used as filler.

**Copy and imagery**
- Stacked marketing buzzwords where a specific verb and noun would do.
- Aphoristic cadence, or any single punctuation mark saturating the copy *(advisory: the
  density is the tell, a few are fine)*.
- A hero illustration assembled from primitive shapes *(advisory)*.
- A broken or placeholder image still in the build.

**Errors to clear first**
- An uncaught script error on load, which can silently kill reveals and interactions.
- Content invisible at rest after every reveal handler ran (see *Rule zero* in the motion
  playbook).
- Text painted under an opaque layer, a positioned popover clipped by an overflow
  container, or cards cut off at a scroller's edge.
