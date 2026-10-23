<!-- Flexible template: drop a part that does not apply and say why in one line; keep the order of the six parts. -->
# Design system audit report: [product name]

> A report describes what was read, what it shows and what is still unknown. The `audit` mode is read-only. The `extract` mode writes an as-is proposal into the run folder. Neither mode updates a canonical file, marks anything `approved` or turns an inference into a brand decision.

| Field | Value |
|---|---|
| Mode | `audit` or `extract` |
| Run id and date | `[id]`, `[YYYY-MM-DD]` |
| Run folder | `[the folder this run writes to]` |
| Baseline | `[branch and commit]`, `[clean or dirty]` |
| Scope and allowlist | `[folders read]`; excluded: `[secrets, env files, generated, vendored, links]` |
| Surface | `[web, mobile, email, ...]` |
| Output folder | `[path, or not-written]` |
| Owner and status | `[owner or unknown]`, `[draft, pending or as-is]` |
| Canonical map | `[canonical-map.json path, or none found in scope]` |

## 1 Naming consistency

Names of tokens, components, props and files that follow different patterns for the same thing.

| Group | Pattern A (`path:line`) | Pattern B (`path:line`) | Suggested single name |
|---|---|---|---|
| `[tokens, components, props]` | `[...]` | `[...]` | `[...]` |

## 2 Token coverage and hardcoded values

| Measure | Count | Out of | Examples (`path:line`) |
|---|---:|---:|---|
| Values that use a token | `[n]` | `[N]` | `[...]` |
| Hardcoded colours | `[n]` | `[N]` | `[...]` |
| Hardcoded spacing, radius, type | `[n]` | `[N]` | `[...]` |

Each count names the denominator and what it covers. Runtime values not measured are `unverified`.

## 3 Component completeness

| Component | Source (`path:line`) | Variants | States seen | Docs | Missing |
|---|---|---|---|---|---|
| `[name]` | `[...]` | `[...]` | `[default, hover, focus, disabled, ...]` | `[yes, no]` | `[...]` |

A state nobody observed is `unknown`, not filled in from expectation.

## 4 Drift between system and code

| Domain | System says (`path`) | Code says (`path:line`) | Impact | Proposal | Owner decision |
|---|---|---|---|---|---|
| `[brand, tokens, components]` | `[...]` | `[...]` | `[...]` | `[...]` | `[pending or recorded]` |

The code at the baseline is the present; owner-confirmed guidance is the target. Record both and let the owner choose.

## 5 Verifier result

- Command: `[the command you ran, for example python scripts/verify-design-system.py --package <dir>]`
- Result: `[paste the PASS line, or every error and warning line]`
- Not checked by it: live render, browser display, real import.

## 6 Up to three priorities

1. `[the change with the most effect, and its evidence]`
2. `[...]`
3. `[...]`

## Coverage, unknowns and next step

- Coverage: `[n]` of `[N]` `[unit]` inside `[scope]`; excluded: `[...]`. This says nothing about what lies outside the scope.
- Unknown or not checked: `[open questions and checks still needed]`
- Owner decisions pending: `[list, or none]`
- Reviewer record: `[name, date, verdict, or pending]`
- Promotion needs: the owner's confirmation and a reviewer's check of diff, links and sources.
- Next step: `[one action]`
