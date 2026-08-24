# 06 — Motion spec (v3)

**Tokens:** `--ease-out: cubic-bezier(0.23,1,0.32,1)` · `--ease-lift:
cubic-bezier(0.16,1,0.3,1)` · `--ease-card: cubic-bezier(0.18,0.89,0.32,1.06)` ·
`--ease-in-out: cubic-bezier(0.77,0,0.175,1)` · `--dur-press: 140ms` · `--dur-ui: 220ms` ·
`--dur-reveal: 560ms` · `--dur-deal: 780ms` · `--dur-slam: 520ms`.

**Everything below animates `transform` or `opacity` and nothing else.** There is no
`clip-path`, no `width`/`height`, no `background-position`, no `filter` animation anywhere
in the file. That was a constraint, and it changed at least one design decision — see
*the shutter, not the fill* below.

---

## The budget, and who set it

**Frequency tier: marketing / showcase, with an owner-mandated wide delight budget.**
Recorded in `00-owner-directive.md`. The owner reviewed the live v1.1 page and asked for
an immediate "wow" on first view, with motion as a feature of every section rather than of
the four demonstration rigs alone.

**This inverts the v2 spec's own headline claim.** v2 said, in writing, that the refusal
list should be longer than the accepted list, because a page arguing that motion must be
earned would be refuted by motion that could not survive its own review. That is still the
*default*, and it is still the right default. It is not what this page does now, and the
honest way to say that is: **the restraint preference did not lose an argument, it was
outranked by the person who owns the surface.**

What did not change is the test. Each of the 21 below was still asked the same four
questions — how often does it fire, what is it for, does it cost anything the reader can
feel, does it fight the function — and 18 candidates still failed. A wide budget bought
*more* motion, not *cheaper* motion.

---

## Accepted — 21

### Interaction feedback (unchanged from v1.1)

| # | Where | Purpose | Trigger | Properties | Curve + duration |
| --- | --- | --- | --- | --- | --- |
| 1 | Every button and link-button | Feedback | `:active` | `transform: scale(0.97)` | 140 ms `ease-out` |
| 2 | Buttons, nav links, rig buttons, segmented control | Feedback | `:hover` | `background`, `color`, `border-color` | 220 ms `ease-out`, gated on `(hover:hover) and (pointer:fine)` |
| 3 | Sticky header border | State | scroll > 8 px | `border-color` | 220 ms `ease-out` |
| 4 | Language toggle, pressed | State | click | `background`, `color` | 220 ms `ease-out` |

### The load choreography — the first 1.8 seconds

Fired by `.lit`, set on the second animation frame, again on `load`, and again on a 900 ms
timer. Nothing here is blocked on anything; every element's final state is its CSS default
without the `.js` class.

| # | At | What happens | Properties | Curve + duration |
| --- | --- | --- | --- | --- |
| 5 | **0 ms** | **The stage lights up.** A soft, neutral lift comes up behind the three specimens — a light on the objects, not a wash behind the page | `opacity 0 → 1` | 900 ms `ease-out` |
| 6 | **20 ms** | The red rule and eyebrow rise | `opacity`, `translateY(16px → 0)` | 520 ms `ease-lift` |
| 7 | **130 / 220 / 310 ms** | **The headline's three lines rise with weight**, each out of its own mask so the words appear from behind the line above | `opacity`, `translateY(26px → 0)` | 640 ms `ease-lift`, 90 ms apart |
| 8 | **470 / 590 / 710 ms** | **The three plates deal onto the stage**, bottom of the pile first, each arriving from a different angle and landing into its final tilt | `opacity`, `translate`, `rotate` (−24°→−7°, +15°→−2°, +23°→+3.5°) | 780 ms `ease-card`, 120 ms apart |
| 9 | **440 ms** | The lead paragraph and the two buttons rise together | `opacity`, `translateY(16px → 0)` | 520 ms `ease-lift` |
| 10 | **790 ms** | **The red word gets its moment: the ink floods in.** A flat slate shutter over the already-red word retracts to the right | `transform: scaleX(1 → 0)`, `transform-origin: right` | 560 ms `ease-out` |
| 11 | **840 ms** | The specimen caption rises | `opacity`, `translateY` | 520 ms `ease-lift` |
| 12 | **1230 ms** | **The `GATE 1` stamp slams and settles** — 2.4× down through 0.92, back up to 1.05, resting at 1 | `opacity`, `transform: scale()` keyframe | 520 ms `ease-out` |
| 13 | **1290 ms** | The eight index cells light left to right, ending the sequence on `07 · Sign-off · you` | `opacity 0 → 1` | 320 ms `ease-out`, 36 ms apart |

