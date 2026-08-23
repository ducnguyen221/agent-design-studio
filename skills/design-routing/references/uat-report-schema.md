# UAT report schema

Step 7. Review what was built, fix it, verify the fix, and close Gate 2.

Output: `07-uat-report.md` (and `.json` when a machine will read it).

## The loop

1. **Mechanical pre-pass.** If a static linter is available, run it first — it finds the
   boring class of defects for free. If it is unavailable or offline, skip it and note
   that in the report; the manual checks below still apply.
2. **Hard floor check.** The pass/fail list below. Any failure is a defect, not a
   suggestion.
3. **Five-dimension critique.** Scored, with evidence.
4. **Motion review.** Run the motion playbook's review bar against Step 6's output.
5. **Fix, one issue at a time.** Each fix is its own commit with a before/after
   screenshot. Never batch unrelated fixes — when something regresses, you need to know
   which change caused it.
6. **Re-verify** the specific thing you fixed, at every viewport it affects.
7. **Close Gate 2.**

## The hard floor — pass or fail, no score

Declared at Step 3, verified here. Every row is checked at all three viewports.

- [ ] Body text ≥14px; labels and captions ≥12px.
- [ ] Text contrast ≥4.5:1, measured on **computed** colors on **every distinct surface**
      — including text inheriting the body color inside a dark or tinted region.
- [ ] Focus visible on every interactive element; the whole modeled flow is
      keyboard-operable; focus placed deliberately after each view change.
- [ ] Dialogs: accessible name, contained focus, Escape closes, focus returns to trigger.
- [ ] `prefers-reduced-motion` honored wherever motion exists.
- [ ] Every declared UI state exists and was exercised: loading, empty, error, validation,
      disabled, permission-denied — or is explicitly listed as out of scope.
- [ ] No accidental horizontal overflow at any viewport.
- [ ] No console errors.
- [ ] No dead controls. Anything the real system would own is labeled as a boundary.
- [ ] Every named brand's real logo is present; no product drawn as a CSS silhouette.
- [ ] Meaning never carried by color alone.

A failure here blocks Gate 2 regardless of how well the design scores below.

## Five dimensions, scored 0–10

Score with evidence, not adjectives. Every score cites something specific.

**0. Concept — weighted highest.**
Ask whether the design has an idea before asking how well it is executed. Execution is a
multiplier, and multiplying an empty concept only makes the emptiness bigger.

| Score | Standard |
| --- | --- |
| 9–10 | An idea grown from this content; the visual motif could not be swapped out |
| 7–8 | A clear intent; the motif relates to the content but would survive a neighboring topic |
| 5–6 | Style without concept: good-looking, saying nothing |
| 3–4 | A generic template wearing this content |
| 1–2 | Not even a style choice — decoration piled up |

Test it: *Can you state the idea in one sentence? Cover every word and logo — is the
subject still recognizable? Swap in a different client's name — does it still work?* If
the last answer is yes, it is a template, and this dimension caps at 5.

**Veto rule: concept ≤5 caps the overall score at 6.0.** Fix the concept before polishing
execution.

**1. Direction consistency.** Does the design actually deliver the direction chosen at
Gate 1, or has it drifted toward a house default? Check that the color, type, and layout
decisions trace back to `03-direction-decision.md`, and that no element contradicts the
stated intent.

**2. Visual hierarchy.** Does the eye move the way the designer intended? Heading-to-body
size contrast of at least 2.5× (3× is comfortable); three or four legible levels built
from size, weight, and color; white space guiding rather than merely existing. Squint at
it: if the hierarchy survives blurred, it is real.

**3. Craft.** One spacing system, used consistently (an 8-point scale is a safe default).
Equal spacing between equivalent elements. Controlled color count — one primary, one
secondary, one accent, plus a neutral ramp. At most two type families, with variation
carried by weight and size. Precise edge alignment.

**4. Function.** Every element earns its place: *remove it — is the design worse?* If not,
remove it. The primary action sits where the eye lands first. Information density matches
the medium and the viewing distance.

**5. Originality.** Avoided the known defaults (see the taste calibration reference).
Found a specific expression inside the chosen direction. Contains at least one decision
that is surprising and, on reflection, obviously right.

## Scoring guide

Overall is the weighted read, not a mean: **8.0+** excellent · **6.0–7.9** good ·
**4.0–5.9** needs work · **below 4.0** not acceptable. Concept ≤5 caps it at 6.0
regardless.

## The report

```markdown
# 07 — UAT report
**Date:** YYYY-MM-DD · **Build reviewed:** <path or commit>
**Gate 2 state:** pending | human-approved | policy-auto-selected

## Hard floor
PASS / FAIL — <failing rows listed, each with file:line and viewport>

## Scores
| Dimension | Score | One-line evidence |
|---|---|---|
| Concept | /10 | <the idea, in one sentence — or the absence of one> |
| Direction consistency | /10 | |
| Visual hierarchy | /10 | |
| Craft | /10 | |
| Function | /10 | |
| Originality | /10 | |
| **Overall** | **/10** | <band, and whether the concept cap applied> |

## Keep
- <what genuinely works, in design language — this calibrates the fixes>

## Fix
Ordered by severity: **blocking** / **important** / **polish**

**1. <name>** — blocking
- Now: <what it does today, with file:line>
- Problem: <why it is a problem>
- Fix: <the concrete change, with values>
- Verified: <before/after screenshot paths, commit>

## Quick wins
If there are only five minutes, do these three:
- [ ] <highest leverage>
- [ ] <second>
- [ ] <third>

## Motion review
<verdict from the motion playbook's review bar: block or approve, with findings>

## Unverified
<checks that could not be run — no browser, linter offline, device unavailable>

## Gate 2
Human-approved: "<their words>", YYYY-MM-DD
— or —
Policy-auto-selected: <criteria, decision, and the grant that permitted it>
```

## Reviewer discipline

- **Default to flagging. Approval is earned.** "It works" is not the bar.
- **Cite `file:line`.** A finding without a location is an opinion.
- **One fix per commit**, each with before/after evidence.
- **Say what you could not check.** Reading source is not a substitute for looking at the
  rendered result, and a report that hides its blind spots is worse than one that admits
  them.
- If a checker skill disagrees with the owner's decision, record both positions here
  rather than editing over the top of each other.
