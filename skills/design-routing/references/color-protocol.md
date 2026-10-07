# Color protocol

Step 5, second half of a new UI build. Derive a **palette candidate** after the brand
asset protocol and before any component is styled. Existing-product token values
remain as-is unless the owner approves a change; an extract/audit does not run this
protocol to rewrite its colors.

Output: a palette candidate with one written justification sentence per key color,
source and intended role, passed to `agent-design-studio:design-system` `create/extend`.
That skill declares the canonical token source and any delta. The run may retain a
legacy `04-design-system/tokens.json` map for existing examples, but it is not
DTCG data or a second canonical source.

## The rule

> **Never invent a color.** Every hue in the design traces back to a real asset, real
> content, or a defensible cultural reference — and you can say which, in one sentence.

A color chosen "because it feels right for this kind of product" is a draw from a
statistical prior. The prior is shared by every model and every default template, which
is why so many pages look related to each other and to nothing in particular.

## Three steps: sample, converge, justify

### 1 — Sample

Take the primary hue from one of exactly three sources:

| Source | Use it when | How |
| --- | --- | --- |
| **Brand assets** | A brand exists | Sample directly from the logo, guidelines, or official site |
| **Real content imagery** | The design carries real photos, screenshots, or artwork | Sample the dominant color of the images that will actually appear |
| **Cultural context of the subject** | Neither of the above; the subject has its own color memory | Derive from the subject's own world, deliberately, then justify it |

The third is the interesting one, and it needs specificity to be worth anything. "Red"
is not a decision. A muted, orange-leaning, slightly greyed red reads as traditional and
ceremonial; a fully saturated primary red reads as retail and urgency. Same hue family,
opposite meanings — the difference is chroma and lightness, not the name.

The same split applies everywhere: an indigo-leaning, low-chroma blue reads handmade and
quiet, while the familiar bright screen-blue reads as generic software efficiency. A
yellow-leaning, desaturated green reads natural; a fluorescent green reads terminal. A
warm off-white reads editorial; pure white reads laboratory. **A two-percent shift in the
background's warmth is the entire difference in character.**

If you find yourself reaching for the bright screen-blue, treat it as a signal that you
sampled nothing and are drawing from the prior.

### 2 — Converge

Compress to **two or three chromatic hues plus one neutral ramp**. More than that is not
a palette; it is a collection.

Work in a perceptually uniform color space (`oklch()` in CSS). Its lightness channel is
perceptually even, so a lightness ladder written down *is* the hierarchy system, and
adjusting lightness will not drift the hue the way older models do.

**Neutral ramp** — five steps is usually enough:

```
L 0.15   ink / strongest text
L 0.35   secondary text, strong borders
L 0.65   muted text, dividers, disabled
L 0.92   surfaces, subtle fills
L 0.98   page background
```

**Separation between chromatic hues:** at least **60° of hue** apart, *or* a lightness
difference of **≥0.3**. Two colors closer than that will not read as two roles; they
read as one color rendered inconsistently.

**Chroma by surface area** — the table that separates a printed-feeling palette from a
fluorescent one:

| Where the color is used | oklch chroma | Reads as |
| --- | --- | --- |
| Large background areas | 0.01 – 0.04 | Paper. Restful over long reading |
| Brand color, headings, emphasis | 0.08 – 0.15 | Ink. Present without being plastic |
| Small accents — buttons, links, badges | 0.15 – 0.22 | Alive, and only because the area is small |
| Above 0.25 across a full screen | avoid | Screen-fluorescent; defensible only for a deliberately electric register |

The reason low chroma reads as expensive: ink on paper physically cannot reach a screen's
maximum saturation — a narrower gamut, absorbent paper, and ambient light all mute it.
Decades of print have trained the eye to associate that muting with quality. Lowering
chroma on screen borrows that memory.

### 3 — Justify

Write **one sentence** per key color in the handoff. If the chosen canonical token
source is DTCG JSON, the Design System skill can place the rationale in
`$description` or `$extensions`; JSON has no comments:

> "Primary sampled from the ochre in the client's logo, chroma lowered to 0.09 so large
> fills read as ink rather than plastic."

> **If you cannot write that sentence, you copied a formula.** Go back to step 1.

This is a gate, not a ritual. It is the cheapest available detector of a palette that
came from nowhere.

## Legacy example of a palette candidate

The JSON below illustrates the previous `_why` map shape used by older runs. Its
CSS color strings and `_why` entries are **not** valid `$value` tokens in the
supported DTCG subset. New systems follow the Design System skill's
`references/token-contract.md`; do not relabel this map as DTCG or copy it into a
new canonical `tokens.json`.

```json
{
  "color": {
    "neutral": { "900": "oklch(0.15 0.01 60)", "700": "oklch(0.35 0.01 60)",
                 "500": "oklch(0.65 0.01 60)", "200": "oklch(0.92 0.008 60)",
                 "50":  "oklch(0.98 0.006 60)" },
    "brand":   { "base": "oklch(0.52 0.09 55)", "_why": "sampled from logo ochre" },
    "accent":  { "base": "oklch(0.62 0.17 250)", "_why": "60° from brand; small areas only" },
    "semantic":{ "danger": "…", "success": "…", "warning": "…" }
  }
}
```

Give the neutral ramp a slight chroma in the same hue family as the brand rather than
pure grey — neutrals that share the brand's temperature make the whole palette read as
one system. Keep it under 0.02.

## Hard floors, checked here and again at review

- Body text contrast ≥ **4.5:1** against its actual background. Check the computed
  colors on each distinct surface, especially text that may be inheriting the body color
  inside a dark or tinted region.
- Body ≥ **14px**, labels and captions ≥ **12px**. No exception for a "quiet" or
  "luxurious" direction — this is the failure mode where a restrained design becomes an
  unreadable one.
- Never carry meaning by color alone. Pair it with text, an icon, or a shape.
- Dark and light variants are defined together, not retrofitted.

## Common mistakes

- Copying the example hex from a style reference. Those are anchors, not recipes; the
  same style applied to different content should produce different values.
- A palette with five chromatic hues and no ramp.
- A neutral ramp of pure greys next to a warm brand color — the greys read as dirty.
- Full-bleed high-chroma backgrounds because they looked energetic in a small preview.
- Adjusting lightness in a non-uniform color space and quietly shifting the hue.
