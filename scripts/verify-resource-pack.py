"""Validate and query the local UI/UX source catalog; never fetch source URLs."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


SKILL = Path("skills/design-routing")
CATALOG = SKILL / "resources/uiux-catalog.json"
INDEX = SKILL / "references/resource-index.md"
ROUTER = SKILL / "SKILL.md"
DISTILL = SKILL / "references/reference-distill.md"
DISTILL_TEMPLATE = SKILL / "templates/reference-design.md"
REQUIRED = {
    "id", "card", "slot", "original_label", "original_url", "canonical_label",
    "canonical_url", "aliases", "category", "use_cases", "source_role",
    "authority", "access_status", "checked_at", "evidence_url", "evidence", "license_status",
    "license_url", "allowed_use_scope", "planned_use", "redistribution_status",
    "cost_access_note", "stack", "decision", "target_reference", "confidence",
    "limitations", "summary", "search_terms", "search_hint", "follow_up",
}
PRIVATE = re.compile(r"(?i)(?:[a-z]:[/\\]users[/\\]|/users/[^/]+/|/home/[^/]+/|onedrive|desktop[/\\]|brain[/\\]|\.opcos[/\\]|\.secret[/\\])")
ID = re.compile(r"\b(?:0[1-9]|[1-6][0-9]|7[0-5])\b")


def _read(root: Path, relative: Path, errors: list[str]) -> str | None:
    target = root / relative
    try:
        if not target.resolve().is_relative_to(root.resolve()):
            errors.append(f"path escapes root: {relative.as_posix()}")
            return None
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read {relative.as_posix()}: {exc.__class__.__name__}")
        return None


def _web_url(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port  # Accessing this rejects nonnumeric and out-of-range ports.
        if parsed.scheme not in {"http", "https"} or host is None or parsed.username is not None or parsed.password is not None:
            return False
        if port is not None and port < 1:
            return False
        if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in host):
            return False
        if ":" in host:
            ipaddress.IPv6Address(host)
            return True
        ascii_host = host.encode("idna").decode("ascii").rstrip(".")
        return bool(ascii_host) and len(ascii_host) <= 253 and all(
            re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
            for label in ascii_host.split(".")
        )
    except (ValueError, UnicodeError):
        return False


def _iso_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
        return parsed.isoformat() == value and parsed <= date.today()
    except ValueError:
        return False


def _records(root: Path, errors: list[str]) -> list[dict] | None:
    raw = _read(root, CATALOG, errors)
    if raw is None:
        return None
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"invalid catalog JSON: {exc.msg}")
        return None
    if not isinstance(document, dict) or not isinstance(document.get("sources"), list):
        errors.append("catalog must contain sources array")
        return None
    if document.get("schema_version") != "1":
        errors.append("catalog schema_version must be 1")
    return document["sources"]


def verify(root: Path) -> list[str]:
    """Return all local catalog, routing, provenance and rights errors."""
    errors: list[str] = []
    records = _records(root, errors)
    if records is None:
        return errors
    if len(records) != 75:
        errors.append(f"source count must be 75, found {len(records)}")
    seen: set[str] = set()
    pairs: set[tuple[int, int]] = set()
    for position, row in enumerate(records, 1):
        if not isinstance(row, dict):
            errors.append(f"source {position} is not an object")
            continue
        label = str(row.get("id", position))
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(sorted(missing))}")
        identifier = row.get("id")
        if not isinstance(identifier, str) or identifier != f"{position:02d}":
            errors.append(f"{label}: ID/order must be {position:02d}")
        if isinstance(identifier, str) and identifier in seen:
            errors.append(f"{label}: duplicate ID")
        if isinstance(identifier, str):
            seen.add(identifier)
        card, slot = row.get("card"), row.get("slot")
        expected = ((position - 1) // 3 + 1, (position - 1) % 3 + 1)
        if type(card) is not int or type(slot) is not int or (card, slot) != expected:
            errors.append(f"{label}: card/slot must be {expected}")
        if type(card) is int and type(slot) is int and (card, slot) in pairs:
            errors.append(f"{label}: duplicate card/slot")
        if type(card) is int and type(slot) is int:
            pairs.add((card, slot))
        for field in ("original_label", "canonical_label", "category", "source_role", "authority", "access_status", "checked_at", "license_status", "allowed_use_scope", "redistribution_status", "cost_access_note", "decision", "confidence", "limitations", "summary", "search_hint"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{label}: empty {field}")
        if not _iso_date(row.get("checked_at")):
            errors.append(f"{label}: invalid checked_at date")
        if not isinstance(row.get("license_status"), str) or row["license_status"] not in {"verified_scope_limited", "unverified_per_item", "not_applicable_reference_or_tool"}:
            errors.append(f"{label}: invalid license_status")
        if type(row.get("license_verified")) is not bool or row.get("license_verified") != (row.get("license_status") == "verified_scope_limited"):
            errors.append(f"{label}: license_verified conflicts with status")
        for field in ("original_url", "canonical_url", "evidence_url"):
            if not _web_url(row.get(field)):
                errors.append(f"{label}: invalid {field}")
        if row.get("license_url") not in ("unknown", "not_applicable") and not _web_url(row.get("license_url")):
            errors.append(f"{label}: license_url needs URL or explicit unknown/not_applicable")
        for field in ("aliases", "use_cases", "stack", "search_terms", "evidence"):
            if not isinstance(row.get(field), list):
                errors.append(f"{label}: {field} must be an array")
            elif field != "evidence" and not all(isinstance(item, str) and item.strip() for item in row[field]):
                errors.append(f"{label}: {field} must contain nonempty strings")
        if not row.get("use_cases"):
            errors.append(f"{label}: use_cases cannot be empty")
        if not row.get("evidence"):
            errors.append(f"{label}: evidence cannot be empty")
        if row.get("planned_use") != "link_only":
            errors.append(f"{label}: planned_use must be link_only")
        if not isinstance(row.get("redistribution_status"), str) or row["redistribution_status"] not in {"allowed", "restricted", "unknown"}:
            errors.append(f"{label}: invalid redistribution_status")
        if row.get("target_reference") != "catalog_only":
            target = row.get("target_reference")
            if not isinstance(target, str) or not target.startswith("references/") or ".." in Path(target).parts:
                errors.append(f"{label}: invalid target_reference")
            else:
                try:
                    if not (root / SKILL / target).is_file():
                        errors.append(f"{label}: missing target_reference {target}")
                except (OSError, ValueError):
                    errors.append(f"{label}: invalid target_reference")
        follow = row.get("follow_up")
        if not isinstance(follow, dict) or follow.get("status") != "pending" or not isinstance(follow.get("candidates"), list) or not follow.get("candidates") or not all(isinstance(item, str) and item in {"docs_or_markdown", "skill_or_recipe", "layout_or_demo"} for item in follow.get("candidates", [])) or not isinstance(follow.get("note"), str) or not follow["note"].strip():
            errors.append(f"{label}: follow_up must be pending with candidates array")
        for evidence in row.get("evidence", []) if isinstance(row.get("evidence"), list) else []:
            if not isinstance(evidence, dict) or not isinstance(evidence.get("status"), str) or evidence["status"] not in {"identity_verified", "content_reviewed", "demo_observed", "runtime_tested", "access_failed", "unverified"}:
                errors.append(f"{label}: invalid evidence status")
                continue
            if evidence["status"] == "runtime_tested":
                errors.append(f"{label}: runtime_tested unsupported in this link-only catalog")
            if evidence["status"] != "unverified" and not (_web_url(evidence.get("url")) and _iso_date(evidence.get("checked_at")) and isinstance(evidence.get("surface"), str) and evidence["surface"].strip()):
                errors.append(f"{label}: {evidence['status']} lacks URL/date/surface")
            if evidence.get("url") and not _web_url(evidence["url"]):
                errors.append(f"{label}: invalid evidence URL")
        if row.get("redistribution_status") == "restricted" and row.get("planned_use") != "link_only":
            errors.append(f"{label}: restricted item cannot be bundled")
        if PRIVATE.search(json.dumps(row, ensure_ascii=False).replace("\\\\", "\\")):
            errors.append(f"{label}: private path in public catalog")
    index = _read(root, INDEX, errors)
    router = _read(root, ROUTER, errors)
    if index is not None:
        if len(index) > 2400:
            errors.append(f"index exceeds 600-token proxy (4 chars/token): {len(index)} chars")
        rows = [line for line in index.splitlines() if line.startswith("| ") and not line.startswith("| ---")]
        choice_rows = [line for line in rows if ID.search(line)]
        if not 1 <= len(choice_rows) <= 12:
            errors.append(f"index choice rows must be 1–12, found {len(choice_rows)}")
        for line in choice_rows:
            if not ID.search(line):
                errors.append("index row has no source ID")
        if PRIVATE.search(index):
            errors.append("private path in resource index")
        if "../resources/uiux-catalog.json" not in index:
            errors.append("missing index catalog link")
    if router is not None and "references/resource-index.md" not in router:
        errors.append("missing router route: references/resource-index.md")
    if router is not None and ("references/reference-distill.md" not in router or "templates/reference-design.md" not in router):
        errors.append("missing reference distill route")
    distill = _read(root, DISTILL, errors)
    template = _read(root, DISTILL_TEMPLATE, errors)
    if distill is not None:
        for guide in ("direction-gate.md", "prototype-playbook.md", "typography-en-vi.md", "color-protocol.md", "image-sourcing.md", "motion-playbook.md"):
            if guide not in distill:
                errors.append(f"reference distill missing canonical guide: {guide}")
    if template is not None:
        for marker in ("## Sources and access", "## What the material shows", "Observed evidence", "Design inference to test", "Unknown / how to check", "## Adapt for this project"):
            if marker not in template:
                errors.append(f"reference template missing: {marker}")
    for readme in (Path("README.md"), Path("README.vi.md")):
        text = _read(root, readme, errors)
        if text is not None and ("sixteen references" if readme.name == "README.md" else "mười sáu tài liệu tham chiếu") not in text:
            errors.append(f"{readme}: reference count not updated")
        if text is not None:
            for link in (INDEX.as_posix(), CATALOG.as_posix(), DISTILL.as_posix(), DISTILL_TEMPLATE.as_posix(), "scripts/verify-resource-pack.py"):
                if link not in text:
                    errors.append(f"{readme}: missing resource link {link}")
    reference_dir = root / SKILL / "references"
    if len(list(reference_dir.glob("*.md"))) != 16:
        errors.append("reference count must be 16")
    return errors


def _fold(value: str) -> str:
    letters = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return "".join(char for char in letters if not unicodedata.combining(char))


def query(records: list[dict], *, text: str = "", use_case: str = "", stack: str = "", role: str = "", identifier: str = "") -> list[dict]:
    """Return at most three exact-filter matches; a mismatch never fills a slot."""
    results: list[dict] = []
    for row in records:
        if identifier and row["id"] != identifier:
            continue
        if use_case and _fold(use_case) not in _fold(" ".join(row["use_cases"] + row["search_terms"])):
            continue
        if role and _fold(role) not in _fold(row["source_role"]):
            continue
        stacks = row["stack"]
        if stack and "any" not in stacks and "stack_neutral" not in stacks and _fold(stack) not in {_fold(item) for item in stacks}:
            continue
        haystack = " ".join([row["original_label"], row["canonical_label"], row["category"], row["search_hint"], *row["aliases"], *row["search_terms"], *row["use_cases"]])
        if text and any(term not in _fold(haystack) for term in _fold(text).split()):
            continue
        matched = [f"{key}: {value}" for key, value in (("query", text), ("use_case", use_case), ("stack", stack), ("role", role), ("id", identifier)) if value]
        results.append({
            "id": row["id"], "name": row["canonical_label"],
            "url": row["canonical_url"], "use_cases": row["use_cases"],
            "source_role": row["source_role"], "search_hint": row["search_hint"],
            "matched_on": matched, "fit": row["summary"],
        })
        if len(results) == 3:
            break
    return results


def self_test(root: Path) -> list[str]:
    errors = verify(root)
    if errors:
        return ["valid fixture failed: " + "; ".join(errors)]
    records = _records(root, errors)
    if [item["id"] for item in query(records, use_case="app_flow")] != ["18"]:
        errors.append("query app_flow must select Mobbin, not website galleries")
    if query(records, use_case="app_flow", identifier="16"):
        errors.append("Siteinspire must not match app_flow")
    if [item["id"] for item in query(records, use_case="font_pairing")] != ["24"]:
        errors.append("font_pairing must select Typewolf editorial")
    if [item["id"] for item in query(records, text="Rive")] != ["51"]:
        errors.append("Rive must be findable as its own runtime/editor")
    if query(records, use_case="theme_tokens", identifier="59"):
        errors.append("ZippyStarter must not match theme editor")
    if not query(records, text="màu sắc"):
        errors.append("Vietnamese color alias must match")
    if query(records, text="no-such-source-abcdef"):
        errors.append("no-match query must return an empty list")
    with tempfile.TemporaryDirectory(prefix="resource-pack-") as temp:
        target = Path(temp)
        for relative in (CATALOG, INDEX, ROUTER, DISTILL_TEMPLATE, Path("README.md"), Path("README.vi.md")):
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((root / relative).read_bytes())
        for relative in (root / SKILL / "references").glob("*.md"):
            if relative.name != INDEX.name:
                destination = target / SKILL / "references" / relative.name
                destination.write_bytes(relative.read_bytes())
        catalog_file = target / CATALOG
        original = json.loads(catalog_file.read_text(encoding="utf-8"))

        def expect(label: str, mutate, needle: str) -> None:
            changed = json.loads(json.dumps(original))
            mutate(changed["sources"])
            catalog_file.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
            found = verify(target)
            if not any(needle in item for item in found):
                errors.append(f"negative {label} did not fail: {found}")
            catalog_file.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")

        expect("duplicate ID", lambda rows: rows[1].update(id="01"), "duplicate ID")
        expect("missing ID", lambda rows: rows.pop(), "source count must be 75")
        expect("card slot", lambda rows: rows[1].update(slot=1), "duplicate card/slot")
        expect("boolean card", lambda rows: rows[0].update(card=True), "card/slot must be")
        expect("bad URL", lambda rows: rows[0].update(canonical_url="https://[bad"), "invalid canonical_url")
        expect("bad scheme", lambda rows: rows[0].update(canonical_url="ftp://example.org"), "invalid canonical_url")
        expect("missing host", lambda rows: rows[0].update(canonical_url="https:///path"), "invalid canonical_url")
        expect("credentials", lambda rows: rows[0].update(canonical_url="https://user:pass@example.org"), "invalid canonical_url")
        expect("host whitespace", lambda rows: rows[0].update(canonical_url="https://bad host.example"), "invalid canonical_url")
        expect("host control", lambda rows: rows[0].update(canonical_url="https://bad\nhost.example"), "invalid canonical_url")
        expect("invalid DNS", lambda rows: rows[0].update(canonical_url="https://-invalid.example"), "invalid canonical_url")
        expect("bad port", lambda rows: rows[0].update(canonical_url="https://example.org:bad"), "invalid canonical_url")
        expect("port zero", lambda rows: rows[0].update(canonical_url="https://example.org:0"), "invalid canonical_url")
        expect("port range", lambda rows: rows[0].update(canonical_url="https://example.org:65536"), "invalid canonical_url")
        expect("bad status type", lambda rows: rows[0]["evidence"][0].update(status=[]), "invalid evidence status")
        expect("missing summary", lambda rows: rows[0].pop("summary"), "missing fields: summary")
        expect("bad alias item", lambda rows: rows[0]["aliases"].append(None), "aliases must contain nonempty strings")
        expect("bad date", lambda rows: rows[0].update(checked_at="tomorrow-ish"), "invalid checked_at date")
        expect("empty evidence", lambda rows: rows[0].update(evidence=[]), "evidence cannot be empty")
        expect("runtime evidence", lambda rows: rows[0]["evidence"].append({"status": "runtime_tested"}), "runtime_tested lacks")
        expect("bogus runtime", lambda rows: rows[0]["evidence"].append({"status": "runtime_tested", "url": "https://example.org/", "checked_at": "garbage", "surface": True}), "runtime_tested unsupported")
        expect("bad license status", lambda rows: rows[0].update(license_status="unknown"), "invalid license_status")
        expect("bad follow up", lambda rows: rows[0]["follow_up"].update(status="installed"), "follow_up must be pending")
        expect("planned use", lambda rows: rows[0].update(planned_use="bundle_in_pack"), "planned_use must be link_only")
        expect("private path", lambda rows: rows[0].update(search_hint="C:\\Users\\someone\\Desktop"), "private path")
        if not _web_url("https://bücher.example/") or not _web_url("https://[2001:db8::1]/"):
            errors.append("valid IDN or IPv6 URL was rejected")
        index = target / INDEX
        index_before = index.read_text(encoding="utf-8")
        index.write_text(index_before + "\n| Extra | 01 | 02 | guide |\n", encoding="utf-8")
        if not any("index choice rows" in item for item in verify(target)):
            errors.append("negative index size did not fail")
        index.write_text(index_before + "x" * 500, encoding="utf-8")
        if not any("index exceeds" in item for item in verify(target)):
            errors.append("negative index budget did not fail")
        index.write_text(index_before, encoding="utf-8")
        router = target / ROUTER
        before = router.read_text(encoding="utf-8")
        router.write_text(before.replace("references/resource-index.md", "references/missing.md"), encoding="utf-8")
        if not any("missing router route" in item for item in verify(target)):
            errors.append("negative router route did not fail")
        router.write_text(before, encoding="utf-8")
        template = target / DISTILL_TEMPLATE
        template_before = template.read_text(encoding="utf-8")
        template.write_text(template_before.replace("Observed evidence", "Unlabeled notes"), encoding="utf-8")
        if not any("reference template missing: Observed evidence" in item for item in verify(target)):
            errors.append("negative reference template did not fail")
        template.write_text(template_before, encoding="utf-8")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--query", default="")
    parser.add_argument("--use-case", default="")
    parser.add_argument("--stack", default="")
    parser.add_argument("--role", default="")
    parser.add_argument("--id", default="")
    args = parser.parse_args()
    errors = self_test(args.root) if args.self_test else verify(args.root)
    if errors:
        for error in errors:
            print("FAIL", error, file=sys.stderr)
        return 1
    if any((args.query, args.use_case, args.stack, args.role, args.id)):
        records = _records(args.root, [])
        print(json.dumps({"results": query(records, text=args.query, use_case=args.use_case, stack=args.stack, role=args.role, identifier=args.id)}, ensure_ascii=True, separators=(",", ":")))
    else:
        print("resource pack verified" + ("; negative fixtures passed" if args.self_test else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
