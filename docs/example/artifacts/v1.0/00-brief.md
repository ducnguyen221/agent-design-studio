# 00 — Brief

Mode: **static-artifact**
Date: 2026-08-24

## Step 0 — Target mode decision

`static-artifact`. The deliverable is `docs/index.html` served from GitHub Pages: one
self-contained file, opened by double-click or by URL, no build step, no framework. There
is no existing product codebase to extend, so `existing-product` does not apply.

**Subject.** A design process, packaged as an agent skill, that takes an AI coding agent
from a brief to a reviewed interface in seven steps.

**Audience.** People who already use AI coding agents (Claude Code, Codex, Antigravity)
and are tired of getting interfaces that look like every other AI-generated page. Two
sub-groups: students learning the craft, and practitioners who want a repeatable process
they can point an agent at. They are technical enough to install a plugin, and they judge
a design tool by whether its own page looks designed.

**The one job.** Convince a visitor within one screenful that this process produces
work their current setup does not — then get them to the install command.

**Success looks like.** A visitor installs the pack, or sends the link to someone else.
The observable proxy: they scroll past the hero.

## Existing material

| Item | Found | Path / note |
| --- | --- | --- |
| Design tokens | None | Greenfield — no design system to inherit |
| Components | None | Single file, no framework |
| Brand assets | None | The project has no logo yet. **Consequence: no brand asset protocol run for a client brand; the color protocol samples from context instead** |
| Palette reference | Yes | The owner's personal site, read locally, extracted per the brand asset protocol. See `04-design-system/assets-manifest.md` |
| Real content | Yes | The seven steps, the artifact contract, and the pack's own reference set — all of it exists and is final. No lorem needed anywhere |
| Screenshots | Generated during this run | The page illustrates itself with artifacts from this very pipeline |

## Constraints

**Must include.** The seven steps. Who it is for. Install commands for two harnesses
(placeholder URLs — real ones land in D4). The artifact trail 00→07 plus `STATUS.md`.
An acknowledgments footer crediting four upstream projects by name.

**Must be bilingual.** English primary, Vietnamese available. Both languages carry the
same content — a Vietnamese visitor must not get a degraded page.

**Must be self-contained.** One HTML file. Every image a data URI. No external requests
except a web font, which must degrade to a system stack.

**Must have real motion**, earned through the motion playbook's gates rather than
decorated on. This is a rare-tier marketing page, so the delight budget applies — but
the page is the showcase for a process that refuses unjustified motion, so every
animation here has to survive its own review or the page contradicts its own argument.

**Must take color inspiration from the reference site without inheriting it.**

## Assumptions

- `ASSUMPTION:` Install URLs are placeholders (`<owner>/agent-design-studio`) until D4
  fixes the repo path. Marked visibly in the artifact so no one ships a fake command.
- `ASSUMPTION:` The visitor arrives from a link — social, a README, or word of mouth —
  not from search. The hero does not need to explain what an agent skill is from zero,
  but must not assume they know this project.
- `ASSUMPTION:` English is the primary language; Vietnamese is a first-class toggle, not
  a machine-translated afterthought.

## Out of scope

Documentation of each reference file. A blog. Versioned docs. Analytics. A newsletter.
Anything requiring a server. The page links to the repository for depth.

## Capability slots for this run

Every slot falls back to the built-in playbook. This is deliberate: the run doubles as a
test of whether the pack is genuinely self-sufficient for a student who installs nothing
else.

| Slot | Filled by |
| --- | --- |
| `intake-advisor` | Built-in (this file) |
| `style-knowledge` | Built-in — direction axes in `direction-gate.md` |
| `codegen` | Direct authorship |
| `taste-canon` | Built-in — `taste-calibration.md` |
| `visual-reviewer` | Built-in — `uat-report-schema.md` |
| `static-lint` | Unavailable offline. Skipped, noted in the UAT report |
| `browser` | Headless browser via `npx`, verified available |

## Escalate?

No. The business question is settled: this page exists to distribute a pack that is
already built.

## Facts verified before designing

- The four upstream projects credited in the footer exist, with the licenses stated, at
  the SHAs recorded during D1. Verified 2026-08-23.
- The install mechanisms named (plugin marketplace for one harness, plugin add for the
  other) match the documented commands of packs already installed on this machine.
- No claim about download counts, users, or endorsements appears anywhere on the page —
  there are none, and inventing social proof is the one failure a visitor cannot detect
  and would be right to punish.
