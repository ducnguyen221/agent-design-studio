"""Generators for a design-system package. This module renders the DESIGN.md front matter; viewer and adapters join in later tasks.

Pure functions: no network, no writes. The only file read is the DESIGN.md body template, when a package has no DESIGN.md yet.
Shape and escaping rules: skills/design-system/references/design-md-spec.md.
"""
from __future__ import annotations

import math
import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system_v3 as v3  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / 'skills' / 'design-system' / 'templates' / 'DESIGN.md'
SPEC_LABEL = 'alpha'
BOM = chr(0xFEFF)
_BARE_KEY = re.compile(r'[A-Za-z_][A-Za-z0-9_-]*')
_YAML_WORDS = {'true', 'false', 'yes', 'no', 'on', 'off', 'y', 'n', 'null', '~'}
_PLAIN_NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)')
_WEIGHT_WORDS = {'normal': '400', 'bold': '700'}


# --------------------------------------------------------------------------- YAML subset

def _escape(ch: str) -> str:
    code = ord(ch)
    if ch == '\\':
        return '\\\\'
    if ch == '"':
        return '\\"'
    if ch == '\n':
        return '\\n'
    if ch == '\t':
        return '\\t'
    # C0 controls, DEL and C1 controls (a YAML reader refuses them raw), the two line separators a YAML reader folds,
    # the two non-characters and lone surrogates (which cannot be written as UTF-8 at all).
    if code < 0x20 or 0x7F <= code <= 0x9F or code in (0x2028, 0x2029, 0xFFFE, 0xFFFF) or 0xD800 <= code <= 0xDFFF:
        return f'\\u{code:04x}'
    return ch


def _quote(text: str) -> str:
    return '"' + ''.join(_escape(c) for c in text) + '"'


def _key(name: str) -> str:
    """A map key: bare when it is a plain word and not a YAML keyword, else quoted."""
    if _BARE_KEY.fullmatch(name) and name.casefold() not in _YAML_WORDS:
        return name
    return _quote(name)


def _number_text(value: object) -> str | None:
    """Plain decimal text of a finite number; None for anything else (booleans included)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and math.isfinite(value):
        # A decimal, never an exponent: a YAML 1.1 reader takes "1e-05" for a string.
        return str(int(value)) if value == int(value) else format(Decimal(repr(value)), 'f')
    return None


def split_front_matter(text: str) -> tuple[str, str]:
    """(front matter block including both fences and the newline after the closing one, rest); ("", text) without a block.

    A leading byte order mark stays with the block. Lines are cut at "\\n" only, so the body keeps every byte.
    """
    pos = 1 if text.startswith('﻿') else 0
    end = text.find('\n', pos)
    if end < 0 or text[pos:end].strip() != '---':
        return '', text
    pos = end + 1
    while pos < len(text):
        end = text.find('\n', pos)
        line = text[pos:] if end < 0 else text[pos:end]
        if line.strip() == '---':
            cut = len(text) if end < 0 else end + 1
            return text[:cut], text[cut:]
        if end < 0:
            break
        pos = end + 1
    return '', text


# --------------------------------------------------------------------------- values

def to_hex(value: str) -> str | None:
    """``#rrggbb`` (``#rrggbbaa`` when alpha is not 1) for a colour string; None when it cannot be converted (lab, lch, color(), junk)."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if v3._HEX.match(text):
        digits = text[1:].lower()
        if len(digits) in (3, 4):
            digits = ''.join(c * 2 for c in digits)
        return '#' + digits
    try:
        red, green, blue, alpha = v3._parse_color_alpha(text)
        channels = [round(c * 255) for c in (red, green, blue)]
        if alpha < 1:
            channels.append(round(alpha * 255))
    except (ValueError, OverflowError):
        return None
    return '#' + ''.join(f'{min(255, max(0, c)):02x}' for c in channels)


def _color_text(value: str) -> tuple[str, bool]:
    """(front matter text, passed through unchanged)."""
    alias = v3._ALIAS.match(value.strip())
    if alias:
        return '{colors.' + alias[1] + '}', False
    converted = to_hex(value)
    return (value, True) if converted is None else (converted, False)


def _dimension(value: object) -> str | None:
    """A length for rounded/spacing/fontSize: bare numbers get ``px``; zero stays ``0``; other strings pass through."""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if _PLAIN_NUMBER.fullmatch(text):
            number = float(text)
            if number == 0:
                return '0'
            as_text = _number_text(number)
            return text if as_text is None else as_text + 'px'
        return text
    as_text = _number_text(value)
    if as_text is None:
        return None
    return '0' if value == 0 else as_text + 'px'


def _weight(value: object) -> str | None:
    """YAML scalar for fontWeight: a number is bare; ``normal``/``bold`` become 400/700; a range stays a quoted string."""
    as_text = _number_text(value)
    if as_text is not None:
        return as_text
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text in _WEIGHT_WORDS:
        return _WEIGHT_WORDS[text]
    return str(int(text)) if re.fullmatch(r'\d{1,4}', text) else _quote(text)


