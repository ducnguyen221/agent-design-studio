"""Derive a DTCG 2025.10 subset file from the tokens.json of a design-system package; never edits the package, fetches or executes anything."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system_v3 as v3  # noqa: E402

_spec = importlib.util.spec_from_file_location('design_system_verifier_for_export', Path(__file__).with_name('verify-design-system.py'))
verifier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verifier)


class Refused(Exception):
    """An input that cannot be used; carries the finished error text (one line per problem)."""


def _inside(out: Path, package: Path) -> bool:
    """True when ``out`` would land in the package folder, also through a link or a ``..`` part (the longest existing part is resolved)."""
    try:
        Path(os.path.realpath(out)).relative_to(Path(os.path.realpath(package)))
    except ValueError:
        return False
    return True


def _tokens(package: Path) -> dict:
    """tokens.json of the package, read with a size cap and checked against the v3 grammar; raises Refused with every problem."""
    try:
        with v3.safe_path(package, 'tokens.json').open('rb') as handle:
            raw = handle.read(v3.CAP_JSON + 1)
    except FileNotFoundError:
        raise Refused('missing_required_file: tokens.json') from None
    except (ValueError, RuntimeError):
        raise Refused('refused_sensitive_path: tokens.json') from None
    if len(raw) > v3.CAP_JSON:
        raise Refused(f'limit_exceeded: tokens.json: file size: {v3.safe_path(package, "tokens.json").stat().st_size} > {v3.CAP_JSON}')
    try:
        doc = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeError, RecursionError):
        raise Refused('token_shape: tokens.json: json') from None
    problems = list(dict.fromkeys(v3.validate_tokens_v3(doc)))
    if problems:
        raise Refused('\n'.join(problems))
    return doc


def _count(node: object) -> int:
    """Number of tokens (nodes with ``$value``) in a DTCG document."""
    if not isinstance(node, dict):
        return 0
    if '$value' in node:
        return 1
    return sum(_count(child) for key, child in node.items() if not key.startswith('$'))


def _write(out: Path, data: bytes) -> None:
    """Write ``data`` to a temporary file in the folder of ``out`` and move it over ``out``: the directory entry is replaced, so a hard
    link to a package file is never written through and a failed write leaves the old file whole."""
    handle, name = tempfile.mkstemp(dir=out.parent, prefix='.export-dtcg-', suffix='.tmp')
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(data)
        os.chmod(name, 0o644)  # mkstemp makes the file private; an export is an ordinary file
        os.replace(name, out)
    except OSError as exc:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise Refused(f'input_error: --out not written: {type(exc).__name__}') from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, help='design-system package folder (format v3)')
    parser.add_argument('--out', type=Path, help='the DTCG file to write; it may not be inside the package')
    args = parser.parse_args(argv)
    try:
        if args.package is None:
            raise Refused('input_error: --package is required')
        if args.out is None:
            raise Refused('input_error: --out is required')
        if not args.package.is_dir():
            raise Refused(f'input_error: package not found: {v3._label(args.package)}')
        if _inside(args.out, args.package):
            raise Refused('input_error: --out inside package')
        if not args.out.parent.is_dir():
            raise Refused(f'input_error: --out folder not found: {v3._label(args.out.parent)}')
        if os.path.lexists(args.out) and (os.path.islink(args.out) or not os.path.isfile(args.out)):
            raise Refused(f'input_error: --out is not a file: {v3._label(args.out)}')
        document, skipped = v3.to_dtcg(_tokens(args.package))
        for line in skipped:
            print(f'SKIP {line}')
        if not document:
            raise Refused('input_error: nothing to export: every token was skipped (see the SKIP lines)')
        problems = verifier.validate_tokens(document)  # never write what the DTCG check refuses
        if problems:
            raise Refused('\n'.join(problems))
        _write(args.out, (json.dumps(document, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    except Refused as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:  # whatever else a hostile package provokes ends as one line, never a traceback
        print(f'input_error: {type(exc).__name__}', file=sys.stderr)
        return 1
    print(f'EXPORTED: {_count(document)} tokens, {len(skipped)} skipped -> {v3._label(args.out)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
