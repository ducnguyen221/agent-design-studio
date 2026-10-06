# Motion playbook

Step 6. One pass that finds the motion worth adding, refuses the rest, builds what
survives, and reviews it against a bar that has to be earned.

Output: `06-motion-spec.md`, plus the implementation.

**When this step runs.** Step 6 is a **second pass over a page that already works**. Build
the thing static in Step 5, confirm it renders, then add motion on top. Planning motion
while writing the initial CSS means writing it twice and entangles two decisions that need
to be judged separately.

Read the selected static hypotheses in `03-direction-decision.md`, then choose from
`motion-patterns.md` only after applying the four gates. For each hypothesis, record
accepted or refused verdicts in `templates/06-motion-spec.md`. Trace an accepted item
from reference URL and observed behavior through hypothesis, recipe ID, token/actual
value, implementation and browser QA. Zero motion keeps the Step 5 build unchanged.
Load `library-selection.md` if a motion dependency is considered in either target mode.
Keep the engine decision here and actual package/bundle/license/exit plan in
`05-implementation.md` only.

---

## Rule zero — motion must never gate content

> **Content renders whether or not the animation ever plays.** An entrance animation
> decorates the arrival of something that is already there. It is never the mechanism that
> makes it there.

This is the most expensive mistake in this file, because it does not look like a bug while
you are building — it looks fine in the browser you have open, and the page is blank
everywhere else.

**The canonical failure.** A scroll-triggered entrance sets `opacity: 0` (or
`transform: scale(0)`) as the resting state and removes it when an observer fires. Then the
observer never fires, and the content is simply gone. All of these are real paths where it
never fires:

- JavaScript disabled or failed to load.
- No `IntersectionObserver` — old browsers, restricted runtimes, some in-app webviews.
- A screenshot or crawler capturing the page before the callback runs.
- Print, where scroll position and viewport intersection are meaningless.
- Anything below the fold in a tool that captures the full page height at once.

A second form of the same bug: applying `transform: scaleX(0)` to a **parent** in order to
animate a rule or bar. Transforms scale children too, so the label inside collapses to
nothing. Animate a dedicated child element, never a container that holds content.

**The contract, all four parts:**

1. **Author the visible state as the default.** The hidden state is added by script, not
   written into the base stylesheet. A class such as `.js` on the root — set by the same
   script that runs the observer — is what arms it. No script, nothing ever hides.
2. **Ship a failsafe that reveals everything unconditionally.** On `load` plus a short
   timeout, reveal every pending element regardless of the observer. The animation is a
   nicety; the deadline is not negotiable.
3. **Bypass entirely when the observer is unavailable or motion is reduced.** Reveal
   immediately; do not attempt a degraded animation.
4. **Force the final state in `@media print`.**

**Self-check before finishing any entrance animation — all four must pass:**

- [ ] Load the page with JavaScript disabled. Is every word visible?
- [ ] Take a full-page screenshot. Is anything below the fold missing?
- [ ] Print to PDF. Is anything missing?
- [ ] Set reduced motion. Is everything visible immediately, with nothing withheld?

If the answer to any is no, the animation is a content bug, not a polish item. Fix it before
anything else in this step.

---

**Posture.** Restraint is the defining trait. Two failure modes, and the first is worse:
animating something that should not animate; and animating the right thing with the
wrong ingredients. The gate below exists to sometimes produce zero lines of code — that
is a success, not a dodge. Never present motion as a menu of options: make the call, give
one line of reasoning, write the code.

---

## Part 1 — Find opportunities, reject most of them

Expect to reject most candidates. Cap at five to seven for a whole product, fewer for one
screen, ordered by leverage.

**Where genuine opportunities live:** pressable things with no pressed state; destructive
actions confirmed by a bare click where hold-to-confirm would prevent slips; content that
swaps or vanishes instantly; accordions that snap; list items added or removed with no
bridge; panels with no visual connection to their trigger; dismissible surfaces leaving by
a different route than they arrived; a grid appearing all at once on an occasionally-seen
screen; draggable things that snap with no physics; and rare high-emotion moments rendered
flat — first run, empty states, completion.

**Every candidate passes four gates, in order. Record the answers.**

**Gate 1 — Frequency.**

