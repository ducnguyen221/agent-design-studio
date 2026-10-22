"""Generators for a design-system package: the DESIGN.md front matter and the offline viewer page. Adapters join in a later task.

Pure functions: no network, no writes. Files are read only by ``collect_package`` and ``inline_asset`` (every read goes through
``safe_path`` first and is size-bounded) and, when a package has no DESIGN.md yet, by ``render_design_md`` (the body template).
Shape and escaping rules: skills/design-system/references/design-md-spec.md and system-contract.md.
"""
from __future__ import annotations

import base64
import html
import json
import math
import re
import sys
from bisect import bisect_left
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, unquote

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

    Leading byte order marks stay with the block. Lines are cut at "\\n" only, so the body keeps every byte.
    """
    pos = len(text) - len(text.lstrip(BOM))
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
    if not front:
        body = body.lstrip(BOM)  # a BOM kept in front of no block would end up in the middle of the new file
    return head + body


# --------------------------------------------------------------------------- viewer: text

VIEWER_MAX = 512_000
VIEWER_WARN = 300_000
INLINE_CAP = 65_536       # one embedded image
INLINE_TOTAL = 250_000    # all embedded images together, counted as data-URI characters
MAX_LISTED = 20_000       # files the page will list
# The content-security policy of the page; ``{script}`` is replaced by the hash of the one script (``viewer_csp``). The fixed
# directives are the list ``VIEWER_CSP_FIXED`` of the verifier, which checks them; a test keeps both in step.
VIEWER_CSP = ("default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src {script}; script-src-attr 'none'; "
              "base-uri 'none'; form-action 'none'")
READ_PIECE = 65_536          # the most one read call asks for when a whole file has to be looked at
EOL_READ_MAX = 12_000_000     # a text file is sized with LF line ends when it is at most this long ...
EOL_READ_TOTAL = 64_000_000   # ... while all such files read so far stay under this total ...
EOL_READ_FILES = 2_000        # ... and there are at most this many of them (any other file is shown with its stored size)
TITLE_SUFFIX = ' — static viewer — not a Claude Design render'
SCREENS = (('overview', 'Overview'), ('colors', 'Colors'), ('typography', 'Typography'), ('spacing', 'Spacing'),
           ('components', 'Components'), ('assets', 'Assets'), ('files', 'Files'), ('agents', 'Agents'))
IMAGE_TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
               '.webp': 'image/webp', '.svg': 'image/svg+xml', '.avif': 'image/avif'}


class PackageError(ValueError):
    """The package cannot be turned into a page; the message is a finished error line."""


def _esc(text: object) -> str:
    """HTML escape for text and attribute values.

    An equals sign, a colon before two slashes and a double slash are written as character references. Text copied from a
    package then holds no ``name=value`` shape and no ``//``: it can neither read as an event attribute or an outside
    reference to a scanner, nor fake one of the ``data-*=`` attributes the coverage counts look for. A browser shows the
    same characters.
    """
    return html.escape(str(text), quote=True).replace('=', '&#61;').replace('://', '&#58;//').replace('//', '/&#47;')


def _line(text: object, limit: int = 200) -> str:
    """One printable line: whitespace collapsed, control characters dropped, bounded."""
    clean = ''.join(c for c in str(text) if c.isprintable() or c.isspace())
    return ' '.join(clean.split())[:limit]


class _Seek:
    """``str.find`` with a memory. The first hit at or after ``start`` is reused for any later query that starts at or before
    it, and a miss is final, so a scan that keeps failing never re-reads the same stretch of text."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.memo: dict[str, tuple[int, int]] = {}

    def find(self, needle: str, start: int) -> int:
        known = self.memo.get(needle)
        if known is not None:
            at, hit = known
            if at <= start and (hit < 0 or start <= hit):
                return hit
        hit = self.text.find(needle, start)
        self.memo[needle] = (start, hit)
        return hit


_HREF_PATH = re.compile(r'[A-Za-z0-9_][A-Za-z0-9._~/%@+,=-]*')
_HREF_FRAGMENT = re.compile(r'[A-Za-z0-9_.-]*')


_DECODE_ROUNDS = 5


def _decoded(path: str) -> str | None:
    """The path with its percent escapes undone, again and again until it stops changing; None when it never settles."""
    for _ in range(_DECODE_ROUNDS):
        plain = unquote(path)
        if plain == path:
            return path
        path = plain
    return None


def _safe_href(target: str) -> str | None:
    """A relative file link or None. No scheme, no leading slash, no parent step, no query, nothing but a short safe alphabet.

    A browser reads ``%2e%2e`` as a parent step and ``%2F`` as a slash, so the rules are applied twice: to the text as written
    and to the text with its percent escapes undone (to a fixed point, a few rounds at most).
    """
    target = target.strip()
    if not target or len(target) > 300:
        return None
    path, hash_mark, fragment = target.partition('#')
    if not _HREF_PATH.fullmatch(path) or '//' in path or (hash_mark and not _HREF_FRAGMENT.fullmatch(fragment)):
        return None
    plain = _decoded(path)
    if plain is None or '//' in plain or any(not c.isprintable() or c in '\\:?#' for c in plain):
        return None
    if any(part in ('..', '.') or (part and not part.strip(' .')) for part in plain.split('/')):
        return None
    return target


_PAREN = re.compile(r'[()]')


class _Parens:
    """Where the parenthesis that closes an opening one sits, answered from one pass over the text.

    ``closer(start)`` is the first ``)`` at or after ``start`` that balances a ``(`` standing just before ``start``, or -1.
    The running depth after each parenthesis is kept; the closer is the first later parenthesis that leaves a lower depth
    than the one before ``start``, found with the usual next-smaller-value stack. Building costs one pass, asking costs a
    binary search, so no link head ever scans the text behind it again.
    """

    def __init__(self, text: str) -> None:
        self.where = [m.start() for m in _PAREN.finditer(text)]
        depth, levels = 0, [0]
        for at in self.where:
            depth += 1 if text[at] == '(' else -1
            levels.append(depth)
        self.lower = [-1] * len(levels)
        waiting: list[int] = []
        for index, level in enumerate(levels):
            while waiting and levels[waiting[-1]] > level:
                self.lower[waiting.pop()] = index
            waiting.append(index)

    def closer(self, start: int) -> int:
        first = bisect_left(self.where, start)
        if first >= len(self.where) or self.lower[first] < 0:
            return -1
        return self.where[self.lower[first] - 1]


