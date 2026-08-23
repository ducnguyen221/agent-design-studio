# Prototype playbook

Used at Step 3 instead of a wireframe when the open question is behavior, and again at
Step 5 when the deliverable is an interactive artifact rather than production code.

Output: a self-contained `.html` file plus screenshots, recorded in the step's artifact.

## Two modes, one skill

| Mode | The open question | Behavior |
| --- | --- | --- |
| **Mockup** | Visual hierarchy, layout, typography, color, whether it fits | Mostly static. Structure and focus styles are real; controls may be unwired |
| **Prototype** | Navigation, input, state change, feedback, recovery, transition | The modeled flow actually works |

Never add behavior to a mockup to make it feel more complete — an unwired control that
looks wired is a lie reviewers will approve. Say which mode this is, in the handoff.

If both are asked for, keep identical content and structure across them so the only
difference a reviewer sees is fidelity.

## Derive the direction from context

Before designing, inspect: the conversation, supplied references, the project's design
documentation, tokens, existing components, product screenshots, nearby artifacts.

Authority order: the user's explicit instructions → the project's established design
language and interaction conventions → the product, audience, content, and scenario →
your own judgment.

When no design system exists, derive a specific direction from the subject itself (Step
4 does this properly). What you must not do is fall back on a house style. A field tool,
an editorial workflow, and a financial approval screen should not feel like the same
product.

## Scope one credible experience

Choose the smallest flow that can answer the question. Then make it real:

- Use realistic, internally consistent names, dates, statuses, quantities, and copy.
- Navigation works within the modeled scope.
- Forms have labels, sensible defaults, validation, and submission feedback.
- Dialogs appear only where interruption or confirmation is genuinely part of the flow.
- Transitions clarify continuity or state change — never decoration (see the motion
  playbook before adding any).
- **No dead buttons.** If an action belongs to the real system, explain the boundary
  instead of pretending it completed.

Depth in one flow beats breadth across a fake product.

## Model the states that this flow can reach

List them before building, then implement the ones the scenario reaches: loading, empty,
error, success, validation, disabled, permission-denied, and any domain state from the
brief.

Rules of thumb: an asynchronous-looking action shows loading, success, and failure or
recovery. A collection considers empty. A gated action shows *why* it is disabled. Do
not force irrelevant states into the main flow to satisfy a checklist; name the omitted
ones in the handoff instead.

## Interaction completeness

- Native elements wherever they carry the right semantics.
- The entire modeled flow is operable by keyboard.
- Focus is always visible and deliberately placed after any meaningful transition.
- Dialogs have an accessible name, contain focus, close on Escape, and restore focus to
  the trigger.
- Form errors are programmatically associated with their controls; important status
  changes are announced.
- Nothing essential hides behind hover — touch has no hover.
- `prefers-reduced-motion` is respected while state feedback survives.
- Touch targets are comfortable; no page-level horizontal overflow.

In mockup mode, semantic structure and visible focus styles still apply even where
controls are unwired.

## Build contract

One self-contained `.html` file with CSS and JS inline. No build tooling, no auth, no
live API, no external service. Responsive composition rather than a shrunken desktop
canvas. A small token set specific to the chosen direction. Accessible contrast, and
never color alone to convey state.

## Verify before handing off

At wide and narrow widths: exercise every modeled state and control; test Tab,
Shift+Tab, Enter, Space, arrow keys where relevant, and Escape on dialogs; check the
console; check overflow; check long content; check disabled behavior; check focus
restoration; check reduced-motion mode.

Inspect computed foreground and background colors on **every distinct surface** —
especially text inside a dark or tinted region that may be inheriting the body color.
This is the most common invisible contrast failure.

If no browser is available, say plainly which visual and interaction checks remain
unverified. Reading the source is not a substitute for looking at the result.

Hand off with: absolute file path, fidelity mode, the scenario modeled, the states
implemented, the states deliberately omitted, and the production behavior left out.
