# 05 — Implementation (v2)

Two passes, per the taste-calibration reference: the plan, then the plan critiqued, then
the code.

**Output:** `05-build-source.html` (source, image placeholders) → `05-build.html`
(self-contained, images inlined) → `docs/index.html` in the repo. Same file, one build
step.

---

## Pass 1 — the plan

### The five form questions

1. **Narrative role.** A hero and a close in one page. The page has to do the persuading
   *and* the explaining, because there is no second page.
2. **Viewing distance.** 1m laptop, primary. The review frame is 1905×937 — one screenful,
   three seconds.
3. **Emotional temperature.** Confident and sober, with one thing that is unmistakably
   *made*. v1 was sober and nothing else, and that is what read as a document.
4. **Capacity.** Seven sections plus a live demo section. The live section is the largest
   single addition over v1 and it earns its space by being the product's own argument.
5. **Visual motif — the important one.** *The stage is slate; wherever a human decides,
   the page turns to paper.* The process alternates between a machine surface and a human
   surface, and the page alternates the same way. Gate rows invert to full-bleed paper
   bands. The deliverables band is paper. Every artifact is a paper plate on the slate.

That motif belongs to this content. Swap in another client and it collapses — which is the
template test, passed in the right direction.

### Colour

Three hue families, derived in `04-design-system/tokens.json`:

- **Slate H 258, chroma 0.012–0.015** — five steps. Direction B's ground, pushed one notch
  cooler-neutral and pulled to the bottom of the large-surface chroma band so it reads as
  ink, not navy.
- **Warm paper / chalk H 85–90** — carried unchanged from v1, where it was sampled and
  justified. Demoted from ground to exhibit material, which is the whole idea.
- **Drafting red H 30** — the only chromatic colour on the page. Four values: on-stage,
  deep fill, text-safe-on-paper, wash.

**Deleted, not adjusted: direction B's cyan (H 205).** It was half of flagged default #4.
A cool accent on a cool ground is the sameness the direction was rejected for; the warm
accent against slate is a different animal and does the same job.

Chalk is warm (H 90) rather than slate-hued for the same reason, at text scale: a warm
white on a slate ground repeats the paper/stage opposition in every paragraph.

### Type

Two families, three roles — the same two as v1, redistributed. In v1 mono carried the
page's character; here the oversized display face does, and mono drops back to labels,
stamps, filenames and code.

- Display: system grotesque stack, 640 weight, tracking −0.038em, leading 0.94, up to 92px
  (settled at 80px after the first-viewport fit check).
- Body: same family, 400, 17px, 1.65.
- Mono: labels at 12px, 0.14em tracking, uppercase.

Heading-to-body is **5.4×** at desktop against a 2.5× floor. v1 ran 3.6×. The size increase
is not decoration — it is the direction.

**No webfont.** The page stays self-contained with zero network requests, which is a
property worth more here than a specific grotesque. Recorded as a trade, not an oversight:
if a webfont is ever added it should be self-hosted and subset, never a third-party link on
a page that currently has none.

### Layout

Full-bleed alternating bands inside a 1320px container. Deliberately *not* one skeleton
repeated:

```
HERO      headline full width · sub+CTA left / plate stack right · 8-token spine
STEPS     ruled rows, full-bleed — two of them invert to paper
MOTION    two-column header + 2×2 live rigs
TRAIL     full-bleed PAPER band — specimen sheet + two notes
STORY     prose left / two large evidence plates right
INSTALL   two code panes
WHO       two cards
FOOTER    acknowledgements, two columns
```

Section headers run **two columns** — heading left, lead right. A stacked header left the
right half of every band empty, which is precisely the even unfilled rhythm v1 was
rejected for.

### Signature

Two, because one was not enough to carry seven bands:

1. **The paper plate.** A framed, slightly rotated specimen lifted off the slate by a
   single neutral shadow, with a stamped mono caption. Used five times: three in the hero
   stack, two as evidence in the story.
2. **The paper inversion at each gate.** A full-bleed band changing ground mid-page. It is
   the loudest thing on the page and it is carrying the page's one structural claim.

---

## Pass 2 — critiquing the plan before building

*Would I have produced this for any similar brief?*

- **Deep slate + oversized type + a single warm accent** — yes, I might. This is the most
  reachable answer for a developer-tool page in 2026. **Revised:** the answer is not the
  palette, it is the paper. Slate alone is a style; slate that *turns into paper wherever
  a person decides* is a claim about the content. Every place the plan could have used a
  tinted panel, it uses paper instead, and the two gate rows became full-bleed rather than
  tinted cells so the inversion is unmissable.
- **A step list with big ghosted numerals** — yes, generic. **Revised:** added the third
  column and the leader rule, so each row states *what it leaves on disk*. The row is now
  a specification line rather than a feature bullet, and the leader is v1's callout device
  carried forward with a job to do.
- **"Interactive demos" on a marketing page** — usually decoration. **Revised:** each rig
  demonstrates a rule the product actually teaches, and every value is printed on screen
  as a label because the value *is* the lesson. If a rig cannot state which line of the
  playbook it proves, it is cut. One was: a spring-vs-tween rig, dropped because the
  playbook's spring guidance is about gesture handoff and a click-to-run rig would have
  misrepresented it.
- **Showing the rejected v1 page** — could read as self-flagellation. **Kept**, and made
  concrete: it sits beside the actual step-2 wireframe, at the same crop, so the argument
  is visual rather than confessional. The two frames look alike. That is the point, and it
  is the strongest single piece of evidence on the page.

### The element removed before delivering

The hero originally carried an animated red underline drawing itself beneath the word
*design*. It was cut: it read as a second accent competing with the plate stack, it did not
survive the inline-positioning it needed, and the word is already the only red thing at
80px. One bold moment per area — the plates own the hero's lower half, the type owns the
upper half, and the underline was a third voice.

---

## Build notes

- **Every grid child carries `min-width: 0`.** Grid items default to `min-width: auto`, so
  a long command inside `<pre>` forces its column wider than the viewport. That was v1's
  mobile overflow bug; the rule is inherited here rather than re-learned.
- **`img { height: auto }` is not optional** when `width`/`height` attributes are present
  for aspect-ratio reservation — without it the attribute height wins and images distort.
  Caught in the first render pass.
- **Specificity.** The reduced-motion override for `.rm-note` originally sat in a media
  block *above* the base `.rm-note { display: none }` rule, so equal specificity meant the
  later base rule always won and the note never appeared under the preference. Fixed by
  keeping the override adjacent to the rule it overrides. This is the exact CSS-collision
  trap the taste reference warns about, and it cost a real bug.
- **The rig markup is progressive.** Rig A works with no JavaScript at all (pure `:active`).
  Rigs B–D need script, and their *explanations* are static text that renders regardless.
- **Images** are five JPEGs inlined as data URIs, 620–760px wide, 17–33 KB each. Total page
  226 KB, self-contained, no network requests. The two evidence plates are cropped to the
  1905×937 review aspect so they show a **first viewport**, not a stitched full page —
  which is the same distinction the new UAT rule makes.

## Deliberate leftovers

- **Font stack is system.** See above. A named grotesque would sharpen the display type.
- **`--s1` and `--s7` are declared and unused.** They are the ends of a complete 8px
  scale; a scale with holes punched in it to satisfy a usage count is a worse artifact
  than an unused step. Recorded rather than hidden.
- Two genuinely dead things were found by a usage sweep and **deleted**, not documented:
  a `--mark-wash` token nothing referenced, and a `.prose` utility class no element
  carried. An unreferenced token is not restraint, it is residue.
