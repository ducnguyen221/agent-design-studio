#!/usr/bin/env python3
"""
Structural check for docs/example/ — the published example run.

Guards the things that rot silently when somebody edits this folder later:
required artifacts vanish, a link goes stale, a path picks up a leading slash and
breaks under the Pages project subpath, an image is renamed, an `alt` is dropped.

    python docs/example/verify.py

Exits 0 when everything holds, 1 on the first category that fails. Stdlib only.
"""
from __future__ import annotations

import html.parser
import pathlib
import re
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
DOCS = HERE.parent

# The published location. A reference starting with "/" resolves to the domain root
# and therefore breaks on a project Pages site served from this subpath.
PAGES_SUBPATH = "/agent-design-studio/example/"

# ---- what the fixture promises to contain ---------------------------------------
REQUIRED = {
    "v1.0": [
        "00-brief.md", "01-fidelity.md", "02-wireframe.html",
        "03-direction-decision.md", "03-directions/a.html", "03-directions/b.html",
        "03-directions/c.html", "04-design-system/tokens.json",
        "04-design-system/components.md", "04-design-system/assets-manifest.md",
        "05-implementation.md", "06-motion-spec.md", "07-uat-report.md", "STATUS.md",
    ],
    "v1.1": [
        "03-direction-decision.md", "04-design-system/tokens.json",
        "04-design-system/components.md", "04-design-system/assets-manifest.md",
        "05-implementation.md", "06-motion-spec.md", "07-uat-report.md", "STATUS.md",
    ],
    "v1.2": [
        "00-owner-directive.md", "05-implementation.md", "06-motion-spec.md",
        "07-uat-report.md", "STATUS.md",
    ],
}
TOP_LEVEL = ["index.html", "ABOUT.md", "artifact.css", "verify.py"]


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []   # (attr-kind, value)
        self.ids: set[str] = set()
        self.imgs_without_alt: list[str] = []
        self.h1 = 0
        self.title = ""
        self.lang = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if a.get("name") and tag == "a":
            self.ids.add(a["name"])
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1 += 1
        elif tag == "a" and a.get("href"):
            self.refs.append(("href", a["href"]))
        elif tag == "img":
            if a.get("src"):
                self.refs.append(("src", a["src"]))
            if not (a.get("alt") or "").strip():
                self.imgs_without_alt.append(a.get("src", "<no src>"))
        elif tag == "link" and a.get("href"):
            self.refs.append(("href", a["href"]))
        elif tag == "script" and a.get("src"):
            self.refs.append(("src", a["src"]))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def rel(p: pathlib.Path) -> str:
    try:
        return p.relative_to(DOCS).as_posix()
    except ValueError:
        return str(p)


