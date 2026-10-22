"""Generate the derived files of a design-system package from tokens.json; never fetch, execute or read outside the package."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system_build as build  # noqa: E402
import design_system_v3 as v3  # noqa: E402


class Refused(Exception):
    """A package file that cannot be used; carries the finished error line."""


def _read(package: Path, rel: str, cap: int) -> bytes | None:
    """At most cap + 1 bytes of a package file, after the path checks; None when the file does not exist."""
    try:
        with v3.safe_path(package, rel).open('rb') as handle:
            return handle.read(cap + 1)
    except FileNotFoundError:
        return None
    except (ValueError, RuntimeError):
        raise Refused(f'refused_sensitive_path: {rel}') from None


def _json(package: Path, rel: str, bad_json: str, too_large) -> object:
    raw = _read(package, rel, v3.CAP_JSON)
    if raw is None:
        raise Refused(f'missing_required_file: {rel}')
    if len(raw) > v3.CAP_JSON:
        raise Refused(too_large(v3.safe_path(package, rel).stat().st_size))
    try:
        return json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeError, RecursionError):
        raise Refused(bad_json) from None


def _inputs(package: Path) -> tuple[dict, dict]:
    """tokens.json and design-system.json, checked; raises Refused with every problem found."""
    problems: list[str] = []
    loaded: dict[str, object] = {}
    for rel, bad_json, too_large in (
            ('tokens.json', 'token_shape: tokens.json: json', lambda n: f'limit_exceeded: tokens.json: file size: {n} > {v3.CAP_JSON}'),
            ('design-system.json', 'invalid_index_value: design-system.json: json',
             lambda n: f'invalid_index_value: design-system.json: size: {n} > {v3.CAP_JSON}')):
        try:
            loaded[rel] = _json(package, rel, bad_json, too_large)
        except Refused as exc:
            problems.append(str(exc))
    if 'design-system.json' in loaded:
        problems.extend(v3.validate_index(loaded['design-system.json']))
    if 'tokens.json' in loaded:
        problems.extend(v3.validate_tokens_v3(loaded['tokens.json'], package))
    if problems:
        raise Refused('\n'.join(dict.fromkeys(problems)))
    return loaded['tokens.json'], loaded['design-system.json']


def _design_md(package: Path, tokens: dict, index: dict, check: bool) -> tuple[str, list[str]]:
    """Write (or, with check, only diff) DESIGN.md; return (state, warnings). Raises Refused on stale or unusable input."""
    raw = _read(package, 'DESIGN.md', v3.CAP_KEPT)
    if raw is not None and len(raw) > v3.CAP_KEPT:
        raise Refused(f'limit_exceeded: DESIGN.md: file size: {v3.safe_path(package, "DESIGN.md").stat().st_size} > {v3.CAP_KEPT}')
    try:
        existing = '' if raw is None else raw.decode('utf-8')
    except UnicodeError:
        raise Refused('input_error: DESIGN.md: not valid UTF-8') from None
    try:
        text = build.render_design_md(existing, tokens, index)
    except OSError:
        raise Refused('input_error: DESIGN.md template not found') from None
    warnings = [f'WARN {line}' for line in build.design_md_warnings(tokens)]
    if text == existing and raw is not None:
        return 'unchanged', warnings
    if check:
        raise Refused('design_md_missing: DESIGN.md' if raw is None else 'design_md_stale: DESIGN.md')
    v3.safe_path(package, 'DESIGN.md').write_bytes(text.encode('utf-8'))
    return 'written', warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, help='design-system package folder (format v3)')
    parser.add_argument('--design-md', action='store_true', help='regenerate the DESIGN.md front matter from tokens.json')
    parser.add_argument('--check', action='store_true', help='write nothing; exit 1 when a generated file is out of date')
    args = parser.parse_args(argv)
    if not args.design_md:
        print('input_error: choose --design-md/--viewer/--adapters', file=sys.stderr)
        return 1
    if args.package is None:
        print('input_error: --package is required', file=sys.stderr)
        return 1
    if not args.package.is_dir():
        print(f'input_error: package not found: {v3._label(args.package)}', file=sys.stderr)
        return 1
    try:
        tokens, index = _inputs(args.package)
        state, warnings = _design_md(args.package, tokens, index, args.check)
    except Refused as exc:
        print(exc, file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError, RecursionError) as exc:
        print(f'input_error: {type(exc).__name__}', file=sys.stderr)
        return 1
    for warning in warnings:
        print(warning)
    if args.check:
        print('CHECKED: design-md=ok viewer=skipped')
    else:
        print(f'BUILT: design-md={state} viewer=skipped adapters=0 written, 0 skipped')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
