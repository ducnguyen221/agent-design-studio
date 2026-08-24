# 05 — Implementation (v3)

**Build:** `v3/05-build-source.html` → `v3/05-build.py` → `v3/05-build.html` and
`docs/index.html`. 276 KB, self-contained, 0 subresource requests, no runtime, no fonts
downloaded. Six JPEGs inlined as data URIs — all six are real renders from this project's
own runs.

**Scope:** pipeline steps **05 → 07**, iterating inside an already-approved direction.
Direction B is unchanged; the design system in `../04-design-system/` is unchanged except
for two new easing tokens. Gate 1 is exempt for this run — recorded in
`00-owner-directive.md` with the reason.

---

## What changed from v1.1

### 1. Every sentence a human reads was rewritten (both languages)

The rule applied: **if a reader without a design or engineering background would have to
look a word up, the sentence is wrong.** Vocabulary was replaced with what the vocabulary
*means*, not with a synonym.

| Was | Is |
| --- | --- |
| "intake, fidelity, wireframe, three real directions, a token system, motion, review" | "It asks the questions a good designer would ask, sketches a rough skeleton, then builds three genuinely different versions and stops so you can pick one." |
| "Wireframe — structure only, deliberately unfinished so reviewers judge layout" | "The skeleton — a rough sketch of the bones: boxes and labels, no colour, kept deliberately plain so you judge the layout rather than the paint." |
| "Colour sampled from real assets and justified in one sentence. Tokens, components, then the code." | "First the page's rulebook — the colours, sizes and spacing everything has to follow, so nothing drifts — then the page itself." |
| "Scored on six dimensions against a hard floor" | "It marks its own work against a hard checklist … You have the last word." |
| "Direction · gate" (index) | "Pick one · you" |
| "GATE" (band tag) | "YOU DECIDE" |

**What deliberately stayed technical:** every mono stamp — `00-brief.md`,
`06-motion-spec.md`, `03-directions/`, `140ms ease-out`, `cubic-bezier`, `CSS keyframes`,
the `00`–`07` step codes, `SHEET — WHAT LANDS IN THE FOLDER`. These are *objects on the
page*, not prose. They carry the drafting-room aesthetic and they are literal file names a
reader will actually see on disk. Softening them would make real artifacts look decorative.

**The owner's quote is verbatim, including the word "wireframe."** It is a quotation; the
paragraph before it now explains what he was looking at in plain words, so the quote reads
as evidence rather than as jargon.

### 2. Motion became a property of the page

See `06-motion-spec.md` for all 21 accepted and 18 refused with values. Structurally:

- **One reveal mechanism, four characters.** `.rv` is the single class the failsafe knows
  about. `.rv.num`, `.rv.edge` and `.rv.slam` change what it *does* without adding a second
  system the failsafe could miss. This is the single most important line of defence for
  Rule Zero: there is exactly one list of hidden things and exactly one thing that reveals
  them.
- **A load choreography** on `.lit`, which is set on the second animation frame, again on
  `load`, and again on a 900 ms timer.
- **A scroll-linked red thread** through the step list, one rAF-coalesced handler writing
  two transforms.
- **An `IntersectionObserver` pass** for enter animations, with an unconditional
  `revealAll()` 1200 ms after `load`.

### 3. Three structural fixes carried from the v1.1 review

| v1.1 finding | Status |
| --- | --- |
| **#10** — the story's evidence column bottomed out ~90 px above its prose | **Fixed.** A third evidence plate (`v1.1 · the version before this one`) was added. The two columns now end within ~85 px of each other, and the third plate does narrative work: skeleton → turned down → the version before this one |
| **#9** — the hero's upper-right quadrant was empty | **Improved, not closed.** The stage light now occupies that region as a soft lift behind the specimens rather than flat ground. It is composed rather than empty; it is still the quietest part of the frame |
| **#11** — the motion heading ragged to a one-word last line | **Fixed incidentally.** The plainer heading ("Movement has to earn its place. Here it is, running.") resolves in two lines |

### 4. Install section

Carried the post-v1.1 commit: the commands are live, the Codex install is qualified with
its marketplace (`agent-design-studio@agent-design-studio`), and the `PLACEHOLDER` pill and
its Vietnamese string are gone. The `.ph` CSS block was left in place — it is 4 lines and
the state may return at the next release; flagged rather than silently kept.

---

## Design system deltas

Two tokens added to the motion scale in `../04-design-system/tokens.json`'s family. Nothing
forked, nothing renamed.

| Token | Value | Why it exists |
| --- | --- | --- |
| `--ease-lift` | `cubic-bezier(0.16, 1, 0.3, 1)` | Headline lines and step numerals. A heavier settle than `--ease-out`; the difference is legible only above ~500 ms, which is exactly where it is used |
| `--ease-card` | `cubic-bezier(0.18, 0.89, 0.32, 1.06)` | The plate deal. The only curve on the page that overshoots (by 6 %), because a card thrown onto a table does |
| `--dur-deal` | `780ms` | Plate travel |
| `--dur-slam` | `520ms` | Stamps and drawn edges |

No new colours. No new spacing values. The palette is unchanged from v1.1: three hue
families, one chromatic colour.

---

## Four implementation notes worth keeping

**1. The ink-fill is a shutter, not a fill.** The obvious way to flood a word with colour
is to animate `clip-path` or `background-size`, neither of which is a compositor property.
Instead the word is *already red*, and a flat slate-coloured block sits on top of it and
retracts with `transform: scaleX(1 → 0); transform-origin: right`. Scaling a solid
rectangle distorts nothing, so the type is never touched. The cost is one constraint: the
ground behind the headline must be flat, which is why the stage light was moved to sit
behind the specimen stack instead of behind the whole hero. **That constraint made the
design better** — a light coming up on the specimens says more than a wash behind
everything.

**2. Hover and entrance were fighting over the same properties.** The plates animate
`translate` and `rotate` on load with delays of 470–710 ms. Left alone, the first hover
would inherit that delay and feel broken. A `.dealt` class, set 1800 ms after load,
re-declares the same two properties at 260 ms with no delay. The pointer takes ownership
once the entrance has finished with it.

**3. `<div>` is not allowed inside `<ol>`.** The red thread's positioning parent was
originally the step list itself. Browsers hoist an invalid `div` out of an `ol`, which
would have silently broken the absolute positioning. The list is now wrapped in
`.stepswrap`, and the thread is a sibling of the `ol` rather than a child.

**4. The turned-down plate's shake is class-guarded.** A keyframe bound to `:hover` can be
re-fired as fast as the pointer can cross the boundary. The class is added on
`pointerenter`, ignored if already present, and removed on `animationend` — so the refusal
plays once per approach and cannot stack.

---

## Known deviations, stated rather than hidden

- **`translate` and `rotate` longhands** are used so the plates can animate position and
  angle independently of `transform`. Chromium 104+ / Firefox 72+ / Safari 14.1+. Verified
  in Chromium only.
- **`oklch()`, `color-mix()`, `backdrop-filter`** carry over from v1.1 and remain
  unverified outside Chromium.
- **The `.ph` install-placeholder CSS is currently unused** (see above).
