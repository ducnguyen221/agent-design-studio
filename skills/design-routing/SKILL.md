---
name: design-routing
description: Use when a user interface must be designed and built as a whole — a new page, screen, app view, dashboard, or site from a brief, or a full redesign of something already shipping — and the visual direction is not yet settled, so going straight to code would be guessing. Also use when asked to run a design process, to see real options before committing, or to take a UI from brief through build to review. Not for narrow single-step asks: critiquing an existing page, converting an approved design to HTML, picking only a palette or font, charts and data visualizations, slide layout, or generating design images.
---

# Design Routing

The single entrance to a seven-step design process. This file is a router: it decides
the mode, orders the steps, holds the two approval gates, and loads exactly one
reference per step. The substance lives in `references/`.

**Core rule: no step starts before the one before it produced its artifact.** Skipping
forward is how interfaces end up beautiful and wrong, or correct and forgettable.

## Step 0 — Set the target mode

Decide before anything else. It changes what "done" means.

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
| `browser` | Screenshot and interact for every render step | Ask the user to open the file and describe or paste back |

**One owner per capability.** A second skill covering the same ground is a checker that
reports findings, never a second author who edits. Two authors on one surface produce
drift, not quality.

## The seven steps

Load the reference named in the row, do the step, write the artifact, update `STATUS.md`.
Do not preload references for later steps.

| # | Step | Load | Artifact |
| --- | --- | --- | --- |
| 1 | Intake — subject, audience, the one job this screen must do | `ownership-matrix.md` | `00-brief.md` |
| 2 | Fidelity — how finished this needs to be, and why | `choosing-fidelity.md` | `01-fidelity.md` |
| 3 | Wireframe — structure only, deliberately unfinished | `wireframe-playbook.md` | `02-wireframe.html` + `.png` |
| 4 | Direction gate — three genuinely different real renders | `direction-gate.md` | `03-directions/{a,b,c}.html` + `.png`, `03-direction-decision.md` |
| 5 | Design system + build | `brand-asset-protocol.md`, then `color-protocol.md`, then `taste-calibration.md` | `04-design-system/{tokens.json,components.md,assets-manifest.md}`, `05-implementation.md` |
| 6 | Motion pass — a **second pass over the built page**, never planned during Step 5 | `motion-playbook.md` | `06-motion-spec.md` |
| 7 | Review loop | `uat-report-schema.md` | `07-uat-report.md` |

Step 2 may route to `prototype-playbook.md` instead of a wireframe when the open question
is behavior rather than structure. Step 5 in `existing-product` mode also loads
`library-selection.md` when a new dependency is on the table.

All artifacts live in one folder: `<project>/design/<YYYY-MM-DD>-<slug>/`.

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
- **Reduced motion.** Honored wherever motion exists, as a gentler variant rather than
  nothing.

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
| 3 Wireframe | done | 02-wireframe.png | — |
| 4 Direction | GATE 1: pending | 03-directions/ | your choice of A / B / C |
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

This process is for designing an interface. It is not a way to run a whole product
discovery, and it does not replace engineering review of the code it produces. When the
business question underneath the brief is unresolved — who pays, what the user is
actually trying to do, whether this screen should exist — stop at Step 1 and say so.
