# 06 — Motion spec (v2)

**Tokens used:** `--ease-out: cubic-bezier(0.23,1,0.32,1)` · `--ease-in-out:
cubic-bezier(0.77,0,0.175,1)` · `--dur-press: 140ms` · `--dur-ui: 220ms` ·
`--dur-reveal: 560ms` · `--dur-settle: 720ms` · `--stagger: 70ms`. All extend the scale in
`04-design-system/tokens.json`; nothing forked.

**Frequency tier: marketing / showcase.** Under the v1.1 patch to the motion playbook, a
surface seen once per visitor inverts the frequency table — entrance choreography is the
point rather than a violation, and the product's own claims must be demonstrated rather
than stated. Both halves of that patch are spent here deliberately.

**The constraint that shaped every decision:** this page argues that motion must be
earned. Motion here that could not survive its own review would refute the page. That is
why the refusal list is longer than the accepted list.

**What changed from v1.** v1's motion was correct and invisible — the owner's words were
"the motion is invisible on first load," and he was right: every animation was
scroll-triggered, so the first screen a visitor saw was completely static. v2 moves the
entrance budget to **load**, not scroll, so the first viewport is where motion is felt.

---

## Accepted — 9

| # | Where | Purpose | Trigger | Properties | Curve + duration |
| --- | --- | --- | --- | --- | --- |
| 1 | Buttons, `:active` (page + all four rigs) | Feedback | Press | `transform: scale(0.97)` | 140ms `ease-out` |
| 2 | Buttons, nav links, language toggle, hover | Feedback | Hover | `background`, `color`, `border-color` | 220ms `ease-out`, gated on `(hover:hover) and (pointer:fine)` |
| 3 | Sticky header border on first scroll | State indication | Scroll > 8px | `border-color` | 220ms `ease-out` |
| 4 | Language toggle, pressed state | State indication | Click | `background`, `color` | 220ms `ease-out` |
| 5 | **Hero headline, three lines rise** | Delight (rare tier) | **Load** | `opacity 0→1`, `translateY(20px→0)` | 620ms `ease-out`, 90ms stagger |
| 6 | **Exhibit plates settle onto the stage** | Delight (rare tier) | **Load** | `opacity 0→1`, `translate: 0 30px → 0 0` | 720ms `ease-out`, 110ms stagger |
| 7 | Step-spine tokens appear | Preventing a jarring change | Load | `opacity 0→1` | 320ms `ease-out` |
| 8 | Section blocks enter | Preventing a jarring change | Scroll, `IntersectionObserver` | `opacity 0→1`, `translateY(14px→0)` | 460ms `ease-out`, 70ms stagger, capped at 5 |
| 9 | **Step leader rules draw themselves** | Explanation | Scroll | `transform: scaleX(0→1)`, origin left | 560ms `ease-out` |

### Why 5 and 6 are the page's indulgence

They are the first impression, and on a page seen once that *is* the product demo. The
headline rising and the three specimen plates settling onto the slate say, before a word
is read, that this thing produces real artifacts and somebody arranged them. v1 had
nothing here and paid for it.

Both exceed the 300ms UI budget deliberately: neither is a response to an interaction, and
nothing is blocked while they play. Every actual UI *response* on the page — press, hover,
toggle, header state — stays at 220ms or less. Both animate `transform`/`opacity` only.

### Why 9 survives from v1

The leader rule that draws itself between a step and the artifact it leaves on disk is the
one v1 device worth carrying: it is motion with a *nameable* job (it connects two things
that belong together), and it is the only piece of the specimen-sheet language that
transplanted cleanly onto the dark stage. It also uses a dedicated `<i>` element rather
than a container — v1's worst bug was scaling a parent and squashing its own label.

---

## The live motion section — teaching material, not page motion

The four rigs in §02 are the demonstration half of the marketing branch. They are **not
page motion**: nothing plays on its own, every one of them requires a press, and their
values are visible in the interface as labels because *the value is the lesson*.

| Rig | Demonstrates | Values on screen |
| --- | --- | --- |
| A — Press feedback | Why 140ms and why never `ease-in` on UI | none · 140ms `ease-out` · 400ms `ease-in` (the counter-example) |
| B — Curve at equal duration | Duration is not what makes motion feel fast | both 520ms · `linear` vs `cubic-bezier(.23,1,.32,1)` |
| C — Stagger | Why the playbook says 30–80ms | 0ms · **60ms** · 200ms, over 7 tiles |
| D — Interruption | Why anything fired rapidly uses transitions | both 620ms `ease-in-out`; one CSS transition, one CSS keyframe |

