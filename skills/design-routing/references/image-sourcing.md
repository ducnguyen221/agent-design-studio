# Image sourcing

Step 5, second half of the asset work. The brand asset protocol covers the marks and
material of named brands; this file covers everything else the design shows — the subject
itself. Both feed `04-design-system/assets-manifest.md`.

## The checkpoint

Before any design work, answer one question in writing:

> **Are images content here, or are they decoration?**

A design about something that exists in the world — a place, an animal, a person, a
building, an object, a period, a physical product — needs them, almost without exception.
A design about a tool, a dataset, a process, or an argument often needs none; decide that
deliberately and say so. **When you cannot tell, treat them as content.** An unused real
image costs an hour; a missing one costs the design.

**Timing, and it is the part that gets missed.** Answer at Step 2 with the fidelity call.
Gather **before Step 4**, because all three directions consume the same real content —
swapping imagery between them turns the gate into a comparison of photographs instead of
a comparison of designs. Step 5 closes the manifest; it is not where sourcing starts.

## The removal test

> **Remove this image. Is any information lost?**

Nothing lost means decorative stock, and decorative stock is the most reliable tell of
machine-made work. Cut it, and solve the empty space with composition.

The test cuts the other way too. When an image *is* content, it is never substituted with
a color block, a gradient, or a hand-drawn SVG. A page about a bridge containing no
photograph of the bridge has failed, whatever its typography is doing — and a labeled
placeholder (*"photograph of the west span, to be supplied"*) costs less than a bad
substitute or a stock photo of a different bridge.

## Where to look, by need

These are **places that kind of material tends to live**, not sources that are safe by
default. Rights attach to the item, never to the site holding it: one archive routinely
shelves public-domain scans beside items still under copyright.

| What you need | Where it tends to live | Read before using |
| --- | --- | --- |
| The subject's own material — the client's photos, an organization's press page, the author's own images | Ask first, always. Best fit, and rights are usually one message away | Whether it may be published, and under whose name |
| Historical, scientific, artistic, natural-history subjects; vintage illustration and engraving | Open-collection archives — an encyclopedic media commons (Wikimedia Commons), museum open-access programmes, digitized natural-history scan libraries | The item's own licence line. "Public domain" is a claim about one item, and it varies by country |
| Everyday scenes, generic photography, textures | Permissive photo libraries (Unsplash, Pexels and their kind) | Their terms have changed more than once and differ per platform, sometimes per photo. Read them as you download; record which version |
| A named product or company mark | Icon databases and official brand pages — the brand asset protocol owns this row | The trademark warning below |

Search in the source's own language, with proper nouns spelled as that source spells
them: an archive of nineteenth-century plates indexes them under the illustrator, not
under the animal.

### Trademark is a separate question from copyright

**Being able to download a mark is not permission to use it.** A press page exists so
journalists can illustrate coverage; it licenses neither commercial use, nor a comparison
implying a ranking, nor anything that could read as endorsement — and most brand
guidelines forbid recoloring, distorting or reconstructing the mark, which are the exact
edits a design is tempted to make. Record the intended use beside the asset and say
plainly at handoff that clearance is the user's call. We record; we do not rule.

## Per-asset provenance

Every image entering the deliverable carries five fields — same manifest the brand asset
protocol defines, one more section:

```markdown
## Subject imagery
- <short name> — <path in the run folder>
  licence: <exact name and version>     e.g. CC BY-SA 4.0 · Public domain (US, pre-1930)
  source:  <the item's own page URL>    not a search result, not the raw file URL
  author:  <creator, spelled as the licence requires>
  retrieved: YYYY-MM-DD
  transformations: <none | resized to 1600px | cropped to 3:2 | background removed>
```

"Free", "royalty-free" and "open" are not licences. A raw file URL carries no terms, so
the item page is the only link a reviewer can check. Attribution licences are void
without the author's name, and some restrict derivatives — which is why the shipped
file's edits are declared rather than guessed at.

**A field you cannot fill means the asset is not cleared.** Unclear rights are never
resolved by embedding and hoping: use a clearly marked placeholder, and record what was
found and what is unresolved under *Missing, and how it is handled*.

## When nothing suitable turns up

Not finding an image is a **degradation, not a stop**. Re-phrase the search — another
language, the subject's formal name, the creator's name rather than the subject's. Then
try another category above. Then generate one, only where the user has confirmed that
capability and only labeled in the manifest as generated rather than photographed.
Failing all of that, ship a labeled placeholder and say in one sentence at handoff which
images are standing in.

The one exception belongs to the other protocol: a **named brand's logo that cannot be
found is a stop**.

## Embedding: data URIs are an option, not a rule

Embed when the deliverable is a single file that must survive being emailed, moved, or
double-clicked out of a download folder — a row of broken images is the most visible
failure a deliverable has. Use relative paths for anything served from a folder, a site,
or a repo: smaller HTML, images cached separately, editable afterwards.

Embedding costs real things. Base64 inflates a file by roughly a third, nothing caches
independently so one edit re-sends every byte, and a 6 MB page taking four seconds to
show anything has traded one visible failure for another.

**Decide per asset, not per project.** Small marks are cheap to embed and expensive to
lose — which is why the brand asset protocol requires it for logos in a single-file
deliverable. Full-bleed photographs are the opposite trade, and a mixed answer, stated in
the manifest, is frequently the correct one.

## Self-check before leaving the asset work

- [ ] The checkpoint question is answered in the run folder, not held in your head.
- [ ] Every content-essential image is real, and the same set feeds all three directions.
- [ ] Every image has all five provenance fields filled — no "free", no "internet".
- [ ] Every image has passed the removal test.
- [ ] No content-essential subject is drawn in CSS or SVG.
- [ ] Any trademarked mark carries its intended use, flagged for the user.
- [ ] Anything unresolved is a labeled placeholder plus a manifest line, said out loud at
      handoff rather than left to be discovered.
