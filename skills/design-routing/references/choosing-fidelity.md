# Choosing fidelity

Step 2. The first real design decision is not a color — it is how finished the artifact
needs to look. Get this wrong and every later step is either wasted polish or a review
of the wrong question.

Output: `01-fidelity.md`.

## The question that decides it

> **What is the one thing we do not yet know, and what is the cheapest artifact that
> would settle it?**

Answer that, then read it off the table.

| The open question is about… | Build a | Because |
| --- | --- | --- |
| What belongs on the screen, in what order, under what navigation | **Wireframe** | Structure is legible in grayscale; polish would hide it |
| How it should look and feel — hierarchy, type, color, whether it fits the brand | **Mockup** | A still frame answers a still question |
| How it behaves — a flow, validation, recovery, state changes, keyboard | **Prototype** | Only working behavior settles a behavior question |
| Nothing; the decision is made and the work is to ship it | **Production** | Go build it properly |
| How parts relate — architecture, sequence, ownership | **Diagram** | It is not a screen; don't design one |
| What order the work happens in | **Plain document** | HTML earns its place only when the plan needs visual comparison |

**This choice sets the finish level of the deliverable — it does not skip steps.** The
wireframe (Step 3) and the three direction renders (Step 4) are review instruments and are
produced regardless of what you choose here, even when the answer is "production". Choosing
production means the thing you hand over is production-ready; it never means going straight
to it.

## Fidelity is not a ladder you must climb

You may start at prototype if structure is settled and behavior is the risk. You may
stop at wireframe if the answer arrives there. What you may not do is jump to
production because the earlier artifact felt like a detour — that is how a team spends
a week polishing a layout nobody agreed to.

The one ordering rule that holds: **structure before surface**. Never resolve typography
on a layout no one has approved.

## Scope, not screens

A useful artifact covers one path deeply rather than every screen shallowly. Nine
half-built screens answer nothing; one complete flow with its real states answers the
question it was built for. Pick the smallest scope in which the open question can
actually be observed.

Anything the real system would do that this artifact does not — network calls, auth,
persistence, other screens — is named as a boundary rather than faked. Fake completion
is worse than an honest edge, because reviewers approve what they think they saw.

## Fidelity and cost

| Fidelity | Roughly costs | Buys you |
| --- | --- | --- |
| Wireframe | Least | Agreement on content and structure |
| Mockup | Moderate | A visual decision, and a target the build must hit |
| Prototype | More | Proof the interaction works before it is expensive to change |
| Production | Most | A shipped thing — and a costly place to discover you were wrong |

When two fidelities both seem defensible, take the cheaper one. Its output feeds the
more expensive one if you still need it; the reverse is never true.

## Write it down

```markdown
# 01 — Fidelity
**Open question:** <the one thing we do not know>
**Chosen fidelity:** wireframe | mockup | prototype | production
**Why this one:** <one sentence tying it to the open question>
**Scope:** <the smallest flow or screen that can answer it>
**Deliberately deferred:** <what a later, higher-fidelity pass will decide>
**Boundaries:** <what the real system would do that this will not>
```

If "why this one" comes out as "because that's what was asked for", push back once:
briefs routinely ask for production when a mockup would settle the disagreement in an
hour. Say what the cheaper artifact would answer, then follow the user's call.

## Common mistakes

- Producing a polished mockup when the argument is about navigation. Reviewers will
  discuss the button color and the navigation ships wrong.
- Producing a wireframe when the client has already approved structure and is waiting to
  see the look. It reads as stalling.
- Calling something a prototype when nothing works. If the buttons are decorative, it is
  a mockup — label it that way so reviewers know what they are approving.
- Deciding fidelity implicitly by opening an editor. It is a decision; write it down.
