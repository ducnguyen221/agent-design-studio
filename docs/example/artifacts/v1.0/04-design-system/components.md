# 04 — Component and state contract

Direction A — Specimen Sheet. Twelve components. Every one lists the states it can reach;
states it cannot reach are marked *n/a* rather than left blank.

## The signature system

Three devices carry the identity. Everything else is quiet around them, per the
one-bold-moment rule.

1. **Figure captions on the rule** — a mono label sitting astride a hairline, with the
   paper colour knocked out behind it, exactly as a drawing sheet labels a figure.
2. **The gate stamp** — a bordered mono badge reading `GATE`, used only on the two steps
   where a person decides. It is the one place the page makes a structural claim visually.
3. **The index rail** — a vertical mono spine on the left edge naming the sheet.

## Components

| # | Component | States | Notes |
| --- | --- | --- | --- |
| 1 | Sheet frame | default · n/a otherwise | Bordered container, max 1180px. The grid ground is contained **inside** it — fix carried from Gate 1 |
| 2 | Header bar | default · sticky-scrolled | Gains a hairline bottom border once scrolled |
| 3 | Language toggle | EN-active · VI-active · focus · hover | `aria-pressed` carries state; not colour alone — the active side inverts to solid ink |
| 4 | Display heading | default | One mark word in drafting red |
| 5 | Button, primary | default · hover · active · focus-visible · n/a disabled | Solid ink on paper |
| 6 | Button, ghost | default · hover · active · focus-visible · n/a disabled | Hairline border |
| 7 | Figure grid cell | default · gate-variant | 4-across desktop, 2 tablet, 1 mobile |
| 8 | Gate stamp | default | Rebuilt as an inline element — the negative-margin hack from the direction render is gone |
| 9 | File-trail list | default | Mono, with gate lines marked in red |
| 10 | Showcase figure | loaded · **honest-placeholder** | If a screenshot is missing, a labeled dashed block ships. Never a drawn substitute |
| 11 | Install block | placeholder-state · n/a ready | **Currently placeholder.** Visibly stamped as such until D4. This is a real UI state, not a TODO |
| 12 | Footer / acknowledgements | default | The only place proper names appear on the page |

## UI states — page level

| State | Reachable? | Treatment |
| --- | --- | --- |
| loading | **No** | Single static file, no async. Declared out of scope |
| empty | **No** | No collections |
| error | **No** | No requests that can fail |
| validation | **No** | No forms |
| disabled | **No** | No gated actions |
| permission | **No** | Nothing gated |
| **placeholder** | **Yes** | The install commands, until D4 replaces them. Marked visibly on the page |
| **language** | **Yes** | EN default, VI toggle. Both complete — the second language is not degraded |
| **reduced-motion** | **Yes** | All reveals become instant; no transforms |

This is a landing page, so six of the nine standard states are genuinely unreachable.
Declaring them *n/a* in writing is the contract — it is what stops a reviewer at Step 7
from filing a missing-empty-state bug against a page that has no collections.

## Responsive contract

| Viewport | Behaviour |
| --- | --- |
| 1440px | Full sheet, index rail visible, figures 4-across, showcase 3-across |
| 768px | Rail hides, figures 2-across, showcase 1-across, hero single column |
| 390px | Single column throughout, display type steps down via `clamp`, nav links collapse to the toggle only |

No horizontal overflow at any width. The narrow layout is composed, not squeezed: the
figure grid changes from a wide table to a stacked list rather than shrinking.

## Keyboard contract

Tab order: skip-link → wordmark → nav links → language toggle → hero primary → hero ghost
→ in-page section links → install → footer links. Focus is visible on every stop via a
2px ink outline with 2px offset. No focus trap anywhere — there are no dialogs. The
language toggle is two real `<button>` elements, operable with Enter and Space, and it
announces state through `aria-pressed`.