def _inline(text: str) -> str:
    """Inline Markdown to HTML: code spans, ``**bold**``, relative links; everything else is escaped text. One left-to-right pass."""
    out: list[str] = []
    seek = _Seek(text)
    parens: _Parens | None = None
    size, pos, run = len(text), 0, 0

    def flush(upto: int) -> None:
        if upto > run:
            out.append(_esc(text[run:upto]))

    while pos < size:
        char = text[pos]
        if char == '`':
            end = seek.find('`', pos + 1)
            if end > pos + 1:
                flush(pos)
                out.append('<code>' + _esc(text[pos + 1:end]) + '</code>')
                pos = run = end + 1
                continue
        elif char == '*' and text.startswith('**', pos):
            end = seek.find('**', pos + 2)
            if end > pos + 2:
                flush(pos)
                out.append('<strong>' + _esc(text[pos + 2:end]) + '</strong>')
                pos = run = end + 2
                continue
        elif char == '[' or (char == '!' and text.startswith('![', pos)):
            image = char == '!'
            opener = pos + 1 if image else pos
            close = seek.find(']', opener + 1)
            other = seek.find('[', opener + 1)
            if close > 0 and (other < 0 or other > close) and text.startswith('(', close + 1):
                parens = parens or _Parens(text)
                end = parens.closer(close + 2)  # the closing parenthesis that balances the opening one
                if end > 0:
                    flush(pos)
                    label = _esc(text[opener + 1:close])
                    href = None if image else _safe_href(text[close + 2:end])
                    out.append(f'<a href="{_esc(href)}">{label}</a>' if href else label)
                    pos = run = end + 1
                    continue
        pos += 1
    flush(size)
    return ''.join(out)


def _fence_marker(line: str) -> str:
    stripped = line.lstrip()
    return stripped[:3] if stripped[:3] in ('```', '~~~') else ''


def _list_item(line: str) -> tuple[bool, str] | None:
    """(ordered, text) for ``- x``, ``* x``, ``+ x``, ``1. x`` or ``1) x``."""
    text = line.lstrip()
    if text[:2] in ('- ', '* ', '+ '):
        return False, text[2:].strip()
    digits = len(text) - len(text.lstrip('0123456789'))
    if 0 < digits <= 9 and text[digits:digits + 2] in ('. ', ') '):
        return True, text[digits + 2:].strip()
    return None


def _atx_level(line: str) -> tuple[int, str] | None:
    text = line.lstrip(' ')
    if len(line) - len(text) > 3:
        return None
    level = len(text) - len(text.lstrip('#'))
    if not 1 <= level <= 6 or (len(text) > level and text[level] not in ' \t'):
        return None
    return level, text[level:].strip().rstrip('#').strip()


def _cells(row: str) -> list[str]:
    row = row.strip()
    row = row[1:] if row.startswith('|') else row
    row = row[:-1] if row.endswith('|') else row
    return [c.strip() for c in row.split('|')]


def _table_rule(line: str) -> bool:
    cells = _cells(line)
    return bool(cells) and all(c and set(c) <= set('-: ') and '-' in c for c in cells)


def render_markdown(text: str, first_level: int = 3) -> str:
    """Markdown to HTML for headings, paragraphs, lists, tables, quotes, fenced code, bold, code spans and relative links.

    Every character of the input is escaped; raw HTML never passes through. A link to anything but a relative file keeps its
    label and loses the link. ``#`` becomes ``<h{first_level}>``, so a page's single ``h1`` stays single. Linear in the input.
    """
    lines = str(text).replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out: list[str] = []
    para: list[str] = []
    items: list[str] = []
    ordered = False

    def end_para() -> None:
        if para:
            out.append('<p>' + _inline(' '.join(p.strip() for p in para)) + '</p>')
            para.clear()

    def end_list() -> None:
        if items:
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{_inline(i)}</li>' for i in items) + f'</{tag}>')
            items.clear()

    index, count = 0, len(lines)
    while index < count:
        line = lines[index]
        index += 1
        stripped = line.strip()
        marker = _fence_marker(line)
        if marker:
            end_para()
            end_list()
            code = []
            while index < count and not lines[index].strip().startswith(marker):
                code.append(lines[index])
                index += 1
            index += 1
            out.append('<pre><code>' + _esc('\n'.join(code)) + '</code></pre>')
            continue
        if not stripped:
            end_para()
            end_list()
            continue
        heading = _atx_level(line)
        if heading:
            end_para()
            end_list()
            level = min(6, first_level + heading[0] - 1)
            out.append(f'<h{level}>{_inline(heading[1])}</h{level}>')
            continue
        if len(stripped) >= 3 and len(set(stripped)) == 1 and stripped[0] in '-*_':
            end_para()
            end_list()
            out.append('<hr>')
            continue
        item = _list_item(line)
        if item:
            end_para()
            if items and item[0] != ordered:
                end_list()
            ordered = item[0]
            items.append(item[1])
            continue
        if items and line[:1] in (' ', '\t'):
            items[-1] += ' ' + stripped
            continue
        if stripped.startswith('>'):
            end_para()
            end_list()
            quoted = [stripped[1:].strip()]
            while index < count and lines[index].strip().startswith('>'):
                quoted.append(lines[index].strip()[1:].strip())
                index += 1
            out.append('<blockquote><p>' + _inline(' '.join(quoted)) + '</p></blockquote>')
            continue
        if stripped.startswith('|') and index < count and _table_rule(lines[index]):
            end_para()
            end_list()
            head = _cells(stripped)
            index += 1
            rows = []
            while index < count and lines[index].strip().startswith('|'):
                rows.append(_cells(lines[index]))
                index += 1
            body = ''.join('<tr>' + ''.join(f'<td>{_inline(c)}</td>' for c in row) + '</tr>' for row in rows)
            out.append('<div class="scroll"><table><thead><tr>' + ''.join(f'<th scope="col">{_inline(c)}</th>' for c in head)
                       + f'</tr></thead><tbody>{body}</tbody></table></div>')
            continue
        end_list()
        para.append(line)
    end_para()
    end_list()
    return '\n'.join(out)


# --------------------------------------------------------------------------- viewer: SVG

_SVG_ELEMENTS = frozenset((
    'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'text', 'tspan', 'defs', 'lineargradient',
    'radialgradient', 'stop', 'clippath', 'mask', 'desc', 'symbol', 'use', 'pattern', 'filter', 'fegaussianblur',
    'feoffset', 'feflood', 'fecomposite', 'femerge', 'femergenode', 'feblend', 'fecolormatrix', 'fedropshadow'))
_SVG_BAD_ATTRS = frozenset(('src', 'srcdoc', 'srcset', 'action', 'formaction', 'data', 'poster', 'background', 'ping', 'content',
                            'http-equiv', 'is'))
_SVG_TAG_NAME = re.compile(r'[A-Za-z][A-Za-z0-9]{0,31}')
_SVG_ATTR_NAME = re.compile(r'[A-Za-z_:][A-Za-z0-9_:.-]{0,63}')
_SVG_LOCAL_URL = re.compile(r'url\(\s*#[A-Za-z0-9_.:-]{1,64}\s*\)', re.IGNORECASE)
_SVG_LOCAL_REF = re.compile(r'#[A-Za-z0-9_.:-]{1,64}')
_SVG_HANDLER = re.compile(r'\son[a-z]+\s*=', re.IGNORECASE)  # an event attribute, or text shaped like one: refused either way
_SVG_MAX_TAGS = 4000
_SVG_MAX_DEPTH = 64


