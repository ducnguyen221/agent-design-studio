# About this example

A public, **immutable fixture**: the design run that produced this project's own site,
exported so anyone can read what the process actually writes.

Browse it at [`index.html`](index.html). This file is the provenance record — what was
exported, what was changed on the way out, and what was deliberately left behind.

---

## What produced it

| | |
| --- | --- |
| Run date | 2026-08-24 |
| Pack versions that produced it | **1.0.0** (pass 1) → **1.1.0** (pass 2) → **1.2.0** (pass 3) |
| Mode | `static-artifact` |
| Deliverable | this project's own site, `docs/index.html` |
| Exported | 38 source artifacts (27 text, 11 images) + 1 derived crop + 23 generated readable views |

**Three passes, kept as three passes.** This run is presented as history, not merged into
one tidy sweep through seven steps. Pass 1 completed all seven steps, passed its own
review at 7.8, was published, and was then turned down by the owner looking at the live
page. Pass 2 rebuilt on the direction that had lost the original vote. Pass 3 answered two
further owner directives. Each pass kept its own folder, and all three are here.

Presenting them as a single clean run would have been a lie about the most useful thing in
the folder — that a checkpoint caught something no automated check could.

## Frozen on purpose

These artifacts record what the pack produced **at v1.0.0 through v1.2.0**. They are not
retro-fitted when the pack changes. If a later version would have produced something
different, that belongs in a dated note at the bottom of this file — never in an edit to a
historical artifact, which would destroy the only thing a fixture is for.

### Delta notes

*(none yet — v1.3 changes are additive to Step 4 and Step 5 and do not invalidate anything
shown here. The compare board `03-compare.html` introduced in v1.3 did not exist when this
run was made; the run's three direction renders are presented individually, which is what
v1.0–v1.2 specified.)*

---

## Export allowlist

Nothing reaches this folder unless it is named in the allowlist of the (private) export
script. Everything else in the source run folder was left behind by default rather than by
judgement call.

### Pass 1 — `artifacts/v1.0/`, `img/v1.0/`

| Artifact | Exported as | Kind |
| --- | --- | --- |
| `00-brief.md` | `artifacts/v1.0/00-brief.md` (+ `.html` view) | text |
| `01-fidelity.md` | `artifacts/v1.0/01-fidelity.md` (+ view) | text |
| `02-wireframe.html` | `artifacts/v1.0/02-wireframe.html` | runnable |
| `02-wireframe.png` | `img/v1.0/02-wireframe.png` | capture |
| `03-directions/{a,b,c}.html` | `artifacts/v1.0/03-directions/` | runnable |
| `03-directions/{a,b,c}.png` | `img/v1.0/{a,b,c}.png` | capture |
| `thumbs/{a,b,c}.png` | `img/v1.0/thumb-{a,b,c}.png` | capture |
| `03-direction-decision.md` | `artifacts/v1.0/` (+ view) | text · **gate 1** |
| `04-design-system/tokens.json` | `artifacts/v1.0/04-design-system/` (+ view) | text |
| `04-design-system/components.md` | `artifacts/v1.0/04-design-system/` (+ view) | text |
| `04-design-system/assets-manifest.md` | `artifacts/v1.0/04-design-system/` (+ view) | text |
| `05-implementation.md` | `artifacts/v1.0/` (+ view) | text |
| `06-motion-spec.md` | `artifacts/v1.0/` (+ view) | text |
| `07-uat-report.md` | `artifacts/v1.0/` (+ view) | text · **gate 2** |
| `STATUS.md` | `artifacts/v1.0/` (+ view) | text |
| `screens/07-desktop.png` | `img/v1.0/07-desktop.png` | capture |

### Pass 2 — `artifacts/v1.1/`, `img/v1.1/`

