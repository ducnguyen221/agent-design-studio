# Wireframe playbook

Step 3. Turn the brief into a low-fidelity artifact that makes structure — and only
structure — reviewable.

Output: `02-wireframe.html` plus a screenshot `02-wireframe.png` per viewport.

## What a wireframe is for

It answers: what belongs on this screen, in what order, grouped how, under what
navigation, reflowing how. It deliberately does not answer: what it looks like.

**A wireframe must look unfinished.** Not sloppy — unfinished. The moment it looks
designed, reviewers review the design and the structural question goes unanswered. That
is the single most common way this step fails.

Intentional unfinishedness is a discipline, not an excuse. Spacing is still consistent,
type is still legible, the responsive behavior still works. What is absent is polish,
not care.

## Authority order

When sources conflict, decide in this order:

1. The user's explicit instructions and any decision already accepted.
2. The product's existing structure and vocabulary.
3. The user, task, and content being modeled.
4. Your own layout judgment.

Use the product's real words. Never rename an existing concept because a shorter word
fits the column.

## The visual contract

Allowed: one grayscale ramp, the system font stack, plain 1px borders, simple blocks,
one small radius value, one spacing scale.

Not allowed: brand colors, gradients, shadows, illustrations, decorative imagery, icon
sets, styled components, hero photography.

Images and rich media appear as labeled placeholder blocks — `[product photo 16:9]` —
unless the asset itself changes a structural decision.

**Real labels, real content.** Low fidelity is not permission for lorem ipsum or
anonymous boxes. Wording drives layout: a button reading "Publish to all channels"
occupies different space than "Save". Write the words you actually mean.

## Explore structure before settling

When the layout is genuinely unsettled, build two or three structurally different
options in the same file, switchable by a small keyboard-operable control. Differences
must be product decisions:

- navigation model (sidebar vs top vs stepped);
- grouping and order of content;
- where the primary action lives;
- content density;
- overview-at-once vs step-by-step;
- how desktop reflows to mobile.

Recolored cards or a rearranged grid are not separate directions. Name each option and
give it one sentence of trade-off. If structure is already agreed, build one.

Note that this is a *structural* exploration, distinct from the Step 4 direction gate,
which is about visual identity and happens after structure is settled.

## Declare the hard parts here

Everything below is declared at Step 3, not discovered at Step 7.

**Viewport matrix.** Verify at ~390px, ~768px, ~1440px. Record what changes at each
breakpoint: what collapses, what stacks, what hides, what becomes scrollable. Compose
the narrow layout deliberately; do not shrink the wide one.

**UI states.** List every state each surface can reach, and sketch the ones that change
layout:

| State | Declare when | Note in the wireframe |
| --- | --- | --- |
| loading | Anything asynchronous | Where the placeholder sits and whether layout shifts |
| empty | Any collection | What the screen invites the user to do |
| error | Any request that can fail | Where the message appears and what recovery is offered |
| validation | Any form | Inline, next to the field, not a summary at the top |
| disabled | Any gated action | How the reason is communicated |
| permission-denied | Anything role-gated | What the user sees instead |

States the screen genuinely cannot reach are listed as out of scope, in writing.

**Keyboard flow.** Tab order, where focus lands after each navigation or disclosure,
what Escape does. Write it as a short ordered list in the artifact.

## Behavior: only what the review needs

Wire up links, tabs, and next/back when navigation is part of the question. Use native
controls and keep focus visible. Do not build animation, persistence, fake APIs, or
state management. Remove controls with no review purpose, or label them out of scope.

## Build contract

One self-contained `.html` file, CSS and JS inline, no build step, no network. Semantic
landmarks, headings, lists, form elements, real buttons. Useful at wide and narrow
widths with no horizontal overflow.

## Verify, then hand off

Open it at each viewport. Check reading order, wrapping, overflow, focus visibility, and
every click path you implemented. Confirm the structural options stay distinct at both
sizes — options that converge on mobile were never two options.

Hand off with: the absolute file path, the option names and trade-offs, the declared
state list, the keyboard flow, and an explicit list of what was deferred to later steps.

## Common mistakes

- Adding a brand color "just to show where the accent goes". Now it is a mockup.
- Placeholder text that is shorter than the real content, so the layout lies.
- Declaring states in prose but drawing none of the ones that change the layout.
- Building six screens instead of one screen and its states.
