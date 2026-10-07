---
name: design-routing
description: "Use when a user interface must be designed and built as a whole — a new page, screen, app view, dashboard, or site from a brief, or a full redesign of something already shipping — and the visual direction is not yet settled, so going straight to code would be guessing. Also use when asked to run a design process, to see real options before committing, or to take a UI from brief through build to review. Also use to distill a user-supplied UI image, URL, or sample content into a reusable Markdown design reference before building. Not for other narrow single-step asks: critiquing an existing page, converting an approved design to HTML, picking only a palette or font, drawing charts or data visualizations, tuning the layout of an existing deck, or generating standalone images."
---

# Design Routing

The single entrance to a seven-step design process. This file is a router: it decides
the mode, orders the steps, holds the two approval gates, and loads only the current
step's references. The substance lives in `references/`.

**Core rule: no step starts before the one before it produced its artifact.** Skipping
forward is how interfaces end up beautiful and wrong, or correct and forgettable.

## Choose the output before the seven steps

Read the brief and existing brand/code material first. Record whether the requested
output is a reference, screen, flow, or reusable system. Ask once for the missing
audience, task, surface, constraints, reference/template preference and asset rights.
Offer at most three specific samples when useful; let the user send a link or image and
record the source they select or reject. If a missing choice could change the brand or
system, keep selection `pending` and continue only independent read-only work. Silence
is not approval and does not authorize invented brand rules.

| Output | Route |
| --- | --- |
| Reference analysis only | Distill one Markdown below and stop. |
| Design System from selected reference/brand material | Distill with a conditional Design System handoff, then use `agent-design-studio:design-system` `create`; no screen directions or build. |
| Design System from source code | Declare repo/commit/dirty baseline, allowed scope and a run output directory; use `agent-design-studio:design-system` `extract`. Keep source and approved DS unchanged. No screen directions or build. |
| Audit or extend an existing Design System | Use `agent-design-studio:design-system` `audit` or `extend` according to the requested change. |
| New screen or flow | Continue Step 0 and the seven steps below. |

The Design System skill owns its long-lived contract and canonical map. This router
owns the timing and gates of a UI build; it does not write a second canonical system.

## Reference-only preparation

If the request is to distill a supplied image, URL or sample content into Markdown without
building a new interface, load `references/reference-distill.md` and
`templates/reference-design.md`. Produce one reference design Markdown file. This does not
start the seven-step build or its gates. If implementation is requested later, carry the
chosen constraints into Step 1–4. If the sample accompanies a build request, distill it
as an input during intake, then continue the seven steps and normal rendered gate. If
the user asks for a reusable Design System, include the conditional handoff and route
to the Design System skill.

## Step 0 — Set the target mode

Decide before anything else. Step 0 is mode-setting preflight, not one of the seven
steps — it changes what "done" means for all seven.

| Mode | When | Deliverable |
| --- | --- | --- |
| `static-artifact` | Landing page, deck, report, demo, one-off microsite | Self-contained HTML/CSS the user can open by double-clicking |
| `existing-product` | A screen or flow inside a shipping application | Code in the product's own framework and conventions |

In `existing-product` mode, before Step 1: read the repository's agent instructions,
component library, design tokens, routing, and test conventions. HTML here is a
*prototype for review only* — never the deliverable. Never introduce a second design
system next to the one the repo already has.

State the chosen mode in one line and continue.

## Capability slots

This pack is self-sufficient. Where the host environment already provides a stronger
specialist, delegate to it; otherwise run the built-in playbook. Decide once, at Step 1,
and record the choice in `STATUS.md`.

| Slot | If the host has a suitable skill | Otherwise |
| --- | --- | --- |
| `intake-advisor` | Use it to run Step 1 | `references/ownership-matrix.md` intake block |
| `style-knowledge` | Use its style/palette/font library as raw material for Step 4 | Style axes in `references/direction-gate.md` |
| `codegen` | Use it to build directions and the implementation | Write the HTML/framework code directly |
| `taste-canon` | Use it as the anti-generic authority for Step 5 | `references/taste-calibration.md` |
| `visual-reviewer` | Use it to drive the Step 7 fix loop | `references/uat-report-schema.md` |
| `static-lint` | Run it as a mechanical pre-pass in Step 7 | Skip; the manual checklist still applies |
| `browser` | Screenshot and interact for every render step | Renders cannot be verified — mark the affected checks `unverified`, hold the gate at `pending`, and say so |

