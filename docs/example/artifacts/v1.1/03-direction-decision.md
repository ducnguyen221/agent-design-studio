# 03 — Direction decision (v2)

**Gate 1 state:** `human-approved`
**Date:** 2026-08-24
**Supersedes:** `../2026-08-24-agent-design-studio-site/03-direction-decision.md`
(`policy-auto-selected`, direction A — Specimen Sheet)

## What happened

v1.0 shipped. The site went live at `ducnguyen.vn/agent-design-studio` on direction A, the
specimen sheet, auto-selected under the D3 session grant with all three renders preserved
on disk "so the decision can be overruled at final review."

The owner looked at the live page and overruled it.

> It reads as a wireframe — a spec document, not a designed website. The full-page grid
> feels like *chia ô* (chopped into boxes). There is almost no colour. The motion is
> invisible on first load. One even rhythm all the way down. It has to read as a product
> somebody invested in.
>
> — Đức, 2026-08-24, on the live v1.0 page

**This is the gate mechanism working exactly as designed, and it is worth saying so
plainly.** The pack's own gate-state model exists because an auto-selected decision is a
*provisional* decision: the renders stay on disk, the reasoning is written down, and a
person can come back and overrule it with the evidence in front of them. That is what
happened. The auto-selection was not a mistake in the process — shipping it without ever
running the human gate would have been.

What *was* a process defect is that nothing in the pack caught the problem before the
owner did. v1's own UAT scored **Craft 7 — its lowest dimension — and passed it anyway**,
because the overall 7.8 looked respectable and every hard-floor row was green. A page can
be measurably correct and still read as unfinished, and v1.0 is now the pack's canonical
example of it. Three patches went into the skill in the same session (see the v1.1 notes
in `SOURCES.md`).

## Decision

**Chosen: B — Weighted Editorial, de-defaulted.**

B was already on disk from the v1 run, already scored, and already carried the note that
made this switch cheap:

> "B is the most immediately impressive render and the strongest single screenful — and it
> is disqualified for exactly that reason … Kept on disk: if the owner overrules on impact
> grounds, B is the fallback, but the gradient headline must go regardless."

The owner has now overruled on impact grounds. B is promoted, under the constraint its own
rejection note recorded.

### What carries over from B

- Deep slate ground rather than warm paper.
- Oversized confident display type as the primary visual event — type is the image.
- Full-bleed stacked bands instead of a bordered sheet.

### What is banned, and stays banned

B was rejected in v1 for landing on two flagged AI defaults at once. Promoting it does not
un-flag them. Explicitly refused in this build:

| Refused | Where it was in B | What replaces it |
| --- | --- | --- |
| **Gradient headline** (`linear-gradient` clipped to text) | `h1 .g` in `03-directions/b.html` | The mark word set in flat drafting red, with a red rule under it |
| **Neon glow on a dark ground** | Not in the render but the genre's next move | Zero glow, zero bloom, zero coloured shadow. Every surface is matte |
| **Uniform navy + cyan sameness** (flagged default #4) | `--brand: oklch(0.72 0.118 205)` cyan on `--ground` navy | The cool accent is deleted outright. The only chromatic colour on the page is drafting red at H 30 |
| Rounded pill buttons and 16px card radius | `border-radius: 99px` / `16px` | 2px. The v1 drawing-sheet discipline survives here |

Deleting the cyan is the decisive move. Flagged default #4 is *specifically* the deep-navy
+ generic-cool-neon pairing; a deep slate whose only accent is a warm drafting red is a
different animal, and the taste reference says so in as many words — authored dark design
carries strong stylistic information and is the cure for sameness, not an instance of it.

## The concept — how A and B become one page

The two directions are not being swapped. They are being **composed into a single idea**,
which is what makes this a concept rather than a restyle:

> **The stage is slate. Wherever a human decides, the page turns to paper.**

The dark ground is the machine's working surface — where the agent runs. The warm paper
from direction A survives as **exhibit material**: every artifact the process *produces or
hands to a person* appears as a light paper plate on the dark stage. The two gate steps
invert to paper bands mid-page. The artifact trail is a full-bleed paper band. The real
renders from this page's own run are paper plates, framed and stamped.

Form from content, stated in one line: *the process alternates between a machine surface
and a human surface, and the page alternates the same way.* That motif belongs to this
content and to no neighbouring topic — the fifth form question, answered concretely.

It also means v1 was not thrown away. The warm paper, the mono labels, the `GATE` stamps
and the drafting red are all still here, doing a job they were not doing before: they are
the drawings, and they now have a stage to sit on.

## Carried forward into Step 5

- **Layout skeleton:** full-bleed alternating bands — slate, slate, slate-with-paper-rows,
  slate, full paper, slate, slate — inside a 1320px container. No bordered sheet, no
  index rail, no uniform figure grid. The v1 skeleton is gone.
- **Type roles:** oversized semibold sans display (up to 92px, tracking −0.038em) · sans
  body 17px · mono for labels, stamps, filenames and code. Mono keeps its v1 job.
- **Colour:** three hue families only — slate H 258, warm paper/chalk H 85–90, drafting red
  H 30. No fourth hue. Values derived in `04-design-system/tokens.json`.
- **Signature elements, two of them:** (1) the paper plate — a framed, slightly rotated
  specimen lifted off the slate with a shadow and a stamped caption; (2) the paper
  inversion at each gate row.
- **The delight budget is spent, deliberately.** Per the v1.1 motion patch, a page seen
  once per visitor runs on the delight budget, and a product that sells motion craft must
  demonstrate it rather than assert it. This build carries a live, interactive motion
  section. Values and refusals in `06-motion-spec.md`.

## Fixes required before build, carried from v1's report

1. **Craft floor.** v1's Craft 7 shipped. Under the v1.1 rule, a public deliverable below
   Craft 8 does not ship. This build is judged against that.
2. **Three-second test.** The first viewport is now captured and judged **on its own**, at
   1905×937 — the real frame, not a stitched full-page render that flatters the page.
3. Rule zero contract carried over intact from v1 (it worked): visible-by-default markup,
   `.js`-armed hidden states, unconditional failsafe reveal, reduced-motion and no-observer
   bypass, `@media print` final state.
4. The 12px label floor and 4.5:1 contrast floor are re-measured on the new ground. A dark
   ground moves every pairing; none of v1's measurements transfer.