def _svg_tag(text: str, pos: int) -> tuple[int, bool, str, list[tuple[str, str]], bool] | None:
    """Read one tag that starts at ``text[pos] == '<'``: (end, closing, name, attributes, self-closing); None for anything else.

    The grammar is a strict subset of what a browser accepts: a letter or ``/`` after ``<``, attribute values in matching quotes
    with no ``<``, ``>`` or ``&`` inside, no bare attributes. Comments, declarations and processing instructions never match.
    """
    size = len(text)
    pos += 1
    closing = text.startswith('/', pos)
    pos += closing
    match = _SVG_TAG_NAME.match(text, pos)
    if not match:
        return None
    name, pos = match[0], match.end()
    attrs: list[tuple[str, str]] = []
    while True:
        gap = pos
        while pos < size and text[pos] in ' \t\r\n':
            pos += 1
        if pos >= size:
            return None
        if text[pos] == '>':
            return pos + 1, closing, name, attrs, False
        if text.startswith('/>', pos):
            return pos + 2, closing, name, attrs, True
        if closing or pos == gap:
            return None
        attr = _SVG_ATTR_NAME.match(text, pos)
        if not attr:
            return None
        pos = attr.end()
        while pos < size and text[pos] in ' \t\r\n':
            pos += 1
        if pos >= size or text[pos] != '=':
            return None
        pos += 1
        while pos < size and text[pos] in ' \t\r\n':
            pos += 1
        if pos >= size or text[pos] not in '"\'':
            return None
        end = text.find(text[pos], pos + 1)
        if end < 0:
            return None
        value = text[pos + 1:end]
        if any(c in value for c in '<>&\\') or any(ord(c) < 32 or ord(c) == 127 for c in value):
            return None
        attrs.append((attr[0], value))
        pos = end + 1
        if len(attrs) > 64:
            return None


def _svg_attrs_ok(attrs: list[tuple[str, str]]) -> bool:
    for raw_name, value in attrs:
        name = raw_name.casefold()
        low = ''.join(value.split()).casefold()
        if name.startswith(('on', 'data-')) or name in _SVG_BAD_ATTRS:
            return False
        if name == 'id':
            if not _SVG_LOCAL_REF.fullmatch('#' + value):
                return False
            continue
        if name in ('href', 'xlink:href'):
            if not _SVG_LOCAL_REF.fullmatch(value):
                return False
            continue
        if name == 'xmlns' or name.startswith('xmlns:'):
            continue
        if '//' in low or 'javascript' in low or 'vbscript' in low or 'data:' in low:
            return False
        if 'url(' in _SVG_LOCAL_URL.sub('', low) or 'expression' in low or '@import' in low:
            return False
    return True


def _scan_svg(text: object) -> list[str] | None:
    """Strictly check an inline SVG; return the text of its ``<text>`` elements, or None when anything is outside the allowed subset.

    Allowed: one well-formed ``<svg>`` tree of drawing elements from a fixed list, attributes that cannot run code or load
    anything (no ``on*``, no ``data-*``, links only to ``#id``, ``url()`` only to ``#id``), plain text between the tags.
    """
    if not isinstance(text, str) or not 5 <= len(text) <= v3.CAP_PREVIEW or text.count('<') > _SVG_MAX_TAGS * 2:
        return None
    text = text.strip()
    if not text.startswith('<svg') or not text.endswith('</svg>') or '\x00' in text or _SVG_HANDLER.search(text):
        return None
    stack: list[str] = []
    texts: list[str] = []
    capture = -1
    done = False
    pos, tags, size = 0, 0, len(text)
    while pos < size:
        lt = text.find('<', pos)
        data = text[pos:] if lt < 0 else text[pos:lt]
        if '//' in data or (done and data.strip()):
            return None
        if capture >= 0:
            texts[capture] += data
        if lt < 0:
            break
        tag = _svg_tag(text, lt)
        tags += 1
        if tag is None or tags > _SVG_MAX_TAGS:
            return None
        pos, closing, name, attrs, selfclose = tag
        low = name.casefold()
        if low not in _SVG_ELEMENTS or not _svg_attrs_ok(attrs) or done:
            return None
        if closing:
            if not stack or stack.pop() != low:
                return None
            done = not stack
        else:
            if bool(stack) == (low == 'svg'):  # the root opens an empty stack; no other svg may open inside it
                return None
            if low == 'text' and 'text' not in stack:
                texts.append('')
            if not selfclose:
                stack.append(low)
                if len(stack) > _SVG_MAX_DEPTH:
                    return None
        capture = len(texts) - 1 if 'text' in stack else -1
    if stack or not done:
        return None
    return [' '.join(t.split()) for t in texts]


_SVG_OPEN = re.compile(r'<svg', re.IGNORECASE | re.ASCII)
_SVG_CLOSE = re.compile(r'</svg>', re.IGNORECASE | re.ASCII)


def extract_cover_svg(text: str) -> str | None:
    """The first ``<svg>...</svg>`` element of a preview page, or None. Searched in the text as it is: a lower-cased copy can
    change length (U+0130), and a Unicode-aware match would take U+017F for an ``s``."""
    if not isinstance(text, str):
        return None
    start = _SVG_OPEN.search(text)
    if not start:
        return None
    end = _SVG_CLOSE.search(text, start.start())
    return None if end is None else text[start.start():end.end()]


_SVG_ID_PREFIX = 'cover-'
_SVG_TAG_TEXT = re.compile(r'<[^<>]*>')
_SVG_ATTR_TEXT = re.compile(r"""(\s+)([A-Za-z_:][A-Za-z0-9_:.-]*)(\s*=\s*)(?:"([^"]*)"|'([^']*)')""")
_SVG_URL_REF = re.compile(r'(url\(\s*#)([A-Za-z0-9_.:-]{1,64})', re.IGNORECASE)
_SVG_ID_LISTS = frozenset(('aria-labelledby', 'aria-describedby', 'aria-controls', 'aria-owns', 'aria-details', 'aria-flowto',
                           'aria-activedescendant'))


def isolate_svg_ids(svg: str) -> str:
    """An SVG that passed ``sanitize_svg`` with every id carrying the prefix ``cover-``, and every reference to one (``#id`` in a
    link, ``url(#id)`` in a value, the id lists of ARIA attributes) carrying it too. An inline SVG shares its ids with the page
    around it: without the prefix a cover with ``<g id="colors">`` would take the place of the page's own anchor.

    Only attribute values of tags change; the tags are read with the same strict grammar the check used.
    """
    def fix(attr: re.Match) -> str:
        lead, name, equals = attr[1], attr[2], attr[3]
        quote_mark, value = ('"', attr[4]) if attr[4] is not None else ("'", attr[5])
        low = name.casefold()
        if low == 'id':
            name, value = 'id', _SVG_ID_PREFIX + value  # written in lower case: a scanner that looks for ``id=`` sees it
        elif low in ('href', 'xlink:href') and value.startswith('#'):
            value = '#' + _SVG_ID_PREFIX + value[1:]
        elif low in _SVG_ID_LISTS:
            value = ' '.join(_SVG_ID_PREFIX + token if token else token for token in value.split(' '))
        else:
            value = _SVG_URL_REF.sub(lambda m: m[1] + _SVG_ID_PREFIX + m[2], value)
        return f'{lead}{name}{equals}{quote_mark}{value}{quote_mark}'

    return _SVG_TAG_TEXT.sub(lambda tag: _SVG_ATTR_TEXT.sub(fix, tag[0]), svg)