def main() -> int:
    fails: list[str] = []
    notes: list[str] = []

    # ---- 1. required artifacts ---------------------------------------------------
    for name in TOP_LEVEL:
        if not (HERE / name).is_file():
            fails.append(f"missing top-level file: {name}")
    for ver, files in REQUIRED.items():
        for f in files:
            src = HERE / "artifacts" / ver / f
            if not src.is_file():
                fails.append(f"missing artifact: artifacts/{ver}/{f}")
                continue
            # every markdown/json artifact must also have its readable view
            if src.suffix in {".md", ".json"}:
                view = src.with_suffix(src.suffix + ".html")
                if not view.is_file():
                    fails.append(f"missing readable view: {rel(view)}")
    notes.append(f"required artifacts: {sum(len(v) for v in REQUIRED.values())} checked")

    # ---- 2. links, anchors, images, path shape -----------------------------------
    pages = sorted(HERE.rglob("*.html"))
    parsed: dict[pathlib.Path, Page] = {}
    for page in pages:
        p = Page()
        p.feed(page.read_text(encoding="utf-8", errors="replace"))
        parsed[page] = p

    n_refs = 0
    dangling_in_fixture_artifacts = 0
    for page, p in parsed.items():
        # An exported artifact is a historical record and is never edited to satisfy
        # this script. Its files must exist and must be safe; its own in-page anchors
        # are whatever they were on the day. The three direction renders, for one,
        # carry nav links to sections a first-screenful render never contained.
        is_artifact = (HERE / "artifacts") in page.parents
        for kind, raw in p.refs:
            if raw.startswith(("http://", "https://", "mailto:", "data:", "tel:")):
                continue
            n_refs += 1
            if raw.startswith("//"):
                fails.append(f"{rel(page)}: protocol-relative reference {raw!r}")
                continue
            if raw.startswith("/"):
                fails.append(
                    f"{rel(page)}: root-absolute reference {raw!r} — breaks under "
                    f"{PAGES_SUBPATH}")
                continue
            if raw.startswith("#"):
                if raw[1:] and raw[1:] not in p.ids:
                    if is_artifact:
                        dangling_in_fixture_artifacts += 1
                    else:
                        fails.append(
                            f"{rel(page)}: anchor {raw!r} has no target on the page")
                continue
            path_part, _, frag = raw.partition("#")
            path_part = urllib.parse.unquote(path_part.split("?")[0])
            if not path_part:
                continue
            target = (page.parent / path_part).resolve()
            if not target.exists():
                fails.append(f"{rel(page)}: dead {kind} {raw!r}")
                continue
            if DOCS not in target.parents and target != DOCS:
                fails.append(
                    f"{rel(page)}: reference {raw!r} escapes docs/ -> {target}")
                continue
            if frag and target.suffix == ".html":
                tp = parsed.get(target)
                if tp is None:
                    tp = Page()
                    tp.feed(target.read_text(encoding="utf-8", errors="replace"))
                    parsed[target] = tp
                if frag not in tp.ids:
                    fails.append(f"{rel(page)}: anchor #{frag} missing in {rel(target)}")
    notes.append(f"internal references: {n_refs} resolved across {len(pages)} pages")
    if dangling_in_fixture_artifacts:
        notes.append(
            f"in-page anchors dangling inside exported artifacts: "
            f"{dangling_in_fixture_artifacts} — expected, not edited "
            f"(the artifacts are a frozen record)")

    # ---- 3. every image on disk is referenced, every reference exists -------------
    on_disk = {q.resolve() for q in (HERE / "img").rglob("*.png")}
    referenced = set()
    for page, p in parsed.items():
        for kind, raw in p.refs:
            if raw.startswith(("http", "data:", "#")):
                continue
            t = (page.parent / urllib.parse.unquote(raw.split("#")[0].split("?")[0]))
            if t.suffix.lower() == ".png":
                referenced.add(t.resolve())
    orphans = on_disk - referenced
    if orphans:
        fails.append(
            "images present but never referenced: "
            + ", ".join(sorted(rel(o) for o in orphans)))
    else:
        notes.append(f"images: {len(on_disk)} on disk, all referenced")

    # ---- 3b. links inside ABOUT.md (the provenance note ships with links) --------
    about = (HERE / "ABOUT.md")
    if about.is_file():
        n_md = 0
        for m in re.finditer(r"\]\(([^)#][^)]*)\)", about.read_text(encoding="utf-8")):
            href = m.group(1).strip()
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            n_md += 1
            if not (HERE / urllib.parse.unquote(href.split("#")[0])).exists():
                fails.append(f"ABOUT.md: dead link {href!r}")
        notes.append(f"ABOUT.md: {n_md} local links resolve")

    # ---- 4. accessibility floor ---------------------------------------------------
    for page, p in parsed.items():
        if not p.lang:
            fails.append(f"{rel(page)}: <html> has no lang attribute")
        if not p.title.strip():
            fails.append(f"{rel(page)}: empty or missing <title>")
        if p.h1 != 1:
            fails.append(f"{rel(page)}: expected exactly one <h1>, found {p.h1}")
        for src in p.imgs_without_alt:
            fails.append(f"{rel(page)}: <img src={src!r}> has no alt text")
    notes.append(f"a11y floor: lang / title / single h1 / img alt over {len(pages)} pages")

    # ---- 5. no machine paths crept back in ---------------------------------------
    # Matches real occurrences, not mentions: ABOUT.md documents the shapes it redacts
    # ("file:///", "localhost"), so each pattern requires what would follow in an
    # actual path or URL rather than the bare token.
    leak = re.compile(
        r"[A-Za-z]:\\Users\\[A-Za-z0-9]"
        r"|/c/Users/[A-Za-z0-9]"
        r"|/home/[a-z0-9]+/"
        r"|file:///[A-Za-z0-9]"
        r"|localhost[:/]"
        r"|127\.0\.0\.1[:/]",
        re.IGNORECASE)
    scanned = 0
    for f in list(HERE.rglob("*.html")) + list(HERE.rglob("*.md")) \
            + list(HERE.rglob("*.json")) + list(HERE.rglob("*.css")):
        scanned += 1
        for m in leak.finditer(f.read_text(encoding="utf-8", errors="replace")):
            fails.append(f"{rel(f)}: machine-local string {m.group(0)!r}")
    notes.append(f"leak scan: {scanned} text files clean")

    # ---- report -------------------------------------------------------------------
    for n in notes:
        print(f"  ok   {n}")
    if fails:
        print(f"\nFAILED — {len(fails)} problem(s):", file=sys.stderr)
        for f in fails:
            print(f"   {f}", file=sys.stderr)
        return 1
    print("\nexample fixture verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
