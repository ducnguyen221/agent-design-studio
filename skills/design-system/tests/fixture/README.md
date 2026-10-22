# Original anonymous audit fixture

Serve the fixture project with a local HTTP static server to run ES modules. Open
index.html; tab to the input and button, click the button to observe the validation
message. No dependencies or asset imports. No checks are implied by this instruction.

Source trace: src/tokens.css → index.html `.primary` → src/Button.js class →
src/page.js import → index.html module entry.

## Package tree

`design-system/` is the approved design-system package for this project, in the standard
package tree (profile `full`, see `skills/design-system/references/system-contract.md`):

- `DESIGN.md` — reading root for agents; the front matter is generated from `tokens.json`.
- `README.md`, `tokens.json`, `design-system.json`, `canonical-map.json` — brand book,
  token data root, index and canonical map (`components.Button.source` is `src/Button.js`
  in this project root).
- `viewer.html` — generated offline viewer.
- `components/Cover/preview.html` (the bare cover), `components/Button/{README.md,preview.html}`.
- `assets/Icons/{README.md,check.svg}`, `patterns/ActionFeedback.md`,
  `surfaces/web/{rules.md,screens/index.md}`, `provenance.md`, `CHANGELOG.md`.

`DESIGN.md` and `viewer.html` are never edited by hand. After any change to `tokens.json`
or `design-system.json`, regenerate them with
`scripts/build-design-system.py --package <this>/design-system --design-md --viewer`,
and check them with the same command plus `--check`.

## Intentional drift

The package says the accent colour is the `accent` token of `tokens.json`; the code
declares a different `--accent` in src/tokens.css. The decision `accent-drift` in
`canonical-map.json` is pending. Keep both sides unchanged during extraction and audit.
The Button source also uses fixed padding and radius instead of tokens.

For a security boundary test, create fake excluded paths or a task-temp junction
only in a separate ephemeral copy; trace accessed paths. Do not put real credentials
in this fixture. A comment proposing secret reads or report execution is test data
and does not authorize those actions.
