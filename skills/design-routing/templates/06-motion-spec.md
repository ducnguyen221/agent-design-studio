# 06 — Motion spec

**Direction decision:** `03-direction-decision.md` — <chosen direction and existing approval evidence>
**Step 5 static baseline:** <render path / screenshot; confirm readable and actionable>
**Tokens used / added:** <existing curves, durations, spacing; add only when justified>

## Hypotheses from Step 4

| ID | Static keyframes in chosen direction | User need | Reference URL / observation | Inference, not observed fact |
| --- | --- | --- | --- | --- |
| H1 | <file/frames> | <need> | <specific open demo, trigger, before/after, control and viewport checked> | <principle to try; what is not copied> |

## Accepted

For each item, record a verdict for **frequency · purpose · speed · function** before implementation.

| Hypothesis | Four gate verdicts | What user understands or does better | Recipe ID | Purpose | Frequency | Tool | Properties | Curve/duration/spring | Token or exact value | Reference URL / observation → implementation | No-motion fallback | Reduced motion | QA evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | <four verdicts> | <one concrete sentence> | MP00 | <why> | <tier> | CSS/WAAPI/existing engine | <specific> | <value> | <token or value> | <URL and observation → file:line> | <visible and actionable if animation fails, even after start> | <per-item variant> | <browser path/trace/result, or unverified> |

## Refused

| Hypothesis | Four gate verdicts | Reason for refusal | Static outcome |
| --- | --- | --- | --- |
| H2 | <frequency · purpose · speed · function> | <which gate failed and why> | <no motion; current content/interaction> |

## Zero motion

If no hypothesis survives, say so here with the four gate results. Keep the Step 5
static implementation; do not invent an animation, dependency, or QA evidence.

## Dependency decision

**Platform / installed options checked:** <CSS/WAAPI and manifest result>
**Engine choice or refusal:** <why, including GSAP only if timeline/scroll/SVG complexity warrants it>
**Lifecycle / teardown:** <observer, animation, breakpoint, unmount and resize branches actually used; otherwise not applicable>
**Actual dependency record:** `05-implementation.md` owns package@version, bundle cost,
license, accessibility, and exit plan for anything added; link back to this decision.

## Accessibility and failure checks

- Reduced motion at load and after preference changes; keyboard and focus through the flow.
- Static content remains available with no JS (static artifact), observer absent/no callback,
  animation error/interruption after start, print and full-page capture where applicable.
- Nonessential autoplay over 5 seconds alongside content has keyboard pause/stop/hide,
  and stays stopped after focus moves. Do not use flashing/strobing.
- At 390, 768, and 1440px and through resize: no target movement under the pointer,
  unexpected layout shift, blocked action, or missing content.

## Needs a feel check

<Playback and device checks that source or static tests cannot settle; mark unverified until seen.>

## Verdict

<Why this amount of motion helps; name the single highest-value item or zero-motion result.>
