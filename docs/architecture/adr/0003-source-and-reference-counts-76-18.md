# 0003. Raise the verifier counts to 76 sources and 18 references

Status: accepted · Sprint: agent-design-studio:SPR-01 (program P3) · Related: ADR 0002; `scripts/verify-resource-pack.py`
Gate approval: 75 to 76 was approved by the owner in the sprint's decision list (item D-B8); 16 to 18 was approved at Gate 1 on 2026-10-26 by the reviewer acting under the owner's written delegation. Both records are in the sprint ledger, outside this repository.

## Context

`verify-resource-pack.py` pins two exact numbers: the catalog holds 75 sources, and `skills/design-routing/references/` holds 16 Markdown files. The same numbers are written in both READMEs, in `agents/openai.yaml` and in the catalog's `scope` string. This sprint adds exactly one catalog source (a link-only rule library, tag-pinned) and exactly two reference files for the `static-artifact` lane (`static-artifact-build.md`, `static-artifact-qa.md`). All other new material was folded into existing files, so no further file was added.

## Options

| Option | How | Trade-off | When it fits |
|---|---|---|---|
| A. Change the pinned numbers to 76 and 18 | Edit the constants, the id pattern, the negative-test message and the prose that repeats them | Small diff; every other check keeps its strength | The count grows by a known, reviewed amount |
| B. Replace the exact counts with minimums | `>=` instead of `!=` | Future additions pass without review, which is what the exact pin exists to stop | Never for a pack that promises a curated set |
| C. Keep 75 and 16 by dropping the source and folding the two lane files into others | No gate edit | Loses the lookup path for the dropped data and mixes the lane rules into files with other owners | Only if the owner refuses any gate edit |

## Decision

Option A. The numbers move to 76 sources and 18 references and nothing else about the gates moves.

- Changed: the source-id pattern accepts `76`; the source count is 76; the negative test expects "source count must be 76"; the reference count is 18; the README checks look for "eighteen references" and its Vietnamese counterpart; both READMEs, the router's adapter comment and the catalog `scope` string say 76 sources, 26 cards, 18 references and 22 in the pack.
- Not changed: the private-path pattern; the 2,400-character cap and the 12-row cap on `references/resource-index.md` (the new source is folded into an existing row); the requirement that every source is `link_only`; the 31 required fields; the license and evidence checks; the card and slot arithmetic.

## Consequences

- Easier: the verifier still fails on any unreviewed addition or removal, now around the new totals.
- Harder: the next source or reference file needs the same edit set; the numbers live in the places listed above and nowhere else is checked.
- Way back: revert the gate commit together with the commits that added source 76 and the two lane files; the verifier then returns to 75 and 16.
