# Static-artifact QA — render, look, fix

Step 7 for an HTML deck, report or microsite that the `static-artifact` lane built, and the
entry point when such a file is edited later. It is the host's `visual-reviewer` slot
for these artifacts; the report format, the hard floor and the six-dimension critique
stay in [uat-report-schema.md](uat-report-schema.md). This file adds the checks and the
rendering method that slide-shaped pages need. Build rules are in
[static-artifact-build.md](static-artifact-build.md).

## The loop

1. **Render** every slide at each size in the list below, one image per slide per size.
   A single thumbnail of the whole deck is not a render.
2. **Look** at each image, not at the source. Source that reads correctly proves nothing
   about what a browser draws.
3. **Judge** against the slide checks below and the hard floor.
4. **Fix** the smallest thing that fixes it. Change only the slide that is wrong; if the
   same geometry is wrong on several slides, fix it where it is shared; do not break the
   classes the theme relies on. One issue, one commit, as the UAT schema requires.
5. **Re-render** that slide at every size the fix touches.

Allow about four rounds per slide as a starting point. When a slide is still wrong after
that, simplify its layout; if it is still wrong, mark the check `unverified` and tell the
user rather than leaving it silently failing.

**Sizes.** Slide-shaped artifacts are checked at the size of the slide, plus the sizes
people actually open them at: 1920×1080, 1280×720, 768×1024, 375×667 and 667×375. Add
1440×900, 1024×768, 414×896 and 896×414 when the deck must be reliable on a wide range
of devices.

## Slide checks

Thresholds marked *start* are starting points to adjust to the deck's own frame, not
accessibility rules.

| Check | What a pass looks like |
| --- | --- |
| Nothing clipped | No slide has content outside its own box; measured, not eyeballed (see below) |
| Clear of the heading | Body content starts under the title with a visible gap; measure against this deck's header, not a constant (*start*: about a fifth of the height) |
| Clear of the foot | Nothing sits on a footer or on the bottom margin (*start*: about 6% of the height) |
| Vertical balance | The main block sits between header and footer; space above and below it is roughly equal (*start*) |
| Same role, same size | Elements that play one role (buttons, cards, nodes on a ring) share dimensions and even spacing; geometry meant to be fixed uses fixed units, not font-relative ones |
| No collisions | No text over an image, an icon, or other text unless the design layers it on purpose |
| Legible | Body text at or above 14px and labels at or above 12px at every size, as in the UAT hard floor |
| Emptiness is intended | Empty areas read as composition. A slide that is deliberately one sentence in a vast field passes; a half-blank slide with no reason for the gap fails (see "Quiet is not bare" in [taste-calibration.md](taste-calibration.md)) |
| Content is there without help | With the entrance observer never firing, and again with reduced motion, no text is hidden (the count of still-hidden reveal elements is 0) |

Also fail the slide on any of these: a circle or card visibly larger than its siblings,
controls crowded to one side, a heading touching the top edge.

## Measure, then look

`overflow: hidden` removes the evidence. After rendering, ask the page itself, per slide:
does the content's scroll height exceed its client height, and does any child's box leave
the slide's box? Both questions are needed. In a column that centres its content, text
that runs past the **top** edge is cut off but does not add to the scroll height, so the
scroll-height test alone passes a slide that has lost its title.

```python
"""Render every .slide at several sizes, measure overflow, close only our own browser.
Usage: python -I render_slides.py deck.html out-dir   (keep it in .tmp/, delete afterwards)"""
import json, pathlib, sys
from playwright.sync_api import sync_playwright

deck, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
SIZES = [(1920, 1080), (1280, 720), (768, 1024), (375, 667), (667, 375)]
MEASURE = """() => [...document.querySelectorAll('.slide')].map((s, i) => ({
  slide: i + 1,
  clipped: s.scrollHeight > s.clientHeight + 1 || s.scrollWidth > s.clientWidth + 1,
  outOfBox: [...s.children].some(c => { const r = c.getBoundingClientRect(), b = s.getBoundingClientRect();
    return r.top < b.top - 1 || r.bottom > b.bottom + 1 || r.left < b.left - 1 || r.right > b.right + 1; }),
  hiddenReveals: [...s.querySelectorAll('.reveal')].filter(e => getComputedStyle(e).opacity === '0').length
}))"""

report = []
with sync_playwright() as p:
    browser = p.chromium.launch()              # a browser process of our own
    try:
        for w, h in SIZES:
            page = browser.new_page(viewport={"width": w, "height": h})
            try:
                page.goto(deck.as_uri())       # file URL, no server needed
                page.wait_for_timeout(1800)    # longer than the entrance failsafe
                for i, el in enumerate(page.query_selector_all(".slide"), 1):
                    el.scroll_into_view_if_needed()
                    page.wait_for_timeout(100)
                    page.screenshot(path=str(out / f"slide{i}-{w}x{h}.png"))
                report.append({"size": f"{w}x{h}", "slides": page.evaluate(MEASURE)})
            finally:
                page.close()
    finally:
        browser.close()                        # ends exactly the process we started
print(json.dumps(report, indent=1))
```

Adapt the `.slide` and `.reveal` selectors to the deck. A `clipped` or `outOfBox` of
`true`, or any `hiddenReveals` above 0, is a finding; the screenshot shows what the user
would see. Run it with the Python that already has Playwright and a Chromium in its
cache; if either is missing, report "blocked" and mark every render check `unverified`
(the `browser` slot in `SKILL.md`). Do not install packages to make the render work.

## Rendering safely

- **Start a browser of your own and close the one you started.** Use the context manager
  and the `finally` close above, so the process ends even when a step fails.
- **Never end a browser by name or sweep every browser process.** That also closes the
  user's own windows and the sessions of other tools. A private browser process per
  checker makes it unnecessary, and it also makes parallel rendering safe.
- **Do not point a bare browser executable at the file** and expect an image: what
  it does depends on whether another instance is already running, and a run that
  writes nothing looks like a pass. A driven browser with its own profile is repeatable.
- Load the page by `file://` URL. If a server is truly needed, follow the serving rules
  in [static-artifact-build.md](static-artifact-build.md).

## Several checkers on a long deck

For a deck of a few dozen slides, split the slides among checkers, each rendering its
range with its own browser process. Each reports findings as the file, slide, size, the
problem and the fix, and **does not edit**. One owner per file then applies the fixes,
so the rule in [ownership-matrix.md](ownership-matrix.md) that two reviewers never edit
in parallel still holds; the checkers only parallelize the looking.

## Close

Record the sizes rendered, the measurement output, and every finding with its fix commit
in `07-uat-report.md`. Any size or branch not rendered is `unverified`, never passed.
