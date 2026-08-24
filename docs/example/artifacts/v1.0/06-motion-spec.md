# 06 — Motion spec

**Tokens used:** `--ease-out: cubic-bezier(0.23,1,0.32,1)` · `--dur-press: 140ms` ·
`--dur-ui: 220ms` · `--dur-reveal: 520ms` · `--stagger: 60ms`. All extend the existing
scale in `tokens.json`; nothing forked.

**Frequency tier for this surface:** rare / first-time. A marketing page is seen once or
twice per visitor, which is where the delight budget lives. That is the *only* reason
anything here is allowed to exceed the sub-300ms UI rule.

**The constraint that shaped every decision:** this page argues that motion must be
justified. Motion here that could not survive its own review would refute the page.

## Accepted

| # | Where | Purpose | Tier | Tool | Properties | Curve + duration |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Buttons, `:active` | Feedback | Tens/day | CSS transition | `transform: scale(0.97)` | 140ms `ease-out` |
| 2 | Buttons + nav links, hover | Feedback | Tens/day | CSS transition | `background`, `color`, `border-color` | 220ms `ease-out`, gated on `(hover:hover) and (pointer:fine)` |
| 3 | Sticky header border on first scroll | State indication | Occasional | CSS transition | `border-color` | 220ms `ease-out` |
| 4 | Language toggle | State indication | Rare | CSS transition | `background`, `color` | 220ms `ease-out` |
| 5 | **Figure rule draws itself** | Explanation | Rare | CSS transition, `IntersectionObserver` adds a class | `transform: scaleX(0 → 1)`, origin left | 520ms `ease-out` |
| 6 | **Figure caption arrives after its rule** | Explanation | Rare | CSS transition | `opacity 0→1`, `translateY(4px→0)` | 220ms `ease-out`, 260ms delay |
| 7 | Figure-grid cells enter | Preventing a jarring change | Rare | CSS transition, staggered by index | `opacity 0→1`, `translateY(10px→0)` | 300ms `ease-out`, 60ms stagger |
| 8 | Gallery figures enter | Preventing a jarring change | Rare | CSS transition | `opacity 0→1`, `translateY(10px→0)` | 300ms `ease-out`, 60ms stagger |

### Why 5 and 6 are the page's one indulgence

They are the signature. A drawing sheet is *drawn* — a rule extends from its origin and
then its label lands on it. The motion states what the artifact is, which is the
"explanation" purpose, and explanation is permitted on a marketing surface.

520ms exceeds the 300ms UI budget deliberately and with a stated reason: it is a scroll
entrance on a rare-tier page, not a response to an interaction. Nothing waits on it, and
nothing is blocked while it plays. Every UI *response* on the page stays at 220ms or less.

Both use `transform` and `opacity` only. The rule scales on the X axis from its left
origin rather than animating `width`, so no layout runs.

## Rejected (required)

| Location | Considered | Rejected because |
| --- | --- | --- |
| Hero heading | Word-by-word or character-by-character reveal | **Gate 2 — purpose.** No nameable purpose. It delays the one sentence carrying the entire argument. The most-copied AI motion cliché available |
| The mark word "design" | Colour-cycle or gradient sweep | **Gate 2 — purpose.** Decoration. Also a flagged default look; the page would contradict its own taste reference |
| Whole page | Scroll-linked parallax on the grid ground | **Gate 4 — function.** The grid is the ground the content is read against. Moving it fights reading, and full-viewport ambient motion is on the reduced-motion avoid list |
| Language toggle | Cross-fade or slide between EN and VI text | **Gate 1 — frequency**, and correctness. It fires on a deliberate action the user wants completed *now*; animating a full page of text swap looks like a page reload |
| Step figure cells | Hover lift with a shadow | **Gate 4 — function.** They are figure regions in a drawing, not cards. A lift would say "clickable", and they are not |
| Install code blocks | Typewriter effect on the commands | **Gate 2 — purpose**, and honesty. It would dramatise a command that does not work yet |
| Nav links | Scroll-spy underline that animates between sections | **Gate 3 — speed.** Fires continuously during scroll on a five-section page; cost exceeds benefit |
| Gallery images | Lightbox with a shared-element zoom | Scope. Real value, but it needs focus management, Escape handling, and focus restoration — a dialog contract this page does not otherwise have. Deferred rather than half-built |

Eight accepted, eight refused. The refusals are the deliverable as much as the accepted
list is.

## Accessibility

Every reveal is wrapped in a reduced-motion guard. Under `prefers-reduced-motion: reduce`
all transforms are dropped and elements render in their final state immediately — content
is never withheld from a user who asked for less motion. Press and hover feedback survive
as instant colour changes, because they aid comprehension.

The `IntersectionObserver` sets the visible class regardless of the preference, so if
JavaScript runs the content appears either way. And every revealed element is styled
visible by default with the hidden state applied only inside a `.js` class that the script
adds — so with JavaScript disabled the whole page renders normally.

## Needs a feel check

- The 260ms delay between rule and caption (item 6) is judged from values, not from
  watching it. Check at 3× duration in an animation inspector; if the caption feels
  disconnected rather than sequenced, close the gap to ~180ms.
- The 60ms stagger across eight figure cells totals 420ms for the last cell. On a fast
  scroll the last cell may still be arriving as it leaves the viewport. Watch it on a real
  scroll before accepting.

## Verdict

This page needs very little motion, and it gets very little: four transitions that are
plain interface feedback, and one idea — the sheet drawing itself — used exactly twice per
section. The highest-leverage item is #5; if only one animation survived, that is the one.
