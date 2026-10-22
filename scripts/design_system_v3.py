"""Pure checks for a design-system package in Claude Design format v3.

No network, no file writes. Every file read goes through ``safe_path`` and the sensitive-name
pattern first. Rules and error codes: skills/design-system/references/{system-contract,
token-contract,design-md-spec}.md. Errors are ``<code>: <path>[: detail]``; warnings use the same
shape without the ``WARN `` prefix, which the CLI adds.
"""
from __future__ import annotations

import html
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit

FORMAT_VERSION = 3
FORMAT_READ_ON = '2026-10-22'
UNCHECKED = ('live-render', 'browser-display', 'real-import')
STATUSES = {'draft', 'pending', 'approved', 'deprecated', 'as-is', 'proposed'}
PROFILES = ('full', 'minimal')
EXCLUDED = {'.secret', 'node_modules', 'vendor', 'dist', 'build', 'generated', '.git', '__pycache__'}
SENSITIVE = re.compile(r'(?i)(?:^\.env|^(?:auth|oauth_creds)\.json$|^id_(?:rsa|dsa|ecdsa|ed25519)|credentials|\.(?:pem|key|pfx|p12|crt|cer|ppk|kdbx)$)')

NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$')
JS_IDENT = re.compile(r'^[A-Za-z_$][A-Za-z0-9_$]*$')
SHORT_NAME = re.compile(r'~\d')
SECTION_NAMES = ('Overview', 'Colors', 'Typography', 'Layout', 'Elevation & Depth', 'Shapes', 'Components', "Do's and Don'ts")
OVERVIEW_LINES = ('Read order', 'Owner', 'Status')
REFUSED_FILES = {'skill.md', 'agents.md', 'claude.md', 'gemini.md', 'package.json', 'tsconfig.json', 'deno.json', 'bunfig.toml',
                 'package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lock', 'bun.lockb', 'deno.lock'}
GENERATED_ROOT_FILES = {'manifest.json', 'tokens.css', 'migration-map.json', 'publish-progress.json'}
GENERATED_ROOT_DIRS = {'api', 'archived'}
LEGACY_DIRS = ('brand', 'foundations', 'integrations', 'specimens', 'ui-kit')
TEXT_SUFFIXES = {'.md', '.mdx', '.json', '.html', '.css', '.svg', '.txt', '.js', '.ts', '.yml', '.yaml', '.csv'}
FONT_MAGIC = (b'wOFF', b'wOF2', b'\x00\x01\x00\x00', b'true', b'OTTO')
FORBIDDEN_TAGS = ('iframe', 'frame', 'object', 'embed', 'portal', 'noscript')

MAX_THEMES, MAX_COLORS, MAX_FAMILIES, MAX_GROUPS, MAX_STYLES, MAX_OTHER = 8, 600, 12, 12, 80, 60
CAP_README, CAP_TOKENS, CAP_PREVIEW, CAP_COMPONENT_README = 200_000, 512_000, 256_000, 64_000
CAP_FONT_STORED, CAP_ASSET_STORED, CAP_SVG_RAW, CAP_PACKAGE_STORED = 1_000_000, 12_000_000, 2_000_000, 14_000_000
CAP_JSON = CAP_KEPT = 512_000  # design-system.json and canonical-map.json; DESIGN.md and other kept text files
MAX_SECTIONS, MAX_FILES, MAX_DEPTH = 24, 1000, 16


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


def external_url(value: object) -> bool:
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


def _label(value: object, limit: int = 120) -> str:
    """Printable, bounded form of an untrusted name for error lines."""
    return ''.join(c if c.isprintable() else '?' for c in str(value))[:limit]


def _is_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))


# --------------------------------------------------------------------------- colour