def sanitize_svg(text: str) -> str | None:
    """The SVG itself when it holds only drawing elements and inert attributes (see ``_scan_svg``), else None.

    Nothing is rewritten: an SVG with a script, an event attribute, an outside link or any element outside the list is refused
    whole, so what reaches the page is byte for byte what passed the check.
    """
    return text.strip() if _scan_svg(text) is not None else None


def viewer_csp(script: str) -> str:
    """The content-security policy for a page whose one script is ``script``."""
    return VIEWER_CSP.replace('{script}', v3.csp_script_hash(script))


def inline_asset(path: Path, cap: int = INLINE_CAP) -> str | None:
    """A ``data:`` URI for an image of at most ``cap`` bytes, or None (not an image type, too large, unreadable, unsafe SVG).

    An SVG is text: it is embedded, and measured against ``cap``, with LF line ends, so that a copy saved with CRLF gives the same page.
    The caller passes a path that already went through ``safe_path``; a sensitive name or a link is refused again here.
    """
    path = Path(path)
    kind = IMAGE_TYPES.get(path.suffix.casefold())
    if kind is None or v3.SENSITIVE.search(path.name):
        return None
    try:
        if path.is_symlink():
            return None
        with path.open('rb') as handle:
            raw = handle.read(2 * cap + 1 if kind == 'image/svg+xml' else cap + 1)  # CRLF doubles a text at most
    except OSError:
        return None
    if kind == 'image/svg+xml':
        raw = v3.eol_lf(raw)
    if len(raw) > cap:
        return None
    if kind == 'image/svg+xml':
        try:
            if sanitize_svg(raw.decode('utf-8')) is None:
                return None
        except UnicodeError:
            return None
    return f'data:{kind};base64,' + base64.b64encode(raw).decode('ascii')


# --------------------------------------------------------------------------- viewer: collecting

def _capped(root: Path, rel: str, cap: int) -> bytes | None:
    """At most cap + 1 bytes of a package file, read only after ``safe_path``; None when it is absent, linked or sensitive."""
    try:
        with v3.safe_path(root, rel).open('rb') as handle:
            return handle.read(cap + 1)
    except (ValueError, RuntimeError, OSError):
        return None


def _text_of(root: Path, rel: str, cap: int) -> str:
    """At most ``cap`` bytes of a text file, line ends as LF (the cut falls at the same place in a copy saved with CRLF).

    Up to ``2 * cap`` stored bytes are read, in pieces of ``READ_PIECE``: CRLF doubles a text at most."""
    try:
        with v3.safe_path(root, rel).open('rb') as handle:
            parts: list[bytes] = []
            total = 0
            while total <= 2 * cap:
                piece = handle.read(min(READ_PIECE, 2 * cap + 1 - total))
                if not piece:
                    break
                parts.append(piece)
                total += len(piece)
    except (ValueError, RuntimeError, OSError):
        return ''
    return v3.eol_lf(b''.join(parts))[:cap].decode('utf-8', errors='replace')


def _lf_size(root: Path, rel: str, size: int, spent: list[int]) -> int:
    """The size a text file has with LF line ends; ``size`` for any other file, one that is too large, or one that cannot be read.

    The file is read in pieces of ``READ_PIECE`` and counted as it goes; ``spent`` holds the bytes and the files read so far, and
    both stay under their limits."""
    if (Path(rel).suffix.casefold() not in v3.TEXT_SUFFIXES or size > EOL_READ_MAX or spent[0] + size > EOL_READ_TOTAL
            or spent[1] >= EOL_READ_FILES):
        return size
    spent[1] += 1
    counted = stored = 0
    carry = b''  # a CR at the end of a piece waits for the first byte of the next one
    try:
        with v3.safe_path(root, rel).open('rb') as handle:
            while True:
                piece = handle.read(READ_PIECE)
                if not piece:
                    break
                stored += len(piece)
                if stored > EOL_READ_MAX:
                    return size
                piece = carry + piece
                carry = piece[-1:] if piece.endswith(b'\r') else b''
                counted += len(v3.eol_lf(piece[:len(piece) - len(carry)]))
    except (ValueError, RuntimeError, OSError):
        return size
    spent[0] += stored
    return counted + len(carry)


def _json_of(root: Path, rel: str, cap: int, required: bool) -> object:
    raw = _capped(root, rel, cap)
    if raw is not None and len(raw) <= cap:
        try:
            return json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeError, RecursionError):
            pass
    if required:
        raise PackageError(f'input_error: {rel}: not readable as JSON within {cap} bytes')
    return {}


def _listed(rel: str) -> bool:
    """False for anything the page must not list: hidden, excluded, sensitive or oddly spelled names."""
    return all(not p.startswith('.') and p.casefold() not in v3.EXCLUDED and not v3.SENSITIVE.search(p) and p == p.rstrip(' .')
               for p in rel.split('/'))


_LINK_LABEL = re.compile(r'\[([^\[\]]{0,200})\]\([^)\s]{0,300}\)')  # bounded on both sides: one start costs at most 500 characters


def _summary(readme: str) -> str:
    """The first sentence of the first paragraph that is not a heading."""
    block: list[str] = []
    fenced = False
    for raw in readme.replace('\r\n', '\n').split('\n'):
        line = raw.strip()
        if _fence_marker(raw):
            fenced = not fenced
        elif fenced:
            continue
        elif not line:
            if block:
                break
        elif not line.startswith('#'):
            block.append(line)
    text = _LINK_LABEL.sub(r'\1', ' '.join(block)).replace('**', '').replace('`', '')
    text = _line(text, 300)
    cut = text.find('. ')
    return text if cut < 0 else text[:cut + 1]