**Second by second, this is what a visitor sees.** At 0.0 s the ground brightens under the
specimen area. At 0.1–0.9 s three lines of type rise into place one after another, and the
supporting paragraph and buttons come up beneath them. At 0.5–1.5 s three paper plates
swing in from off-angle and land in a fan. At 0.8–1.35 s red floods left-to-right through
the last word of the headline. At 1.23 s a stamp lands hard on the top plate and settles.
At 1.29–1.8 s the eight-step index lights up across the bottom of the frame. Then it stops
and the page is still, except for one blinking caret.

### Ambient — exactly one element

| # | Where | Purpose | Properties | Curve + duration |
| --- | --- | --- | --- | --- |
| 14 | The red square in the wordmark | The page is never fully dead; a terminal caret is the one idle motion that means something on a page about tools | `opacity 1 ↔ 0.2` | 1.12 s `steps(1, end)`, infinite |

**Why one and not several.** Ambient motion is the easiest thing on this list to overspend.
One blinking caret in a mono wordmark reads as a machine that is on. Two would read as
decoration; three would read as a screensaver. It is 8 px square, it is nowhere near
anything anyone is reading, and it is the first thing switched off under reduced motion.

### The red thread — the process as one continuous stroke

| # | Where | Purpose | Trigger | Properties |
| --- | --- | --- | --- | --- |
| 15 | A 2 px drafting-red rule down the step list, from `00` to `07`, with a small diamond head travelling at its tip | **Explanation.** It draws the seven steps as one unbroken line and runs *straight through* both paper checkpoint bands — the visual argument that a gate is part of the work, not a pause in it | scroll position | `transform: scaleY(0 → 1)` on the rule, `transform: translateY()` on the head. One `passive` scroll listener, coalesced through `requestAnimationFrame`, writing two transforms |

Progress is `(0.78 × viewportHeight − listTop) / listHeight`, clamped. The head is hidden
at both ends so there is no dot parked at the top or bottom. Without JavaScript the rule
renders at full length and the head never appears.

### Steps that perform

| # | Where | Purpose | Properties | Curve + duration |
| --- | --- | --- | --- | --- |
| 16 | Step numerals | The numeral is the heaviest thing in the row, so it moves like it | `opacity`, `translateY(22px → 0)` | 560 ms `ease-lift` |
| 17 | Step body, then the filename column | The row assembles in reading order | `opacity`, `translateY(14px → 0)` | 460 ms `ease-out`, +70 ms and +140 ms |
| 18 | Leader rule between body and filename | Connects two things that belong together | `transform: scaleX(0 → 1)`, origin left | 560 ms `ease-out`, 150 ms delay |
| 19 | **Gate bands** — the red edge above draws left-to-right, the edge below draws right-to-left, and the `YOU DECIDE` tag slams | The checkpoint rules itself off in front of you and gets stamped, instead of arriving pre-ruled | `scaleX(0 → 1)` + `scale()` keyframe | 520 ms `ease-out` |
| 20 | Section blocks (rigs, notes, evidence plates, audience cards) | Preventing a jarring change | `opacity`, `translateY(14px → 0)` | 460 ms `ease-out`, 70 ms stagger, capped at 5 |

### The plates answer the pointer