`03-direction-decision.md` (carries the owner's rejection), the three
`04-design-system/` files, `05-implementation.md`, `06-motion-spec.md`,
`07-uat-report.md`, `STATUS.md`, and `screens/07-first-viewport-1905.png` as
`img/v1.1/07-first-viewport.png`.

### Pass 3 — `artifacts/v1.2/`, `img/v1.2/`

`00-owner-directive.md`, `05-implementation.md`, `06-motion-spec.md`,
`07-uat-report.md`, `STATUS.md`, and two captures: the desktop and mobile first
viewports.

### Deliberately not exported

| Left out | Why |
| --- | --- |
| `05-build.html`, `05-build-source.html` | The built page itself. It is already published as this site's own `index.html`; shipping a 283 KB copy of it three times over adds nothing |
| `05-build.py`, `uat.py`, `uat-raw.json` | Machine-local build and verification scripts. Not part of the pack's artifact contract, and made almost entirely of absolute paths |
| Full-page stitched captures | 0.6–1.0 MB each, and the review itself rules them out as evidence — a page is judged on its first screenful |
| `07-nojs`, `07-reduced-motion`, `07-tablet`, `07-vi-*` captures | Verification evidence for checks whose results are already stated in the exported UAT reports |
| `07-load-choreography.webm` | 421 KB video of the load sequence; the three stills it was cut from tell the same story at a tenth the weight |
| `thumbs/wire.png` | Redundant with the exported wireframe capture |

---

## Sanitize ledger

**12 substitutions across 6 files.** Every edit is a redaction. No artifact was improved,
corrected, rescored, or rewritten — including where the original reads awkwardly.

### Rules applied

| ID | Matches | Replaced with | Why |
| --- | --- | --- | --- |
| `P1` | Windows absolute paths under a user directory | `` `<local path>` `` | Exposes the author's machine layout |
| `P2` | The private working-area directory name | `` `<private working area>` `` | Internal orchestration path (no hits after `P1`) |
| `P3` | `file:///` URLs | `<local file>` | Local-only reference (no hits) |
| `P4` | The working area leaking as a *relative* fragment glued in front of the deliverable's real path | the true repo path | `P1` only ate absolute paths, so this one survived the first sweep and was caught at review |
| `N0` | An internal reviewing agent's name, preceded by an article | "the design review" | Internal role name, not a public identity |
| `N1` | The same name, possessive | "the design review's" | as above |
| `N2` | The same name, bare | "the design review" | as above |

### Where the edits landed

| File | Rule | Count |
| --- | --- | --- |
| `artifacts/v1.0/04-design-system/assets-manifest.md` | P1 | 1 |
| `artifacts/v1.0/STATUS.md` | P4 | 1 |
| `artifacts/v1.0/07-uat-report.md` | N0 | 2 |
| `artifacts/v1.1/07-uat-report.md` | N1 | 2 |
| `artifacts/v1.1/STATUS.md` | N1 | 1 |
| `artifacts/v1.2/07-uat-report.md` | N1 | 2 |
| `artifacts/v1.2/STATUS.md` | P1 · N2 | 1 · 2 |

### One derived image

| Derived | From | Transformation | Why |
| --- | --- | --- | --- |
| `img/v1.0/07-first-viewport.png` | `img/v1.0/07-desktop.png` | crop to the top 1440×900, from 1440×3542 | Pass 1's only capture is a full-page stitch. The before/after comparison on the index is about the **first screen** — the frame the rejection was actually about — and comparing a stitched page against a first viewport would be exactly the flattering, apples-to-oranges evidence this run's own review ruled out. The full-page original still ships and is linked beside it |

No other image was altered. The remaining 11 are byte-for-byte copies.

### Kept, deliberately

- **The owner's name and his quote.** Both are already published on the page this run
  produced. Redacting them here while they sit in the site's own copy would be theatre.
- **The public repository and site URLs.** They are public.
- **The wireframe's HTML comments.** They record the structural questions the wireframe was
  posing, which is a large part of why a wireframe is worth reading.
- **Every score, every failure, every unfixed item.** A fixture that edits its own evidence
  is worth nothing.

### Checks that ran before export

- Post-substitution sweep for a forbidden-string list: machine paths and user directory,
  internal project and orchestration names, session identifiers, `file://` and localhost
  URLs, upstream source-repository names, credential shapes (API keys, tokens, private
  keys). **0 hits.**
- Every exported PNG parsed chunk by chunk; only image-critical chunks are present.
  **No `tEXt`, `iTXt`, `eXIf` or other metadata chunks in any of the 11 images.**
- HTML comments and URLs in exported HTML reviewed by hand.

---

## The readable views

Each markdown and JSON artifact ships twice: the raw file (canonical) and a `.html` view
of it beside it. The view is a `<pre>` block with a shared stylesheet — no script.

That is deliberate. The pack's own **rule zero** says content must never be gated on
scripting, and a `fetch()`-based viewer would also be dead the moment somebody opened the
folder from disk instead of over HTTP. A `<pre>` is not elegant; it is legible everywhere,
which is the requirement.

## Re-checking this folder

[`verify.py`](verify.py) re-runs the structural checks: the required artifacts exist for
each pass, every internal link and anchor resolves, no path escapes the folder or assumes
a domain root, every referenced image is present, and the basic accessibility floor holds
(`lang`, one `h1`, `alt` on every image, a `title`). Run it from anywhere:

```
python docs/example/verify.py
```

It exits non-zero on the first failure, so it is safe to wire into a check before release.