| How often the user sees it | Verdict |
| --- | --- |
| 100+/day — keyboard shortcuts, command palettes, core navigation, tab switches | **Reject. No animation, ever.** |
| Tens/day — hover states, list navigation, frequent toggles | Reject, or near-imperceptible only |
| Occasional — modals, drawers, toasts, settings | Eligible: standard animation |
| Rare / first-time — onboarding, empty, success, celebration | Eligible: the delight budget |

Keyboard-initiated actions are a disqualifier, not a judgment call. Something opened
hundreds of times a day should open instantly; animation there reads as lag.

**The marketing / showcase branch.** The table above is written for an interface someone
*works in*. A surface seen **once per visitor** — a landing page, a marketing page, a
portfolio, a launch page, a docs home — is the far end of the frequency scale, and the
whole table inverts there:

| | Product interface | Marketing / showcase surface |
| --- | --- | --- |
| Frequency | Dozens to hundreds of times | Once, maybe twice, ever |
| Cost of motion | Paid again on every use | Paid once |
| Default verdict | Reject unless it earns a place | **Eligible — this is where the delight budget lives** |
| Entrance choreography | Usually noise | **The point.** A first visit that arrives dead is a wasted first impression |
| Failure mode to fear | Motion that gets in the way | Motion so timid nobody notices the page moved |

Two consequences worth stating plainly, because the restraint posture in this file is
otherwise easy to over-apply:

1. **Entrance choreography on a once-seen page is not a violation.** Staggered arrivals,
   a headline that rises, an element that settles into place — these are legitimate on a
   surface whose job is to be felt on the first scroll. Purpose-name them *explanation*
   or *delight*; both are valid at the rare tier. The sub-300ms UI budget still governs
   every **response to an interaction**, but a scroll entrance is not a response.

2. **The product's own claims must be demonstrated, not stated.** If the page argues that
   something is fast, smooth, interruptible, or well-crafted, a page that merely *says*
   so in body copy has made the weaker version of its own argument. Build the live
   example: the spring beside the linear, the press state you can press, the toggle you
   can interrupt mid-travel. A demonstrative example is motion with a nameable purpose —
   *explanation* — and it usually outperforms the paragraph it replaces.

**Rule zero does not bend here, and neither does reduced motion.** The delight budget buys
choreography, never a page whose words depend on an animation playing. A once-seen surface
is precisely where a screenshot tool, a crawler, or a reader with reduced motion is most
likely to be the visitor.

**Gate 2 — Purpose.** Name it in one of these words: **feedback** · **spatial
consistency** · **state indication** · **preventing a jarring change** · **explanation**
(marketing and onboarding only) · **delight** (rare tier only). "It looks cool" is not on
the list. Cannot name it? Reject it.

**Gate 3 — Speed.** It fits the budgets in Part 2. If a moment only works as a slow,
showy animation, it fails.

**Gate 4 — Function.** Data the user is reading or acting on does not move for style. A
pointer-tracking flourish belongs on a marketing page, not on a chart someone is making a
decision from.

**Report both halves:** accepted opportunities with exact values, *and* two to five things
you deliberately did not suggest, each with the gate that killed it. The rejection list is
what separates this from a wishlist.

---

## Part 2 — Build it, in this order

Steps 1–2 are the gates above. Do not reach for a curve before knowing whether it animates
at all.

**3 — Cheapest tool that works.** Walk down, stop at the first fit:

| Need | Tool |
| --- | --- |
| Hover, press, color, a state toggle you control with a class or attribute | CSS transition |
| Entry animation on mount, no JS state | CSS starting-style rule |
| Simple predetermined motion | CSS animation; check in the target browser whether the chosen properties can run on the compositor |
| Programmatic control without a library | The browser's Web Animations API; profile the actual effect |
| Springs, layout animations, exit animations, gesture-driven values | A motion library |
| Coordinated timelines, scroll pin/scrub or SVG sequences beyond platform/installed tools | Evaluate a specialist engine, including bundle, license, lifecycle and reduced motion |

CSS/WAAPI can animate compositor-friendly properties without per-frame script work,
but CSS is not automatically off the main thread; paint, layout, and engine behavior
vary. Profile the actual browser and workload. A JS timeline can be justified when it
provides control the platform or installed engine cannot. If the request is really for a *component* (toast, drawer, command
menu, dropdown), pick a library instead of hand-rolling one; hand-rolled versions ship
without focus management.