| # | Where | Purpose | Properties | Curve + duration |
| --- | --- | --- | --- | --- |
| 21 | The three specimen plates lift and straighten under the pointer, their captions darken and grow a short red underline; the evidence plates lift; **the turned-down plate shakes "no"** | Feedback, and one moment of character on the one object the page has already told you was refused | `translate`, `rotate`, `color`, `scaleX` on the underline; `translateX` keyframe for the refusal | 260 ms `ease-out`; the shake is 420 ms `ease-in-out`, class-guarded to one play per approach |

---

## Refused — 18

| Location | Considered | Refused because |
| --- | --- | --- |
| Hero headline | Word-by-word or character-by-character reveal | **Purpose.** No nameable job, and it withholds the one sentence carrying the argument. The most-copied AI motion cliché available. The three-line rise does the same work without hiding a word |
| The word "design" | Gradient sweep or colour cycle | **Purpose**, and it is flagged default #2 in the pack's own taste reference. This is the treatment direction B was originally rejected for; animating it would be worse than shipping it static |
| The dark ground | Scroll-linked parallax | **Function.** The stage is what the content is read against. Full-viewport ambient motion is also on the reduced-motion avoid list |
| The dark ground | Cursor-following spotlight or glow | **Function**, and it is the single most predictable move available on a dark page. It would reintroduce the glow the direction decision banned in writing |
| Language toggle | Cross-fade or slide between EN and VI | **Frequency**, and correctness. It fires on a deliberate action the user wants completed *now*; animating a full page of text swap looks like a reload |
| Step rows | Hover lift with a shadow | **Function.** They are rows in a list, not cards, and they are not clickable. A lift would promise a click that never comes |
| Install commands | Typewriter effect | **Purpose**, and honesty. Fake typing on a command that is real is theatre |
| Nav links | Scroll-spy underline animating between sections | **Cost.** Fires continuously during scroll on a six-section page |
| The two counters (21 / 18) | Number ticker counting up | **Purpose.** Two small integers. A ticker would be motion applied to a number because the number was there |
| Specimen plates | Lightbox with a shared-element zoom | **Scope.** Real value, but it needs focus management, Escape handling and focus restoration — a dialog contract this page does not otherwise have. Deferred rather than half-built |
| **Gate bands** | **3D page-turn — `perspective` + `rotateX` as the band flips to paper** | **Correctness.** Either the paper arrives with dark ink on a slate ground mid-rotation — unreadable transient — or the text has to be hidden behind the flip, which puts content behind an animation. A full-bleed band also clips against its neighbours under 3D. The drawn edges plus the slamming tag give the same beat with nothing at risk |
| **The paper deliverables band** | **Scroll-linked horizontal drift on the sheet, like a specimen conveyor** | **Function.** It moves a list of real filenames the reader is trying to read. "Data the user reads doesn't jitter" is not negotiable, and a filename is data |
| **Step numerals** | **Counting up 00 → 07 as each row enters** | **Purpose.** They are labels, not quantities. Counting them implies an accumulating total that does not exist. The heavier, slower rise gives the numerals character without lying about what they are |
| **The stage** | **Floating paper scraps / particles drifting behind the specimens** | **Purpose and function.** Ambient full-viewport motion with no nameable job, on the exact surface the content is read against. Also the single most predictable answer to "make it feel alive" |
| **Header** | **A scroll-progress bar across the top** | **Redundancy.** The red thread already reports progress, and it reports it *through the thing being progressed through*. Two progress indicators is one too many, and the weaker one would be the generic one |
| **The two CTAs** | **Magnetic cursor — the button leans toward the pointer** | **Function.** It fires continuously, it moves a target while the user is aiming at it, and its only purpose is to be noticed |
| **Mono labels and filenames** | **Text scramble / decode-on-enter** | **Honesty.** These are real paths on disk. Scrambling them makes real artifacts look like set dressing — which is precisely the impression this page exists to refute |
| **The four rigs** | **Autoplay loop so the section is alive without a press** | **Self-refutation.** The section's entire claim is that these only move when you ask. An autoplay loop would make the page argue against itself in the same viewport |

**21 accepted, 18 refused.** For the first time the accepted list is longer. That is the
owner's call, recorded, and the page prints both numbers on its own face.

---

## Rule zero — the contract, measured