def collect_package(root: Path) -> dict:
    """Read a package into the plain data ``render_viewer`` needs. Every read goes through ``safe_path`` and is size-bounded.

    Keys: ``index``, ``design_md`` (body after the front matter), ``readme``, ``tokens``, ``canonical``, ``cover_svg`` (already
    checked, or None), ``components`` ([{name, group, summary, readme_html, marker, rel}] by name), ``assets`` ([{group, path,
    size, inline}] by path), ``files`` ([{path, size}] by path, without dot-names and ``viewer.html``), ``asset_readmes``
    ({group: html}), ``warnings`` (``viewer_asset_skipped: <path>`` lines). Raises PackageError for an unusable index or tokens file.
    """
    root = Path(root)
    index = _json_of(root, 'design-system.json', v3.CAP_JSON, True)
    tokens = _json_of(root, 'tokens.json', v3.CAP_TOKENS, True)
    canonical = _json_of(root, 'canonical-map.json', v3.CAP_JSON, False)
    if not isinstance(index, dict) or not isinstance(tokens, dict):
        raise PackageError('input_error: design-system.json and tokens.json must hold objects')
    if not isinstance(canonical, dict):
        canonical = {}
    _check_canonical(canonical)
    _entries, sizes, dirs, _links = v3._walk(root)
    names = sorted(rel for rel in sizes if _listed(rel) and rel != 'viewer.html')
    if len(names) > MAX_LISTED:
        raise PackageError(f'limit_exceeded: package: files: {len(names)} > {MAX_LISTED}')
    eol_spent = [0, 0]  # bytes and files read to size text files
    measured: dict[str, int] = {}

    def lf(rel: str) -> int:
        """The page shows a text file with the size it has with LF line ends. Read once, and only when the page needs the size."""
        if rel not in measured:
            measured[rel] = _lf_size(root, rel, sizes[rel], eol_spent)
        return measured[rel]
    warnings: list[str] = []

    design = split_front_matter(_text_of(root, 'DESIGN.md', v3.CAP_KEPT))[1].lstrip(BOM)
    readme = _text_of(root, 'README.md', v3.CAP_README)

    svg = extract_cover_svg(_text_of(root, 'components/Cover/preview.html', v3.CAP_PREVIEW))
    cover = sanitize_svg(svg) if svg else None
    if svg and cover is None:
        warnings.append('viewer_asset_skipped: components/Cover/preview.html')

    components = []
    spent = 0  # characters of README HTML so far; the page holds all of it, so the total is bounded, not only each README
    for name in sorted({rel.split('/')[1] for rel in dirs if rel.startswith('components/') and rel.count('/') == 1
                        and rel.split('/')[1] not in {'Cover', 'lib', 'src'} and _listed(rel)}):
        if spent > VIEWER_MAX:
            raise PackageError(f'viewer_too_large: viewer.html: {spent} > {VIEWER_MAX}')
        base = f'components/{name}'
        body = _text_of(root, f'{base}/README.md', v3.CAP_COMPONENT_README) if f'{base}/README.md' in sizes else ''
        if sizes.get(f'{base}/README.md', 0) > v3.CAP_COMPONENT_README and lf(f'{base}/README.md') > v3.CAP_COMPONENT_README:
            body += f'\n\n(README cut at {v3.CAP_COMPONENT_README} bytes)'
        head = _text_of(root, f'{base}/preview.html', 4096) if f'{base}/preview.html' in sizes else ''
        match = v3._marker(head) if head else None
        group = re.search(r'''\bgroup\s*=\s*["']([^"']{1,60})["']''', match[1]) if match else None
        shown = render_markdown(body, 4) if body else ''
        spent += len(shown)
        components.append({'name': name, 'group': _line(group[1], 60) if group else 'Components',
                           'summary': _summary(body), 'readme_html': shown,
                           'marker': _line('@dsCard ' + match[1], 200) if match else '',
                           'rel': f'{base}/preview.html' if f'{base}/preview.html' in sizes else ''})

    assets, asset_readmes, budget = [], {}, INLINE_TOTAL
    for rel in (r for r in names if r.startswith('assets/')):
        parts = rel.split('/')
        group = parts[1] if len(parts) > 2 else ''
        if len(parts) == 3 and parts[2] == 'README.md':
            if spent > VIEWER_MAX:
                raise PackageError(f'viewer_too_large: viewer.html: {spent} > {VIEWER_MAX}')
            asset_readmes[group] = render_markdown(_text_of(root, rel, v3.CAP_COMPONENT_README), 4)
            spent += len(asset_readmes[group])
            continue
        inline = None
        size = lf(rel)
        if Path(rel).suffix.casefold() in IMAGE_TYPES:
            if size <= INLINE_CAP and 4 * math.ceil(size / 3) + 26 <= budget:  # base64 plus the longest ``data:`` prefix
                try:
                    inline = inline_asset(v3.safe_path(root, rel))
                except (ValueError, RuntimeError, OSError):
                    inline = None
            if inline is None or len(inline) > budget:
                inline = None
                warnings.append(f'viewer_asset_skipped: {rel}')
            else:
                budget -= len(inline)
        assets.append({'group': group, 'path': rel, 'size': size, 'inline': inline})

    return {'index': index, 'design_md': design, 'readme': readme, 'tokens': tokens, 'canonical': canonical, 'cover_svg': cover,
            'components': components, 'assets': assets, 'files': [{'path': rel, 'size': lf(rel)} for rel in names],
            'asset_readmes': asset_readmes, 'warnings': warnings}


def count_tokens(tokens: object) -> int:
    """Tokens the page shows: every named entry of every family with a ``tokens`` list, plus every named text style."""
    if not isinstance(tokens, dict):
        return 0
    total = 0
    for family, body in tokens.items():
        if family == 'type':
            groups = body.get('groups') if isinstance(body, dict) else None
            for group in groups if isinstance(groups, list) else []:
                styles = group.get('styles') if isinstance(group, dict) else None
                total += sum(1 for s in styles if isinstance(s, dict) and isinstance(s.get('name'), str)) if isinstance(styles, list) else 0
        elif isinstance(body, dict) and isinstance(body.get('tokens'), list):
            total += sum(1 for t in body['tokens'] if isinstance(t, dict) and isinstance(t.get('name'), str))
    return total


# --------------------------------------------------------------------------- viewer: rendering

_CSS_LENGTH = re.compile(r'(?:\d+(?:\.\d*)?|\.\d+)(?:px|rem|em|%|pt|vw|vh|ch|ex)?')
_CSS_FONT = re.compile(r'''[A-Za-z0-9 ,'"._-]{1,200}''')
_CSS_SHADOW = re.compile(r'[A-Za-z0-9 #.,%()-]{1,160}')