**4 — Properties.**

- **Prefer `transform` and `opacity` for movement** because they often avoid layout;
  compositing is conditional, not guaranteed GPU work. Layout properties such as
  `width`/`height`/`margin`/`padding`/`top`/`left` can force layout and affect nearby
  targets. `clip-path` may help a reveal but must be profiled in its browser/shape.
- **Never scale from zero.** Start at `scale(0.9–0.97)` + `opacity: 0`. Nothing real
  appears from nothing.
- **Anchor the origin at the trigger** for popovers, dropdowns, menus, tooltips. **Modals
  are exempt** — unanchored, so they stay centered.
- **Percentages in `translate()`** are relative to the element's own size, so
  `translateY(100%)` moves it by its own height. Prefer this to hard-coded pixels.
- **Match the transform advice to the engine.** Motion's individual transform values
  may use CSS variables and can have different compositor behavior from animating a
  full transform string; see [Motion performance](https://motion.dev/docs/performance).
  [GSAP's CSS plugin](https://gsap.com/docs/v3/GSAP/CorePlugins/CSS/) explicitly
  supports `x`/`y`/`scale` aliases. Do not ban aliases across engines: profile the
  actual engine/browser combination and avoid per-frame style work when it matters.
- **Never drive a child's transform from a custom property on the parent** — it forces a
  style recalculation for every child.

**5 — Easing and duration, or a spring.**

| Situation | Easing |
| --- | --- |
| Entering or exiting | `ease-out` |
| Moving or morphing on screen | `ease-in-out` |
| Hover or color change | `ease` |
| Constant motion (marquee, progress) | `linear` |
| Default | `ease-out` |

**Never `ease-in` on UI.** It starts slow, delaying exactly the moment the user is
watching; `ease-out` at 200ms *feels* faster than `ease-in` at 200ms. Built-in curves are
too weak for deliberate motion:

```css
--ease-out:    cubic-bezier(0.23, 1, 0.32, 1);   /* strong ease-out for UI */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* sheet / drawer feel */
```

| Element | Duration |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing / explanatory | May be longer |

**UI motion stays under 300ms.** A 180ms dropdown feels more responsive than a 400ms one.

**Reach for a spring instead** when there is drag with momentum, an element that should
feel alive, a gesture the user can interrupt or reverse, or decorative pointer tracking:

```js
{ type: "spring", duration: 0.5, bounce: 0.2 }            // easier to reason about
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }  // more control
```

Keep bounce 0.1–0.3, and avoid bounce in most UI — reserve it for drag-to-dismiss and
deliberately playful interaction.

**6 — Interruption and exit.**

- **Transitions, not keyframes, for anything triggered rapidly.** Transitions retarget
  from the current value; keyframes restart from zero.
- **Springs for gestures** — they carry velocity through an interruption.
- **Exit the way it entered.** A toast that slides up from the bottom leaves through the
  bottom. Symmetric paths are what make swipe-to-dismiss obvious.
- **Asymmetric timing where the user is deciding.** Slow the deliberate phase (a
  hold-to-confirm fill, ~2s linear), snap the system's response (~200ms ease-out).
- **Stagger group entrances 30–80ms apart.** Longer feels slow; stagger is decorative and
  must never block interaction while it plays.

**7 — Reduced motion and pointer gating.** These ship *with* the animation, never after.

```css
@media (prefers-reduced-motion: reduce) {
  .element { animation: fade 0.2s ease; }   /* keep opacity/color, drop movement */
}
@media (hover: hover) and (pointer: fine) {
  .element:hover { transform: scale(1.05); } /* touch fires false hovers on tap */
}
```

Reduced motion means **reduce or remove non-essential motion; preserve state feedback** —
never withhold the answer to what the user just did. Two adjacent preferences deserve the
same care: reduced transparency (solid surfaces, no blur) and increased contrast
(near-solid backgrounds, defined borders). Also avoid full-viewport moving backgrounds,
slow looping oscillation near one cycle per five seconds, and abrupt brightness jumps.

---

## Part 3 — Fluid, physical motion

For gesture-driven interfaces. The through-line: **motion starts from the current
on-screen value, inherits the user's velocity, projects momentum forward, and can be
grabbed and reversed at any instant.** Springs make this natural — they are inherently
interruptible and velocity-aware.

- **Kill latency.** Respond on pointer-*down*, not release. The instant lag appears, the
  sense of directness collapses.
- **Track one-to-one.** A dragged element stays glued to the finger and respects the grab
  offset. Capture the pointer so tracking survives leaving the element's bounds; keep a
  short position/time history for release velocity.
- **Interruptibility matters most.** Never lock out input mid-transition. Animate from the
  *live on-screen* value, never the logical target, or the interruption visibly jumps. On
  reversal, blend velocity rather than hard-cutting it. Decompose 2D motion into
  independent X and Y springs.
- **Two parameters beat three:** *damping ratio* (1.0 = critically damped; below 1.0
  oscillates) and *response* (seconds to reach the target — not a duration).

  | Interaction | Damping | Response |
  | --- | --- | --- |
  | Move / reposition | 1.0 | 0.4 |
  | Rotation | 0.8 | 0.4 |
  | Drawer / sheet | 0.8 | 0.3 |

  Default to critically damped. Add bounce **only when the gesture carried momentum** —
  overshoot after a flick feels right; overshoot on a menu that faded in feels wrong.
- **Hand off velocity at the seam:** continue at the exact release velocity. Normalized
  form: `relativeVelocity = gestureVelocity / (target − current)`.
- **Project momentum; don't snap from the release point.** Project the resting position,
  then snap to the nearest target to *that* point:
  `current + (velocity/1000) · d / (1 − d)`, `d ≈ 0.998` (`0.99` for snappier). Flick
  dismissal is velocity-based, not distance-based.
- **Rubber-band at boundaries** rather than stopping hard; **hint in the gesture's
  direction** so intermediate frames telegraph the outcome.
- **Gesture details:** highlight on touch-down, commit on touch-up, allow cancel by
  dragging away and back; ~10px before committing to a direction; detect plausible
  gestures in parallel then cancel the losers; ignore extra touch points mid-drag.
- **Multi-sensory feedback**, if any: obvious cause, visual + sound + haptic on the *same
  frame*, reserved for meaningful moments. Over-feedback trains people to ignore it.

When a crossfade shows two overlapping states however you tune it, a subtle blur during
the transition (under 20px — heavy blur is expensive) merges them into one perceived
transformation.

---

## Part 4 — Mobile and native

Three things change: **no hover** (every hover affordance must live in press, position, or
nothing); **two runtimes** (motion touching the app's JS runtime stutters the moment the
app does anything else — the craft is keeping motion off it); and **the finger is on the
element** (interruptibility and velocity handoff are baseline, not polish).

Consequences: use the animation library that runs on the UI runtime, not the framework's
bridge-crossing default. **Tab switches never slide** — tabs are peers, sliding implies
depth that isn't there, and the user pays for it dozens of times a session. Use native
presentations for screen transitions, bottom sheets, tab bars, context menus, and large
collapsing headers. `transform` and `opacity` often avoid layout work, but are not free;
layout-affecting properties may move neighboring targets. Measure on the target device.
Use a continuously-tracked animated value only
when the value is continuous or interruptible — a two-state toggle is a transition. **Feel
is judged on a release build on the slowest supported device.**

---

## Part 5 — The review bar

Default to flagging. **Approval is earned, not assumed.** A transition that "works" but
feels sluggish, lands from the wrong origin, fires too often, or drops frames is a
regression.

| Never | Instead |
| --- | --- |
| `transition: all` | Name the exact properties |
| Entrance from `scale(0)` | `scale(0.95)` + `opacity: 0` |
| `ease-in` on a UI element | `ease-out` or a strong custom curve |
| A weak built-in curve on a deliberate animation | A strong cubic-bezier |
| Animation on a keyboard shortcut or 100+/day action | No animation |
| UI duration over 300ms with no stated reason | 150–250ms |
| Centered origin on a trigger-anchored popover | Origin at the trigger (modals exempt) |
| Keyframes on toasts, toggles, rapidly-fired elements | Transitions |
| Animating layout properties | `transform` / `opacity` |
| Motion-specific shorthand transform path is slow in a measured case | Try a full transform string in that engine; GSAP aliases need their own measurement |
| A parent custom property driving child transforms | `transform` on the element itself |
| Ungated `:hover` motion | Gate on fine pointer + real hover |
| Missing reduced-motion handling | Reduce or remove non-essential motion; preserve state feedback |
| Symmetric timing on press-and-hold | Slow the deliberate phase, snap the response |
| Everything entering at once | 30–80ms stagger |

**Prefer earlier fixes over later ones:** delete it → reduce it → fix the easing → fix
origin and physicality → make it interruptible → move it to the GPU → make the timing
asymmetric → polish (blur a crossfade, stagger a group, spring for something alive) →
accessibility and cohesion.

**Cohesion.** Motion matches the component's personality and the rest of the product: a
playful product can be bouncier, a professional dashboard stays crisp and fast. When
unsure whether motion feels right, the strongest move is usually to delete it.

**When feel cannot be judged from code,** say so instead of guessing at a value, and name
the check: play it at 2–5× duration or in the animation inspector; step it frame by frame
to catch coordinated properties drifting apart; test gestures on a real device; look again
the next day with fresh eyes.

---

## Part 6 — Naming what you see

When someone describes an effect loosely, return the term so the whole team can ask for
the same thing. Lead with the best match; add one alternate only when two genuinely
compete.

**Entrances / exits** — *fade* · *slide in* · *scale in* · *pop in* (scale-in with slight
overshoot) · *reveal* (uncovered by an animated clip or mask) · *enter/exit*.

**Sequencing** — *stagger* (cascade of small delays) · *orchestration* (several animations
timed to read as one) · *delay* · *duration* · *fill mode* (whether the first/last frame
persists outside the run) · *stepped*.

**Movement** — *translate* · *scale* · *rotate* · *skew* · *3D tilt / flip* · *perspective*
· *transform origin* · *origin-aware* (grows from its trigger, not its own center).

**Between states** — *crossfade* (one fades out as another fades in, same spot) · *morph*
(one shape becomes another) · *shared element transition* (travels and transforms from one
position to another) · *layout animation* (size/position change animates instead of
snapping) · *continuity transition* (visually connects before and after) · *accordion* ·
*direction-aware* (forward and back slide opposite ways).

**Scroll / navigation** — *scroll reveal* · *scroll-driven* (progress tied to scroll
position) · *parallax* · *page transition* · *view transition*.

**Feedback** — *hover effect* · *press/tap feedback* · *hold to confirm* · *drag* · *drag
to reorder* · *swipe to dismiss* · *rubber-banding* (resistance and snap-back past a
boundary) · *shake* (error jitter) · *ripple*.

**Easing** — *ease-out* (fast then slow; the UI default) · *ease-in* (usually wrong) ·
*ease-in-out* · *linear* · *cubic-bezier* · *asymmetric easing*.

**Springs** — *spring* · *stiffness/tension* · *damping* · *mass* · *bounce* · *momentum* ·
*velocity* · *perceptual duration* (feels finished while still micro-settling) ·
*interruptible animation*.

**Ambient** — *marquee* · *loop* · *alternate/yoyo* · *orbit* · *pulse* · *float* · *idle
animation*.

**Polish** — *blur* · *clip-path* · *mask* (clip-path with soft edges) · *before/after
slider* · *line drawing* (a vector path drawing itself) · *text morph* · *skeleton /
shimmer* · *number ticker* · *tabular numbers* (fixed-width digits so counters don't
jitter) · *typewriter*.

**Performance** — *frame rate* · *jank* · *dropped frame* · *compositing* · *will-change* ·
*layout thrashing*.

**Principles** — *purposeful animation* · *anticipation* (wind-up before a move) ·
*follow-through* (parts settling after the main motion) · *squash and stretch* ·
*perceived performance* · *frequency of use* · *spatial consistency* · *hardware
acceleration* · *reduced motion*.

---

## The motion spec

```markdown
# 06 — Motion spec
**Tokens used / added:** <curves and durations; extend the existing scale, never fork it>

## Accepted
| # | Where | Purpose | Frequency tier | Tool | Properties | Curve + duration / spring |
|---|---|---|---|---|---|---|

## Rejected (required)
- <location> — <what was considered>. **Rejected: <which gate killed it>.**

## Accessibility
Reduced-motion variant per item; hover gating wherever hover motion exists.

## Needs a feel check
<items whose quality cannot be settled from code, and how to check them>

## Verdict
<how much motion this interface actually needs; the single highest-leverage item>
```

If nothing survives the gates, say so plainly. That is a good result, not a failure.