Content renders whether or not any animation ever plays.

1. **Visible is the default.** Every hidden state lives under `.js`, a class the script
   itself adds. No script, nothing ever hides.
2. **One list, one revealer.** `.rv` is the only class the failsafe knows about;
   `.rv.num`, `.rv.edge` and `.rv.slam` change its *character*, not its mechanism. There is
   no second hidden-state system that the failsafe could fail to cover.
3. **Unconditional failsafes.** `.lit` fires on the second animation frame, again on
   `load`, and again on a 900 ms timer. `revealAll()` runs 1200 ms after `load` regardless
   of the observer.
4. **Bypass when unavailable.** Reduced motion or a missing `IntersectionObserver` lights
   everything, marks the deal complete, reveals everything, and pins the thread at full
   length — immediately, with no degraded animation attempted.
5. **`@media print`** forces every final state and hides the thread head.

**Measured — elements still at opacity < 0.08 after settle:**

| Condition | Count | What it is |
| --- | --- | --- |
| Normal, 1905 × 937 | **0** | — |
| `<script>` removed from the document (true no-JS render) | **1** | `i.threadhead` — an 8 px `aria-hidden` decoration with no content, correctly invisible when there is no scroll position to report |
| `prefers-reduced-motion: reduce` | **0** | — |
| `@media print` | **0** | — |

## Accessibility

Under `prefers-reduced-motion: reduce`: every entrance, the stage light, the ink shutter,
the plate deal, the stamp, the caret and the thread's scroll linkage are switched off and
rendered final. **Measured:** `.thread` computes to `transform: none` (full length),
`.shut` to `scaleX(0)` (word fully red), `.wm i` to `animation-name: none`, 0 elements
hidden, and the explanatory note computes to `display: block`.

Press and hover feedback survive as instant colour changes, because they answer what the
user just did.

**The four rigs keep animating under the preference, and that is still a deliberate call.**
They only move when pressed — the same category as a video the user pressed play on — and a
visible note in that section says so, in both languages. The alternative is four dead boxes
and no explanation. The one-rule reversal if a reviewer disagrees:
`.pbtn, .tgl i, .carrier, .tiles i { transition-duration: 1ms !important }` inside the
reduce block, and change the note.

## Two design decisions the transform-only rule forced

**The shutter, not the fill.** The obvious ink-fill animates `clip-path`. That is not a
compositor property, so it was refused. The word is instead *already red* with a flat slate
block on top that retracts by `scaleX`. That required the ground behind the headline to be
perfectly flat — which is why the stage light sits behind the specimen stack rather than
behind the whole hero. The constraint produced the better idea: a light coming up on the
objects reads as a stage, and a wash behind everything reads as a gradient.

**The gate bands rule themselves off instead of turning.** See the refusal table. The
version that survived is cheaper, safer, and on-concept — a checkpoint being ruled and
stamped is more literally what the band means than a page turning over.

## Needs a feel check

- **The whole 1.8 s entrance**, watched by a human on a cold cache. Every timing here was
  judged from values, still frames at 21 / 603 / 1403 ms, and a 4-second capture. That is
  better evidence than v1.1 had and it is still not a person watching.
- **The plate deal's overshoot.** `--ease-card` overshoots 6 %. Whether that reads as weight
  or as bounce is the single judgement most likely to be argued with.
- **The thread's scroll rate.** The 0.78 × viewport anchor was chosen so the line is
  roughly at the row you are reading. It has not been tried on a trackpad with momentum, or
  on a very tall or very short window.
- **The refusal shake.** It needs someone to actually hover the turned-down plate and say
  whether it reads as wit or as a glitch.

## Verdict

The highest-leverage item is #10, the ink flooding the red word — it is the only moment on
the page where the motion *is* the message. Second is #15, the red thread, because it is
the only animation here that explains something a static page could not. Third is #8, the
plates dealing, which is what makes the first second feel like an object was placed rather
than a page loaded.

If the budget were narrowed again tomorrow, #14 (the caret) and #21 (the shake) go first —
they are the two that are purely charm. Everything else has a sentence.
