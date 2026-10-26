# Changelog

All notable changes to this pack. Newest first.

## 1.5.0 — 2026-10-26

- Third-party notices (sprint P3, TK7): `NOTICE` and `LICENSES/` record four upstream works that contributed ideas or short passages, with owner, license, revision, derivation level and keep/drop decision. No third-party file is redistributed.
- UI/UX rule-library distillation (sprint P3, TK6): the choice rules are condensed into `direction-gate.md` (24 sector cautions), `uat-report-schema.md` (interaction and structure checks) and `ownership-matrix.md` (charts and React performance point elsewhere). The library's own data is not carried over: no 67-style or 96-palette tables, no search CLI, no `--persist` output. The local UTF-8 patch for its search script is not carried over either, since no script is. Catalog source 76 (Next Level Builder UI/UX rule library, tag `v2.15.0`, MIT, link only) is the lookup path for that data. The source gate moves from 75 to 76 and the reference gate from 16 to 18; see ADR 0003.
