"""Validate local Design System contracts; never fetch, execute or emit CSS."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system_v3 as v3  # noqa: E402
from design_system_v3 import EXCLUDED, SENSITIVE, STATUSES, safe_path  # noqa: E402,F401  (re-exported: tests and callers use these names)

_external_url = v3.external_url
TYPES = {'color', 'dimension', 'fontFamily', 'fontWeight', 'number', 'duration'}


def _number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))


def _token_name(value: str) -> bool:
    return bool(value) and not value.startswith('$') and not any(c in '.{}#/\\:' or ord(c) < 32 or ord(c) == 127 for c in value)


def _valid_value(kind: str, value: object) -> bool:
    if kind == 'number':
        return _number(value)
    if kind == 'fontWeight':
        return (_number(value) and 1 <= value <= 1000) or (isinstance(value, str) and value in {
            'thin', 'hairline', 'extra-light', 'ultra-light', 'light', 'normal', 'regular', 'medium',
            'semi-bold', 'demi-bold', 'bold', 'extra-bold', 'ultra-bold', 'black', 'heavy', 'extra-black', 'ultra-black'})
    if kind == 'fontFamily':
        return (isinstance(value, str) and bool(value.strip())) or (
            isinstance(value, list) and bool(value) and all(isinstance(v, str) and v.strip() for v in value))
    if kind in {'dimension', 'duration'}:
        units = {'px', 'rem'} if kind == 'dimension' else {'ms', 's'}
        return isinstance(value, dict) and set(value) == {'value', 'unit'} and _number(value['value']) and isinstance(value['unit'], str) and value['unit'] in units
    if kind == 'color':
        if not isinstance(value, dict) or not {'colorSpace', 'components'} <= value.keys() or set(value) - {'colorSpace', 'components', 'alpha'}:
            return False
        components = value['components']
        return value['colorSpace'] == 'srgb' and isinstance(components, list) and len(components) == 3 and all(
            _number(v) and 0 <= v <= 1 for v in components) and _number(value.get('alpha', 1)) and 0 <= value.get('alpha', 1) <= 1
    return False


def validate_tokens(document: object) -> list[str]:
    """Validate the declared DTCG subset, including inherited types and aliases."""
    errors: list[str] = []
    tokens: dict[str, tuple[object, object]] = {}

    def walk(node: object, parts: tuple[str, ...], inherited: object = None) -> None:
        location = '.'.join(parts) or '<root>'
        if not isinstance(node, dict):
            errors.append(f'invalid_structure: {location}')
            return
        kind = node.get('$type', inherited)
        if '$value' in node:
            if not parts:
                errors.append('invalid_structure: root token')
            if any(not key.startswith('$') for key in node):
                errors.append(f'invalid_structure: token/group collision {location}')
            tokens[location] = (kind, node['$value'])
            if not isinstance(kind, str) or kind not in TYPES:
                errors.append(f'unsupported_type: {location}')
            return
        for key, child in node.items():
            if not isinstance(key, str):
                errors.append(f'invalid_structure: {location}')
            elif not key.startswith('$'):
                if not _token_name(key):
                    errors.append(f'invalid_name: {location}')
                else:
                    walk(child, (*parts, key), kind)

    if not isinstance(document, dict) or not document:
        return ['invalid_structure: token document must be nonempty object']
    walk(document, ())
    if not tokens:
        errors.append('invalid_structure: no tokens')
    finished: set[str] = set()

    def visit(name: str, active: set[str]) -> None:
        if name in active:
            errors.append(f'reference_cycle: {name}')
            return
        if name in finished:
            return
        kind, value = tokens[name]
        if isinstance(value, str) and (value.startswith('{') or value.endswith('}')):
            match = re.fullmatch(r'\{([^{}]+)\}', value)
            if not match or not all(_token_name(part) for part in match[1].split('.')):
                errors.append(f'unsupported_reference: {name}')
            elif match[1] not in tokens:
                errors.append(f'missing_target: {name}')
            else:
                target = match[1]
                if tokens[target][0] != kind:
                    errors.append(f'type_mismatch: {name}')
                visit(target, active | {name})
        elif isinstance(kind, str) and kind in TYPES and not _valid_value(kind, value):
            errors.append(f'invalid_value: {name}')
        finished.add(name)

    for name in tokens:
        visit(name, set())
    return errors


def validate_manifest(document: object, root: Path) -> list[str]:
    """Check index paths against the explicitly supplied project root."""
    errors: list[str] = []
    if not isinstance(document, dict):
        return ['invalid_manifest: expected object']
    system = document.get('system')
    if document.get('schemaVersion') != '1' or not isinstance(system, dict) or not all(
        isinstance(system.get(key), str) and system[key] for key in ('id', 'version', 'status')):
        errors.append('invalid_manifest: schemaVersion/system')
    elif system['status'] not in STATUSES:
        errors.append('invalid_status: system')
    canonical = document.get('canonical')
    if not isinstance(canonical, dict) or not canonical:
        errors.append('invalid_manifest: canonical')
    else:
        for domain, source in canonical.items():
            if not isinstance(domain, str) or not domain or any(ord(c) < 32 or ord(c) == 127 for c in domain) or not isinstance(source, dict):
                errors.append('invalid_canonical: domain/source')
            elif source.get('kind') == 'external':
                if 'path' in source or not _external_url(source.get('url')):
                    errors.append(f'invalid_external: {domain}')
            elif not isinstance(source.get('kind'), str) or source['kind'] not in {'file', 'repo-path'} or not isinstance(source.get('path'), str) or 'url' in source:
                errors.append(f'invalid_canonical: {domain}')

    def walk(node: object) -> None:
        if isinstance(node, list):
            ids: set[str] = set()
            for item in node:
                if isinstance(item, dict) and 'id' in item:
                    identifier = item['id']
                    if not isinstance(identifier, str) or not identifier or identifier in ids:
                        errors.append('invalid_id: duplicate or empty')
                    else:
                        ids.add(identifier)
                walk(item)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key in {'path', 'doc', 'preview', 'usage', 'rules'}:
                    try:
                        target = safe_path(root, value)
                        if not target.exists():
                            errors.append(f'missing_path: {key}')
                    except (ValueError, OSError, RuntimeError):
                        errors.append(f'invalid_path: {key}')
                elif key == 'status' and (not isinstance(value, str) or value not in STATUSES):
                    errors.append('invalid_status: record')
                elif isinstance(value, (dict, list)):
                    walk(value)
    walk(document)
    return errors


def verify_pack(root: Path) -> list[str]:
    required = ['SKILL.md', 'references/system-contract.md', 'references/source-code-audit.md',
                'references/token-contract.md', 'templates/design-index.md',
                'templates/component-spec.md', 'templates/audit-report.md']
    errors: list[str] = []
    targets: dict[str, Path] = {}
    for name in required:
        try:
            target = safe_path(root, f'skills/design-system/{name}')
            if target.is_file():
                targets[name] = target
            else:
                errors.append(f'missing_skill_file: {name}')
        except (ValueError, OSError, RuntimeError):
            errors.append(f'invalid_skill_path: {name}')
    if 'SKILL.md' in targets:
        try:
            text = targets['SKILL.md'].read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            return [*errors, 'cannot_read_skill: SKILL.md']
        for marker in ('create', 'extract', 'audit', 'extend', *required[1:]):
            if marker not in text:
                errors.append(f'missing_skill_route: {marker}')
    return errors


def _load(root: Path, name: str) -> object:
    return json.loads(safe_path(root, name).read_text(encoding='utf-8'))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--package', type=Path, help='design-system package folder (format v3)')
    parser.add_argument('--profile', choices=v3.PROFILES, help='full or minimal; default: profile in canonical-map.json, else full')
    parser.add_argument('--format-version', default=str(v3.FORMAT_VERSION), help='only 3 is supported')
    parser.add_argument('--tokens', help='tokens.json in the v3 list grammar, relative to root')
    parser.add_argument('--dtcg', help='DTCG subset JSON relative to root')
    parser.add_argument('--canonical-map', help='canonical-map.json relative to root')
    parser.add_argument('--manifest', help='deprecated alias of --canonical-map')
    parser.add_argument('--legacy-tokens', help='explicit legacy map; never DTCG certified')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args(argv)
    if args.self_test:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern='test_design_system.py')
        return 0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1
    if args.format_version != str(v3.FORMAT_VERSION):
        print('input_error: unsupported --format-version', file=sys.stderr)
        return 1
    errors: list[str] = []
    warnings: list[str] = []
    map_file = args.canonical_map or args.manifest
    try:
        if args.package is not None:
            if not args.package.is_dir():
                print(f'input_error: package not found: {v3._label(args.package)}', file=sys.stderr)
                return 1
            package_errors, package_warnings = v3.verify_package(args.package, args.profile)
            errors.extend(package_errors)
            warnings.extend(package_warnings)
        if args.tokens:
            errors.extend(v3.validate_tokens_v3(_load(args.root, args.tokens), args.package))
        if args.dtcg:
            errors.extend(validate_tokens(_load(args.root, args.dtcg)))
        if args.manifest:
            warnings.append('deprecated_flag: --manifest')
        if map_file:
            errors.extend(v3.validate_canonical_map(_load(args.root, map_file), args.package or args.root))
        if args.legacy_tokens:
            legacy = _load(args.root, args.legacy_tokens)
            if not isinstance(legacy, dict) or not legacy:
                errors.append('invalid_legacy: expected nonempty map')
            else:
                print('legacy: readable map; DTCG validation not applied')
        if args.package is None and not any((args.tokens, args.dtcg, map_file, args.legacy_tokens)):
            errors.extend(verify_pack(args.root))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'input_error: {type(exc).__name__}', file=sys.stderr)
        return 1
    for warning in warnings:
        print(f'WARN {warning}')
    for error in dict.fromkeys(errors):
        print(error, file=sys.stderr)
    if not errors:
        print(v3.pass_line(warnings, bundle=args.package is not None and v3.has_bundle(args.package)))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