def _css_length(value: object) -> str | None:
    """A non-negative CSS length from a token value, else None; a bare number is pixels."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        text = _number_text(value)
        return None if text is None or text.startswith('-') else text + 'px'
    if not isinstance(value, str) or not 0 < len(value.strip()) <= 24 or not _CSS_LENGTH.fullmatch(value.strip()):
        return None
    text = value.strip()
    return text + 'px' if text[-1].isdigit() or text[-1] == '.' else text


def _css_weight(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return str(int(value)) if 1 <= value <= 1000 else None
    if isinstance(value, str):
        first = value.split()[0] if value.split() else ''
        if first in _WEIGHT_WORDS:
            return _WEIGHT_WORDS[first]
        if first.isdigit() and len(first) <= 4 and 1 <= int(first) <= 1000:
            return str(int(first))
    return None


def _css_line_height(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        text = _number_text(value)
        return text if text is not None and 0 < value <= 10 else None
    if isinstance(value, str) and _CSS_LENGTH.fullmatch(value.strip()) and len(value.strip()) <= 24:
        return value.strip()
    return None


def _css_font(stack: object) -> str | None:
    return stack.strip() if isinstance(stack, str) and _CSS_FONT.fullmatch(stack.strip()) else None


def _style_attr(declarations: list[str]) -> str:
    return ' style="' + _esc(';'.join(declarations)) + '"' if declarations else ''


def _hex_for_css(value: object) -> str | None:
    return to_hex(value) if isinstance(value, str) else None


def _table(head: list[str], rows: list[str], caption: str) -> str:
    cols = ''.join(f'<th scope="col">{_esc(h)}</th>' for h in head)
    return (f'<div class="scroll"><table><caption class="mut">{_esc(caption)}</caption><thead><tr>{cols}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def _contrast_floor(pair: dict) -> float:
    """The minimum ratio a pair declares, or the default for its size; a number too large for a float counts as not declared."""
    try:
        declared = float(pair['min']) if v3._is_number(pair.get('min')) and pair['min'] > 0 else 0.0
    except OverflowError:
        declared = 0.0
    return declared if declared > 0 else (3.0 if pair.get('large') is True else 4.5)


def _check_canonical(canonical: dict) -> None:
    """Refuse a contrast minimum that is beyond float range or infinite; it would stop the page build."""
    checks = canonical.get('checks') if isinstance(canonical.get('checks'), dict) else {}
    pairs = checks.get('contrast') if isinstance(checks.get('contrast'), list) else []
    for pair in pairs:
        value = pair.get('min') if isinstance(pair, dict) else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                finite = math.isfinite(float(value))
            except OverflowError:
                finite = False
            if not finite:
                raise PackageError('invalid_manifest: canonical-map.json: checks.contrast.min')


def _colors(tokens: dict, canonical: dict) -> str:
    body = tokens.get('color') if isinstance(tokens.get('color'), dict) else {}
    themes = body.get('themes') if isinstance(body.get('themes'), list) else []
    theme_ids = [t['id'] for t in themes if isinstance(t, dict) and isinstance(t.get('id'), str)]
    columns = theme_ids or [None]
    entries = [t for t in body.get('tokens', []) if isinstance(t, dict) and isinstance(t.get('name'), str)] \
        if isinstance(body.get('tokens'), list) else []
    by_name = {t['name']: t for t in entries}
    rows = []
    for token in entries:
        cells = []
        for theme in columns:
            raw = v3._theme_value(token, theme_ids, theme)
            if raw is None:
                cells.append('<td>-</td>')
                continue
            try:
                swatch = _hex_for_css(v3._resolve_color(by_name, theme_ids, token['name'], theme)[0])
            except ValueError:
                swatch = None
            chip = '<span class="sw"' + _style_attr(['background:' + swatch]) + '></span>' if swatch else ''
            cells.append(f'<td>{chip}<code>{_esc(_line(raw, 120))}</code></td>')
        rows.append(f'<tr data-token="{_esc(token["name"])}"><th scope="row">{_esc(_line(token["name"], 80))}</th>{"".join(cells)}'
                    f'<td>{_esc(_line(token.get("usage", ""), 300))}</td></tr>')
    head = ['Token', *[str(t) if t is not None else 'Value' for t in columns], 'Usage']
    parts = [_table(head, rows, 'Colour tokens by theme') if rows else '<p class="empty">No colour tokens</p>']
    checks = canonical.get('checks') if isinstance(canonical.get('checks'), dict) else {}
    pairs = [p for p in checks.get('contrast', []) if isinstance(p, dict)] if isinstance(checks.get('contrast'), list) else []
    pair_rows = []
    for pair in pairs:
        fg, bg = pair.get('fg'), pair.get('bg')
        if not isinstance(fg, str) or not isinstance(bg, str):
            continue
        floor = _contrast_floor(pair)
        for theme in columns:
            try:
                ratio = v3.contrast_ratio(v3._resolve_color(by_name, theme_ids, fg, theme)[0],
                                          v3._resolve_color(by_name, theme_ids, bg, theme)[0])
                shown, verdict = f'{ratio:.2f}', 'Pass' if ratio >= floor - 1e-9 else 'Fail'
            except (ValueError, OverflowError, RecursionError):
                shown, verdict = '-', 'Not measured'
            pair_rows.append(f'<tr><th scope="row">{_esc(_line(fg, 60))} on {_esc(_line(bg, 60))}</th><td>{_esc(theme or "-")}</td>'
                             f'<td>{shown}</td><td>{floor:g}</td><td>{verdict}</td></tr>')
    parts.append('<h3>Contrast pairs</h3>')
    parts.append(_table(['Pair', 'Theme', 'Ratio', 'Minimum', 'Result'], pair_rows, 'Declared contrast pairs')
                 if pair_rows else '<p class="empty">No contrast pairs declared</p>')
    return '\n'.join(parts)


def _typography(tokens: dict) -> str:
    body = tokens.get('type') if isinstance(tokens.get('type'), dict) else {}
    families = body.get('families') if isinstance(body.get('families'), dict) else {}
    parts = []
    if families:
        rows = [f'<tr><th scope="row">{_esc(_line(k, 60))}</th><td><code>{_esc(_line(v, 200))}</code></td></tr>' for k, v in families.items()]
        parts.append(_table(['Family', 'Stack'], rows, 'Font families'))
    fonts = [f['file'] for f in body.get('fonts', []) if isinstance(f, dict) and isinstance(f.get('file'), str)] \
        if isinstance(body.get('fonts'), list) else []
    if fonts:
        parts.append('<p class="mut">Font files are listed, not embedded: ' + ', '.join(f'<code>{_esc(_line(f, 120))}</code>' for f in fonts) + '</p>')
    groups = body.get('groups') if isinstance(body.get('groups'), list) else []
    styled = 0
    for group in groups:
        styles = group.get('styles') if isinstance(group, dict) and isinstance(group.get('styles'), list) else []
        cards = []
        for style in styles:
            if not isinstance(style, dict) or not isinstance(style.get('name'), str):
                continue
            styled += 1
            key = style.get('family', group.get('family'))
            stack = families.get(key) if isinstance(key, str) else None
            size, weight, height = (style.get(k) for k in ('fontSize', 'fontWeight', 'lineHeight'))
            css = []
            if _css_font(stack):
                css.append(f'font-family:{_css_font(stack)}')
            if _css_length(size):
                css.append(f'font-size:min({_css_length(size)},72px)')
            if _css_weight(weight):
                css.append(f'font-weight:{_css_weight(weight)}')
            if _css_line_height(height):
                css.append(f'line-height:{_css_line_height(height)}')
            facts = ' / '.join(_line(x, 40) for x in (key if isinstance(key, str) else '', size if size is not None else '',
                                                      weight if weight is not None else '', height if height is not None else '') if x != '')
            cards.append(f'<div class="card" data-token="{_esc(style["name"])}"><p><strong>{_esc(_line(style["name"], 80))}</strong>'
                         f' <span class="mut">{_esc(facts)}</span></p><p class="sample"{_style_attr(css)}>'
                         f'The quick brown fox jumps over the lazy dog</p><p class="mut">{_esc(_line(style.get("usage", ""), 300))}</p></div>')
        if cards:
            name = group.get('name') if isinstance(group.get('name'), str) else 'Styles'
            parts.append(f'<h3>{_esc(_line(name, 80))}</h3>' + '\n'.join(cards))
    if not styled:
        parts.append('<p class="empty">No text styles</p>')
    return '\n'.join(parts)


def _spacing(tokens: dict) -> str:
    parts = []
    for family, body in tokens.items():
        if family in ('color', 'type') or not isinstance(body, dict) or not isinstance(body.get('tokens'), list):
            continue
        rows = []
        for token in body['tokens']:
            if not isinstance(token, dict) or not isinstance(token.get('name'), str):
                continue
            value = token.get('value')
            sample = ''
            length = _css_length(value)
            if family == 'spacing' and length:
                sample = '<div class="bar"' + _style_attr(['width:min(' + length + ',100%)']) + '></div>'
            elif family == 'radius' and length:
                sample = '<div class="box"' + _style_attr(['border-radius:' + length]) + '></div>'
            elif family == 'shadow' and isinstance(value, str) and _CSS_SHADOW.fullmatch(value.strip()) \
                    and not any(w in value.casefold() for w in ('url', 'var(', 'expression', 'attr(')):
                sample = '<div class="box"' + _style_attr(['box-shadow:' + value.strip()]) + '></div>'
            rows.append(f'<tr data-token="{_esc(token["name"])}"><th scope="row">{_esc(_line(token["name"], 80))}</th>'
                        f'<td><code>{_esc(_line(value, 120))}</code></td><td>{sample}</td><td>{_esc(_line(token.get("usage", ""), 300))}</td></tr>')
        if rows:
            parts.append(f'<h3>{_esc(_line(family, 60))}</h3>' + _table(['Token', 'Value', 'Sample', 'Usage'], rows, f'{family} tokens'))
    return '\n'.join(parts) if parts else '<p class="empty">No spacing, radius or other tokens</p>'


def _components(data: dict) -> str:
    components = data.get('components') or []
    if not components:
        return '<p class="empty">No components</p>'
    cards = []
    for comp in components:
        link = (f'<p><a href="{_esc(quote(comp["rel"], safe="/"))}">Open preview.html</a> '
                f'<span class="mut">(a separate page; the viewer does not embed it)</span></p>') if comp.get('rel') else ''
        cards.append(f'<article class="card" data-component="{_esc(comp["name"])}"><h3>{_esc(_line(comp["name"], 80))} '
                     f'<span class="mut">{_esc(_line(comp.get("group", ""), 60))}</span></h3>'
                     f'<p>{_esc(comp.get("summary", ""))}</p>'
                     + (f'<p class="mut"><code>{_esc(comp["marker"])}</code></p>' if comp.get('marker') else '')
                     + link + comp.get('readme_html', '') + '</article>')
    return '\n'.join(cards)


def _assets(data: dict) -> str:
    assets = data.get('assets') or []
    readmes = data.get('asset_readmes') or {}
    groups = sorted({a['group'] for a in assets} | set(readmes))
    if not groups:
        return '<p class="empty">No assets</p>'
    parts = []
    for group in groups:
        items = []
        for asset in (a for a in assets if a['group'] == group):
            if asset.get('inline'):
                shown = f'<img alt="{_esc(_line(asset["path"], 160))}" src="{asset["inline"]}">'
            else:
                shown = '<span class="mut">listed, not embedded</span>'
            items.append(f'<li data-asset="{_esc(asset["path"])}"><code>{_esc(_line(asset["path"], 160))}</code> '
                         f'<span class="mut">{asset["size"]} bytes</span><br>{shown}</li>')
        parts.append(f'<h3>{_esc(_line(group or "(no group)", 80))}</h3>' + readmes.get(group, '')
                     + ('<ul class="plain">' + ''.join(items) + '</ul>' if items else '<p class="empty">No files</p>'))
    return '\n'.join(parts)


def _tree(entries: list[tuple[str, int]], sizes: bool) -> str:
    root: dict = {}
    for path, size in entries:
        node = root
        parts = path.split('/')
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            node = child if isinstance(child, dict) else {}
        node[parts[-1]] = size

    def count(node: dict) -> int:
        return sum(count(v) if isinstance(v, dict) else 1 for v in node.values())

    def render(node: dict, depth: int) -> str:
        items = []
        for name in sorted(node):
            child = node[name]
            if isinstance(child, dict):
                total = count(child)
                label = _esc(_line(name, 80)) + '/' + ('' if sizes else f' <span class="mut">({total} {"file" if total == 1 else "files"})</span>')
                items.append(f'<li><details{" open" if depth < 1 or sizes else ""}><summary>{label}</summary>'
                             f'{render(child, depth + 1)}</details></li>')
            elif sizes:
                items.append(f'<li><code>{_esc(_line(name, 80))}</code> <span class="mut">{child} bytes</span></li>')
            elif depth == 0:
                items.append(f'<li><code>{_esc(_line(name, 80))}</code></li>')
        return '<ul class="plain">' + ''.join(items) + '</ul>'

    return render(root, 0) if root else '<p class="empty">No files</p>'


def _overview_value(design: str, label: str) -> str:
    for line in v3._section_lines(design, 'Overview'):
        text = line.lstrip()
        text = text[1:].lstrip() if text[:1] in ('-', '*') else text
        text = text.lstrip('*')
        if text[:len(label)].casefold() == label.casefold():
            rest = text[len(label):].lstrip('*').lstrip()
            if rest.startswith(':'):
                return rest[1:].strip().strip('*').strip()
    return ''


def _overview(data: dict) -> str:
    index = data.get('index') if isinstance(data.get('index'), dict) else {}
    system = data.get('canonical', {}).get('system') if isinstance(data.get('canonical'), dict) else None
    system = system if isinstance(system, dict) else {}
    design = data.get('design_md') or ''
    cover = data.get('cover_svg')
    cover = sanitize_svg(cover) if isinstance(cover, str) and cover else None  # the page checks again what it embeds
    texts = (_scan_svg(cover) or []) if cover else []
    tagline = texts[1] if len(texts) > 1 else _summary(data.get('readme') or '')
    facts = [('Status', system.get('status')), ('Version', system.get('version')), ('System id', system.get('id')),
             ('Owner', _overview_value(design, 'Owner'))]
    rows = ''.join(f'<dt>{label}</dt><dd>{_esc(_line(value))}</dd>' for label, value in facts if value)
    body = '\n'.join(v3._section_lines(design, 'Overview')).strip()
    entries = [(f['path'], f['size']) for f in data.get('files') or []]
    return '\n'.join((
        f'<figure aria-label="Cover">{isolate_svg_ids(cover)}</figure>' if cover else '<p class="empty">No cover image</p>',
        f'<p class="lead">{_esc(_line(index.get("title", "")))}'
        + (f' <span class="mut">{_esc(_line(tagline))}</span>' if tagline else '') + '</p>',
        f'<dl>{rows}</dl>' if rows else '',
        '<h3>From DESIGN.md</h3>' + (render_markdown(body, 4) if body else '<p class="empty">DESIGN.md has no Overview section</p>'),
        '<h3>Package tree</h3>' + _tree(entries, False)))


def _agents(data: dict) -> str:
    value = _overview_value(data.get('design_md') or '', 'Read order')
    items = [_line(p, 120) for p in value.split(',') if p.strip()]
    order = ('<ol>' + ''.join(f'<li><code>{_esc(i.strip("`"))}</code></li>' for i in items) + '</ol>') if items \
        else '<p class="empty">DESIGN.md has no Read order line</p>'
    rows = [('Claude Design', '<code>README.md</code> inside the package', 'Reads the package folder itself; wrapper files are refused there.'),
            ('Claude Code', '<code>CLAUDE.md</code> in the parent folder', 'Holds <code>@AGENTS.md</code>; that file points at <code>design-system/DESIGN.md</code>.'),
            ('Codex', '<code>AGENTS.md</code> in the parent folder', 'Points at <code>design-system/DESIGN.md</code>.'),
            ('Gemini CLI', '<code>GEMINI.md</code> in the parent folder', 'A short pointer at <code>design-system/DESIGN.md</code>.')]
    table = _table(['Harness', 'First file', 'Route'], [f'<tr><th scope="row">{a}</th><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows],
                   'How each tool finds the system')
    return '<h3>Read order from DESIGN.md</h3>' + order + '<h3>By harness</h3>' + table


_SCRIPT = ('(function(){var q=document.getElementById("q");if(!q){return;}var rows=document.querySelectorAll("[data-token]");'
           'var n=document.getElementById("qn");q.addEventListener("input",function(){var s=q.value.toLowerCase().trim();var c=0;'
           'rows.forEach(function(r){var m=!s||r.textContent.toLowerCase().indexOf(s)>-1;r.hidden=!m;if(m){c++;}});'
           'if(n){n.textContent=s?c+" of "+rows.length+" tokens shown":"";}});})();')

_STYLE = (
    ':root{color-scheme:light dark;--bg:#fff;--fg:#1b1b1f;--mut:#5c5c66;--line:#d3d3dc;--card:#f4f4f8;--acc:#0b5cad}'
    '@media(prefers-color-scheme:dark){:root{--bg:#131317;--fg:#ececf1;--mut:#a6a6b2;--line:#35353f;--card:#1c1c22;--acc:#7ab4f5}}'
    '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;'
    'overflow-wrap:anywhere}header,main,nav{max-width:72rem;margin:0 auto;padding-left:16px;padding-right:16px}header{padding-top:24px}'
    'h1{font-size:1.75rem;margin:0 0 4px}h2{font-size:1.4rem;margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}'
    'h3{font-size:1.1rem;margin:20px 0 8px}h4,h5,h6{font-size:1rem;margin:14px 0 6px}'
    'nav{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:center;padding-top:10px;padding-bottom:10px;position:sticky;top:0;'
    'background:var(--bg);border-bottom:1px solid var(--line)}nav a,main a{color:var(--acc)}'
    'nav label{margin-left:auto}input{font:inherit;padding:4px 8px;max-width:100%;color:var(--fg);background:var(--bg);'
    'border:1px solid var(--line);border-radius:6px}'
    'section{padding:20px 0 28px;scroll-margin-top:56px}.scroll{overflow-x:auto}'
    'table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}'
    'caption{text-align:left;padding-bottom:4px}code,pre{font:.85rem/1.4 ui-monospace,Menlo,Consolas,monospace;background:var(--card)}'
    'pre{padding:10px;overflow:auto}.sw{display:inline-block;width:1.1rem;height:1.1rem;border:1px solid var(--line);'
    'vertical-align:middle;margin-right:6px}.card{border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:12px 0;'
    'background:var(--card)}.bar{height:10px;background:var(--acc);max-width:100%}.box{width:56px;height:36px;background:var(--card);'
    'border:1px solid var(--line)}img,svg{max-width:100%;height:auto}figure{margin:0 0 16px}.mut{color:var(--mut)}.lead{font-size:1.1rem}'
    '.plain{list-style:none;padding-left:18px}.plain .plain{padding-left:14px}dt{font-weight:600}dd{margin:0 0 6px}'
    '@supports selector(:has(a)){main:has(section:target) section:not(:target){display:none}'
    'main:not(:has(section:target)) section:not(#overview){display:none}}')


def render_viewer(data: dict) -> str:
    """The self-contained ``viewer.html`` text for ``collect_package`` data. Same data, same bytes: nothing time- or order-dependent."""
    index = data.get('index') if isinstance(data.get('index'), dict) else {}
    tokens = data.get('tokens') if isinstance(data.get('tokens'), dict) else {}
    canonical = data.get('canonical') if isinstance(data.get('canonical'), dict) else {}
    title = _line(index.get('title') or 'Design system', 160)
    bodies = {'overview': _overview(data), 'colors': _colors(tokens, canonical), 'typography': _typography(tokens),
              'spacing': _spacing(tokens), 'components': _components(data), 'assets': _assets(data),
              'files': '<p class="mut">Sizes of text files are measured with LF line endings.</p>\n'
                       + _tree([(f['path'], f['size']) for f in data.get('files') or []], True), 'agents': _agents(data)}
    nav = ''.join(f'<a href="#{key}">{label}</a>' for key, label in SCREENS)
    sections = '\n'.join(f'<section id="{key}" aria-labelledby="h-{key}"><h2 id="h-{key}">{label}</h2>\n{bodies[key]}\n</section>'
                         for key, label in SCREENS)
    return '\n'.join((
        '<!doctype html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<meta http-equiv="Content-Security-Policy" content="{viewer_csp(_SCRIPT)}">',
        f'<title>{_esc(title + TITLE_SUFFIX)}</title>', f'<style>{_STYLE}</style>', '</head>', '<body>',
        f'<header><h1>{_esc(title)}</h1><p class="mut">Static viewer generated from the package files. Not a Claude Design render.</p></header>',
        f'<nav aria-label="Screens">{nav}<label>Filter tokens <input id="q" type="search"></label><span id="qn" class="mut" role="status"></span></nav>',
        f'<main>\n{sections}\n</main>', f'<script>{_SCRIPT}</script>', '</body>', '</html>', ''))
