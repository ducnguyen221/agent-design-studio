# agent-design-studio

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Your agent can already write UI. This teaches it to design.**

A seven-step UI design process an AI coding agent runs end to end — intake, fidelity,
wireframe, three real directions, a token system, motion, review. A separate Design System
skill creates, extracts, audits, documents and extends the system a product owns, as one
folder of files that imports into Claude Design and that any agent can read. Both leave
traceable artifacts; the UI process keeps its two human decision gates.

🔗 **[ducnguyen221.github.io/agent-design-studio](https://ducnguyen221.github.io/agent-design-studio)** ·
🇻🇳 **[Tiếng Việt](README.vi.md)**

---

## Why this exists

Ask an agent for a landing page and you get the first thing it thought of, in the same
three looks it produces for everyone. Not because the model lacks taste — because nothing
in the request forced a choice. There was no brief, no alternative to reject, no floor to
clear, and no reviewer.

This pack supplies all four through two skills. `design-routing` is the UI workflow and its
eighteen references carry the craft — decision orders, thresholds, curve values, colour
maths, and the parts that tell the agent to stop and build nothing. `design-system` owns
reusable system work across products and codebases and has four references of its own,
so the pack holds twenty-two.

**Every capability is a slot.** If your setup has a stronger specialist for a step, the
router uses it; if not, the built-in playbook runs. The two skills have separate jobs:
the router owns a UI build or reference-only analysis; the Design System skill owns
long-lived system work.

## The seven steps

| Step | What happens | Artifact |
| --- | --- | --- |
| **0** Target mode | Self-contained artifact, or a screen inside a real codebase. It changes what "done" means | — |
| **1** Intake | Subject, audience, and the single job this screen must do. Read what already exists first | `00-brief.md` |
| **2** Fidelity | How finished this needs to be — the first real design decision | `01-fidelity.md` |
| **3** Wireframe | Structure only, deliberately unfinished. States, viewports and keyboard flow declared here | `02-wireframe.html` + `.png` |
| **4** Direction — **GATE** | Three genuinely different renders with up to two static motion hypotheses each | `03-directions/{a,b,c}` + `03-direction-decision.md` |
| **5** System + build | Colour sampled from real assets; render the chosen page statically before motion | `04-design-system/` + `05-implementation.md` |
| **6** Motion | Recheck each hypothesis against four gates, choose a purpose-led recipe or refuse it | `06-motion-spec.md` |
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

The `design-system` scripts (build, verify, export) need Python 3.12 or later and nothing
else; the references and templates need no runtime.

**Claude Code** (2.1.275 or later, one step)

```
/plugin install agent-design-studio --marketplace ducnguyen221/agent-design-studio
```

Older versions add the marketplace first:

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
cp -r agent-design-studio/skills/design-system ~/.agents/skills/
cp -r agent-design-studio/scripts ~/.agents/scripts
```

The build and verify commands of the Design System skill run from `scripts/`, which must sit
two folders above the skill folder (here `~/.agents/scripts`); copy it too, or work from a
full clone.

No package dependencies and no build step. A browser is what turns renders into verified
renders — without one, visual checks stay `unverified` and the gates stay `pending`. The
process reaches the network in two places by design: verifying that a product or exemplar
really exists, and downloading real brand assets instead of guessing at them.

## Using it

**→ [GUIDE.md](GUIDE.md) — how to brief it well**: the six inputs that matter,
fill-in prompt templates, what to say at the two checkpoints, and where to find
inspiration. Five minutes that change the quality of everything it builds for you.

For English/Vietnamese type decisions, use the
[typography reference](skills/design-routing/references/typography-en-vi.md): contextual
font shortlists, starting sizes and checks for real glyphs, loading and text resizing.

For outside UI/UX examples, start with links in your brief and then use the
[resource index](skills/design-routing/references/resource-index.md). It routes to a
76-source [JSON catalog](skills/design-routing/resources/uiux-catalog.json). Shortlist
two or three fitting sources, inspect relevant samples when needed, and choose a
direction together at Step 4. The catalog is link-only: entry pages do not establish
observed demos, runtime results, or permission to reuse code and assets. Optional local
filtering: `python scripts/verify-resource-pack.py --query "loading" --stack React`;
`--self-test` checks the pack without fetching sites.

For a supplied UI image, link, or sample content that needs analysis before a build, use
the [reference distillation guide](skills/design-routing/references/reference-distill.md)
and its [Markdown template](skills/design-routing/templates/reference-design.md). It
separates observation, inference and unknowns, then carries your chosen constraints into
the design process. Analysis alone does not start a render gate.

For a reusable product Design System, invoke `design-system` directly. It has five modes:
`create` from selected references or brand material, `extract` from a codebase,
`audit` an existing system against implementation, `document` one component, and
`extend` an approved system. The result starts as a run-scoped proposal/report; existing
canonical sources stay in charge until the owner confirms a promotion and a reviewer
checks it. The folder it produces is described in [Design System folder](#design-system-folder).

Use this handoff when reference analysis should inform a reusable system: first select
references with the user, distill them with the guide and
[reference template](skills/design-routing/templates/reference-design.md), then pass the
selected source IDs, observed/inferred/unknown claims, rights status, and owner questions
to `design-system`. A reference shortlist or distill does not approve brand decisions.
For the product-owned folder contract, see
[system-contract.md](skills/design-system/references/system-contract.md); start at
[DESIGN.md](skills/design-system/templates/DESIGN.md), then use the
[component README template](skills/design-system/templates/component-v3/README.md) and
[audit report](skills/design-system/templates/audit-report.md) as needed.

On whole-interface asks it usually triggers on its own:

> "Build me a landing page for our scheduling tool."
> "Redesign the customer portal — it looks dated."
> "Design the onboarding screen in our React app, here's the brief."

When many design skills are installed, invoking `design-routing` directly is the reliable
path (`/agent-design-studio:design-routing`). Some hosts send "make me a page" to a built-in
artifact tool before any skill is considered; see
[Using with design:design-system](#using-with-designdesign-system).

It deliberately stays out of other narrow single-step work — critiquing an existing page,
converting an approved design to HTML, picking a palette, drawing charts, or editing a
PowerPoint or other non-HTML deck. Those have better-suited tools, and this process would
be overkill. Designing a new deck, report, or infographic as a whole surface is a different
matter: that is in scope, and runs in static-artifact mode, as is the visual layout check and
fix loop (render, look, fix) for any HTML deck or microsite, which is not functional or
browser-flow testing. A critique-only pass over an existing page, with no
fixing, stays out.

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
    ├── image-sourcing.md       are images content or decoration, and proving where each came from
    ├── color-protocol.md       sample → converge → justify, with the chroma table
    ├── taste-calibration.md    the defaults to avoid, and writing as design material
    ├── typography-en-vi.md     contextual font choices, type scale and EN/VI checks
    ├── motion-playbook.md      the full motion lifecycle, and what to refuse
    ├── motion-patterns.md      six purpose-led recipes with failure and reduced-motion states
    ├── resource-index.md       source shortlist by task; catalog loads only on demand
    ├── reference-distill.md    supplied sample to Markdown design reference
    ├── library-selection.md    choosing a dependency, or not adding one
    ├── static-artifact-build.md building decks and microsites as one self-contained file
    ├── static-artifact-qa.md   render, look and fix loop for any HTML deck or microsite
    └── uat-report-schema.md    the scored review and the hard floor
└── templates/
    ├── 06-motion-spec.md        traceable motion decision template
    ├── static-motion-demo.html  original CSS/WAAPI example
    ├── react-motion-demo.tsx    original React example; no extra motion package
    └── reference-design.md      one-file reference analysis template
```

```
skills/design-system/
├── SKILL.md                    create / extract / audit / document / extend router
├── agents/openai.yaml          Codex adapter; implicit invocation on
├── references/
│   ├── system-contract.md      package tree, required files, read order, error codes
│   ├── token-contract.md       v3 token grammar, derived DTCG, legacy maps
│   ├── design-md-spec.md       DESIGN.md: front matter keys and the eight sections
│   └── source-code-audit.md    scoped source evidence and coverage
├── templates/
│   ├── brand-v3/               starter package (profile minimal), fictional brand
│   ├── DESIGN.md               DESIGN.md starter: eight sections
│   ├── component-v3/           component README and preview
│   ├── agent-adapters/         AGENTS.md / CLAUDE.md / GEMINI.md templates (.tmpl)
│   ├── audit-report.md         run-scoped evidence, coverage and drift
│   └── extend-proposal.md      delta, migration and promotion record
└── tests/fixture/              anonymous full-profile package used by the verifier
```

`design-routing` keeps its eighteen references and its UI build/reference-only scope.
`design-system` is a separate entrypoint for product-owned, reusable system work, with four
references: twenty-two in the pack. Each skill loads only the references for its current task,
so context stays lean.

## Verify a Design System contract

From this repository, run `python scripts/verify-design-system.py --self-test` for
the contract tests, or `python scripts/verify-design-system.py` for the skill pack.
To check a package folder, use `--package <dir>` (`--profile full|minimal`). Single files
have their own flags, with paths relative to `--root`: `--tokens` (v3 list grammar),
`--canonical-map`, `--dtcg` (the DTCG subset) and `--legacy-tokens` (a legacy map only);
`--manifest` remains a deprecated alias of `--canonical-map`. The checks never fetch
outside pointers, run package code or generate CSS. Structural success does not verify
rendering, source coverage, accessibility or asset rights. CI
(`.github/workflows/verify-skills.yml`) runs the same checks on every push to `main` and
`sprint/**`.

## This site was designed by the process

[`docs/index.html`](docs/index.html) was produced by running all seven steps — wireframe,
three directions, a gate, a derived palette, a motion pass with eight refusals, and a
review that found three blocking defects and fixed them. The page shows its own artifacts.

Five improvements in v1.0 came from that run: a style catalogue that was promised and
missing, a rule that motion must never gate content availability, and three clarifications.
Being the first user is the cheapest review there is.

**The whole run is published**, including the version a person turned down:
[**browse it**](https://ducnguyen.vn/agent-design-studio/example/), or read the files in
[`docs/example/`](docs/example/). The brief, the wireframe, three directions that still
run in a browser, the design system, the motion spec with its refusals, and three review
reports — one of which passed a page that was rejected an hour later. Every change made
before publishing is listed in [`docs/example/ABOUT.md`](docs/example/ABOUT.md).

## Contributing

Issues and pull requests welcome. The one rule that matters: **every reference is a
playbook an agent can execute** — decision orders, checklists, thresholds, tables. If a
change reads like an essay, it belongs somewhere else.

## Design System folder

`design-system` keeps a system as one folder, the same one Claude Design imports (package
format v3, read 22 Oct 2026, research preview):

```
design-system/
├── DESIGN.md            entry file for any agent: front matter from tokens.json + 8 sections
├── README.md            brand book that Claude Design reads first
├── tokens.json          every token value, the data root
├── design-system.json   index, written last
├── canonical-map.json   one owner per domain, contrast pairs, decisions
├── viewer.html          offline page, generated
├── components/          Cover/ plus one folder per component (README.md, preview.html)
└── assets/              one folder per group, each with a README of sources and rights
```

The folder follows the published package format; an import into Claude Design itself has
not been run yet, which is why the verifier's PASS line lists `real-import` as unchecked.

DESIGN.md is the entry file for any agent; README.md is the brand book Claude Design reads
first; tokens.json holds every value. The `DESIGN.md` front matter and `viewer.html` are
derived from the files next to them, so edit `tokens.json`, regenerate, then verify (paths
below start at a clone of this repository; an installed plugin has the same `scripts/` folder):

```bash
python scripts/build-design-system.py --package design-system --design-md --viewer
python scripts/verify-design-system.py --package design-system
```

`viewer.html` is a static page, not a Claude Design render. It shows tokens, component
summaries and assets as text and inline images, works offline and runs no package code;
open a component's `preview.html` to see it drawn.

Claude Design refuses `AGENTS.md`, `CLAUDE.md` and `GEMINI.md` inside the package, so
those wrappers live one folder up, in the project that uses the system. Pass the folder
that holds `design-system/`; existing files are never overwritten (a proposal is printed
and counted as skipped):

```bash
python scripts/build-design-system.py --package design-system --adapters <project-root>
```

To start, copy `skills/design-system/templates/brand-v3/` to `design-system/` and replace
every placeholder. `python scripts/export-dtcg.py --package design-system --out tokens.dtcg.json`
derives a DTCG file when another tool wants one; it lists every token it had to skip.

## Using with design:design-system

Anthropic's `design` plugin also ships a skill named `design-system`. Both can be
installed. Four things to know:

1. **Measured activation.** Six prompts were run headless on Claude Code 2.1.309 with
   claude-sonnet-5-5, once each (22-23 Oct 2026). Five behaved as expected: three requests
   for system work (an audit with the folder path given, component documentation, a brand
   note turned into a folder) loaded `agent-design-studio:design-system` as the first tool
   call, and a palette-only ask and a brand-kit image ask did not. The Anthropic skill was
   never called. This is the second run on the same six prompts: the first run scored 4/6,
   and the description was then revised once, aimed at the audit case that had missed, so
   the 5/6 is measured on the prompts the revision was fitted to. One run per prompt is a
   sample, not a rate. The next measurement should add at least one differently worded
   prompt for each class (an audit with the path given, a whole-page brief) and more than
   one run each.
2. **Whole pages may need the skill named.** The one miss was a plain "build a landing page
   for a bakery" brief: the host sent it to its built-in artifact tool before any skill
   was considered, and in our runs a skill's wording did not reach that step. In such a host call
   `/agent-design-studio:design-routing` or say "use design-routing" for whole-page work;
   automatic activation on a bare page brief is not guaranteed there.
3. **Call by full name.** A bare `/design-system` is ambiguous when both plugins are
   installed. Use `/agent-design-studio:design-system` (in prose: `agent-design-studio:design-system`),
   or turn one of the two plugins off in `/plugin`.
4. **Where the trigger text lives.** The description agents match against is the 947
   characters in the front matter of `skills/design-system/SKILL.md`; edit it there to
   change when the skill activates.

## Acknowledgments

This process distils ideas from eight open projects: the four in the table below, and
four more recorded in [NOTICE](NOTICE) with their licenses and exact revisions. The
reasoning was re-expressed in our own words; the specific thresholds and values we learned
from them are used with gratitude, and where a passage follows a source more closely,
NOTICE says so. The debt is real and specific.

The new motion recipes also use [React Bits Animated Content](https://reactbits.dev/c/animations/animated-content)
as a live visual reference and [GSAP's demo/docs](https://demos.gsap.com/) and
[Motion's performance docs](https://motion.dev/docs/performance) for engine-specific
decisions. React Bits components are **not** included or ported: its
[MIT + Commons Clause license](https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md)
restricts redistribution of components. GSAP's [runtime license](https://gsap.com/community/standard-license/)
is separate from the MIT license of its [official agent skills](https://github.com/greensock/gsap-skills).

| Project | License | What it taught this pack |
| --- | --- | --- |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | MIT | Motion craft: the decision order, the frequency gates, the curve and duration values, springs and interruptibility, and the standard that approval is earned |
| [anthropics/skills → `skills/frontend-design`](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Apache-2.0 | Anti-generic calibration, the two-pass plan-then-critique method, restraint, and writing treated as design material |
| [plannotator/effective-html](https://github.com/plannotator/effective-html) | MIT | Choosing fidelity first, wireframes kept deliberately unfinished, prototypes that model real states, and the one-entrance routing shape |
| [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) | MIT | The three-direction gate, the brand asset protocol, the colour derivation method, and the scored critique |

The Design System skill also follows two published shapes, re-expressed in our own words:
Google Labs' [Design Markdown](https://github.com/google-labs-code/design.md)
(Apache-2.0, spec `alpha`, read 22 Oct 2026) for the section and key names of `DESIGN.md`, and
Anthropic's `design:design-system` skill for the idea of audit, document and extend modes.

Thank you to their authors.

## Author

**Nguyễn Quang Đức** (Tobi) — founder and CEO of KPIM and co-founder of COMPA Class; Data/AI practitioner and instructor in Vietnam.

Website: https://ducnguyen.vn · GitHub: [@ducnguyen221](https://github.com/ducnguyen221) · Contact: ducnguyen.ams@gmail.com

## License

[MIT](LICENSE) © 2026 Nguyễn Quang Đức

Third-party credits and license texts: [NOTICE](NOTICE) and [LICENSES/](LICENSES/).

## 🤝 ACD Ecosystem Integration

Khai báo vai của repo trong hệ thống nhiều repo ACD (Role, Upstream, Downstream, Bundles, Handoff) tại [ECOSYSTEM.md](ECOSYSTEM.md).
