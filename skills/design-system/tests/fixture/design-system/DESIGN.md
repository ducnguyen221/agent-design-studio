# Anonymous fixture contract

Owner: fixture author. Status: approved fixture baseline, not a production claim.
Token source is `src/tokens.css`; component source is `src/Button.js`; paths are
relative to the fixture project root. Extract/audit must leave this baseline unchanged.

Intentional drift: this document says accent is `#654321`, whereas CSS declares
`#123456`. An audit must report both and hold owner decision pending.

Runtime, accessibility and token-to-render parity are unverified until a browser run.

## Read the system

- [Identity and content](brand/identity.md)
- [Colors and token authority](foundations/colors.md)
- [Button contract](components/button.md)
- [Action feedback pattern](patterns/action-feedback.md)
- [Entry screen](surfaces/web/screens/index.md)
- [Asset rights](assets/manifest.md)
- [Machine index](manifest.json)

These six specifications document this anonymous fixture only. The code baseline
describes as-is; brand/content rules below belong to this original demo. No third-party
assets or product branding are included. Domain sources remain single in the index.
