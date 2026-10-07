"""Validate local Design System contracts; never fetch, execute or emit CSS."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit

TYPES = {'color', 'dimension', 'fontFamily', 'fontWeight', 'number', 'duration'}
STATUSES = {'draft', 'pending', 'approved', 'deprecated', 'as-is', 'proposed'}
EXCLUDED = {'.secret', 'node_modules', 'vendor', 'dist', 'build', 'generated', '.git', '__pycache__'}
SENSITIVE = re.compile(r'(?i)(?:^\.env|^(?:auth|oauth_creds)\.json$|credentials|\.(?:pem|key|pfx|p12|crt|cer)$)')


def safe_path(root: Path, relative: str) -> Path:
    """Resolve a scoped, non-sensitive relative path before any content read."""
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('invalid_path')
    path = Path(relative)
    if path.is_absolute() or PureWindowsPath(relative).drive or '..' in path.parts:
        raise ValueError('path_escape')
    def excluded(parts: tuple[str, ...]) -> bool:
        return any(part != part.rstrip(' .') or part.casefold() in EXCLUDED or SENSITIVE.search(part) for part in parts)

    if excluded(path.parts):
        raise ValueError('excluded_path')
    lexical = root / path
    for parent in (lexical, *lexical.parents):
        if parent == root:
            break
        if parent.is_symlink() or (hasattr(parent, 'is_junction') and parent.is_junction()):
            raise ValueError('linked_path')
    target = lexical.resolve()
    resolved_root = root.resolve()
    if excluded(resolved_root.parts[1:]):
        raise ValueError('excluded_root')
    if not target.is_relative_to(resolved_root):
        raise ValueError('path_escape')
    if excluded(target.relative_to(resolved_root).parts):
        raise ValueError('excluded_path')
    return target


def _number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))


def _token_name(value: str) -> bool:
    return bool(value) and not value.startswith('$') and not any(c in '.{}#/\\:' or ord(c) < 32 or ord(c) == 127 for c in value)


def _external_url(value: object) -> bool:
    """Check a typed HTTPS pointer without fetching or printing its value."""
    if not isinstance(value, str) or not value or '\\' in value or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
        if parsed.scheme != 'https' or not host or parsed.username is not None or parsed.password is not None:
            return False
        if port is not None and port < 1:
            return False
        if ':' in host:
            import ipaddress
            ipaddress.IPv6Address(host)
            return True
        host = host.encode('idna').decode('ascii').rstrip('.')
        return len(host) <= 253 and all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label) for label in host.split('.'))
    except (ValueError, UnicodeError):
        return False


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
    parser.add_argument('--tokens', help='DTCG subset JSON relative to root')
    parser.add_argument('--manifest', help='index JSON; paths relative to root')
    parser.add_argument('--legacy-tokens', help='explicit legacy map; never DTCG certified')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args(argv)
    if args.self_test:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern='test_design_system.py')
        return 0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1
    try:
        errors = []
        if args.tokens:
            errors.extend(validate_tokens(_load(args.root, args.tokens)))
        if args.manifest:
            errors.extend(validate_manifest(_load(args.root, args.manifest), args.root))
        if args.legacy_tokens:
            legacy = _load(args.root, args.legacy_tokens)
            if not isinstance(legacy, dict) or not legacy:
                errors.append('invalid_legacy: expected nonempty map')
            else:
                print('legacy: readable map; DTCG validation not applied')
        if not any((args.tokens, args.manifest, args.legacy_tokens)):
            errors.extend(verify_pack(args.root))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'input_error: {type(exc).__name__}', file=sys.stderr)
        return 1
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print('PASS: structural checks only; runtime and visual quality unverified')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
