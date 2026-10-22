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
    crlf = existing.count('\r\n') * 2 > existing.count('\n')  # the file's own line ends are kept when it is rewritten
    existing = v3.eol_lf(existing)  # a file saved with CRLF (or CR) is the same file
    try:
        text = build.render_design_md(existing, tokens, index)
    except OSError:
        raise Refused('input_error: DESIGN.md template not found') from None
    warnings = [f'WARN {line}' for line in build.design_md_warnings(tokens)]
    if text == existing and raw is not None:
        return 'unchanged', warnings
    if crlf:
        text = text.replace('\n', '\r\n')
    size = len(text.encode('utf-8'))
    if size > v3.CAP_KEPT:  # the file this run would leave behind must be one the next run accepts
        raise Refused(f'limit_exceeded: DESIGN.md: file size: {size} > {v3.CAP_KEPT}')
    if check:
        raise Refused('design_md_missing: DESIGN.md' if raw is None else 'design_md_stale: DESIGN.md')
    v3.safe_path(package, 'DESIGN.md').write_bytes(text.encode('utf-8'))
    return 'written', warnings


def _viewer(package: Path, check: bool) -> tuple[str, list[str]]:
    """Write (or, with check, only diff) viewer.html; return (state, warnings). Raises Refused on a missing, stale or oversized page."""
    try:
        data = build.collect_package(package)
    except build.PackageError as exc:
        raise Refused(str(exc)) from None
    text = build.render_viewer(data).encode('utf-8')
    warnings = [f'WARN {line}' for line in data['warnings']]
    if len(text) > build.VIEWER_MAX:
        raise Refused(f'viewer_too_large: viewer.html: {len(text)} > {build.VIEWER_MAX}')
    if len(text) > build.VIEWER_WARN:
        warnings.append(f'WARN viewer_large: viewer.html: {len(text)} > {build.VIEWER_WARN}')
    raw = _read(package, 'viewer.html', build.VIEWER_MAX)
    if raw is not None and v3.eol_lf(raw) == v3.eol_lf(text):
        return 'unchanged', warnings
    if check:
        raise Refused('viewer_missing: viewer.html' if raw is None else 'viewer_stale: viewer.html')
    v3.safe_path(package, 'viewer.html').write_bytes(text)
    return 'written', warnings


def _adapter_plan(package: Path, root: Path) -> tuple[str, tuple[list[str], list[str]]]:
    """(package path relative to root in POSIX form, what ``--adapters`` would write and skip); raises Refused with the finished
    error line. Nothing is written here, so a bad argument stops the run before any generated file is touched."""
    if not root.is_dir():
        raise Refused(f'input_error: adapters root not found: {v3._label(root)}')
    try:
        rel = package.resolve().relative_to(root.resolve()).as_posix()
        return rel, build.write_adapters(root, rel, check=True)
    except FileNotFoundError as exc:
        raise Refused(f'input_error: adapter template not found: {exc.args[0]}') from None
    except (ValueError, OSError):  # a package outside the root, or one whose path cannot go into a code span
        raise Refused('input_error: package outside adapters root') from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, help='design-system package folder (format v3)')
    parser.add_argument('--design-md', action='store_true', help='regenerate the DESIGN.md front matter from tokens.json')
    parser.add_argument('--viewer', action='store_true', help='regenerate viewer.html, the offline page, from the package files')
    parser.add_argument('--adapters', type=Path, metavar='ROOT',
                        help='write AGENTS.md, CLAUDE.md and GEMINI.md into ROOT, the folder that holds the package; never overwrites')
    parser.add_argument('--check', action='store_true', help='write nothing; exit 1 when a generated file is out of date')
    args = parser.parse_args(argv)
    if not (args.design_md or args.viewer or args.adapters is not None):
        print('input_error: choose --design-md/--viewer/--adapters', file=sys.stderr)
        return 1
    if args.package is None:
        print('input_error: --package is required', file=sys.stderr)
        return 1
    if not args.package.is_dir():
        print(f'input_error: package not found: {v3._label(args.package)}', file=sys.stderr)
        return 1
    try:
        package_rel, plan = _adapter_plan(args.package, args.adapters) if args.adapters is not None else ('', ([], []))
        states = {'design-md': 'skipped', 'viewer': 'skipped'}
        warnings: list[str] = []
        if args.design_md or args.viewer:
            tokens, index = _inputs(args.package)
            if args.design_md:
                states['design-md'], found = _design_md(args.package, tokens, index, args.check)
                warnings.extend(found)
            if args.viewer:
                states['viewer'], found = _viewer(args.package, args.check)
                warnings.extend(found)
        written, skipped = plan if args.check or args.adapters is None else build.write_adapters(args.adapters, package_rel)
    except Refused as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:  # whatever else a hostile package provokes ends as one line, never a traceback
        print(f'input_error: {type(exc).__name__}', file=sys.stderr)
        return 1
    for warning in warnings:
        print(warning)
    for name in skipped:
        print(f'WARN adapter_exists: {name}')
        if not args.check:  # what the file would hold, for the owner to merge by hand
            print(f'--- proposed {name} ---')
            print(build.adapter_text(name, package_rel), end='')
            print('--- end ---')
    if args.check:
        line = 'CHECKED: ' + ' '.join(f'{name}={"skipped" if state == "skipped" else "ok"}' for name, state in states.items())
        print(line + (f' adapters={len(written)} to write, {len(skipped)} present' if args.adapters is not None else ''))
    else:
        print(f'BUILT: design-md={states["design-md"]} viewer={states["viewer"]} adapters={len(written)} written, {len(skipped)} skipped')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
