# Brand asset protocol

Step 5, first half. Runs whenever the design will show a real, recognizable brand or
product — the client's own, or any third party named or compared inside the design.

Output: `04-design-system/assets-manifest.md`.

## The premise: assets outrank specifications

A brand is recognized by what people have seen, and the ranking is not close:

| Asset | Recognition value | Required when |
| --- | --- | --- |
| Logo | Highest — one glance is enough | **Always**, for every named brand in the design |
| Product photography / renders | Very high — for physical goods the product *is* the subject | Always, for a physical product |
| Interface screenshots | Very high — for software the interface *is* the subject | Always, for a digital product |
| Color values | Moderate — helpful, but many brands share a blue | Supporting |
| Typefaces | Low on their own | Supporting |
| Tone words | Low; useful for self-checking | Supporting |

The failure this protocol exists to prevent: extracting a color and a font, drawing the
product as a CSS silhouette, and shipping. That output is a generic tech layout with an
accent color. It carries no identity, and it is indistinguishable from the same layout
made for a competitor.

**Two triggers, and the second is the one that gets missed:**
1. Making material *for* a brand.
2. Showing one or more real brands *inside* a design — a comparison, a ranking, a
   review deck, a logo row, a named product in an infographic.

Trigger 2 applies even when you have no brand direction of your own and even when the
direction gate is running. Choosing a visual style and collecting named brands' logos
are parallel tasks, not alternatives.

## Before you start: confirm the thing exists

Never assert a product's existence, release status, version, or specifications from
memory. Search and confirm first. The characteristic failure — deciding a product has
not launched yet and designing an abstract concept piece for something that shipped last
week, with full official press assets available — costs hours and is prevented by
seconds of checking.

Warning signs that you are about to guess: *"I think it's…"*, *"as far as I know…"*,
*"that probably hasn't shipped"*, *"the current version is…"*. Each of those means stop
and verify.

## The five steps

### 1 — Ask, as a list

A vague "do you have brand guidelines?" gets a vague answer. Ask for the specific items:

> For **&lt;brand&gt;**, which of these do you have?
> 1. Logo (SVG or high-resolution PNG) — needed for any brand
> 2. Product photos or official renders — needed for a physical product
> 3. Interface screenshots — needed for a digital product
> 4. Color values (hex / RGB / palette)
> 5. Fonts (display and body)
> 6. Brand guidelines PDF, design-system link, or brand page URL
>
> Send what you have; I will find the rest.

### 2 — Search official channels, by asset type

| Asset | Where to look |
| --- | --- |
| Logo | The brand's `/brand`, `/press`, or press-kit page; a brand subdomain; the inline SVG in the site header |
| Product image | Official product page hero and gallery; press releases; frames from the official launch video |
| Interface screenshot | App-store listing screenshots; the site's screenshots section; official demo video frames |
| Color | Inline CSS or theme config on the official site; the guidelines PDF |
| Fonts | The stylesheet links on the official site; the guidelines |

### 3 — Download, with fallbacks

Do not try one URL and give up. Most official sites render client-side, so a direct
guess at a static asset path usually returns an empty shell rather than a file.

For a **logo**, in descending order of success rate:
1. A public icon/logo aggregator API — highest hit rate for well-known software and
   internet brands, and it returns clean vectors, often with light and dark variants.
2. The official brand or press page asset, downloaded directly.
3. The homepage HTML, with the inline logo SVG node extracted from it.
4. The site's high-resolution favicon — an almost-never-fails fallback that is still the
   real mark.
5. The company's social-profile avatar — last resort.

For **product images**: official product-page hero (usually 2000px+), then the press kit,
then frames pulled from the official launch video, then a public-domain media repository.
Generating an image from an official reference is acceptable only as a labeled
substitute. Hand-drawing the product in CSS or SVG is not.

For **interface screenshots**: store listings, the official screenshots section, demo
video frames, or — if the user has an account — their own capture. Do not assemble one
from a mockup generator.

Verify each download is a real file: check the type, and confirm a supposed SVG actually
begins with an SVG tag rather than an HTML error page.

**Authenticity is not permission.** The orders above rank sources by how likely the asset
is to be the *real* mark. They say nothing about the right to reuse it — an official press
page settles authenticity and may still restrict redistribution, modification, or
commercial use. When reuse rights are unclear, do not embed the asset: use a clearly
marked placeholder in its place, and record the gap in `assets-manifest.md` under
*Missing, and how it is handled*, naming what was found and what is unresolved. This
pack's MIT license covers the pack itself, never third-party brand assets that end up in
an output — those carry whatever terms their owner sets.

### 4 — Quality bar for everything except logos

Logos are pass/fail: if one exists you use it, whatever its quality, because it is the
foundation of recognition. Everything else clears a bar:

> **Search several channels. Gather around ten candidates. Keep two. Each must be an 8
> out of 10 or better — otherwise use none.**

Score on: resolution (≥2000px, more for large-format), rights clarity (official >
public domain > free stock > unclear — unclear scores zero), fit with the brand's
character, consistency of light and composition between the ones you keep, and whether
the image can carry a role on its own rather than decorate.

A mediocre image subtracts. An honest placeholder — a labeled block saying what is
missing — costs the design less than a weak stock photo does.

### 5 — Extract color from the assets, then freeze the spec

Pull hex values from the downloaded SVG, CSS, and HTML; count occurrences; drop pure
black, white, and greys; the top remaining values are candidates.

Two traps:
- **Demo contamination.** A product screenshot often shows *someone else's* brand color
  in the demo content. When two strong colors appear, determine which belongs to the
  product itself.
- **Multiple faces.** A brand's marketing site and its product interface frequently use
  different palettes. Both are genuine. Choose the face that matches this deliverable.

Then write `assets-manifest.md`:

```markdown
# 04 — Assets manifest
Collected: YYYY-MM-DD · Completeness: complete | partial | inferred

## Logos
- <brand> primary: <path> · source: <url> · light/dark variants: yes/no
- (one row per named brand in the design)

## Product images / screenshots
- <name>: <path> · <resolution> · source: <url> · license: <…> · score: <n>/10

## Color candidates (raw — the color protocol decides the final palette)
- <hex> — extracted from <file>, appears <n> times, believed to be <role>

## Fonts
Display: <…> · Body: <…> · Source: <…>

## Off-limits
<colors, treatments, or usages the brand forbids>

## Missing, and how it is handled
<asset> — not found; handled by <ask user | labeled placeholder | generated from
official reference, disclosed to user>
```

Then enforce it structurally: HTML references the manifest's file paths, logos are
`<img>` elements pointing at real files, and CSS custom properties are injected from the
spec so no step can quietly introduce a near-miss color. Brand consistency should hold
because of the structure, not because everyone remembered.

## Self-check before leaving Step 5's first half

- [ ] Every brand name appearing in the design has its logo collected.
- [ ] A physical product has a real product image; a digital product has a real screenshot.
- [ ] No product is drawn as a CSS or SVG silhouette.
- [ ] Colors came from real assets, not from memory.
- [ ] Anything missing is disclosed to the user rather than papered over.
- [ ] If the deliverable is a single double-clickable file, images and logos are embedded
      as data URIs — relative paths break the moment the file is moved or emailed, and a
      row of broken images is the most visible possible failure.

**If a logo cannot be found: stop and ask.** Do not proceed with a generic substitute.
The thirty minutes this protocol costs is the cheapest insurance in the process.