def _line_height(value: object) -> str | None:
    """YAML scalar for lineHeight: unitless is a bare number, anything else a quoted string."""
    as_text = _number_text(value)
    if as_text is not None:
        return as_text
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if _PLAIN_NUMBER.fullmatch(text):
        number = _number_text(float(text))
        if number is not None:
            return number
    return _quote(text)


# --------------------------------------------------------------------------- entries

def _color_entries(tokens: dict) -> list[tuple[str, str, bool]]:
    body = tokens.get('color')
    if not isinstance(body, dict) or not isinstance(body.get('tokens'), list):
        return []
    themes = body.get('themes') if isinstance(body.get('themes'), list) else []
    theme_ids = [t['id'] for t in themes if isinstance(t, dict) and isinstance(t.get('id'), str)]
    first = theme_ids[0] if theme_ids else None
    entries = []
    for token in body['tokens']:
        if not isinstance(token, dict) or not isinstance(token.get('name'), str):
            continue
        value = v3._theme_value(token, theme_ids, first)
        if value is None:
            continue
        text, passthrough = _color_text(value)
        entries.append((token['name'], text, passthrough))
    return entries


def _length_entries(tokens: dict, family: str) -> list[tuple[str, str]]:
    body = tokens.get(family)
    if not isinstance(body, dict) or not isinstance(body.get('tokens'), list):
        return []
    entries = []
    for token in body['tokens']:
        if isinstance(token, dict) and isinstance(token.get('name'), str):
            text = _dimension(token.get('value'))
            if text is not None:
                entries.append((token['name'], text))
    return entries


def _typography_entries(tokens: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    body = tokens.get('type')
    if not isinstance(body, dict) or not isinstance(body.get('groups'), list):
        return []
    families = body.get('families') if isinstance(body.get('families'), dict) else {}
    entries = []
    for group in body['groups']:
        styles = group.get('styles') if isinstance(group, dict) else None
        for style in styles if isinstance(styles, list) else []:
            if not isinstance(style, dict) or not isinstance(style.get('name'), str):
                continue
            fields: list[tuple[str, str]] = []
            family = families.get(style.get('family', group.get('family')))
            if isinstance(family, str):
                fields.append(('fontFamily', _quote(family)))
            size = _dimension(style['fontSize']) if 'fontSize' in style else None
            if size is not None:
                fields.append(('fontSize', _quote(size)))
            weight = _weight(style['fontWeight']) if 'fontWeight' in style else None
            if weight is not None:
                fields.append(('fontWeight', weight))
            height = _line_height(style['lineHeight']) if 'lineHeight' in style else None
            if height is not None:
                fields.append(('lineHeight', height))
            entries.append((style['name'], fields))
    return entries


def design_md_warnings(tokens: dict) -> list[str]:
    """``design_md_color_passthrough: <name>`` for each colour copied through because it has no sRGB conversion."""
    if not isinstance(tokens, dict):
        return []
    return [f'design_md_color_passthrough: {v3._label(name)}' for name, _text, passthrough in _color_entries(tokens) if passthrough]


# --------------------------------------------------------------------------- DESIGN.md

def render_front_matter(tokens: dict, index: dict) -> str:
    """The generated front matter block, fences included, ending with a newline. Same input, same bytes."""
    title = index.get('title') if isinstance(index, dict) and isinstance(index.get('title'), str) else ''
    lines = ['---', f'version: {SPEC_LABEL}', f'name: {_quote(title)}']
    tokens = tokens if isinstance(tokens, dict) else {}
    colors = _color_entries(tokens)
    if colors:
        lines.append('colors:')
        lines.extend(f'  {_key(name)}: {_quote(text)}' for name, text, _passthrough in colors)
    typography = _typography_entries(tokens)
    if typography:
        lines.append('typography:')
        for name, fields in typography:
            if not fields:
                lines.append(f'  {_key(name)}: {{}}')
                continue
            lines.append(f'  {_key(name)}:')
            lines.extend(f'    {field}: {text}' for field, text in fields)
    for family, label in (('radius', 'rounded'), ('spacing', 'spacing')):
        entries = _length_entries(tokens, family)
        if entries:
            lines.append(f'{label}:')
            lines.extend(f'  {_key(name)}: {_quote(text)}' for name, text in entries)
    lines.append('---')
    return '\n'.join(lines) + '\n'


def render_design_md(existing: str, tokens: dict, index: dict) -> str:
    """New DESIGN.md text: fresh front matter, then the body of ``existing`` untouched.

    An empty ``existing`` takes its body from the skill template (its sample front matter dropped, line ends normalised to LF).
    """
    head = render_front_matter(tokens, index)
    if existing == '':
        _sample, body = split_front_matter(TEMPLATE.read_bytes().decode('utf-8').replace('\r\n', '\n'))
        return head + body
    front, body = split_front_matter(existing)
    if not front and body.startswith(BOM):
        body = body[1:]  # a BOM kept in front of no block would end up in the middle of the new file
    return head + body
