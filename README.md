# agent-design-studio

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Your agent can already write UI. This teaches it to design.**

A seven-step design process an AI coding agent runs end to end — intake, fidelity,
wireframe, three real directions, a token system, motion, review. Every step leaves an
artifact on disk. Two steps stop and wait for a person.

🔗 **[ducnguyen221.github.io/agent-design-studio](https://ducnguyen221.github.io/agent-design-studio)** ·
🇻🇳 **[Tiếng Việt](README.vi.md)**

---

## Why this exists

Ask an agent for a landing page and you get the first thing it thought of, in the same
three looks it produces for everyone. Not because the model lacks taste — because nothing
in the request forced a choice. There was no brief, no alternative to reject, no floor to
clear, and no reviewer.

This pack supplies all four. It is one skill and eleven references: a router that decides
what happens next, and playbooks that carry the actual craft — decision orders, thresholds,
curve values, colour maths, and the parts that tell the agent to stop and build nothing.

**Every capability is a slot.** If your setup has a stronger specialist for a step, the
router uses it; if not, the built-in playbook runs. No second pack is required to get the
whole process.

## The seven steps

| Step | What happens | Artifact |
| --- | --- | --- |
| **0** Target mode | Self-contained artifact, or a screen inside a real codebase. It changes what "done" means | — |
| **1** Intake | Subject, audience, and the single job this screen must do. Read what already exists first | `00-brief.md` |
| **2** Fidelity | How finished this needs to be — the first real design decision | `01-fidelity.md` |
| **3** Wireframe | Structure only, deliberately unfinished. States, viewports and keyboard flow declared here | `02-wireframe.html` + `.png` |
| **4** Direction — **GATE** | Three genuinely different renders, built for real. Never a written menu of adjectives | `03-directions/{a,b,c}` + `03-direction-decision.md` |
| **5** System + build | Colour sampled from real assets and justified in one sentence. Then the code | `04-design-system/` + `05-implementation.md` |
| **6** Motion | Every animation passes four gates or is refused in writing. Refusals are part of the output | `06-motion-spec.md` |
| **7** Review — **GATE** | Scored on six dimensions against a hard floor. Fixed one commit at a time, then verified | `07-uat-report.md` |

Everything lands in `<project>/design/<date>-<slug>/`.

### What makes it different from a prompt

- **Three directions, built for real.** Not three adjectives to choose between. Three
  rendered pages, produced by three deliberately incompatible logics so they cannot
  converge, screenshotted and put side by side. Then the process *stops* — picking one is
  yours.
- **Colour is derived, never invented.** Sampled from brand assets, real imagery, or the
  subject's own world; converged in a perceptually uniform space; and justified in one
  sentence. If that sentence cannot be written, the palette was copied from a formula.
- **Motion has to earn it.** Four gates — frequency, purpose, speed, function. The output
  includes what was *refused* and why. On most surfaces that list is longer than the
  accepted one.
- **A floor that does not move.** Body ≥14px, labels ≥12px, contrast ≥4.5:1, visible focus,
  full keyboard operation, reduced motion honoured, and every UI state declared from the
  wireframe onward — not discovered at review.
- **Two gates that autonomous runs cannot skip silently.** Each gate is a file in one of
  three states: `pending`, `human-approved`, or `policy-auto-selected`. An unattended run
  either holds a grant and records its reasoning, or it stops and says so.

## STATUS.md — the page for everyone else

Every run maintains a one-page dashboard: which step is done, which is waiting, who it is
waiting on, and a link to every artifact. Written for the person paying for the work rather
than the one doing it, so nobody has to ask where things stand.

## Install

**Claude Code**

```
/plugin marketplace add ducnguyen221/agent-design-studio
/plugin install agent-design-studio
```

**Codex**

```
codex plugin marketplace add ducnguyen221/agent-design-studio
codex plugin add agent-design-studio@agent-design-studio
```

**Any other agent that reads `SKILL.md`**

```bash
git clone https://github.com/ducnguyen221/agent-design-studio
cp -r agent-design-studio/skills/design-routing ~/.agents/skills/
```

No package dependencies and no build step. A browser is what turns renders into verified
renders — without one, visual checks stay `unverified` and the gates stay `pending`. The
process reaches the network in two places by design: verifying that a product or exemplar
really exists, and downloading real brand assets instead of guessing at them.

## Using it

**→ [GUIDE.md](GUIDE.md) — how to brief it well**: the six inputs that matter,
fill-in prompt templates, what to say at the two checkpoints, and where to find
inspiration. Five minutes that change the quality of everything it builds for you.

On whole-interface asks it usually triggers on its own:

> "Build me a landing page for our scheduling tool."
> "Redesign the customer portal — it looks dated."
> "Design the onboarding screen in our React app, here's the brief."

When many design skills are installed, invoking `design-routing` directly is the reliable
path.

It deliberately stays out of narrow single-step work — critiquing an existing page,
converting an approved design to HTML, picking a palette, drawing charts, or tuning the
layout of an existing deck. Those have better-suited tools, and this process would be
overkill. Designing a new deck, report, or infographic as a whole surface is a different
matter: that is in scope, and runs in static-artifact mode.

## What's inside

```
skills/design-routing/
├── SKILL.md                    the router: modes, slots, steps, gates, floor
└── references/
    ├── ownership-matrix.md     one owner per capability, and the intake step
    ├── choosing-fidelity.md    wireframe / mockup / prototype / production
    ├── wireframe-playbook.md   structure only, and the state + viewport contract
    ├── prototype-playbook.md   modelling real behaviour and real states
    ├── direction-gate.md       three anti-convergence logics + a 40-entry style catalogue
    ├── brand-asset-protocol.md finding real logos and assets instead of guessing
    ├── color-protocol.md       sample → converge → justify, with the chroma table
    ├── taste-calibration.md    the defaults to avoid, and writing as design material
    ├── motion-playbook.md      the full motion lifecycle, and what to refuse
    ├── library-selection.md    choosing a dependency, or not adding one
    └── uat-report-schema.md    the scored review and the hard floor
```

The router loads only the current step's references, so context stays lean.

## This site was designed by the process

[`docs/index.html`](docs/index.html) was produced by running all seven steps — wireframe,
three directions, a gate, a derived palette, a motion pass with eight refusals, and a
review that found three blocking defects and fixed them. The page shows its own artifacts.

Five improvements in v1.0 came from that run: a style catalogue that was promised and
missing, a rule that motion must never gate content availability, and three clarifications.
Being the first user is the cheapest review there is.

## Contributing

Issues and pull requests welcome. The one rule that matters: **every reference is a
playbook an agent can execute** — decision orders, checklists, thresholds, tables. If a
change reads like an essay, it belongs somewhere else.

## Acknowledgments

This process distils ideas from four open projects. The reasoning was re-expressed in our
own words rather than copied; the specific thresholds and values we learned from them are
used with gratitude. The debt is real and specific.

| Project | License | What it taught this pack |
| --- | --- | --- |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | MIT | Motion craft: the decision order, the frequency gates, the curve and duration values, springs and interruptibility, and the standard that approval is earned |
| [anthropics/skills → `skills/frontend-design`](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Apache-2.0 | Anti-generic calibration, the two-pass plan-then-critique method, restraint, and writing treated as design material |
| [plannotator/effective-html](https://github.com/plannotator/effective-html) | MIT | Choosing fidelity first, wireframes kept deliberately unfinished, prototypes that model real states, and the one-entrance routing shape |
| [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) | MIT | The three-direction gate, the brand asset protocol, the colour derivation method, and the scored critique |

Thank you to their authors.

## License

[MIT](LICENSE) © 2026 Duc Nguyen