**One owner per capability.** A second skill covering the same ground is a checker that
reports findings, never a second author who edits. Two authors on one surface produce
drift, not quality.

**A verbal description is never visual verification.** With no browser or screenshot
capability, asking the user what they see collects useful information but closes nothing:
the render checks stay `unverified` and their gate stays `pending` until something
actually looks at the rendered result.

## The seven steps

Load the reference named in the row, do the step, write the artifact, update `STATUS.md`.
Do not preload references for later steps — load one when the work it governs starts,
which for one reference below is earlier than the step that writes its artifact.

| # | Step | Load | Artifact |
| --- | --- | --- | --- |
| 1 | Intake — subject, audience, the one job this screen must do | `ownership-matrix.md` | `00-brief.md` |
| 2 | Fidelity — how finished this needs to be, and why | `choosing-fidelity.md`, then `image-sourcing.md` if images are content | `01-fidelity.md` |
| 3 | Wireframe — structure only, deliberately unfinished | `wireframe-playbook.md` | `02-wireframe.html` + `.png` |
| 4 | Direction gate — three genuinely different real renders, each with up to two static motion hypotheses | `direction-gate.md`; `typography-en-vi.md` when EN/VI type is a direction decision | `03-directions/{a,b,c}.html` + `.png`, `03-compare.html`, `03-direction-decision.md` |
| 5 | Design System delta + static build, confirmed in a browser before animation | `brand-asset-protocol.md`, then `color-protocol.md`, then `taste-calibration.md`; `typography-en-vi.md` for EN/VI font and scale choices; `agent-design-studio:design-system` `create/extend` for the system contract | `04-design-system/` proposal and canonical pointer, `05-implementation.md` |
| 6 | Motion pass — decide and implement only after the static page works | `motion-playbook.md`, then `references/motion-patterns.md` and `templates/06-motion-spec.md` | `06-motion-spec.md` |
| 7 | Review loop | `uat-report-schema.md`; `typography-en-vi.md` for EN/VI type verification | `07-uat-report.md` |

Step 2 may route to `prototype-playbook.md` instead of a wireframe when the open question
is behavior rather than structure; Step 3's artifact is then `02-prototype.html` + `.png`,
replacing `02-wireframe`.

**Imagery is the one task that starts before the step that files it.** Answer one
checkpoint question at Step 2, alongside the fidelity call: **are images content here, or
decoration?** If the answer is content — or if you cannot tell — load
`image-sourcing.md` **then, right after Step 2**, and source the real set *before* Step 4,
because all three directions must consume the same images or the gate compares
photographs instead of designs. Step 5 does not start this work; it closes it, folding the
sourced assets into `04-design-system/assets-manifest.md`. If the answer is decoration,
the file is never loaded at all.

Step 5 may load `library-selection.md` for a non-motion dependency in
`existing-product` mode. Step 6 loads it whenever a motion dependency is considered in
either mode. Check the manifest and CSS/WAAPI first; record the chosen or refused engine
in `06-motion-spec.md`. `05-implementation.md` is the sole ledger of packages actually
added, their bundle cost, license, and exit plan, linking back to the motion decision.
For a starting point, `templates/static-motion-demo.html` and
`templates/react-motion-demo.tsx` are original examples, not required dependencies.

At Step 5, pass the approved direction, selected reference handoff, brand/asset rights,
surface, current token/component source and target Design System baseline to
`agent-design-studio:design-system` `create` or `extend`. Keep its draft/delta and
evidence in the run's `04-design-system/`; existing product CSS/TS/Figma sources retain
their declared authority. The router can implement the static screen, but only the
Design System skill authors the system contract. Promote approved deltas to the stable
system after the Step 7 ship review; unresolved owner/reviewer decisions stay pending.

