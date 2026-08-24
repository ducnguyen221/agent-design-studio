# 03 — Direction decision

**Gate 1 state:** `policy-auto-selected`
**Date:** 2026-08-24
**Grant:** The D3 session grant explicitly permits auto-selection for this run. All three
renders and screenshots are preserved so the decision can be overruled at final review.

## Presented

| # | Logic | Anchor | File | Screenshot |
| --- | --- | --- | --- | --- |
| A | Dice roll | Clock seconds `30` → `30 % 20 + 1` = **11** → *Engineering drawing / annotated specimen* | `03-directions/a.html` | `a.png` |
| B | Verified exemplar | **By-Kin** (UK studio site). Verified 2026-08-24 via search: winner of Awwwards Site of the Day, Awwwards Developer Award, an FWA, and CSS Design Awards Web of the Day. Documented design language: *confident editorial typography, weighted smooth scroll, transitions*. | `03-directions/b.html` | `b.png` |
| C | Unlimited-budget studio | A practice in the lineage of Japanese reductive design — emptiness as content, materiality, extreme restraint | `03-directions/c.html` | `c.png` |

### The dice-roll catalogue used

The `style-knowledge` slot was unfilled on this run, so the roll needed a catalogue. The
pack does not ship one — see the gap note at the bottom. The list below was constructed
for this run and is recorded so the roll is auditable and reproducible:

1 editorial brutalism · 2 Swiss grid · 3 terminal/docs · 4 risograph print · 5 blueprint ·
6 museum archival · 7 control room · 8 zine collage · 9 Bauhaus geometric · 10 soft
neo-brutalist · **11 engineering drawing / annotated specimen** · 12 kinetic type poster ·
13 dark cinematic · 14 field guide · 15 broadsheet · 16 modernist book · 17 isometric
diagram · 18 monospace manifesto · 19 gallery editorial · 20 wayfinding system

### Structural differences (verified, not asserted)

| | A | B | C |
| --- | --- | --- | --- |
| Skeleton | Bordered sheet + vertical index rail + bordered figure grid | Full-bleed stacked sections + **horizontal scroll-snap rail** | Single 660px centred column, list rhythm |
| Ground | Warm paper | Deep slate | Near-white |
| Steps shown as | 4×2 bordered figure cells | Horizontal cards | Vertical ruled list |
| Type | Mono labels + tight sans display | Oversized sans, 104px | Light-weight sans, centred |

No two share a skeleton.

## Decision

**Chosen: A — Specimen Sheet.**

### Criteria applied

Scored against the pack's own review dimensions, concept weighted highest.

| Criterion | A | B | C |
| --- | --- | --- | --- |
| Concept — form derived from content | **9** | 5 | 6 |
| Survives the swap-the-client-name test | **9** | 3 | 4 |
| Distance from the flagged AI defaults | **9** | 2 | 6 |
| Room for *justified* motion | **9** | 7 | 4 |
| Immediate impact in one screenful | 7 | **9** | 5 |
| Readability floor headroom | 8 | 8 | **9** |

### Why A won

1. **The form comes from the content.** A process specification drawn as an engineering
   specimen sheet — figure captions, callout leaders, dimension rules, `GATE` stamps — is a
   motif this content has and no neighbouring topic does. That is the fifth form question
   answered concretely, and concept is the dimension that vetoes everything else.
2. **It fails the template test in the right direction.** Swap in another client and A
   collapses; B and C survive the swap, which means they are styles rather than concepts.
3. **It is the only one that is not a version of what the pack tells people to avoid.**
4. **Motion has something to explain.** Leaders that draw themselves and rules that extend
   are motion with a stated purpose. B's motion would be scroll decoration; C's has almost
   nowhere to go.

### Why B was rejected

B is the most immediately impressive render and the strongest single screenful — and it is
disqualified for exactly that reason. Deep ground plus a bright cool accent plus a
**gradient headline** is simultaneously flagged default #2 and #4 in the pack's own taste
reference. Shipping it as the face of a pack whose central argument is *do not spend your
freedom on the default* would refute the product on its own homepage. It is also the
closest of the three to the inspiration site, which the brief explicitly warned against.

Kept on disk: if the owner overrules on impact grounds, B is the fallback, but the gradient
headline must go regardless.

### Why C was rejected

C has the best readability headroom and the calmest craft, but it is the weakest concept —
a well-set centred column that would suit any thoughtful software product. Its hero is
entirely typographic with no anchor beyond one underline, which is precisely the failure
mode the direction-gate reference warns about: restraint far enough that the first screen
reads as unfinished rather than composed. It also strands the motion step.

## Carried forward into Step 5

- **Layout skeleton:** bordered sheet, vertical index rail, figure-numbered sections.
- **Type roles:** tight semibold sans display · sans body · mono for labels, captions,
  file names, and stamps. Mono is the character-carrying face here, not decoration.
- **Colour starting point:** warm paper ground, cool cyan-leaning ink and hairlines, one
  drafting-red mark. Final values derived in `color-protocol` — nothing fixed here.
- **Signature element:** the callout/leader system — figure captions that sit on the rule,
  `GATE` stamps, and leaders that connect a label to the thing it names.

### Fixes required before build (found by looking at the render)

1. The page-wide background grid escapes the sheet and leaves unresolved edges. Contain it
   inside the sheet or drop it.
2. The `GATE` stamp is positioned with a negative-margin hack that will break at other
   widths. Rebuild it as a proper inline element.
3. Hero at 390px is unverified — the index rail hides, so the composition changes and needs
   its own check.
4. A carries only two sections. The build must add showcase, install, audience, footer,
   and the Vietnamese layer.

---

## Process gap found during this step — for v1.1

`SKILL.md`'s capability-slot table promises that when `style-knowledge` is unfilled, the
fallback is *"style axes in `references/direction-gate.md`"*. **That section does not
exist.** `direction-gate.md` describes the dice-roll logic but ships no catalogue to roll
against, so the fallback promise is unfulfillable as written — a student installing only
this pack cannot run direction A as specified.

Two possible fixes, for the reviewer to choose: ship a compact catalogue of ~20 style names
per output form inside `direction-gate.md`, or reword the slot fallback to say the agent
constructs a catalogue for the run and records it in the decision file — which is what
happened here, and it worked. Logged in `07-uat-report.md`.
