"""Verify the motion route and recipe contract without runtime dependencies."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path


FIELDS = (
    "intent", "surface", "trigger", "reject_if", "mode", "minimum_tool",
    "fallback", "reduced_motion", "verification",
)
REFERENCE = "references/motion-patterns.md"
TEMPLATE = "templates/06-motion-spec.md"
DEMOS = ("templates/static-motion-demo.html", "templates/react-motion-demo.tsx")
ACCEPTED_COLUMNS = (
    "Hypothesis", "Four gate verdicts", "What user understands or does better",
    "Recipe ID", "Purpose", "Frequency", "Tool", "Properties",
    "Curve/duration/spring", "Token or exact value",
    "Reference URL / observation → implementation", "No-motion fallback",
    "Reduced motion", "QA evidence",
)


def verify(root: Path) -> list[str]:
    skill_dir = root / "skills" / "design-routing"
    errors: list[str] = []
    router = skill_dir / "SKILL.md"
    if not router.is_file():
        return ["missing router: skills/design-routing/SKILL.md"]
    route_text = router.read_text(encoding="utf-8")
    for relative in (REFERENCE, TEMPLATE, *DEMOS):
        target = skill_dir / relative
        if not target.is_file():
            errors.append(f"missing target: {relative}")
        if relative not in route_text:
            errors.append(f"missing router route: {relative}")
    catalog = skill_dir / REFERENCE
    if not catalog.is_file():
        return errors

    text = catalog.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## (MP\d{2}) — .+$", text, re.MULTILINE))
    all_sections = list(re.finditer(r"^## .+$", text, re.MULTILINE))
    if not 6 <= len(headings) <= 8:
        errors.append(f"recipe count must be 6–8, found {len(headings)}")
    ids = [match.group(1) for match in headings]
    if len(ids) != len(set(ids)):
        errors.append("duplicate recipe ID")
    for index, match in enumerate(headings):
        end = next((section.start() for section in all_sections if section.start() > match.start()), len(text))
        block = text[match.end():end]
        for field in FIELDS:
            found = re.search(rf"^- {re.escape(field)}:[ \t]*(.*)$", block, re.MULTILINE)
            if not found:
                errors.append(f"{match.group(1)} missing field: {field}")
            elif not found.group(1).strip():
                errors.append(f"{match.group(1)} empty field: {field}")
    spec = skill_dir / TEMPLATE
    if spec.is_file():
        spec_text = spec.read_text(encoding="utf-8")
        for marker in (
            "Tokens used / added", "## Accepted", "## Refused", "## Zero motion",
            "## Needs a feel check", "## Dependency decision",
        ):
            if marker not in spec_text:
                errors.append(f"motion spec missing: {marker}")
        accepted = re.search(r"^## Accepted[ \t]*$([\s\S]*?)(?=^## |\Z)", spec_text, re.MULTILINE)
        if not accepted:
            errors.append("motion spec missing Accepted section")
        else:
            table = re.search(r"^\|([^\n]+)\|\s*$", accepted.group(1), re.MULTILINE)
            columns = [part.strip() for part in table.group(1).split("|")] if table else []
            for column in ACCEPTED_COLUMNS:
                if column not in columns:
                    errors.append(f"accepted table missing column: {column}")
    return errors


def self_test(root: Path) -> list[str]:
    """Mutate disposable copies, never source files, to prove negative cases."""
    errors = verify(root)
    if errors:
        return ["valid fixture failed before mutation: " + "; ".join(errors)]
    source = root / "skills" / "design-routing"
    with tempfile.TemporaryDirectory(prefix="motion-pack-") as temp:
        target = Path(temp) / "skills" / "design-routing"
        for relative in ("SKILL.md", REFERENCE, TEMPLATE, *DEMOS):
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((source / relative).read_bytes())

        def expect(label: str, change, needle: str) -> None:
            path, original, altered = change
            path.write_text(altered, encoding="utf-8")
            result = verify(Path(temp))
            if not any(needle in item for item in result):
                errors.append(f"negative test {label} did not fail as expected: {result}")
            path.write_text(original, encoding="utf-8")

        router = target / "SKILL.md"
        catalog = target / REFERENCE
        spec = target / TEMPLATE
        router_text = router.read_text(encoding="utf-8")
        catalog_text = catalog.read_text(encoding="utf-8")
        spec_text = spec.read_text(encoding="utf-8")
        expect("wrong route", (router, router_text, router_text.replace(REFERENCE, "references/other.md")), "missing router route")
        expect("renamed template", (router, router_text, router_text.replace(TEMPLATE, "templates/other.md")), "missing router route")
        spec.rename(target / "templates" / "other.md")
        if not any("missing target: " + TEMPLATE in item for item in verify(Path(temp))):
            errors.append("negative test missing template did not fail")
        (target / "templates" / "other.md").rename(spec)
        first = re.search(r"^- intent: .+$", catalog_text, re.MULTILINE)
        if first:
            expect("empty field", (catalog, catalog_text, catalog_text[:first.start()] + "- intent: " + catalog_text[first.end():]), "empty field: intent")
            expect("missing field", (catalog, catalog_text, catalog_text[:first.start()] + catalog_text[first.end():]), "missing field: intent")
            next_heading = re.search(r"^## MP\d{2} — .+$", catalog_text[first.end():], re.MULTILINE)
            if next_heading:
                position = first.end() + next_heading.start()
                unrelated = catalog_text[:first.start()] + catalog_text[first.end():position] + "## Unrelated section\n\n- intent: misplaced\n\n" + catalog_text[position:]
                expect("field in unrelated section", (catalog, catalog_text, unrelated), "missing field: intent")
        else:
            errors.append("negative tests cannot locate intent field")
        first_heading = re.search(r"^## MP\d{2} — .+$", catalog_text, re.MULTILINE)
        second_heading = re.search(r"^## MP\d{2} — .+$", catalog_text[first_heading.end():], re.MULTILINE) if first_heading else None
        if first_heading and second_heading:
            start = first_heading.end() + second_heading.start()
            changed = catalog_text[:start] + catalog_text[start:].replace(second_heading.group(0)[:7], first_heading.group(0)[:7], 1)
            expect("duplicate ID", (catalog, catalog_text, changed), "duplicate recipe ID")
        else:
            errors.append("negative tests cannot locate two recipe headings")
        if spec_text == "":
            errors.append("spec template unexpectedly empty")
        for column in ACCEPTED_COLUMNS:
            changed = spec_text.replace("| " + column + " |", "| Renamed " + column + " |", 1)
            if changed == spec_text:
                errors.append(f"negative test cannot locate accepted column: {column}")
            else:
                expect("accepted column " + column, (spec, spec_text, changed), "accepted table missing column: " + column)
        changed = spec_text.replace("| Purpose |", "| Renamed Purpose |", 1) + "\n## Other\n\nPurpose\n"
        expect("marker outside accepted", (spec, spec_text, changed), "accepted table missing column: Purpose")
        changed = spec_text.replace("## Accepted", "## Accepted items", 1)
        expect("renamed Accepted section", (spec, spec_text, changed), "missing Accepted section")
        changed = spec_text.replace("## Accepted", "## Removed", 1)
        expect("missing Accepted section", (spec, spec_text, changed), "missing Accepted section")
        changed = spec_text.replace("## Accepted", "## Accepted items", 1)
        for column in ACCEPTED_COLUMNS:
            changed = changed.replace("| " + column + " |", "| Changed " + column + " |", 1)
        expect("renamed section and columns", (spec, spec_text, changed), "missing Accepted section")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    errors = self_test(args.root) if args.self_test else verify(args.root)
    for error in errors:
        print("FAIL", error)
    if errors:
        return 1
    print("motion pack verified" + ("; negative fixtures passed" if args.self_test else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
