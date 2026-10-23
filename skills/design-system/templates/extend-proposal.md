<!-- Flexible template: keep the seven parts in order. A part that does not apply says so in one line and gives the reason. -->
# Extension proposal: [component, pattern or token name]

> A proposal changes nothing canonical. It stays `pending` until the owner confirms it and a reviewer checks it.

## 1 Problem

What cannot be built or said with the system today, for whom, and the evidence (`path:line`, a screen, a request).

## 2 Closest existing part and why it falls short

Name the nearest component, pattern or token and what it already covers. State the exact gap, so the owner can see why reuse is not enough.

## 3 Proposed API, variants and states

| Item | Proposal |
|---|---|
| Name | `[ASCII JavaScript identifier]` |
| Props | `[name: type, default]` |
| Variants | `[...]` |
| States | `[default, hover, focus-visible, active, disabled, loading, error, empty]` |

## 4 Tokens used

List the existing tokens the part uses, by name. A token that does not exist yet is marked `candidate` with a one-line usage, and no value is final until the owner accepts it.

| Token | Status (`existing` or `candidate`) | Used for |
|---|---|---|
| `[name]` | `[...]` | `[...]` |

## 5 Accessibility

Role, keyboard behaviour, focus handling, what a screen reader announces, and the colour pairs that need a contrast check.

## 6 Open questions

Each question names who can answer it. Unknown facts say `unknown` and how to find out.

## 7 Migration

What existing code or documents change, in what order, and how to undo it. Append a dated entry to `CHANGELOG.md`; never rewrite an old one.

## Promotion

- Status: `pending`
- Owner: `[name or unknown]`
- Reviewer: `[name or pending]`
- After a token is written to `tokens.json`: run `python scripts/build-design-system.py --package <dir> --design-md --viewer`, then `python scripts/verify-design-system.py --package <dir>`.