_HEX = re.compile(r'^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
_ALIAS = re.compile(r'^\{([A-Za-z0-9][A-Za-z0-9_.-]{0,63})\}$')
_FUNC_NAMES = {'rgb', 'rgba', 'hsl', 'hsla', 'oklch', 'oklab', 'lab', 'lch', 'color'}
_NUMBER = re.compile(r'^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)(%|deg)?$')
_FORBIDDEN_COLOR = re.compile(r'(?i)\b(?:var|url|color-mix)\s*\(')
_BARE_WORD = re.compile(r'^[A-Za-z]+$')


def _func(text: str) -> tuple[str, str] | None:
    """(lower-case name, trimmed arguments) of ``name( ... )`` with no nested parentheses; one pass, no backtracking."""
    opening = text.find('(')
    if opening < 1 or not text.endswith(')'):
        return None
    name, inner = text[:opening].lower(), text[opening + 1:-1]
    if name not in _FUNC_NAMES or '(' in inner or ')' in inner:
        return None
    return name, inner.strip()


def _split_function(name: str, args: str) -> tuple[list[tuple[float, str]], tuple[float, str] | None, str | None]:
    """Split colour-function arguments into numbers; raise ValueError('invalid_color') on bad syntax."""
    left, slash, right = args.partition('/')
    tokens = [t for t in re.split(r'[\s,]+', left.strip()) if t]
    alpha_token = right.strip() if slash else None
    space = None
    if name == 'color':
        if not tokens or not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', tokens[0]):
            raise ValueError('invalid_color')
        space, tokens = tokens[0], tokens[1:]
    if alpha_token is None and len(tokens) == 4 and name != 'color':
        alpha_token = tokens.pop()
    if len(tokens) != 3 or (alpha_token is not None and len(alpha_token.split()) != 1):
        raise ValueError('invalid_color')

    def number(token: str) -> tuple[float, str]:
        match = _NUMBER.match(token)
        if not match:
            raise ValueError('invalid_color')
        return float(match[1]), match[2] or ''

    return [number(t) for t in tokens], (number(alpha_token) if alpha_token else None), space


def _alpha(token: tuple[float, str] | None) -> float:
    if token is None:
        return 1.0
    value, unit = token
    return min(1.0, max(0.0, value / 100 if unit == '%' else value))


def _linear_to_srgb(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055


def _oklab_to_srgb(lightness: float, a: float, b: float) -> tuple[float, float, float]:
    l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    red = 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    green = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    blue = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_
    return _linear_to_srgb(red), _linear_to_srgb(green), _linear_to_srgb(blue)


def _hsl_to_srgb(hue: float, sat: float, light: float) -> tuple[float, float, float]:
    hue = (hue % 360) / 360
    sat, light = min(1.0, max(0.0, sat)), min(1.0, max(0.0, light))
    q = light * (1 + sat) if light < 0.5 else light + sat - light * sat
    p = 2 * light - q

    def channel(t: float) -> float:
        t %= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    return channel(hue + 1 / 3), channel(hue), channel(hue - 1 / 3)


def _parse_color_alpha(value: str) -> tuple[float, float, float, float]:
    """Convert a colour string to sRGB 0..1 plus alpha, clamping out-of-gamut values."""
    if not isinstance(value, str):
        raise ValueError('invalid_color')
    text = value.strip()
    if _HEX.match(text):
        digits = text[1:]
        if len(digits) in (3, 4):
            digits = ''.join(c * 2 for c in digits)
        channels = [int(digits[i:i + 2], 16) / 255 for i in range(0, len(digits), 2)]
        return channels[0], channels[1], channels[2], channels[3] if len(channels) == 4 else 1.0
    parts = _func(text)
    if not parts:
        raise ValueError('invalid_color')
    name, args = parts
    numbers, alpha_token, _space = _split_function(name, args)
    alpha = _alpha(alpha_token)
    if name in {'lab', 'lch', 'color'}:
        raise ValueError('unsupported_space')
    clamp = lambda x: min(1.0, max(0.0, x))
    if name.startswith('rgb'):
        rgb = tuple(clamp(n / 100 if unit == '%' else n / 255) for n, unit in numbers)
    elif name.startswith('hsl'):
        rgb = _hsl_to_srgb(numbers[0][0], numbers[1][0] / 100, numbers[2][0] / 100)
    else:
        lightness = numbers[0][0] / 100 if numbers[0][1] == '%' else numbers[0][0]
        third = lambda n: n[0] * 0.4 / 100 if n[1] == '%' else n[0]
        if name == 'oklab':
            rgb = _oklab_to_srgb(lightness, third(numbers[1]), third(numbers[2]))
        else:
            chroma, hue = max(0.0, third(numbers[1])), math.radians(numbers[2][0])
            rgb = _oklab_to_srgb(lightness, chroma * math.cos(hue), chroma * math.sin(hue))
    return rgb[0], rgb[1], rgb[2], alpha


def parse_color(value: str) -> tuple[float, float, float]:
    """sRGB channels 0..1. ValueError('invalid_color') or ValueError('unsupported_space')."""
    return _parse_color_alpha(value)[:3]


def _classify_color(value: object) -> str:
    """One of: ok, alias, forbidden, invalid (syntax only; lab/lch/color() count as ok)."""
    if not isinstance(value, str):
        return 'invalid'
    text = value.strip()
    if _FORBIDDEN_COLOR.search(text):
        return 'forbidden'
    if _ALIAS.match(text):
        return 'alias'
    if _HEX.match(text):
        return 'ok'
    parts = _func(text)
    if parts:
        try:
            _split_function(*parts)
        except ValueError:
            return 'invalid'
        return 'ok'
    return 'forbidden' if _BARE_WORD.match(text) else 'invalid'


def _luminance(rgb: tuple[float, float, float]) -> float:
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 2 contrast ratio; a translucent foreground is composited over the background, a translucent background over white."""
    fr, fg_, fb, fa = _parse_color_alpha(fg)
    br, bg_, bb, ba = _parse_color_alpha(bg)
    back = tuple(ba * c + (1 - ba) for c in (br, bg_, bb))
    front = tuple(fa * c + (1 - fa) * b for c, b in zip((fr, fg_, fb), back))
    high, low = sorted((_luminance(front), _luminance(back)), reverse=True)
    return (high + 0.05) / (low + 0.05)


# --------------------------------------------------------------------------- tokens

_LENGTH = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:px|rem|em|%|pt|vw|vh|ch|ex)?$')
_WEIGHT_RANGE = re.compile(r'^(\d{1,4})(?:\s+(\d{1,4}))?$')


def _valid_length(value: object) -> bool:
    if _is_number(value):
        return True
    return isinstance(value, str) and (value.strip() == '0' or bool(_LENGTH.match(value.strip())))


def _valid_weight(value: object) -> bool:
    if _is_number(value):
        return 1 <= value <= 1000
    if not isinstance(value, str):
        return False
    if value.strip() in {'normal', 'bold'}:
        return True
    match = _WEIGHT_RANGE.match(value.strip())
    return bool(match) and all(1 <= int(g) <= 1000 for g in match.groups() if g)


def _valid_line_height(value: object) -> bool:
    if _is_number(value):
        return 0 <= value < 10
    return _valid_length(value)


def _theme_value(token: dict, theme_ids: list, theme: object) -> str | None:
    """Colour value of one theme: its own entry, else the first theme that has one."""
    value = token.get('value')
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get(theme), str):
            return value[theme]
        for theme_id in theme_ids:
            if isinstance(value.get(theme_id), str):
                return value[theme_id]
    return None


def _font_rel(file: str) -> str:
    return file if file.startswith('fonts/') else f'fonts/{file}'


def _check_font(root: Path, rel: str) -> list[str]:
    """Existence, four-byte signature and stored size of one font file; a sensitive or escaping path is refused, never opened."""
    try:
        path = safe_path(root, rel)
    except ValueError:
        return [f'refused_sensitive_path: {_label(rel)}']
    except (OSError, RuntimeError):
        return [f'font_file_missing: {_label(rel)}']
    try:
        if not path.is_file():
            return [f'font_file_missing: {_label(rel)}']
        raw = path.stat().st_size
        with path.open('rb') as handle:
            head = handle.read(4)
    except (OSError, RuntimeError):
        return [f'font_file_missing: {_label(rel)}']
    errors = []
    if head not in FONT_MAGIC:
        errors.append(f'font_file_invalid: {_label(rel)}')
    stored = 4 * math.ceil(raw / 3)
    if stored > CAP_FONT_STORED:
        errors.append(f'font_file_too_large: {_label(rel)}: {raw} raw, {stored} stored > {CAP_FONT_STORED}')
    return errors


def _listed_fonts(doc: object) -> list[str]:
    fonts = doc.get('type', {}).get('fonts') if isinstance(doc, dict) and isinstance(doc.get('type'), dict) else None
    if not isinstance(fonts, list):
        return []
    return [_font_rel(f['file']) for f in fonts if isinstance(f, dict) and isinstance(f.get('file'), str) and f['file']]


def _alias_errors(aliases: dict[str, list[str]], names: list[str]) -> list[str]:
    errors: list[str] = []
    known = set(names)
    for name in names:
        for target in aliases.get(name, ()):
            if target not in known:
                errors.append(f'missing_target: tokens.json: color.{_label(name)} -> {{{_label(target)}}}')
    state: dict[str, int] = {}
    stack: list[str] = []
    cycles: set[frozenset[str]] = set()

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for target in aliases.get(node, ()):
            if target not in known:
                continue
            if state.get(target) == 1:
                cycle = stack[stack.index(target):]
                if frozenset(cycle) not in cycles:
                    cycles.add(frozenset(cycle))
                    chain = ' -> '.join(_label(c) for c in [*cycle, target])
                    errors.append(f'reference_cycle: tokens.json: color.{_label(target)}: {chain}')
            elif target not in state:
                visit(target)
        stack.pop()
        state[node] = 2

    for name in names:
        if name not in state:
            visit(name)
    depth: dict[str, int] = {}

    def height(node: str, active: frozenset[str]) -> int:
        if node in depth:
            return depth[node]
        best = 0
        for target in aliases.get(node, ()):
            if target in known and target not in active:
                best = max(best, 1 + height(target, active | {node}))
        depth[node] = best
        return best

    deep = {n for n in names if height(n, frozenset()) > MAX_DEPTH}
    targets_of_deep = {t for n in deep for t in aliases.get(n, ())}
    for name in names:
        if name in deep and name not in targets_of_deep:
            errors.append(f'alias_too_deep: tokens.json: color.{_label(name)}: {depth[name]}')
    return errors


def _color_token(name: str, value: object, theme_ids: list[str], errors: list[str], aliases: dict[str, list[str]]) -> None:
    where = f'color.{_label(name)}'
    if isinstance(value, str):
        entries = [('', value)]
    elif isinstance(value, dict):
        entries = []
        for theme, text in value.items():
            if theme not in theme_ids or not isinstance(text, str):
                errors.append(f'invalid_value: tokens.json: {where}@{_label(theme)}')
            else:
                entries.append((f'@{theme}', text))
        if not value:
            errors.append(f'invalid_value: tokens.json: {where}')
    else:
        errors.append(f'invalid_value: tokens.json: {where}')
        return
    for suffix, text in entries:
        kind = _classify_color(text)
        if kind == 'forbidden':
            errors.append(f'forbidden_color_syntax: tokens.json: {where}{_label(suffix)}')
        elif kind == 'invalid':
            errors.append(f'invalid_value: tokens.json: {where}{_label(suffix)}')
        elif kind == 'alias':
            aliases.setdefault(name, []).append(_ALIAS.match(text.strip())[1])


def _validate_type(body: object, root: Path | None, errors: list[str], style_names: dict[str, str]) -> None:
    if not isinstance(body, dict):
        errors.append('token_shape: tokens.json: type')
        return
    families = body.get('families', {})
    if not isinstance(families, dict) or not all(isinstance(v, str) and v.strip() for v in families.values()):
        errors.append('token_shape: tokens.json: type.families')
        families = {}
    for key in families:
        if not NAME_RE.match(key):
            errors.append(f'token_name_invalid: tokens.json: type.families.{_label(key)}')
    fonts = body.get('fonts', [])
    if not isinstance(fonts, list):
        errors.append('token_shape: tokens.json: type.fonts')
    else:
        seen: set[str] = set()
        for i, entry in enumerate(fonts):
            if not isinstance(entry, dict) or ('file' in entry and (not isinstance(entry['file'], str) or not entry['file'])):
                errors.append(f'token_shape: tokens.json: type.fonts[{i}]')
            elif root is not None and 'file' in entry:
                rel = _font_rel(entry['file'])
                if rel not in seen:
                    seen.add(rel)
                    errors.extend(_check_font(root, rel))
    groups = body.get('groups', [])
    if not isinstance(groups, list):
        errors.append('token_shape: tokens.json: type.groups')
        return
    if len(groups) > MAX_GROUPS:
        errors.append(f'limit_exceeded: tokens.json: type.groups: {len(groups)} > {MAX_GROUPS}')
    total = 0
    for gi, group in enumerate(groups):
        if not isinstance(group, dict):
            errors.append(f'token_shape: tokens.json: type.groups[{gi}]')
            continue
        styles = group.get('styles', [])
        if not isinstance(styles, list):
            errors.append(f'token_shape: tokens.json: type.groups[{gi}].styles')
            continue
        for si, style in enumerate(styles):
            total += 1
            if not isinstance(style, dict) or not isinstance(style.get('name'), str):
                errors.append(f'token_shape: tokens.json: type.groups[{gi}].styles[{si}]')
                continue
            name = style['name']
            where = f'type.{_label(name)}'
            if not NAME_RE.match(name):
                errors.append(f'token_name_invalid: tokens.json: {where}')
                continue
            if name in style_names:
                errors.append(f'duplicate_name: tokens.json: {_label(name)}: type, type')
            style_names[name] = 'type'
            family = style.get('family', group.get('family'))
            if (family is not None and (not isinstance(family, str) or (families and family not in families))) or \
                    ('fontSize' in style and not _valid_length(style['fontSize'])) or \
                    ('fontWeight' in style and not _valid_weight(style['fontWeight'])) or \
                    ('lineHeight' in style and not _valid_line_height(style['lineHeight'])):
                errors.append(f'invalid_value: tokens.json: {where}')
    if total > MAX_STYLES:
        errors.append(f'limit_exceeded: tokens.json: type.styles: {total} > {MAX_STYLES}')


def validate_tokens_v3(doc: object, root: Path | None = None) -> list[str]:
    """Check tokens.json against the v3 list grammar; ``root`` (package) enables the font file checks."""
    if not isinstance(doc, dict):
        return ['token_shape: tokens.json: <root>']
    errors: list[str] = []
    if len(doc) > MAX_FAMILIES:
        errors.append(f'limit_exceeded: tokens.json: families: {len(doc)} > {MAX_FAMILIES}')
    theme_ids: list[str] = []
    color_body = doc.get('color')
    if isinstance(color_body, dict):
        themes = color_body.get('themes')
        if not isinstance(themes, list):
            errors.append('token_shape: tokens.json: color.themes')
        else:
            if len(themes) > MAX_THEMES:
                errors.append(f'limit_exceeded: tokens.json: color.themes: {len(themes)} > {MAX_THEMES}')
            for i, theme in enumerate(themes):
                if not isinstance(theme, dict) or not isinstance(theme.get('id'), str):
                    errors.append(f'token_shape: tokens.json: color.themes[{i}]')
                elif not NAME_RE.match(theme['id']):
                    errors.append(f'token_name_invalid: tokens.json: color.themes.{_label(theme["id"])}')
                elif theme['id'] in theme_ids:
                    errors.append(f'duplicate_name: tokens.json: {_label(theme["id"])}: color.themes, color.themes')
                else:
                    theme_ids.append(theme['id'])
    names: dict[str, str] = {}
    style_names: dict[str, str] = {}
    aliases: dict[str, list[str]] = {}
    color_names: list[str] = []
    color_seen: set[str] = set()
    for family, body in doc.items():
        if not isinstance(family, str) or family == 'motion' or not NAME_RE.match(family):
            errors.append(f'unsupported_family: tokens.json: {_label(family)}')
            continue
        if family == 'type':
            _validate_type(body, root, errors, style_names)
            continue
        if not isinstance(body, dict) or not isinstance(body.get('tokens'), list):
            errors.append(f'token_shape: tokens.json: {family}')
            continue
        tokens = body['tokens']
        cap = MAX_COLORS if family == 'color' else MAX_OTHER
        if len(tokens) > cap:
            errors.append(f'limit_exceeded: tokens.json: {family}.tokens: {len(tokens)} > {cap}')
        for i, token in enumerate(tokens):
            if not isinstance(token, dict) or not isinstance(token.get('name'), str) or 'value' not in token:
                errors.append(f'token_shape: tokens.json: {family}[{i}]')
                continue
            name = token['name']
            where = f'{family}.{_label(name)}'
            if not NAME_RE.match(name):
                errors.append(f'token_name_invalid: tokens.json: {where}')
                continue
            if name in names:
                errors.append(f'duplicate_name: tokens.json: {_label(name)}: {names[name]}, {family}')
            else:
                names[name] = family
            usage = token.get('usage')
            if not isinstance(usage, str) or not usage.strip() or len(usage) > 1000:
                errors.append(f'missing_usage: tokens.json: {where}')
            value = token['value']
            if family == 'color':
                if name not in color_seen and len(color_names) < MAX_COLORS:  # beyond the cap is already an error
                    color_seen.add(name)
                    color_names.append(name)
                _color_token(name, value, theme_ids, errors, aliases)
            elif family in {'spacing', 'radius'}:
                if not _valid_length(value):
                    errors.append(f'invalid_value: tokens.json: {where}')
            elif not (_is_number(value) or (isinstance(value, str) and value.strip())):
                errors.append(f'invalid_value: tokens.json: {where}')
    errors.extend(_alias_errors(aliases, color_names))
    return errors


def token_warnings(doc: object) -> list[str]:
    """Warnings for tokens.json: a text style without ``usage``."""
    groups = doc.get('type', {}).get('groups') if isinstance(doc, dict) and isinstance(doc.get('type'), dict) else None
    out: list[str] = []
    for group in groups if isinstance(groups, list) else []:
        for style in group.get('styles', []) if isinstance(group, dict) and isinstance(group.get('styles'), list) else []:
            if isinstance(style, dict) and isinstance(style.get('name'), str) and \
                    (not isinstance(style.get('usage'), str) or not style['usage'].strip()):
                out.append(f'missing_usage: tokens.json: type.{_label(style["name"])}')
    return out


def _token_names(doc: object) -> set[str]:
    names: set[str] = set()
    if isinstance(doc, dict):
        for family, body in doc.items():
            if family != 'type' and isinstance(body, dict) and isinstance(body.get('tokens'), list):
                names.update(t['name'] for t in body['tokens'] if isinstance(t, dict) and isinstance(t.get('name'), str))
    return names


def _style_count(doc: dict) -> int:
    groups = doc.get('type', {}).get('groups') if isinstance(doc.get('type'), dict) else None
    return sum(len(g['styles']) for g in groups if isinstance(g, dict) and isinstance(g.get('styles'), list)) if isinstance(groups, list) else 0


def check_minimal_profile(tokens: object) -> list[str]:
    """Counts the ``minimal`` profile demands; the README and component rules live elsewhere."""
    if not isinstance(tokens, dict):
        return []
    def count(family: str) -> int:
        body = tokens.get(family)
        return len(body['tokens']) if isinstance(body, dict) and isinstance(body.get('tokens'), list) else 0
    themes = tokens.get('color', {}).get('themes') if isinstance(tokens.get('color'), dict) else None
    out = []
    if not 6 <= count('color') <= 10:
        out.append(f'minimal_profile_violation: tokens.json: color: {count("color")} not in 6..10')
    if not isinstance(themes, list) or len(themes) != 1:
        out.append(f'minimal_profile_violation: tokens.json: themes: {len(themes) if isinstance(themes, list) else 0} != 1')
    if not 5 <= _style_count(tokens) <= 7:
        out.append(f'minimal_profile_violation: tokens.json: text styles: {_style_count(tokens)} not in 5..7')
    if count('spacing') != 4:
        out.append(f'minimal_profile_violation: tokens.json: spacing: {count("spacing")} != 4')
    if count('radius') != 3:
        out.append(f'minimal_profile_violation: tokens.json: radius: {count("radius")} != 3')
    return out


# --------------------------------------------------------------------------- contrast

def _resolve_color(tokens: dict[str, dict], theme_ids: list, name: str, theme: object, seen: tuple[str, ...] = ()) -> tuple[str, str]:
    token = tokens.get(name)
    if token is None or name in seen or len(seen) > MAX_DEPTH:
        raise ValueError('unresolved')
    value = _theme_value(token, theme_ids, theme)
    if value is None:
        raise ValueError('unresolved')
    alias = _ALIAS.match(value.strip())
    if alias:
        return _resolve_color(tokens, theme_ids, alias[1], theme, (*seen, name))
    return value, name


def check_contrast(tokens: dict, pairs: object) -> tuple[list[str], list[str]]:
    """Measure each declared pair in every theme; return (errors, warnings)."""
    where = 'canonical-map.json: checks.contrast'
    if not isinstance(pairs, list) or not pairs:
        return [], [f'contrast_unchecked: {where}']
    errors: list[str] = []
    warnings: list[str] = []
    color = tokens.get('color') if isinstance(tokens, dict) and isinstance(tokens.get('color'), dict) else {}
    by_name = {t['name']: t for t in color.get('tokens', []) if isinstance(t, dict) and isinstance(t.get('name'), str)} \
        if isinstance(color.get('tokens'), list) else {}
    theme_ids = [t['id'] for t in color.get('themes', []) if isinstance(t, dict) and isinstance(t.get('id'), str)] \
        if isinstance(color.get('themes'), list) else []
    themes: list = theme_ids or [None]
    reported: set[str] = set()
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            errors.append(f'invalid_manifest: {where}[{index}]')
            continue
        problems = len(errors)
        for side in ('fg', 'bg'):
            name = pair.get(side)
            if not isinstance(name, str) or not name:
                errors.append(f'invalid_manifest: {where}[{index}].{side}')
            elif name not in by_name:
                errors.append(f'invalid_manifest: {where}[{index}].{side}: unknown token {_label(name)}')
        if 'min' in pair and (not _is_number(pair['min']) or pair['min'] <= 0):
            errors.append(f'invalid_manifest: {where}[{index}].min')
        if 'large' in pair and not isinstance(pair['large'], bool):
            errors.append(f'invalid_manifest: {where}[{index}].large')
        if len(errors) > problems:
            continue
        minimum = float(pair['min']) if 'min' in pair else (3.0 if pair.get('large') else 4.5)
        for theme in themes:
            suffix = f'@{theme}' if theme is not None else ''
            try:
                fg, _owner = _resolve_color(by_name, theme_ids, pair['fg'], theme)
                bg, _owner = _resolve_color(by_name, theme_ids, pair['bg'], theme)
                ratio = contrast_ratio(fg, bg)
            except ValueError as exc:
                if str(exc) == 'unsupported_space':
                    for owner in _unsupported_owners(by_name, theme_ids, pair, theme):
                        if owner not in reported:
                            reported.add(owner)
                            warnings.append(f'contrast_unsupported_space: tokens.json: color.{_label(owner)}{suffix}')
                continue
            if ratio < minimum - 1e-9:
                shown = f'{ratio:.2f}'
                if float(shown) >= minimum:
                    shown = f'{ratio:.3f}'
                errors.append(f'contrast_below_min: {where}[{index}]{suffix}: {shown} < {minimum}')
    return errors, warnings


def _unsupported_owners(by_name: dict, theme_ids: list, pair: dict, theme: object) -> list[str]:
    """Tokens of a pair whose resolved colour cannot be converted to sRGB."""
    owners = []
    for side in ('fg', 'bg'):
        try:
            value, owner = _resolve_color(by_name, theme_ids, pair[side], theme)
            parse_color(value)
        except ValueError as exc:
            if str(exc) == 'unsupported_space':
                owners.append(owner)
    return owners


# --------------------------------------------------------------------------- index and canonical map

def validate_index(doc: object) -> list[str]:
    """Check design-system.json; a format version other than 3 stops all further checks."""
    name = 'design-system.json'
    if not isinstance(doc, dict):
        return [f'invalid_index_value: {name}: <root>']
    if 'v' not in doc:
        return [f'missing_index_key: {name}: v']
    if type(doc['v']) is not int or doc['v'] != FORMAT_VERSION:
        return [f'unsupported_format_version: {name}: v: {_label(doc["v"])}']
    errors = []
    for key in ('layout', 'title', 'namespace'):
        if key not in doc:
            errors.append(f'missing_index_key: {name}: {key}')
    if 'layout' in doc and doc['layout'] != 'files':
        errors.append(f'invalid_index_value: {name}: layout')
    if 'title' in doc and (not isinstance(doc['title'], str) or not doc['title'].strip()):
        errors.append(f'invalid_index_value: {name}: title')
    if 'namespace' in doc and (not isinstance(doc['namespace'], str) or not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', doc['namespace'])):
        errors.append(f'invalid_index_value: {name}: namespace')
    if 'createdOnFiles' in doc:
        marker = doc['createdOnFiles']
        if not isinstance(marker, dict):
            errors.append(f'invalid_index_value: {name}: createdOnFiles')
        else:
            if marker.get('v') != 1 or isinstance(marker.get('v'), bool):
                errors.append(f'invalid_index_value: {name}: createdOnFiles.v')
            at = marker.get('at')
            try:
                if not isinstance(at, str):
                    raise ValueError
                datetime.fromisoformat(at)
            except ValueError:
                errors.append(f'invalid_index_value: {name}: createdOnFiles.at')
    return errors


def _check_path(base: Path, relative: str, label: str, errors: list[str]) -> None:
    try:
        if not safe_path(base, relative).exists():
            errors.append(f'missing_path: canonical-map.json: {label}')
    except (ValueError, OSError, RuntimeError):
        errors.append(f'invalid_path: canonical-map.json: {label}')


def validate_canonical_map(doc: object, package_root: Path) -> list[str]:
    """Check canonical-map.json; ``file`` paths are relative to the package, ``repo-path`` to its parent folder."""
    name = 'canonical-map.json'
    if not isinstance(doc, dict):
        return [f'invalid_manifest: {name}: expected object']
    errors: list[str] = []
    system = doc.get('system')
    if doc.get('schemaVersion') != '1' or not isinstance(system, dict) or not all(
            isinstance(system.get(key), str) and system[key] for key in ('id', 'version', 'status')):
        errors.append(f'invalid_manifest: {name}: schemaVersion/system')
    elif system['status'] not in STATUSES:
        errors.append(f'invalid_status: {name}: system')
    if doc.get('profile') is not None and doc['profile'] not in PROFILES:
        errors.append(f'invalid_manifest: {name}: profile')
    canonical = doc.get('canonical')
    if not isinstance(canonical, dict) or not canonical:
        errors.append(f'invalid_manifest: {name}: canonical')
    else:
        for domain, source in canonical.items():
            label = f'canonical.{_label(domain)}'
            if not isinstance(domain, str) or not domain or not isinstance(source, dict):
                errors.append(f'invalid_canonical: {name}: {label}')
            elif source.get('kind') == 'external':
                if 'path' in source or not external_url(source.get('url')):
                    errors.append(f'invalid_external: {name}: {label}')
            elif source.get('kind') not in ('file', 'repo-path') or not isinstance(source.get('path'), str) or 'url' in source:
                errors.append(f'invalid_canonical: {name}: {label}')
            else:
                base = package_root if source['kind'] == 'file' else package_root.parent
                _check_path(base, source['path'], f'{label}.path', errors)
    components = doc.get('components')
    if components is not None:
        if not isinstance(components, dict):
            errors.append(f'invalid_manifest: {name}: components')
        else:
            for comp, entry in components.items():
                label = f'components.{_label(comp)}'
                source = entry.get('source') if isinstance(entry, dict) else None
                if not isinstance(source, str) or not source:
                    errors.append(f'invalid_manifest: {name}: {label}')
                elif re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://', source):
                    if not external_url(source):
                        errors.append(f'invalid_external: {name}: {label}.source')
                else:
                    _check_path(package_root.parent, source, f'{label}.source', errors)
    checks = doc.get('checks')
    if checks is not None:
        if not isinstance(checks, dict):
            errors.append(f'invalid_manifest: {name}: checks')
        elif 'contrast' in checks and not isinstance(checks['contrast'], list):
            errors.append(f'invalid_manifest: {name}: checks.contrast')
    decisions = doc.get('decisions')
    if decisions is not None:
        if not isinstance(decisions, list):
            errors.append(f'invalid_manifest: {name}: decisions')
        else:
            ids: set[str] = set()
            for item in decisions:
                if isinstance(item, dict) and 'id' in item:
                    if not isinstance(item['id'], str) or not item['id'] or item['id'] in ids:
                        errors.append(f'invalid_id: {name}: decisions')
                    else:
                        ids.add(item['id'])
    return errors


# --------------------------------------------------------------------------- Markdown helpers

_FENCE = re.compile(r'^\s*(```|~~~)')


def _atx(line: str) -> tuple[int, str] | None:
    """(level, text) of an ATX heading line such as ``## Name ##``, else None; one pass, no backtracking."""
    if not line.startswith('#'):
        return None
    level = len(line) - len(line.lstrip('#'))
    if level > 6 or level == len(line) or line[level] not in ' \t':
        return None
    rest = line[level:]
    body = rest.lstrip(' \t')
    if not body:
        return (level, '') if len(rest) > 1 else None
    text = body.rstrip(' \t').rstrip('#').rstrip(' \t')
    return level, (text or body[0]).strip()


def _headings(text: str) -> list[tuple[int, str]]:
    """ATX headings outside fenced code, as (level, text)."""
    out = []
    fenced = False
    for line in text.replace('\r\n', '\n').split('\n'):
        if _FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            heading = _atx(line)
            if heading:
                out.append(heading)
    return out


def _strip_fences(text: str) -> str:
    kept = []
    fenced = False
    for line in text.replace('\r\n', '\n').split('\n'):
        if _FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            kept.append(line)
    return '\n'.join(kept)


def validate_readme(text: str, size: int, profile: str, token_names: set[str], title: str | None = None) -> tuple[list[str], list[str]]:
    """README.md rules; ``title`` (the index title) enables the repeated level-1 heading check. Only the first CAP_README characters are scanned."""
    errors: list[str] = []
    warnings: list[str] = []
    text = text[:CAP_README]
    if size > CAP_README:
        errors.append(f'readme_too_large: README.md: {size} > {CAP_README}')
    headings = _headings(text)
    for level, heading in headings:
        if heading.casefold() in {'provenance', 'next steps'}:
            errors.append(f'readme_forbidden_section: README.md: {_label(heading)}')
        if level == 1 and title and heading.casefold() == title.strip().casefold():
            errors.append(f'readme_forbidden_section: README.md: # {_label(heading)}')
    if profile == 'minimal':
        paragraphs: list[str] = []
        current: list[str] = []
        for line in _strip_fences(text).split('\n'):
            if _atx(line) is not None:
                continue
            if line.strip():
                current.append(line)
            elif current:
                paragraphs.append(' '.join(' '.join(current).split()))
                current = []
        if current:
            paragraphs.append(' '.join(' '.join(current).split()))
        if len(paragraphs) > 1:
            errors.append(f'minimal_profile_violation: README.md: {len(paragraphs)} paragraphs, expected 1')
        else:
            length = len(paragraphs[0]) if paragraphs else 0
            if length < 80:
                errors.append(f'minimal_profile_violation: README.md: paragraph {length} < 80 characters')
    else:
        present = {h.casefold() for level, h in headings if level == 2}
        for required in ('Content fundamentals', 'Visual foundations', 'Iconography'):
            if required.casefold() not in present:
                errors.append(f'readme_missing_section: README.md: {required}')
    seen: set[str] = set()
    unknown: list[str] = []
    for span in re.findall(r'`([^`\n]+)`', _strip_fences(text)):
        if span in seen:
            continue
        seen.add(span)
        if re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', span) and re.search(r'[-_0-9]', span) and span not in token_names:
            unknown.append(span)
    warnings.extend(f'readme_unknown_token: README.md: {_label(s)}' for s in unknown)
    return errors, warnings


# --------------------------------------------------------------------------- previews

_MARKER = re.compile(r'^﻿?\s*<!--\s*@dsCard\b([^>]*?)-->')
_URL = re.compile(r'https?://[^\s"\'<>`)]+', re.IGNORECASE)
_EXACT_VERSION = r'\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.+-]+)?'
# A dotted version anywhere in a path. Anchored at the start of a digit run so each start position costs one run, not a quadratic rescan.
_SEMVER_IN_PATH = re.compile(r'(?<!\d)\d+\.\d+\.\d+')
_PACKAGE_CDNS = {'cdn.jsdelivr.net', 'unpkg.com', 'esm.sh', 'cdn.skypack.dev'}
_VERSIONED_CDNS = {'cdnjs.cloudflare.com', 'cdn.tailwindcss.com', 'code.jquery.com', 'ajax.googleapis.com',
                   'stackpath.bootstrapcdn.com', 'maxcdn.bootstrapcdn.com', 'cdn.datatables.net'}


def _marker(text: str) -> re.Match | None:
    return _MARKER.match(text.split('\n', 1)[0])


def is_template_preview(text: str) -> bool:
    """A preview whose marker carries ``page`` and ``group="Templates"``."""
    match = _marker(text)
    return bool(match) and bool(re.search(r'\bpage\b', match[1])) and bool(re.search(r'''group\s*=\s*["']Templates["']''', match[1]))


def _unpinned(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or '').lower()
    segments = [s for s in parts.path.split('/') if s]
    if host in _PACKAGE_CDNS:
        kind = ''
        if host == 'cdn.jsdelivr.net' and segments and segments[0] in {'npm', 'gh'}:
            kind, segments = segments[0], segments[1:]
        if kind == 'gh':
            name = segments[1] if len(segments) > 1 else ''
        elif segments and segments[0].startswith('@'):
            name = segments[1] if len(segments) > 1 else ''
        else:
            name = segments[0] if segments else ''
        if '@' not in name:
            return True
        return not re.fullmatch(_EXACT_VERSION, name.rsplit('@', 1)[1])
    if host in _VERSIONED_CDNS:
        return not _SEMVER_IN_PATH.search(parts.path)
    return False


def validate_preview(text: str, rel: str, size: int | None = None) -> list[str]:
    """Marker on line 1, size cap, no embedding tags, CDN urls pinned to an exact version.

    ``size`` is the byte size of the whole file when ``text`` holds only its first CAP_PREVIEW bytes; only that much is scanned.
    """
    errors = []
    if not _marker(text):
        errors.append(f'card_marker_missing: {_label(rel)}')
    if size is None:
        size = len(text.encode('utf-8'))
    text = text[:CAP_PREVIEW]
    if size > CAP_PREVIEW:
        errors.append(f'preview_too_large: {_label(rel)}: {size} > {CAP_PREVIEW}')
    for tag in FORBIDDEN_TAGS:
        if re.search(rf'<\s*{tag}\b', text, re.IGNORECASE):
            errors.append(f'forbidden_tag: {_label(rel)}: {tag}')
    seen: set[str] = set()
    for url in _URL.findall(text):
        if url not in seen and _unpinned(url):
            seen.add(url)
            errors.append(f'unpinned_cdn: {_label(rel)}: {_label(url)}')
    return errors


def preview_warnings(text: str, rel: str) -> list[str]:
    match = _marker(text)
    height = re.search(r'\bheight\s*=\s*"?(\d+)', match[1]) if match else None
    if not height:
        return []
    low, high = (240, 360) if rel == 'components/Cover/preview.html' else (40, 4000)
    return [] if low <= int(height[1]) <= high else [f'card_marker_height: {_label(rel)}: {height[1]}']


# --------------------------------------------------------------------------- DESIGN.md

_REF = re.compile(r'\{(colors|typography|rounded|spacing)\.[A-Za-z0-9_.-]+\}')


def _front_matter_split(text: str) -> tuple[str, str]:
    """(front matter block including both fences, body); the block is empty when absent."""
    lines = text.replace('\r\n', '\n').lstrip('﻿').split('\n')
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                return '\n'.join(lines[:i + 1]), '\n'.join(lines[i + 1:])
    return '', '\n'.join(lines)


def _section_lines(body: str, name: str) -> list[str]:
    inside, fenced, lines = False, False, []
    for line in body.split('\n'):
        if _FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            heading = _atx(line)
            if heading and heading[0] == 2:
                inside = heading[1] == name
                continue
        if inside:
            lines.append(line)
    return lines


def _labelled(line: str, label: str) -> bool:
    """True when ``line`` reads ``[-*] [**]Label[**]:`` in any letter case; one pass, no backtracking."""
    text = line.lstrip()
    for start in (text, text[1:] if text[:1] in ('-', '*') else None):
        if start is None:
            continue
        start = start.lstrip().lstrip('*')
        if start[:len(label)].casefold() == label.casefold() and start[len(label):].lstrip('*').lstrip().startswith(':'):
            return True
    return False


def validate_design_md_structure(text: str) -> list[str]:
    """Eight level-2 sections in order, and the three Overview lines. Only the first CAP_KEPT characters are scanned."""
    _front, body = _front_matter_split(text[:CAP_KEPT])
    found = [h for level, h in _headings(body) if level == 2 and h in SECTION_NAMES]
    errors = [f'design_md_section_missing: DESIGN.md: {name}' for name in SECTION_NAMES if name not in found]
    if not errors:
        repeated = [n for n in SECTION_NAMES if found.count(n) > 1]
        if repeated:
            errors.extend(f'design_md_section_order: DESIGN.md: {n} repeated' for n in repeated)
        else:
            for before, after in zip(found, found[1:]):
                if SECTION_NAMES.index(before) > SECTION_NAMES.index(after):
                    errors.append(f'design_md_section_order: DESIGN.md: {before} before {after}')
                    break
    if 'Overview' in found:
        overview = _section_lines(body, 'Overview')
        for label in OVERVIEW_LINES:
            if not any(_labelled(line, label) for line in overview):
                errors.append(f'design_md_overview_incomplete: DESIGN.md: {label}')
    return errors


def design_md_token_keys(tokens: object) -> set[str]:
    """The ``{group}.{key}`` names the DESIGN.md front matter carries for these tokens."""
    keys: set[str] = set()
    if not isinstance(tokens, dict):
        return keys
    for family, group in (('color', 'colors'), ('radius', 'rounded'), ('spacing', 'spacing')):
        body = tokens.get(family)
        if isinstance(body, dict) and isinstance(body.get('tokens'), list):
            keys.update(f'{group}.{t["name"]}' for t in body['tokens'] if isinstance(t, dict) and isinstance(t.get('name'), str))
    type_body = tokens.get('type')
    groups = type_body.get('groups') if isinstance(type_body, dict) else None
    for entry in groups if isinstance(groups, list) else []:
        styles = entry.get('styles') if isinstance(entry, dict) else None
        keys.update(f'typography.{s["name"]}' for s in styles if isinstance(s, dict) and isinstance(s.get('name'), str)) \
            if isinstance(styles, list) else None
    return keys


def check_design_md_refs(text: str, keys: set[str]) -> list[str]:
    """References in the body (outside fenced code) that name a key the front matter lacks."""
    _front, body = _front_matter_split(text[:CAP_KEPT])
    errors: list[str] = []
    reported: set[str] = set()
    for match in _REF.finditer(_strip_fences(body)):
        reference = match[0]
        if reference[1:-1] not in keys and reference not in reported:
            reported.add(reference)
            errors.append(f'design_md_broken_ref: DESIGN.md: {reference}')
    return errors


# --------------------------------------------------------------------------- paths

def _refused(path: str) -> bool:
    parts = path.split('/')
    low = [p.casefold() for p in parts]
    if low[-1] in REFUSED_FILES or 'node_modules' in low or 'artifact-type' in low:
        return True
    if any((p.startswith('.') and p != '.image-slots.state.json') or SHORT_NAME.search(p) for p in parts):
        return True
    if low[-1] == 'index.html' and (len(parts) == 1 or (len(parts) == 3 and low[0] == 'components')):
        return True
    return low[-1] == 'design-system.json' and len(parts) > 1


def _generated(path: str) -> bool:
    parts = [p.casefold() for p in path.split('/')]
    return (len(parts) == 1 and parts[0] in GENERATED_ROOT_FILES) or parts[0] in GENERATED_ROOT_DIRS


def check_refused(paths: list[str]) -> list[str]:
    """Paths Claude Design refuses and files the page writes itself; names only, nothing is opened."""
    out = []
    for path in paths:
        if _refused(path):
            out.append(f'refused_path: {_label(path)}')
        elif _generated(path):
            out.append(f'generated_file_present: {_label(path)}')
    return out


def check_layout(paths: list[str]) -> list[str]:
    """Warnings from names alone: section budget, legacy folders, nested index.html."""
    out = []
    sections = sorted(p for p in paths if p.casefold().endswith(('.md', '.mdx')) and p != 'README.md'
                      and not p.startswith(('components/', 'archived/')))
    if len(sections) > MAX_SECTIONS:
        out.append(f'sections_over_limit: {len(sections)} > {MAX_SECTIONS}: ' + ', '.join(_label(p) for p in sections))
    firsts = {p.split('/')[0] for p in paths}
    out.extend(f'legacy_layout_dir: {name}' for name in LEGACY_DIRS if name in firsts)
    for path in paths:
        parts = path.split('/')
        if parts[-1].casefold() == 'index.html' and not (len(parts) == 1 or (len(parts) == 3 and parts[0].casefold() == 'components')):
            out.append(f'index_html_nested: {_label(path)}')
    return out


def has_bundle(root: Path) -> bool:
    """True when components/ holds a platform bundle, a declaration index or a lib folder."""
    try:
        with os.scandir(Path(root) / 'components') as entries:
            return any(e.name.startswith('bundle.') or e.name == 'index.d.ts' or (e.name == 'lib' and e.is_dir()) for e in entries)
    except OSError:
        return False


def pass_line(warnings: list[str], bundle: bool = False) -> str:
    extra = []
    if any(w.startswith(('contrast_unchecked', 'contrast_unsupported_space')) for w in warnings):
        extra.append('contrast')
    if bundle:
        extra.append('bundle')
    return (f'PASS: structural checks only; Claude Design format v{FORMAT_VERSION} pinned {FORMAT_READ_ON} (research preview); '
            f'unchecked: {", ".join((*UNCHECKED, *extra))}')


# --------------------------------------------------------------------------- viewer.html

CAP_VIEWER, WARN_VIEWER = 512_000, 300_000
_V_FLAGS = re.IGNORECASE | re.ASCII  # ASCII only: U+017F must not read as an ``s`` and U+0130 must not change a length
_V_RAW_OPEN = re.compile(r'<(script|style)(?=[\s/>])[^<>]*>|<!--', _V_FLAGS)
_V_RAW_CLOSE = {'script': re.compile(r'</script(?=[\s/>])', _V_FLAGS), 'style': re.compile(r'</style(?=[\s/>])', _V_FLAGS),
                'comment': re.compile(r'--!?>')}
_V_TAG = re.compile(r'<([A-Za-z][A-Za-z0-9:-]*)(?=[\s/>])([^<>]*)>', _V_FLAGS)
_V_ATTR = re.compile(r'''([^\s"'<>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'<>]+)))?''')
_V_FORBIDDEN_TAG = re.compile(r'<(iframe|frameset|frame|object|embed|portal|form|base|applet)(?=[\s/>]|$)', _V_FLAGS)
_V_TITLE = re.compile(r'<title(?=[\s/>])[^<>]*>\s*[^<\s]', _V_FLAGS)
_V_HANDLER = re.compile(r'''[\s"'/]on[a-z]+\s*=''', _V_FLAGS)
_V_URL_CALL = re.compile(r'url\(', _V_FLAGS)
_V_IMPORT = re.compile(r'@import\b', _V_FLAGS)
_V_SCHEME = re.compile(r'[a-z][a-z0-9+.-]*:')
_V_LOAD_ATTRS = ('src', 'srcset', 'href', 'xlink:href', 'poster', 'action', 'formaction', 'ping', 'background', 'data')
_V_API = (
    ('fetch', re.compile(r'\bfetch\b')), ('XMLHttpRequest', re.compile(r'\bXMLHttpRequest\b')),
    ('import(', re.compile(r'\bimport\s*\(')), ('importScripts', re.compile(r'\bimportScripts\b')),
    ('eval(', re.compile(r'\beval\s*\(')), ('new Function', re.compile(r'\bnew\s+Function\b')),
    ('WebSocket', re.compile(r'\bWebSocket\b')), ('EventSource', re.compile(r'\bEventSource\b')),
    ('serviceWorker', re.compile(r'\bserviceWorker\b')), ('sendBeacon', re.compile(r'\bsendBeacon\b')),
    ('new Worker', re.compile(r'\bnew\s+(?:Shared)?Worker\b')), ('window.open', re.compile(r'\bwindow\s*\.\s*open\b')),
    ('document.write', re.compile(r'\bdocument\s*\.\s*write(?:ln)?\b')),
)
# Machine-local traces a published page must not carry. Each pattern is spelled so that its own source line holds none of them.
# Both spellings of a Windows profile path count, a macOS home folder (case matters: a lower-case API route is no trace and a
# folder named ``Users`` inside the package, or the tail of a Windows path, is preceded by a name character or a colon), and a network share.
_V_LEAKS = (('user profile path', re.compile(r'c:[\\/]users', _V_FLAGS)), ('home path', re.compile(r'/home/', _V_FLAGS)),
            ('home path', re.compile(r'(?<![\w.:-])/Us' + r'ers/[\w.-]', re.ASCII)),
            ('file URL', re.compile(r'file:/{3}', _V_FLAGS)), ('local host name', re.compile(r'local' + 'host', _V_FLAGS)),
            ('loopback address', re.compile(r'127\.0\.0\.1')), ('workstation folder', re.compile(r'[.]opc' + 'os', _V_FLAGS)),
            ('network share path', re.compile(r'\\\\[\w.-]+\\[\w$.-]', re.ASCII)))
_V_LEAD = ''.join(map(chr, range(33)))


def eol_lf(value):
    """``value`` (text or bytes) with every CRLF and every lone CR turned into LF: a file saved with other line ends is the same file.

    The staleness checks of DESIGN.md and viewer.html and the build command match files through this, on both sides."""
    if isinstance(value, bytes):
        return value.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    return value.replace('\r\n', '\n').replace('\r', '\n')


def _split_raw_text(text: str) -> tuple[str, list[str], list[str]]:
    """(markup without script bodies, style bodies and comments, script bodies, style bodies).

    One pass; each search resumes where the last one ended. A comment is inert, so a tag written inside one does not count
    (a policy meta in a comment is no policy); one that never closes runs to the end of the page, as in a browser."""
    markup: list[str] = []
    bodies: dict[str, list[str]] = {'script': [], 'style': []}
    pos = 0
    while True:
        opened = _V_RAW_OPEN.search(text, pos)
        if not opened:
            markup.append(text[pos:])
            break
        name = opened[1].lower() if opened[1] else 'comment'
        if name == 'comment':
            markup.append(text[pos:opened.start()])
            body_start = opened.end()
            if text.startswith('>', body_start) or text.startswith('->', body_start):  # ``<!-->`` and ``<!--->`` are empty comments
                pos = body_start + (1 if text.startswith('>', body_start) else 2)
                continue
            closed = _V_RAW_CLOSE['comment'].search(text, body_start)
            if not closed:
                break
            pos = closed.end()
            continue
        markup.append(text[pos:opened.end()])
        closed = _V_RAW_CLOSE[name].search(text, opened.end())
        bodies[name].append(text[opened.end():closed.start() if closed else len(text)])
        if not closed:
            break
        pos = closed.start()
    return ''.join(markup), bodies['script'], bodies['style']


def _tag_attrs(body: str) -> dict[str, str]:
    """Attribute name (lower case) to raw value for one tag body; the first spelling of a name wins, as in a browser."""
    found: dict[str, str] = {}
    for m in _V_ATTR.finditer(body):
        name = m[1].lower()
        if name not in found:
            found[name] = m[2] if m[2] is not None else m[3] if m[3] is not None else (m[4] or '')
    return found


def _outside(value: str, allow_data: bool = False) -> bool:
    """True when an attribute value or a ``url()`` target leaves the page: a scheme, a leading slash or backslash, ``http:`` anywhere.

    Entities are undone first (a browser does), tabs and line ends inside are dropped, leading control characters and spaces too.
    Only the first 2000 characters are looked at, so the cost is bounded by the text, never by one huge value."""
    probe = html.unescape(value[:2000]).replace('\t', '').replace('\r', '').replace('\n', '').lstrip(_V_LEAD).lower()
    if not probe or probe.startswith('#'):
        return False
    if allow_data and probe.startswith('data:image/'):
        return False
    return probe[0] in '/\\' or bool(_V_SCHEME.match(probe)) or 'http:' in probe or 'https:' in probe


def _url_targets(css: str):
    """The start of every ``url(...)`` target in a piece of CSS (quotes and spaces dropped); 80 characters are enough to classify."""
    for m in _V_URL_CALL.finditer(css):
        yield css[m.end():m.end() + 80].lstrip(' \t\r\n\f"\'')


def _expected_counts(data: dict) -> dict[str, int]:
    from design_system_build import count_tokens  # late: that module imports this one
    return {'data-token': count_tokens(data.get('tokens')),
            'data-component': len(data['components']) if isinstance(data.get('components'), list) else 0,
            'data-asset': len(data['assets']) if isinstance(data.get('assets'), list) else 0}


def validate_viewer(text: str, size: int, data: dict) -> tuple[list[str], list[str]]:
    """Check a ``viewer.html`` page: (errors, warnings). ``text`` is the page (at most CAP_VIEWER bytes of it), ``size`` its byte size,
    ``data`` what ``collect_package`` returned for the package; the coverage counts come from it and an empty ``data`` skips that check.

    Regex on the string only, no HTML parser. Every scan runs once over the text or over a bounded slice and none nests a
    quantifier, so the cost grows linearly with the size of the page."""
    errors: list[str] = []
    warnings: list[str] = []

    def err(code: str, detail: str = '') -> None:
        line = f'{code}: viewer.html' + (f': {detail}' if detail else '')
        if line not in errors:
            errors.append(line)

    if size > CAP_VIEWER:
        errors.append(f'viewer_too_large: viewer.html: {size} > {CAP_VIEWER}')
    elif size > WARN_VIEWER:
        warnings.append(f'viewer_large: viewer.html: {size} > {WARN_VIEWER}')
    text = text if isinstance(text, str) else ''
    markup, scripts, styles = _split_raw_text(text)

    forbidden = [m[1].lower() for m in _V_FORBIDDEN_TAG.finditer(markup)]
    external = csp = lang = img_without_alt = False
    h1 = 0
    for tag in _V_TAG.finditer(markup):
        name = tag[1].lower()
        attrs = _tag_attrs(tag[2])
        if name == 'h1':
            h1 += 1
        elif name == 'link' and 'stylesheet' in attrs.get('rel', '').lower().split():
            forbidden.append('link rel=stylesheet')
        elif name == 'meta':
            equiv = attrs.get('http-equiv', '').strip().lower()
            if equiv == 'refresh':
                forbidden.append('meta refresh')
            elif equiv == 'content-security-policy' and "default-src 'none'" in attrs.get('content', '').lower():
                csp = True
        elif name == 'html' and attrs.get('lang', '').strip():
            lang = True
        elif name == 'img' and 'alt' not in attrs:
            img_without_alt = True
        for attr, value in attrs.items():
            if attr in _V_LOAD_ATTRS and _outside(value, allow_data=attr == 'src'):
                external = True
            elif 'url(' in value[:100_000].lower() and any(_outside(t, allow_data=True) for t in _url_targets(html.unescape(value[:100_000]))):
                external = True
    if any(_V_IMPORT.search(body) or any(_outside(t, allow_data=True) for t in _url_targets(body)) for body in styles):
        external = True
    if external:
        err('viewer_external_ref', 'src/href/url() leaves the page')
    for name in dict.fromkeys(forbidden):
        err('viewer_forbidden_tag', name)
    if _V_HANDLER.search(markup):
        err('viewer_inline_handler', 'on* attribute')
    for label, pattern in _V_API:
        if any(pattern.search(body) for body in scripts):
            err('viewer_forbidden_api', label)
    if not csp:
        err('viewer_missing_csp')
    if not lang:
        err('viewer_a11y', 'lang missing')
    if not _V_TITLE.search(markup):
        err('viewer_a11y', 'title missing')
    if h1 != 1:
        err('viewer_a11y', f'h1 count {h1}')
    if img_without_alt:
        err('viewer_a11y', 'img alt missing')
    if isinstance(data, dict) and data:
        for attribute, expected in _expected_counts(data).items():
            found = len(re.findall(r'(?<![\w-])' + attribute + r'\s*=', markup))
            if found != expected:
                err('viewer_coverage', f'{attribute} {found} != {expected}')
    unescaped = html.unescape(text)  # the generator writes ``:`` before two slashes as a reference; a browser (and a reader) sees the URL
    for label, pattern in _V_LEAKS:
        if pattern.search(text) or pattern.search(unescaped):
            err('viewer_leak', label)
    return errors, warnings


# --------------------------------------------------------------------------- package

def _no_descend(name: str, top: bool) -> bool:
    return (name.startswith('.') or name.casefold() in {'node_modules', 'artifact-type'} or bool(SHORT_NAME.search(name))
            or bool(SENSITIVE.search(name)) or name != name.rstrip(' .') or (top and name.casefold() in GENERATED_ROOT_DIRS))


def _is_link(entry: os.DirEntry) -> bool:
    return entry.is_symlink() or (hasattr(entry, 'is_junction') and entry.is_junction())


def _walk(root: Path) -> tuple[list[str], dict[str, int], set[str], list[str]]:
    """Names of everything under root (entries), file sizes, directory names, linked entries; flagged folders are listed, not entered."""
    entries: list[str] = []
    files: dict[str, int] = {}
    dirs: set[str] = set()
    links: list[str] = []

    def visit(directory: str, prefix: str, depth: int) -> None:
        try:
            with os.scandir(directory) as scan:
                items = sorted(scan, key=lambda e: e.name)
        except OSError:
            return
        for entry in items:
            rel = prefix + entry.name
            entries.append(rel)
            if _is_link(entry):
                links.append(rel)
            elif entry.is_dir(follow_symlinks=False):
                dirs.add(rel)
                if depth < 32 and not _no_descend(entry.name, not prefix):
                    visit(entry.path, rel + '/', depth + 1)
            elif entry.is_file(follow_symlinks=False):
                files[rel] = entry.stat(follow_symlinks=False).st_size

    visit(str(root), '', 0)
    return entries, files, dirs, links


_FAIL = object()


def _stored_size(rel: str, raw: int) -> int:
    return raw if Path(rel).suffix.casefold() in TEXT_SUFFIXES else 4 * math.ceil(raw / 3)


def verify_package(root: Path, profile: str | None = None) -> tuple[list[str], list[str]]:
    """Verify a design-system package folder; return (errors, warnings). Reads only after the path checks pass."""
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    reported: set[str] = set()

    def err(line: str) -> None:
        if line not in reported:
            reported.add(line)
            errors.append(line)

    def read(rel: str, cap: int) -> bytes | None:
        """At most cap + 1 bytes: one byte past the cap is enough to know the file is too large."""
        try:
            with safe_path(root, rel).open('rb') as handle:
                return handle.read(cap + 1)
        except (ValueError, RuntimeError):
            err(f'refused_sensitive_path: {_label(rel)}')
        except OSError:
            pass
        return None

    def load(rel: str, bad_json: str, cap: int, too_large) -> tuple[object, int]:
        if rel not in files:
            err(f'missing_required_file: {rel}')
            return _FAIL, 0
        raw = read(rel, cap)
        if raw is None:
            return _FAIL, 0
        if len(raw) > cap:
            err(too_large(max(len(raw), files.get(rel, 0))))
            return _FAIL, 0
        try:
            return json.loads(raw.decode('utf-8')), len(raw)
        except (ValueError, UnicodeError, RecursionError):
            err(bad_json)
            return _FAIL, 0

    def text_of(rel: str, cap: int) -> tuple[str, int] | None:
        """(text of the first cap bytes, byte size of the whole file)."""
        raw = read(rel, cap) if rel in files else None
        if raw is None:
            return None
        return raw[:cap].decode('utf-8', errors='replace'), (max(len(raw), files.get(rel, 0)) if len(raw) > cap else len(raw))

    entries, files, dirs, links = _walk(root)
    sensitive = [e for e in entries if e not in links and any(SENSITIVE.search(p) for p in e.split('/'))]
    for entry in (*links, *sensitive):
        err(f'refused_sensitive_path: {_label(entry)}')
    skip = {*links, *sensitive}
    names = [e for e in entries if e not in skip]
    for line in check_refused(names):
        err(line)
    warnings.extend(check_layout(names))
    if len(files) > MAX_FILES:
        warnings.append(f'file_count_high: {len(files)} > {MAX_FILES}')

    index, _ = load('design-system.json', 'invalid_index_value: design-system.json: json', CAP_JSON,
                    lambda n: f'invalid_index_value: design-system.json: size: {n} > {CAP_JSON}')
    title = None
    index_ok = False
    if index is not _FAIL:
        problems = validate_index(index)
        index_ok = not problems
        for line in problems:
            err(line)
        if any(line.startswith('unsupported_format_version') for line in problems):
            return errors, warnings
        if isinstance(index, dict):
            title = index.get('title') if isinstance(index.get('title'), str) else None
            if 'createdOnFiles' not in index:
                warnings.append('index_marker_missing: design-system.json: createdOnFiles')

    cmap, _ = load('canonical-map.json', 'invalid_manifest: canonical-map.json: json', CAP_JSON,
                   lambda n: f'invalid_manifest: canonical-map.json: size: {n} > {CAP_JSON}')
    if cmap is not _FAIL:
        for line in validate_canonical_map(cmap, root):
            err(line)
    chosen = profile or (cmap.get('profile') if isinstance(cmap, dict) and cmap.get('profile') in PROFILES else None) or 'full'
    components_map = cmap.get('components') if isinstance(cmap, dict) and isinstance(cmap.get('components'), dict) else {}

    tokens, _ = load('tokens.json', 'token_shape: tokens.json: json', CAP_TOKENS,
                     lambda n: f'limit_exceeded: tokens.json: file size: {n} > {CAP_TOKENS}')
    tokens_ok = False
    if tokens is not _FAIL:
        token_errors = validate_tokens_v3(tokens, root)
        for line in token_errors:
            err(line)
        tokens_ok = not token_errors
        warnings.extend(token_warnings(tokens))
        listed = set(_listed_fonts(tokens))
        for rel in sorted(f for f in files if f.startswith('fonts/') and f not in listed and f not in skip):
            for line in _check_font(root, rel):
                err(line)
        if chosen == 'minimal':
            for line in check_minimal_profile(tokens):
                err(line)
    token_names = _token_names(tokens) if tokens is not _FAIL else set()

    readme = text_of('README.md', CAP_README) if 'README.md' in files else None
    if 'README.md' not in files:
        err('missing_required_file: README.md')
    if readme:
        readme_errors, readme_warnings = validate_readme(readme[0], readme[1], chosen, token_names, title)
        for line in readme_errors:
            err(line)
        warnings.extend(readme_warnings)

    buildable = index_ok and tokens_ok and isinstance(index, dict) and isinstance(tokens, dict)  # the generators need valid inputs
    if 'DESIGN.md' not in files:
        err('design_md_missing: DESIGN.md')
    else:
        design = text_of('DESIGN.md', CAP_KEPT)
        if design:
            for line in validate_design_md_structure(design[0]):
                err(line)
            if tokens is not _FAIL:
                for line in check_design_md_refs(design[0], design_md_token_keys(tokens)):
                    err(line)
            if buildable:
                import design_system_build as build  # late: that module imports this one
                try:
                    if eol_lf(build.split_front_matter(design[0])[0]) != eol_lf(build.render_front_matter(tokens, index)):
                        err('design_md_stale: DESIGN.md')
                except Exception as exc:  # a package the generator cannot read is reported, not raised
                    err(f'design_md_stale: DESIGN.md: cannot regenerate ({type(exc).__name__})')

    if 'viewer.html' not in files:
        err('viewer_missing: viewer.html')
    else:
        page = read('viewer.html', CAP_VIEWER)
        if page is not None:
            size = max(len(page), files['viewer.html']) if len(page) > CAP_VIEWER else len(page)
            collected = fresh = None
            if buildable:
                import design_system_build as build  # late: that module imports this one
                try:
                    collected = build.collect_package(root)
                    fresh = build.render_viewer(collected).encode('utf-8')
                except build.PackageError as exc:  # carries a finished line
                    err(str(exc))
                except Exception as exc:  # whatever else a hostile package provokes is named by its type, never raised
                    err(f'viewer_stale: viewer.html: cannot regenerate ({type(exc).__name__})')
            viewer_errors, viewer_warnings = validate_viewer(page[:CAP_VIEWER].decode('utf-8', errors='replace'), size, collected or {})
            for line in viewer_errors:
                err(line)
            warnings.extend(viewer_warnings)
            if fresh is not None and size <= CAP_VIEWER and eol_lf(page) != eol_lf(fresh):
                err('viewer_stale: viewer.html')

    cover = 'components/Cover/preview.html'
    if cover not in files:
        err(f'cover_missing: {cover}')
    else:
        page = text_of(cover, CAP_PREVIEW)
        if page:
            for line in validate_preview(page[0], cover, page[1]):
                err(line)
            warnings.extend(preview_warnings(page[0], cover))
            count = len(re.findall(r'<svg\b', page[0], re.IGNORECASE))
            if count != 1:
                err(f'cover_shape: {cover}: {count} svg')
    for rel in sorted(f for f in files if f.startswith('components/Cover/') and f != cover and f not in skip):
        err(f'cover_not_bare: {_label(rel)}')
    if 'components/bundle.js' in files and 'components/bundle.js' not in skip:
        try:
            with safe_path(root, 'components/bundle.js').open('rb') as handle:
                header = handle.read(4096).split(b'\n', 1)[0].decode('utf-8', errors='replace')
        except (ValueError, OSError, RuntimeError):
            header = ''
        if '@ds-bundle' in header and re.search(r'"name"\s*:\s*"Cover"', header):
            err('cover_not_bare: components/bundle.js: bundle header lists Cover')

    comps = sorted(d.split('/')[1] for d in dirs if d.startswith('components/') and d.count('/') == 1
                   and d.split('/')[1] not in {'Cover', 'lib', 'src'} and d not in skip)
    for comp in comps:
        base = f'components/{comp}'
        if chosen == 'minimal':
            err(f'minimal_profile_violation: {_label(base)}: only Cover is allowed')
            continue
        if not JS_IDENT.match(comp):
            err(f'component_name_invalid: {_label(base)}')
        preview = text_of(f'{base}/preview.html', CAP_PREVIEW)
        if preview:
            for line in validate_preview(preview[0], f'{base}/preview.html', preview[1]):
                err(line)
            warnings.extend(preview_warnings(preview[0], f'{base}/preview.html'))
            if is_template_preview(preview[0]):
                continue
        for needed in ('README.md', 'preview.html'):
            if f'{base}/{needed}' not in files:
                err(f'component_incomplete: {_label(base)}: {needed}')
        if comp not in components_map:
            err(f'component_without_source: {_label(base)}')
        size = files.get(f'{base}/README.md', 0)
        if size > CAP_COMPONENT_README:
            warnings.append(f'component_readme_large: {_label(base)}/README.md: {size} > {CAP_COMPONENT_README}')

    for group in sorted(d.split('/')[1] for d in dirs if d.startswith('assets/') and d.count('/') == 1 and d not in skip):
        base = f'assets/{group}'
        readme_text = text_of(f'{base}/README.md', CAP_KEPT)
        if f'{base}/README.md' not in files:
            err(f'asset_group_readme_missing: {_label(base)}/README.md')
        for rel in sorted(f for f in files if f.startswith(f'{base}/') and f != f'{base}/README.md' and f not in skip):
            inner = rel[len(base) + 1:]
            if readme_text and inner not in readme_text[0] and inner.rsplit('/', 1)[-1] not in readme_text[0]:
                err(f'asset_unlisted: {_label(rel)}')
            raw = files[rel]
            if rel.casefold().endswith('.svg'):
                if raw > CAP_SVG_RAW:
                    err(f'asset_too_large: {_label(rel)}: {raw} > {CAP_SVG_RAW}')
            elif Path(rel).suffix.casefold() in TEXT_SUFFIXES:
                if raw > CAP_ASSET_STORED:
                    err(f'asset_too_large: {_label(rel)}: {raw} raw, {raw} stored > {CAP_ASSET_STORED}')
            elif _stored_size(rel, raw) > CAP_ASSET_STORED:
                err(f'asset_too_large: {_label(rel)}: {raw} raw, {_stored_size(rel, raw)} stored > {CAP_ASSET_STORED}')

    kept_exempt = ('assets/', 'fonts/')
    for rel, raw in sorted(files.items()):
        if rel not in skip and not rel.startswith(kept_exempt) and rel not in {'tokens.json', 'viewer.html', 'README.md', 'design-system.json', 'canonical-map.json'} \
                and not rel.endswith('/preview.html') and raw > CAP_TOKENS:
            warnings.append(f'kept_file_large: {_label(rel)}: {raw} > {CAP_TOKENS}')
    total = sum(_stored_size(rel, raw) for rel, raw in files.items() if rel not in skip)
    if total > CAP_PACKAGE_STORED:
        warnings.append(f'package_total_large: {total} > {CAP_PACKAGE_STORED}')

    if cmap is not _FAIL and tokens is not _FAIL and tokens_ok and isinstance(cmap, dict) and isinstance(tokens, dict):
        checks = cmap.get('checks')
        pairs = checks.get('contrast') if isinstance(checks, dict) else None
        contrast_errors, contrast_warnings = check_contrast(tokens, pairs if isinstance(pairs, list) else None)
        for line in contrast_errors:
            err(line)
        warnings.extend(contrast_warnings)
    return errors, warnings