Rig A is pure CSS and needs no script at all. Rig D's keyframe half is gated behind a
`.touched` class, because without it the "return" keyframe fires once at page load — an
unsolicited animation on a rig whose entire point is that it is press-only.

---

## Rejected — 10

| Location | Considered | Rejected because |
| --- | --- | --- |
| Hero heading | Word-by-word or character-by-character reveal | **Gate 2 — purpose.** No nameable purpose, and it delays the one sentence carrying the whole argument. The most-copied AI motion cliché available. The three-line rise does the same job without withholding a word |
| The mark word "design" | Gradient sweep or colour cycle | **Gate 2 — purpose**, and it is flagged default #2 in the pack's own taste reference. This is the exact treatment direction B was originally rejected for; animating it would have been worse than shipping it static |
| The dark ground | Scroll-linked parallax on the stage | **Gate 4 — function.** The stage is what the content is read against. Full-viewport ambient motion is also on the reduced-motion avoid list |
| The dark ground | Cursor-following spotlight or glow | **Gate 4 — function**, and it is the single most predictable move available on a dark page. It would also reintroduce the glow the direction decision banned in writing |
| Language toggle | Cross-fade or slide between EN and VI | **Gate 1 — frequency**, and correctness. It fires on a deliberate action the user wants completed *now*; animating a full page of text swap looks like a page reload |
| Step rows | Hover lift with a shadow | **Gate 4 — function.** They are rows in a specification, not cards, and they are not clickable. A lift would promise a click that never happens |
| Install code blocks | Typewriter effect on the commands | **Gate 2 — purpose**, and honesty. It would dramatise a command that does not work yet |
| Nav links | Scroll-spy underline animating between sections | **Gate 3 — speed.** Fires continuously during scroll on a six-section page; cost exceeds benefit |
| The 9 / 10 counters in the motion spec card | Number ticker counting up | **Gate 2 — purpose.** They are two small integers. A ticker would be motion applied to a number because the number was there |
| Exhibit plates | Lightbox with a shared-element zoom | Scope. Real value, but it needs focus management, Escape handling and focus restoration — a dialog contract this page does not otherwise have. Deferred rather than half-built |

Nine accepted, ten refused. The refusals are the deliverable as much as the accepted list
is, and the page says so on its own face.

---

## Rule zero — the contract, verified

Content renders whether or not any animation ever plays. Four parts, all present:

1. **Visible is the default.** Every hidden state lives under `.js`, a class the same
   script adds. No script, nothing ever hides.
2. **Unconditional failsafe.** `.lit` (load entrances) is set on the next animation frame,
   again on `load`, and again on a 900ms timer. Scroll entrances get `revealAll()` on
   `load` + 1200ms regardless of the observer.
3. **Bypass when unavailable.** Reduced motion or a missing `IntersectionObserver` reveals
   everything immediately; no degraded animation is attempted.
4. **`@media print`** forces the final state.

Measured, not asserted — elements still hidden after settle:

| Condition | Hidden elements |
| --- | --- |
| JavaScript disabled | **0** |
| `prefers-reduced-motion: reduce` | **0** |
| `@media print` | **0** |
| Full-page screenshot capture | **0** |

## Accessibility

Under `prefers-reduced-motion: reduce`, every page entrance — hero lines, plates, spine,
section blocks, leader rules — is switched off and rendered final immediately. Press and
hover feedback survive as instant colour changes, because they answer what the user just
did.

**The four rigs keep working under reduced motion, and that is a deliberate call.** The
preference exists to stop motion the user did not ask for; these only move when pressed,
which is the same category as a video the user pressed play on. A note appears in that
section under the preference saying exactly this, in both languages, so the choice is
disclosed rather than assumed. The alternative — silently disabling the demos — would
leave a reader with the preference set looking at four dead boxes and no explanation.

If this is judged wrong at final review, the fix is one rule: add
`.pbtn, .tgl i, .carrier, .tiles i { transition-duration: 1ms !important }` inside the
reduce block and change the note.

## Needs a feel check

- **The load choreography as a whole.** Headline lines at 90ms apart and plates at 110ms
  apart total roughly 400ms of arrival. Judged from values and still frames; it needs a
  human watching a real first load, ideally on a cold cache.
- **Rig B's honesty.** Whether the linear/eased difference is actually legible at 520ms
  over that track length, or whether it needs a longer travel to read.
- **Rig D's jump.** The keyframe restart is the whole lesson; it needs someone to slam the
  toggle mid-travel and confirm the jump is obvious rather than subtle.

## Verdict

The highest-leverage item is #6, the plates settling. If only one animation survived, it
would be that one — it is the moment the page stops being a document and becomes something
a person arranged. The second is the live section: on a page arguing that motion must be
earned, four working examples are worth more than four paragraphs, and they cost the same.