When an outside UI/UX source would help, start with the brief and any user-supplied links,
then load `references/resource-index.md` and filter its catalog by task and stack. Keep at
most three fitting links. Inspect a specific sample only when needed; report its direct
URL, observation, fit and trade-off before the existing Step 4 direction gate. A source
homepage is not an observed sample. The shortlist informs the three rendered directions;
the user still chooses at that gate. Catalog links grant no code or asset rights.

UI run artifacts live in `<project>/design/<YYYY-MM-DD>-<slug>/`. A reusable Design
System lives at the product's declared canonical location, normally
`<project>/design-system/` for a new product. The run holds proposals and pointers;
it never silently replaces the canonical source.

## The two gates

Gate 1 closes Step 4 (which direction). Gate 2 closes Step 7 (ship or iterate).
Each gate is a file with one of three states, written down — never implied.

| State | Meaning | Required in the artifact |
| --- | --- | --- |
| `pending` | Waiting on a person. Stop the turn and present the options. | The options, rendered, with screenshots |
| `human-approved` | A person chose | Their choice, in their words, and the date |
| `policy-auto-selected` | No person available and the session's grant permits deciding | The choice, the criteria used, the rejected options, and why |

An unattended run does **not** silently skip a gate. It either has a grant to
auto-select and records the reasoning, or it stops at `pending` and says so. Presenting
three options and picking one yourself without recording that you did is the failure
this rule exists to prevent.

## The quality floor

Declared at Step 3 and re-checked at every step after. Not a Step 7 afterthought.

- **Viewports.** Mobile ~390px, tablet ~768px, desktop ~1440px. Design the narrow one as
  its own composition, not a squeezed desktop. No accidental horizontal scroll anywhere.
- **UI states.** Every surface declares which of these it can reach and how each looks:
  loading, empty, error, validation, disabled, permission-denied. States the screen
  cannot reach are listed as deliberately out of scope.
- **Keyboard.** The whole modeled flow is operable by keyboard, focus is always visible,
  and focus is placed deliberately after any view change. Dialogs trap focus, close on
  Escape, and return focus to whatever opened them.
- **Legibility.** Body text ≥14px, labels and captions ≥12px, text contrast ≥4.5:1.
  Never signal state with color alone.
- **Reduced motion.** Honored wherever motion exists: reduce or remove non-essential
  motion; preserve state feedback.

A direction that only works by breaking this floor is not a direction; it is a defect.

## STATUS.md

One page, written for someone who does not read code. Rewritten after every step.

```markdown
# <Project> — design status
Mode: static-artifact | existing-product · Updated: YYYY-MM-DD

| Step | State | Artifact | Waiting on |
|---|---|---|---|
| 1 Intake | done | 00-brief.md | — |
| 2 Fidelity | done | 01-fidelity.md | — |
| 3 Wireframe | done | 02-wireframe.png (or 02-prototype.png) | — |
| 4 Direction | GATE 1: pending | 03-compare.html + 03-directions/ | your choice of A / B / C |
| 5 System + build | not started | — | gate 1 |
| 6 Motion | not started | — | step 5 |
| 7 Review | not started | — | step 6 |

**Next thing that needs a human:** <one sentence, or "nothing">
**Open questions:** <bullets, or "none">
```

## Red flags — stop and go back

- Writing production CSS before Gate 1 closed.
- Colors chosen from memory or from what "feels right for a fintech" — Step 5 forbids it.
- A wireframe with brand colors, shadows, or a gradient in it.
- Three "directions" that share one layout skeleton with different palettes.
- An animation added because the page felt static.
- Step 7 finding a missing empty state — that was Step 3's job.
- Any gate file that does not exist while its step is marked done.

## Scope

Designing a new deck, report, or infographic as a whole surface is in scope — it runs in
`static-artifact` mode like any other one-off artifact. Polishing one that already exists
is not.

This process is for designing an interface. It is not a way to run a whole product
discovery, and it does not replace engineering review of the code it produces. When the
business question underneath the brief is unresolved — who pays, what the user is
actually trying to do, whether this screen should exist — stop at Step 1 and say so.
