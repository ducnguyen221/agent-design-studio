"""Original, anonymous contract fixtures; no external assets or runtime claims."""
import importlib.util
import hashlib
import tempfile
import unittest
import json
import io
import os
import re
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_system_v3 as v3  # noqa: E402

MODULE = Path(__file__).with_name('verify-design-system.py')
spec = importlib.util.spec_from_file_location('design_system_verifier', MODULE)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class TokenTests(unittest.TestCase):
    def test_supported_and_alias(self):
        tokens = {'base': {'$type': 'dimension', '$value': {'value': 4, 'unit': 'px'}},
                  'space': {'$type': 'dimension', '$value': '{base}'}}
        self.assertEqual(verifier.validate_tokens(tokens), [])

    def test_large_integer_number(self):
        self.assertEqual(verifier.validate_tokens({'x': {'$type': 'number', '$value': 10 ** 400}}), [])

    def test_unicode_and_space_alias_names(self):
        self.assertEqual(verifier.validate_tokens({'large size': {'$type': 'number', '$value': 1},
            'khoảng': {'$type': 'number', '$value': '{large size}'},
            'alias': {'$type': 'number', '$value': '{khoảng}'}}), [])

    def test_failures(self):
        cases = [({'$type': 'color', '$value': '#fff'}, 'invalid_value'),
                 ({'$type': 'shadow', '$value': []}, 'unsupported_type'),
                 ({'$type': 'number', '$value': True}, 'invalid_value'),
                 ({'$type': 'dimension', '$value': '{missing}'}, 'missing_target'),
                 ({'$type': 'number', '$value': '{other.json#x}'}, 'unsupported_reference')]
        for token, code in cases:
            with self.subTest(code=code):
                self.assertTrue(any(code in error for error in verifier.validate_tokens({'x': token})))

    def test_cycle_and_type(self):
        self.assertTrue(any('reference_cycle' in e for e in verifier.validate_tokens({
            'a': {'$type': 'number', '$value': '{b}'}, 'b': {'$type': 'number', '$value': '{a}'}})))
        self.assertTrue(any('type_mismatch' in e for e in verifier.validate_tokens({
            'a': {'$type': 'number', '$value': '{b}'}, 'b': {'$type': 'fontWeight', '$value': 400}})))

    def test_group_inheritance(self):
        self.assertEqual(verifier.validate_tokens({'scale': {'$type': 'number', 'one': {'$value': 1}}}), [])

    def test_all_supported_values_and_malformed(self):
        valid = {'color': {'colorSpace': 'srgb', 'components': [0, .5, 1], 'alpha': .5},
                 'duration': {'value': 200, 'unit': 'ms'}, 'fontFamily': ['Example', 'sans-serif'],
                 'fontWeight': 700, 'number': 0, 'dimension': {'value': 1, 'unit': 'rem'}}
        self.assertEqual(verifier.validate_tokens({k: {'$type': k, '$value': v} for k, v in valid.items()}), [])
        for value in [[], None, {}, {'x': 1}, {'x': {'$type': [], '$value': 1}},
                      {'a.b': {'$type': 'number', '$value': 1}},
                      {'x': {'$type': 'number', '$value': 1, 'child': {}}}]:
            with self.subTest(value=value):
                self.assertTrue(verifier.validate_tokens(value))

    def test_invalid_type_values(self):
        bad = [('color', {'colorSpace': 'srgb', 'components': [1, 0, 2]}),
               ('color', {'colorSpace': 'srgb', 'components': [1, 0, 0], 'alpha': True}),
               ('dimension', {'value': 1, 'unit': 'em'}), ('duration', {'value': 2, 'unit': []}),
               ('fontFamily', []), ('fontWeight', 1001), ('number', float('nan'))]
        for kind, value in bad:
            with self.subTest(kind=kind):
                self.assertTrue(verifier.validate_tokens({'x': {'$type': kind, '$value': value}}))


class PathTests(unittest.TestCase):
    def test_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.css').write_text(':root {}', encoding='utf-8')
            self.assertTrue(verifier.safe_path(root, 'source.css').is_file())
            for path in ['../escape', '/absolute', '.env', 'auth.json', 'node_modules/x', 'key.pem']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    verifier.safe_path(root, path)

    def test_manifest_existing_source_and_broken_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.css').write_text(':root {}', encoding='utf-8')
            document = {'schemaVersion': '1', 'system': {'id': 'example', 'version': '0.1', 'status': 'draft'},
                        'canonical': {'tokens': {'kind': 'repo-path', 'path': 'source.css'}}}
            self.assertEqual(verifier.validate_manifest(document, root), [])
            document['canonical']['tokens']['path'] = 'missing.css'
            self.assertTrue(any('missing_path' in error for error in verifier.validate_manifest(document, root)))

    def test_cli_and_manifest_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tokens.json').write_text(json.dumps({'x': {'$type': 'number', '$value': 2}}), encoding='utf-8')
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(verifier.main(['--root', directory, '--dtcg', 'tokens.json']), 0)
                self.assertEqual(verifier.main(['--root', directory, '--legacy-tokens', 'tokens.json']), 0)
                self.assertEqual(verifier.main(['--root', directory, '--dtcg', '.env']), 1)
            self.assertIn('legacy:', output.getvalue())
            self.assertEqual(errors.getvalue().strip(), 'input_error: --dtcg: excluded_path')
            for document in [None, {}, {'schemaVersion': '1', 'system': {'id': 'a', 'version': '1', 'status': 'bad'},
                             'canonical': {'tokens': {'path': '../outside'}}},
                             {'sections': [{'id': 'same'}, {'id': 'same'}]}, {'status': []}]:
                self.assertTrue(verifier.validate_manifest(document, root))

    def test_symlink_scope(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            try:
                (root / 'linked').symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest('host cannot create symlinks; not a passing security claim')
            with self.assertRaises(ValueError):
                verifier.safe_path(root, 'linked/file.css')

    def test_canonical_kind_and_partial_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.css').write_text('', encoding='utf-8')
            doc = {'schemaVersion': '1', 'system': {'id': 'a', 'version': '1', 'status': 'draft'},
                   'canonical': {'tokens': {'kind': 'url', 'path': 'source.css'}}}
            self.assertTrue(any('invalid_canonical' in e for e in verifier.validate_manifest(doc, root)))
            self.assertTrue(verifier.verify_pack(root))
            base = root / 'skills/design-system'
            base.mkdir(parents=True)
            (base / 'SKILL.md').write_text('create', encoding='utf-8')
            self.assertTrue(any('missing_skill_route' in e for e in verifier.verify_pack(root)))

    def test_external_canonical_pointer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            doc = {'schemaVersion': '1', 'system': {'id': 'a', 'version': '1', 'status': 'draft'},
                   'canonical': {'tokens': {'kind': 'external', 'url': 'https://www.figma.com/design/example'}}}
            self.assertEqual(verifier.validate_manifest(doc, root), [])
            for url in ['http://example.com', 'https://user:pass@example.com', 'file:///source',
                        'https://bad host/', 'https://example.com:bad/', 'https:///missing']:
                with self.subTest(url=url):
                    doc['canonical']['tokens']['url'] = url
                    self.assertTrue(verifier.validate_manifest(doc, root))
            doc['canonical']['tokens'] = {'kind': 'external', 'url': 'https://example.com', 'path': 'local.css'}
            self.assertTrue(verifier.validate_manifest(doc, root))

    def test_pack_checks_scope_before_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / 'skills/design-system'
            base.mkdir(parents=True)
            (base / 'SKILL.md').write_text('create', encoding='utf-8')
            with patch.object(verifier, 'safe_path', side_effect=ValueError('linked_path')) as guard, \
                 patch.object(Path, 'read_text', side_effect=AssertionError('unexpected content read')):
                self.assertTrue(verifier.verify_pack(root))
                self.assertTrue(guard.called)

    def test_win32_aliases_never_reach_content_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ['auth.json.', 'oauth_creds.json ', 'source.css.', 'folder /source.css']:
                with self.subTest(path=path), \
                     patch.object(Path, 'read_text', side_effect=AssertionError('unexpected content read')) as reader:
                    with self.assertRaises(ValueError):
                        verifier._load(root, path)
                    reader.assert_not_called()

    def test_resolved_sensitive_segment_never_reaches_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def resolved(path, *args, **kwargs):
                return root if path == root else root / 'auth.json'
            with patch.object(Path, 'resolve', resolved), \
                 patch.object(Path, 'read_text', side_effect=AssertionError('unexpected content read')) as reader:
                with self.assertRaises(ValueError):
                    verifier._load(root, 'source.css')
                reader.assert_not_called()

    def test_excluded_root_never_reaches_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for segment in ['.secret', 'node_modules', 'folder ']:
                resolved_root = root / segment
                def resolved(path, *args, **kwargs):
                    return resolved_root if path == root else resolved_root / 'tokens.json'
                with self.subTest(segment=segment), patch.object(Path, 'resolve', resolved), \
                     patch.object(Path, 'read_text', side_effect=AssertionError('unexpected content read')) as reader:
                    with self.assertRaises(ValueError):
                        verifier._load(root, 'tokens.json')
                    reader.assert_not_called()

    def test_fixture_design_navigation_and_contract(self):
        import re
        root = Path(__file__).resolve().parents[1] / 'skills/design-system/tests/fixture'
        required = {'design-system/README.md', 'design-system/components/Button/README.md',
                    'design-system/patterns/ActionFeedback.md', 'design-system/surfaces/web/rules.md',
                    'design-system/surfaces/web/screens/index.md', 'design-system/assets/Icons/README.md'}
        distances = {'design-system/DESIGN.md': 0}
        queue = list(distances)
        for name in queue:
            source = verifier.safe_path(root, name)
            text = source.read_text(encoding='utf-8')
            for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
                target = (source.parent / link.split('#')[0]).resolve()
                self.assertTrue(target.is_relative_to(root))
                self.assertTrue(target.is_file(), link)
                relative = target.relative_to(root).as_posix()
                if target.suffix == '.md' and relative not in distances:
                    distances[relative] = distances[name] + 1
                    queue.append(relative)
        self.assertTrue(required <= distances.keys(), required - distances.keys())
        self.assertTrue(all(distances[name] <= 3 for name in required))
        canonical = json.loads((root / 'design-system/canonical-map.json').read_text(encoding='utf-8'))
        self.assertEqual(v3.validate_canonical_map(canonical, root / 'design-system'), [])
        self.assertFalse((root / 'design-system/manifest.json').exists())

    def test_canonical_error_labels_do_not_echo_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for domain in ['tokens\nINJECTED', 'tokens\x1b[31m', 'tokens\rINJECTED']:
                doc = {'schemaVersion': '1', 'system': {'id': 'a', 'version': '1', 'status': 'draft'},
                       'canonical': {domain: {'kind': 'invalid'}}}
                errors = verifier.validate_manifest(doc, root)
                self.assertTrue(errors)
                self.assertEqual(errors, ['invalid_canonical: domain/source'])


# ---------------------------------------------------------------------------
# v3 package verifier (SPR-32 TK5). Fixtures below are original and anonymous.
# ---------------------------------------------------------------------------

def put(root, rel, content):
    target = Path(root) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=2)
    if isinstance(content, bytes):
        target.write_bytes(content)
    else:
        target.write_text(content, encoding='utf-8', newline='\n')


SECTIONS = ['Overview', 'Colors', 'Typography', 'Layout', 'Elevation & Depth', 'Shapes', 'Components', "Do's and Don'ts"]
OVERVIEW = '- Read order: README.md, tokens.json\n- Owner: Sample Studio\n- Status: draft\n'


def design_md(sections=SECTIONS, overview=OVERVIEW, extra=''):
    parts = ['---\nversion: alpha\nname: "Sample"\n---\n']
    for name in sections:
        parts.append(f'\n## {name}\n\n' + (overview if name == 'Overview' else 'Names tokens only.\n'))
    return ''.join(parts) + extra


def base_files(profile='full'):
    colors = [
        {'name': 'bg', 'value': {'light': '#ffffff', 'dark': '#111111'}, 'usage': 'page background'},
        {'name': 'text', 'value': {'light': '#111111', 'dark': '#f5f5f5'}, 'usage': 'body text'},
        {'name': 'accent', 'value': '#0057b8', 'usage': 'links and actions'},
        {'name': 'link', 'value': '{accent}', 'usage': 'inline link colour'},
    ]
    styles = [{'name': 'body', 'fontSize': '16px', 'fontWeight': 400, 'lineHeight': 1.5, 'usage': 'body copy'}]
    themes = [{'id': 'light', 'name': 'Light'}, {'id': 'dark', 'name': 'Dark'}]
    spacing = [{'name': 'space-1', 'value': '4px', 'usage': 'tight gap'}]
    radius = [{'name': 'radius-sm', 'value': '2px', 'usage': 'small corners'}]
    readme = '## Content fundamentals\n\nPlain words.\n\n## Visual foundations\n\nQuiet colour.\n\n## Iconography\n\nNone yet.\n'
    if profile == 'minimal':
        colors = [{'name': f'c{i}', 'value': f'#{i}{i}{i}{i}{i}{i}', 'usage': 'sample colour'} for i in range(1, 8)]
        colors[0]['name'], colors[1]['name'] = 'bg', 'text'
        colors[0]['value'], colors[1]['value'] = '#ffffff', '#111111'
        themes = themes[:1]
        styles = [{'name': f's{i}', 'fontSize': f'{12 + i}px', 'fontWeight': 400, 'lineHeight': 1.4, 'usage': 'sample style'} for i in range(5)]
        spacing = [{'name': f'space-{i}', 'value': f'{4 * i}px', 'usage': 'gap'} for i in range(1, 5)]
        radius = [{'name': f'radius-{i}', 'value': f'{i}px', 'usage': 'corner'} for i in range(1, 4)]
        readme = 'A sample studio kit with a quiet palette, a small type scale and a short list of spacing steps for tests.\n'
        colors_for_pairs = [{'fg': 'text', 'bg': 'bg', 'min': 4.5, 'large': False}]
    else:
        colors_for_pairs = [{'fg': 'text', 'bg': 'bg', 'min': 4.5, 'large': False}]
    tokens = {
        'color': {'themes': themes, 'tokens': colors},
        'type': {'fonts': [], 'families': {'sans': 'Inter, sans-serif'},
                 'groups': [{'name': 'Body', 'family': 'sans', 'styles': styles}]},
        'spacing': {'tokens': spacing},
        'radius': {'tokens': radius},
    }
    return {
        'design-system.json': {'v': 3, 'layout': 'files', 'title': 'Sample Studio', 'namespace': 'SampleStudio',
                               'createdOnFiles': {'v': 1, 'at': '2026-10-22T00:00:00Z'}},
        'README.md': readme,
        'tokens.json': tokens,
        'DESIGN.md': design_md(),
        'canonical-map.json': {'schemaVersion': '1', 'system': {'id': 'sample', 'version': '0.1.0', 'status': 'draft'},
                               'profile': profile, 'canonical': {'brand': {'kind': 'file', 'path': 'README.md'}},
                               'components': {}, 'checks': {'contrast': colors_for_pairs}, 'decisions': []},
        'components/Cover/preview.html': '<!-- @dsCard height=300 -->\n<svg viewBox="0 0 960 300"><text>Sample</text><text>Tagline</text></svg>\n',
    }


KEYMAP = {'components__Cover__preview__html': 'components/Cover/preview.html',
          'components__Cover__README__md': 'components/Cover/README.md',
          'components__Cover__Cover__d__ts': 'components/Cover/Cover.d.ts',
          'components__bundle__js': 'components/bundle.js', 'README__md': 'README.md', 'DESIGN__md': 'DESIGN.md',
          'design__system__json': 'design-system.json', 'tokens__json': 'tokens.json',
          'canonical__map__json': 'canonical-map.json'}


def make(root, profile='full', **overrides):
    """Write a valid package; keyword names map to paths through KEYMAP, a None value drops the file."""
    files = base_files(profile)
    for key, value in overrides.items():
        files[KEYMAP[key]] = value
    for rel, content in files.items():
        if content is not None:
            put(root, rel, content)
    return Path(root)


def edit_json(root, rel, change):
    path = Path(root) / rel
    doc = json.loads(path.read_text(encoding='utf-8'))
    change(doc)
    put(root, rel, doc)


def tok(**families):
    """Tokens document with a single light theme; each keyword is a family token list."""
    doc = {'color': {'themes': [{'id': 'light', 'name': 'Light'}], 'tokens': []}}
    for family, tokens in families.items():
        if family == 'color':
            doc['color']['tokens'] = tokens
        else:
            doc[family] = {'tokens': tokens}
    return doc


def color(name, value, usage='sample usage'):
    return {'name': name, 'value': value, 'usage': usage}


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = verifier.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TokensV3Tests(unittest.TestCase):
    def test_valid_document(self):
        self.assertEqual(v3.validate_tokens_v3(base_files()['tokens.json']), [])

    def test_tokens_dtcg_map_rejected(self):
        doc = {'color': {'bg': {'$type': 'color', '$value': {'colorSpace': 'srgb', 'components': [1, 1, 1]}}}}
        self.assertIn('token_shape: tokens.json: color', v3.validate_tokens_v3(doc))
        self.assertIn('token_shape: tokens.json: <root>', v3.validate_tokens_v3([]))

    def test_tokens_shape_details(self):
        doc = tok(color=[color('a', '#fff'), 'oops', {'name': 'b'}, {'name': 3, 'value': '#000'}])
        errors = v3.validate_tokens_v3(doc)
        self.assertIn('token_shape: tokens.json: color[1]', errors)
        self.assertIn('token_shape: tokens.json: color[2]', errors)
        self.assertIn('token_shape: tokens.json: color[3]', errors)
        doc = tok(color=[color('a', '#fff')])
        doc['spacing'] = {'tokens': {'x': 1}}
        doc['radius'] = 'x'
        errors = v3.validate_tokens_v3(doc)
        self.assertIn('token_shape: tokens.json: spacing', errors)
        self.assertIn('token_shape: tokens.json: radius', errors)
        doc = tok()
        del doc['color']['themes']
        self.assertIn('token_shape: tokens.json: color.themes', v3.validate_tokens_v3(doc))

    def test_tokens_missing_usage(self):
        doc = tok(color=[{'name': 'bg', 'value': '#fff'}, color('b', '#000', usage=''), color('c', '#000', usage='x' * 1001),
                         color('d', '#000', usage=5)])
        errors = v3.validate_tokens_v3(doc)
        self.assertIn('missing_usage: tokens.json: color.bg', errors)
        self.assertIn('missing_usage: tokens.json: color.b', errors)
        self.assertIn('missing_usage: tokens.json: color.c', errors)
        self.assertIn('missing_usage: tokens.json: color.d', errors)
        self.assertEqual(v3.validate_tokens_v3(tok(color=[color('ok', '#000', usage='x' * 1000)])), [])

    def test_tokens_forbidden_color_syntax(self):
        doc = tok(color=[color('a', 'var(--x)'), color('b', 'color-mix(in srgb, red, blue)'), color('c', 'red'),
                         color('d', 'url(x.png)')])
        errors = v3.validate_tokens_v3(doc)
        for name in 'abcd':
            self.assertIn(f'forbidden_color_syntax: tokens.json: color.{name}', errors)
        self.assertEqual(len([e for e in errors if e.startswith('forbidden_color_syntax')]), 4)

    def test_tokens_invalid_values(self):
        doc = tok(color=[color('a', '#12'), color('b', 'rgb(1 2)'), color('c', 7), color('d', 'hsl(a b c)'),
                         color('e', 'color(display-p3 0.1 0.2 0.3)'), color('f', 'lab(50 20 -10 / 0.5)')],
                  spacing=[color('s1', '4px'), color('s2', 'big'), color('s3', 4), color('s4', True)],
                  radius=[color('r1', '50%'), color('r2', '0')], shadow=[color('sh', '0 1px 2px #0003'), color('sh2', [])])
        errors = v3.validate_tokens_v3(doc)
        for code in ['color.a', 'color.b', 'color.c', 'color.d', 'spacing.s2', 'spacing.s4', 'shadow.sh2']:
            self.assertIn(f'invalid_value: tokens.json: {code}', errors)
        self.assertEqual(len([e for e in errors if e.startswith('invalid_value')]), 7)

    def test_tokens_alias_missing_cycle_depth(self):
        chain = [color(f'n{i}', f'{{n{i + 1}}}') for i in range(18)] + [color('n18', '#000')]
        doc = tok(color=[color('m', '{nowhere}'), color('c1', '{c2}'), color('c2', '{c1}'), color('self', '{self}')] + chain)
        errors = v3.validate_tokens_v3(doc)
        self.assertIn('missing_target: tokens.json: color.m -> {nowhere}', errors)
        self.assertIn('reference_cycle: tokens.json: color.c1: c1 -> c2 -> c1', errors)
        self.assertIn('reference_cycle: tokens.json: color.self: self -> self', errors)
        self.assertEqual([e for e in errors if e.startswith('alias_too_deep')], ['alias_too_deep: tokens.json: color.n0: 18'])
        ok = tok(color=[color(f'n{i}', f'{{n{i + 1}}}') for i in range(16)] + [color('n16', '#000')])
        self.assertEqual(v3.validate_tokens_v3(ok), [])
        edge = tok(color=[color(f'n{i}', f'{{n{i + 1}}}') for i in range(17)] + [color('n17', '#000')])
        self.assertEqual(v3.validate_tokens_v3(edge), ['alias_too_deep: tokens.json: color.n0: 17'])

    def test_tokens_duplicate_across_families(self):
        doc = tok(color=[color('a', '#000')], spacing=[color('x', '4px')], radius=[color('x', '2px')])
        self.assertEqual(v3.validate_tokens_v3(doc), ['duplicate_name: tokens.json: x: spacing, radius'])
        doc = tok(color=[color('a', '#000'), color('a', '#fff')])
        self.assertIn('duplicate_name: tokens.json: a: color, color', v3.validate_tokens_v3(doc))

    def test_tokens_name_rules_and_label_hygiene(self):
        doc = tok(color=[color('-bad', '#000'), color('x' * 65, '#000'), color('bad\nname\x1b[31m', '#000')])
        errors = v3.validate_tokens_v3(doc)
        self.assertEqual(len([e for e in errors if e.startswith('token_name_invalid')]), 3)
        self.assertTrue(all('\n' not in e and '\x1b' not in e for e in errors))

    def test_tokens_limits(self):
        doc = tok(color=[color('a', '#000')])
        doc['color']['themes'] = [{'id': f't{i}', 'name': f'T{i}'} for i in range(9)]
        self.assertIn('limit_exceeded: tokens.json: color.themes: 9 > 8', v3.validate_tokens_v3(doc))
        many = tok(color=[color(f'c{i}', '#000') for i in range(601)], spacing=[color(f's{i}', '1px') for i in range(61)])
        errors = v3.validate_tokens_v3(many)
        self.assertIn('limit_exceeded: tokens.json: color.tokens: 601 > 600', errors)
        self.assertIn('limit_exceeded: tokens.json: spacing.tokens: 61 > 60', errors)
        families = tok(color=[color('a', '#000')])
        for i in range(12):
            families[f'f{i}'] = {'tokens': [color(f'f{i}x', 'a')]}
        errors = v3.validate_tokens_v3(families)
        self.assertIn('limit_exceeded: tokens.json: families: 13 > 12', errors)
        self.assertFalse([e for e in errors if e.startswith('unsupported_family')])

    def test_tokens_motion_family(self):
        doc = tok(color=[color('a', '#000')])
        doc['motion'] = {'tokens': []}
        doc['bad family'] = {'tokens': []}
        errors = v3.validate_tokens_v3(doc)
        self.assertIn('unsupported_family: tokens.json: motion', errors)
        self.assertIn('unsupported_family: tokens.json: bad family', errors)

    def test_tokens_per_theme_alias_and_inherit(self):
        doc = tok(color=[color('base', '#111111'), color('bg', {'light': '#ffffff', 'dark': '{base}'}),
                         color('late', {'dark': '#222222'}), color('only', {'light': '#333333'})])
        doc['color']['themes'].append({'id': 'dark', 'name': 'Dark'})
        self.assertEqual(v3.validate_tokens_v3(doc), [])
        theme_ids = ['light', 'dark']
        self.assertEqual(v3._theme_value(doc['color']['tokens'][3], theme_ids, 'dark'), '#333333')
        self.assertEqual(v3._theme_value(doc['color']['tokens'][2], theme_ids, 'light'), '#222222')
        self.assertEqual(v3._theme_value(doc['color']['tokens'][1], theme_ids, 'dark'), '{base}')
        bad = tok(color=[color('x', {'ghost': '#000'}), color('y', {}), color('z', {'light': 4}), color('w', {'light': 'nope(1)'})])
        errors = v3.validate_tokens_v3(bad)
        self.assertIn('invalid_value: tokens.json: color.x@ghost', errors)
        self.assertIn('invalid_value: tokens.json: color.y', errors)
        self.assertIn('invalid_value: tokens.json: color.z@light', errors)
        self.assertIn('invalid_value: tokens.json: color.w@light', errors)
        alias = tok(color=[color('a', {'light': '{missing}'})])
        self.assertIn('missing_target: tokens.json: color.a -> {missing}', v3.validate_tokens_v3(alias))

    def test_type_family_shapes(self):
        base = base_files()['tokens.json']
        def variant(change):
            doc = json.loads(json.dumps(base))
            change(doc['type'])
            return v3.validate_tokens_v3(doc)
        self.assertIn('token_shape: tokens.json: type.families', variant(lambda t: t.update(families=[])))
        self.assertIn('token_shape: tokens.json: type.fonts', variant(lambda t: t.update(fonts={})))
        self.assertIn('token_shape: tokens.json: type.fonts[0]', variant(lambda t: t.update(fonts=['x'])))
        self.assertIn('token_shape: tokens.json: type.groups', variant(lambda t: t.update(groups={})))
        self.assertIn('token_shape: tokens.json: type.groups[0]', variant(lambda t: t.update(groups=[3])))
        self.assertIn('token_shape: tokens.json: type.groups[0].styles', variant(lambda t: t['groups'][0].update(styles='x')))
        self.assertIn('token_shape: tokens.json: type.groups[0].styles[0]', variant(lambda t: t['groups'][0].update(styles=[1])))
        self.assertIn('invalid_value: tokens.json: type.body', variant(lambda t: t['groups'][0]['styles'][0].update(fontSize='huge')))
        self.assertIn('invalid_value: tokens.json: type.body', variant(lambda t: t['groups'][0]['styles'][0].update(fontWeight=0)))
        self.assertIn('invalid_value: tokens.json: type.body', variant(lambda t: t['groups'][0]['styles'][0].update(lineHeight=12)))
        self.assertIn('invalid_value: tokens.json: type.body', variant(lambda t: t['groups'][0]['styles'][0].update(family='ghost')))
        self.assertIn('token_name_invalid: tokens.json: type.-x', variant(lambda t: t['groups'][0]['styles'].append({'name': '-x'})))
        self.assertIn('duplicate_name: tokens.json: body: type, type', variant(lambda t: t['groups'][0]['styles'].append({'name': 'body'})))
        for ok_weight in ('normal', 'bold', '300 800', 700, 1000):
            self.assertEqual(variant(lambda t: t['groups'][0]['styles'][0].update(fontWeight=ok_weight)), [])
        self.assertIn('limit_exceeded: tokens.json: type.groups: 13 > 12',
                      variant(lambda t: t.update(groups=[{'name': f'g{i}', 'styles': []} for i in range(13)])))
        self.assertIn('limit_exceeded: tokens.json: type.styles: 81 > 80',
                      variant(lambda t: t.update(groups=[{'name': 'g', 'styles': [{'name': f's{i}'} for i in range(81)]}])))

    def test_font_file_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = base_files()['tokens.json']
            doc['type']['fonts'] = [{'family': 'Brand', 'file': 'Brand.woff2'}]
            self.assertIn('font_file_missing: fonts/Brand.woff2', v3.validate_tokens_v3(doc, Path(directory)))
            self.assertEqual(v3.validate_tokens_v3(doc), [])
            doc['type']['fonts'] = [{'file': '../escape.woff2'}, {'file': '.env'}]
            errors = v3.validate_tokens_v3(doc, Path(directory))
            self.assertIn('refused_sensitive_path: fonts/../escape.woff2', errors)
            self.assertIn('refused_sensitive_path: fonts/.env', errors)
            self.assertNotIn('font_file_missing: fonts/.env', errors)

    def test_font_sensitive_or_escaping_paths_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = base_files()['tokens.json']
            for name in ('../escape.woff2', '.env', 'x.pem', 'sub/../../secret.txt', 'C:/Windows/win.ini', '..\\.env',
                         'credentials.woff2', '%2e%2e/.env', 'dist/a.woff2'):
                doc['type']['fonts'] = [{'file': name}]
                with self.subTest(name=name):
                    self.assertEqual(v3.validate_tokens_v3(doc, Path(directory)), [f'refused_sensitive_path: fonts/{name}'])
            doc['type']['fonts'] = [{'file': 'plain-missing.woff2'}]
            self.assertEqual(v3.validate_tokens_v3(doc, Path(directory)), ['font_file_missing: fonts/plain-missing.woff2'])

    def test_font_file_invalid_and_too_large(self):
        with tempfile.TemporaryDirectory() as directory:
            put(directory, 'fonts/good.woff2', b'wOF2' + b'\0' * 100)
            put(directory, 'fonts/bad.ttf', b'nope' + b'\0' * 100)
            put(directory, 'fonts/big.otf', b'OTTO' + b'\0' * 750001)
            put(directory, 'fonts/edge.otf', b'OTTO' + b'\0' * 749996)
            doc = base_files()['tokens.json']
            doc['type']['fonts'] = [{'file': n} for n in ('good.woff2', 'bad.ttf', 'big.otf', 'edge.otf')]
            errors = v3.validate_tokens_v3(doc, Path(directory))
            self.assertEqual(errors, ['font_file_invalid: fonts/bad.ttf',
                                      'font_file_too_large: fonts/big.otf: 750005 raw, 1000008 stored > 1000000'])


class ReadmeTests(unittest.TestCase):
    FULL = '## Content fundamentals\n\nx\n\n## Visual foundations\n\ny\n\n## Iconography\n\nz\n'

    def test_readme_full_sections(self):
        self.assertEqual(v3.validate_readme(self.FULL, len(self.FULL), 'full', set()), ([], []))
        errors, _ = v3.validate_readme('## Content fundamentals\n\nx\n', 30, 'full', set())
        self.assertEqual(errors, ['readme_missing_section: README.md: Visual foundations',
                                  'readme_missing_section: README.md: Iconography'])
        errors, _ = v3.validate_readme(self.FULL, 200001, 'full', set())
        self.assertEqual(errors, ['readme_too_large: README.md: 200001 > 200000'])

    def test_readme_minimal_paragraph(self):
        text = 'A quiet studio kit with a small palette and a short type scale, written to be read in one go by a person.\n'
        self.assertEqual(v3.validate_readme(text, len(text), 'minimal', set()), ([], []))
        errors, _ = v3.validate_readme('Too short.\n', 11, 'minimal', set())
        self.assertEqual(errors, ['minimal_profile_violation: README.md: paragraph 10 < 80 characters'])
        errors, _ = v3.validate_readme(text + '\n' + text, 2 * len(text) + 1, 'minimal', set())
        self.assertEqual(errors, ['minimal_profile_violation: README.md: 2 paragraphs, expected 1'])
        errors, _ = v3.validate_readme('', 0, 'minimal', set())
        self.assertEqual(len(errors), 1)

    def test_readme_forbidden_section(self):
        text = self.FULL + '\n## Provenance\n\nx\n\n### Next steps\n\ny\n\n```\n## Provenance\n```\n'
        errors, _ = v3.validate_readme(text, len(text), 'full', set())
        self.assertEqual(errors, ['readme_forbidden_section: README.md: Provenance',
                                  'readme_forbidden_section: README.md: Next steps'])
        errors, _ = v3.validate_readme('# Sample Studio\n\n' + self.FULL, 100, 'full', set(), title='Sample Studio')
        self.assertEqual(errors, ['readme_forbidden_section: README.md: # Sample Studio'])
        errors, _ = v3.validate_readme('# Other\n\n' + self.FULL, 100, 'full', set(), title='Sample Studio')
        self.assertEqual(errors, [])

    def test_readme_unknown_token_warns(self):
        text = self.FULL + '\nUse `brand-blue` and `accent-2`, never `npm`, `README.md` or `bg`.\n\n```\n`fenced-name`\n```\n'
        _, warnings = v3.validate_readme(text, len(text), 'full', {'bg', 'accent-2'})
        self.assertEqual(warnings, ['readme_unknown_token: README.md: brand-blue'])


class ComponentTests(unittest.TestCase):
    def verify(self, directory, profile=None):
        return v3.verify_package(Path(directory), profile)

    def test_cover_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html=None)
            self.assertIn('cover_missing: components/Cover/preview.html', self.verify(directory)[0])

    def test_card_marker_line_one(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html='\n<!-- @dsCard height=300 -->\n<svg></svg>\n')
            self.assertIn('card_marker_missing: components/Cover/preview.html', self.verify(directory)[0])
        self.assertEqual(v3.validate_preview('<!-- @dsCard -->\n<p>x</p>', 'components/A/preview.html'), [])
        self.assertEqual(v3.validate_preview('﻿<!-- @dsCard height=100 -->\n', 'components/A/preview.html'), [])

    def test_cover_shape_and_not_bare(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html='<!-- @dsCard height=300 -->\n<svg></svg><svg></svg>\n',
                 components__Cover__README__md='# Cover\n', components__Cover__Cover__d__ts='export {}',
                 components__bundle__js='/* @ds-bundle {"name":"Cover","version":1} */\n')
            errors = self.verify(directory)[0]
            self.assertIn('cover_shape: components/Cover/preview.html: 2 svg', errors)
            self.assertIn('cover_not_bare: components/Cover/README.md', errors)
            self.assertIn('cover_not_bare: components/Cover/Cover.d.ts', errors)
            self.assertIn('cover_not_bare: components/bundle.js: bundle header lists Cover', errors)
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__bundle__js='/* @ds-bundle {"name":"Button"} */\n')
            self.assertEqual([e for e in self.verify(directory)[0] if e.startswith('cover_')], [])

    def test_preview_forbidden_tag_iframe(self):
        text = '<!-- @dsCard -->\n<IFRAME src="x"></IFRAME><object></object><embed><portal></portal><noscript></noscript><frame>\n<p>frameset ok</p>'
        errors = v3.validate_preview(text, 'components/A/preview.html')
        self.assertEqual(errors, [f'forbidden_tag: components/A/preview.html: {t}' for t in
                                  ('iframe', 'frame', 'object', 'embed', 'portal', 'noscript')])
        big = '<!-- @dsCard -->\n' + 'x' * 256000
        self.assertEqual(v3.validate_preview(big, 'p.html'), [f'preview_too_large: p.html: {len(big)} > 256000'])

    def test_preview_unpinned_cdn(self):
        head = '<!-- @dsCard -->\n'
        bad = ['https://cdn.jsdelivr.net/npm/d3', 'https://cdn.jsdelivr.net/npm/d3@latest', 'https://cdn.jsdelivr.net/npm/d3@7',
               'https://cdn.jsdelivr.net/npm/d3@^7.8.5', 'https://unpkg.com/react', 'https://cdnjs.cloudflare.com/ajax/libs/d3/latest/d3.js',
               'https://esm.sh/lodash', 'https://cdn.tailwindcss.com', 'https://cdn.jsdelivr.net/npm/@scope/pkg']
        for url in bad:
            with self.subTest(url=url):
                self.assertEqual(v3.validate_preview(f'{head}<script src="{url}"></script>', 'a.html'), [f'unpinned_cdn: a.html: {url}'])
        good = ['https://cdn.jsdelivr.net/npm/d3@7.8.5/dist/d3.min.js', 'https://unpkg.com/react@18.3.1/umd/react.js',
                'https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js', 'https://esm.sh/lodash@4.17.21',
                'https://cdn.jsdelivr.net/npm/@scope/pkg@1.2.3-beta.1/x.js', 'https://code.jquery.com/jquery-3.7.1.min.js',
                'https://example.com/anything.js']
        for url in good:
            with self.subTest(url=url):
                self.assertEqual(v3.validate_preview(f'{head}<script src="{url}"></script>', 'a.html'), [])

    def test_preview_marker_height_warns(self):
        self.assertEqual(v3.preview_warnings('<!-- @dsCard height=30 -->', 'components/A/preview.html'),
                         ['card_marker_height: components/A/preview.html: 30'])
        self.assertEqual(v3.preview_warnings('<!-- @dsCard height=4001 -->', 'components/A/preview.html'),
                         ['card_marker_height: components/A/preview.html: 4001'])
        self.assertEqual(v3.preview_warnings('<!-- @dsCard height=239 -->', 'components/Cover/preview.html'),
                         ['card_marker_height: components/Cover/preview.html: 239'])
        self.assertEqual(v3.preview_warnings('<!-- @dsCard height=300 -->', 'components/Cover/preview.html'), [])
        self.assertEqual(v3.preview_warnings('<!-- @dsCard -->', 'components/A/preview.html'), [])

    def test_component_name_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'components/my-button/README.md', 'A button.\n')
            put(directory, 'components/my-button/preview.html', '<!-- @dsCard -->\n')
            errors = self.verify(directory)[0]
            self.assertIn('component_name_invalid: components/my-button', errors)

    def test_component_incomplete_and_without_source(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'components/Button/README.md', 'A button.\n')
            put(directory, 'components/Card/preview.html', '<!-- @dsCard -->\n')
            errors = self.verify(directory)[0]
            self.assertIn('component_incomplete: components/Button: preview.html', errors)
            self.assertIn('component_incomplete: components/Card: README.md', errors)
            self.assertIn('component_without_source: components/Button', errors)
            self.assertIn('component_without_source: components/Card', errors)

    def test_component_without_source(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'design-system'
            make(package)
            put(package, 'components/Button/README.md', 'A button.\n' + 'x' * 64000)
            put(package, 'components/Button/preview.html', '<!-- @dsCard height=20 -->\n')
            errors, warnings = self.verify(package)
            self.assertEqual(errors, ['component_without_source: components/Button'])
            self.assertIn('card_marker_height: components/Button/preview.html: 20', warnings)
            self.assertTrue(any(w.startswith('component_readme_large: components/Button/README.md') for w in warnings))
            edit_json(package, 'canonical-map.json', lambda d: d.update(components={'Button': {'source': 'src/Button.js'}}))
            self.assertEqual(self.verify(package)[0], ['missing_path: canonical-map.json: components.Button.source'])
            put(directory, 'src/Button.js', 'export {}')
            self.assertEqual(self.verify(package)[0], [])

    def test_template_page_marker_exempt(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'components/Dashboard/preview.html', '<!-- @dsCard page group="Templates" -->\n<p>x</p>\n')
            self.assertEqual(self.verify(directory)[0], [])
            put(directory, 'components/Other/preview.html', '<!-- @dsCard page group="Other" -->\n')
            errors = self.verify(directory)[0]
            self.assertIn('component_incomplete: components/Other: README.md', errors)

    def test_recognised_bundle_is_not_a_component(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'components/lib/util.js', 'x')
            put(directory, 'components/src/Button.js', 'x')
            put(directory, 'components/index.d.ts', 'x')
            self.assertEqual(self.verify(directory)[0], [])
            self.assertTrue(v3.has_bundle(Path(directory)))
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            self.assertFalse(v3.has_bundle(Path(directory)))


class AssetTests(unittest.TestCase):
    def test_asset_group_readme_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/Wordmark/mark.svg', '<svg></svg>')
            self.assertEqual(v3.verify_package(Path(directory))[0], ['asset_group_readme_missing: assets/Wordmark/README.md'])

    def test_asset_unlisted(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/Wordmark/README.md', 'mark.svg - own work, free to use.\n')
            put(directory, 'assets/Wordmark/mark.svg', '<svg></svg>')
            put(directory, 'assets/Wordmark/sub/other.svg', '<svg></svg>')
            self.assertEqual(v3.verify_package(Path(directory))[0], ['asset_unlisted: assets/Wordmark/sub/other.svg'])
            put(directory, 'assets/Wordmark/README.md', 'mark.svg and sub/other.svg, own work.\n')
            self.assertEqual(v3.verify_package(Path(directory))[0], [])

    def test_asset_too_large(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/G/README.md', 'big.svg big.png ok.png\n')
            put(directory, 'assets/G/big.svg', '<svg>' + ' ' * 2000000 + '</svg>')
            put(directory, 'assets/G/big.png', b'\0' * 9000001)
            put(directory, 'assets/G/ok.png', b'\0' * 9000000)
            errors = v3.verify_package(Path(directory))[0]
            self.assertIn('asset_too_large: assets/G/big.svg: 2000011 > 2000000', errors)
            self.assertIn('asset_too_large: assets/G/big.png: 9000001 raw, 12000004 stored > 12000000', errors)
            self.assertEqual(len([e for e in errors if e.startswith('asset_too_large')]), 2)


class ContrastTests(unittest.TestCase):
    def pairs(self, fg, bg, **extra):
        doc = tok(color=[color('fg', fg), color('bg', bg)])
        pair = {'fg': 'fg', 'bg': 'bg', **extra}
        return v3.check_contrast(doc, [pair])

    def test_contrast_vectors(self):
        self.assertEqual(round(v3.contrast_ratio('#767676', '#ffffff'), 2), 4.54)
        self.assertEqual(round(v3.contrast_ratio('#777777', '#ffffff'), 2), 4.48)
        self.assertAlmostEqual(v3.contrast_ratio('oklch(0 0 0)', 'oklch(1 0 0)'), 21.0, places=1)
        self.assertAlmostEqual(v3.contrast_ratio('#000', '#fff'), 21.0, places=6)
        channels = v3.parse_color('oklch(0.7 0.4 30)')
        self.assertTrue(all(0 <= c <= 1 for c in channels))
        self.assertEqual(self.pairs('#767676', '#ffffff'), ([], []))
        errors, _ = self.pairs('#777777', '#ffffff')
        self.assertEqual(errors, ['contrast_below_min: canonical-map.json: checks.contrast[0]@light: 4.48 < 4.5'])
        self.assertEqual(self.pairs('#777777', '#ffffff', large=True), ([], []))
        errors, _ = self.pairs('#999999', '#ffffff', large=True)
        self.assertEqual(errors, ['contrast_below_min: canonical-map.json: checks.contrast[0]@light: 2.85 < 3.0'])
        self.assertEqual(self.pairs('#777777', '#ffffff', min=4.0), ([], []))

    def test_contrast_pins_wcag_channel_coefficients(self):
        # Each pure channel on white: (1 + 0.05) / (coefficient + 0.05); swapping R and B changes both numbers.
        self.assertEqual(round(v3.contrast_ratio('#0000ff', '#ffffff'), 2), 8.59)
        self.assertEqual(round(v3.contrast_ratio('#ff0000', '#ffffff'), 2), 4.00)
        self.assertEqual(round(v3.contrast_ratio('#00ff00', '#ffffff'), 2), 1.37)
        self.assertEqual(round(v3.contrast_ratio('#ffffff', '#0000ff'), 2), 8.59)

    def test_theme_inheritance_takes_the_first_theme_not_the_nearest_or_last(self):
        ids = ['a', 'b', 'c']
        token = {'name': 'x', 'value': {'a': '#111111', 'b': '#222222'}}
        self.assertEqual(v3._theme_value(token, ids, 'c'), '#111111')
        self.assertEqual(v3._theme_value({'name': 'y', 'value': {'c': '#333333'}}, ids, 'a'), '#333333')
        self.assertEqual(v3._theme_value({'name': 'y', 'value': {'b': '#222222', 'c': '#333333'}}, ids, 'a'), '#222222')
        self.assertIsNone(v3._theme_value({'name': 'z', 'value': {}}, ids, 'a'))
        doc = tok(color=[color('fg', {'a': '#ffffff', 'b': '#111111'}), color('bg', '#ffffff')])
        doc['color']['themes'] = [{'id': t, 'name': t} for t in ids]
        errors, _ = v3.check_contrast(doc, [{'fg': 'fg', 'bg': 'bg'}])
        self.assertEqual(errors, ['contrast_below_min: canonical-map.json: checks.contrast[0]@a: 1.00 < 4.5',
                                  'contrast_below_min: canonical-map.json: checks.contrast[0]@c: 1.00 < 4.5'])

    def test_parse_color_forms(self):
        near = lambda a, b: all(abs(x - y) < 0.01 for x, y in zip(a, b))
        self.assertTrue(near(v3.parse_color('#f00'), (1, 0, 0)))
        self.assertTrue(near(v3.parse_color('#ff000080'), (1, 0, 0)))
        self.assertTrue(near(v3.parse_color('rgb(255 0 0 / 50%)'), (1, 0, 0)))
        self.assertTrue(near(v3.parse_color('rgba(0, 128, 255, 0.5)'), (0, 128 / 255, 1)))
        self.assertTrue(near(v3.parse_color('rgb(100%, 0%, 0%)'), (1, 0, 0)))
        self.assertTrue(near(v3.parse_color('hsl(0 100% 50%)'), (1, 0, 0)))
        self.assertTrue(near(v3.parse_color('hsla(120, 100%, 25%, 1)'), (0, 0.5, 0)))
        self.assertTrue(near(v3.parse_color('oklab(0.628 0.2249 0.1258)'), (1, 0, 0)))
        self.assertTrue(near(v3.parse_color('oklch(62.8% 0.2577 29.23)'), (1, 0, 0)))
        for unsupported in ('lab(50 20 -10)', 'lch(50 20 30)', 'color(display-p3 1 0 0)'):
            with self.assertRaises(ValueError) as caught:
                v3.parse_color(unsupported)
            self.assertEqual(str(caught.exception), 'unsupported_space')
        for broken in ('red', '#12', 'rgb(1 2)', '{alias}', 'rgb(a b c)', ''):
            with self.assertRaises(ValueError) as caught:
                v3.parse_color(broken)
            self.assertEqual(str(caught.exception), 'invalid_color')

    def test_contrast_unchecked_warns(self):
        doc = tok(color=[color('fg', '#000'), color('bg', '#fff')])
        self.assertEqual(v3.check_contrast(doc, []), ([], ['contrast_unchecked: canonical-map.json: checks.contrast']))
        self.assertEqual(v3.check_contrast(doc, None), ([], ['contrast_unchecked: canonical-map.json: checks.contrast']))
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            edit_json(directory, 'canonical-map.json', lambda d: d['checks'].update(contrast=[]))
            errors, warnings = v3.verify_package(Path(directory))
            self.assertEqual(errors, [])
            self.assertIn('contrast_unchecked: canonical-map.json: checks.contrast', warnings)
            code, out, err = cli('--package', directory)
            self.assertEqual((code, err), (0, ''))
            self.assertIn('WARN contrast_unchecked', out)
            self.assertIn('unchecked: live-render, browser-display, real-import, contrast', out)

    def test_contrast_unsupported_space_and_unknown_token(self):
        doc = tok(color=[color('fg', 'lab(10 0 0)'), color('bg', '#fff'), color('x', '#000')])
        errors, warnings = v3.check_contrast(doc, [{'fg': 'fg', 'bg': 'bg'}, {'fg': 'ghost', 'bg': 'bg'}, 'oops', {'fg': 'x', 'bg': 'x', 'min': 'a'}])
        self.assertEqual(warnings, ['contrast_unsupported_space: tokens.json: color.fg@light'])
        self.assertIn('invalid_manifest: canonical-map.json: checks.contrast[1].fg: unknown token ghost', errors)
        self.assertIn('invalid_manifest: canonical-map.json: checks.contrast[2]', errors)
        self.assertIn('invalid_manifest: canonical-map.json: checks.contrast[3].min', errors)

    def test_contrast_uses_theme_inheritance_and_alpha(self):
        doc = tok(color=[color('fg', {'light': '#111111'}), color('bg', {'light': '#ffffff', 'dark': '#000000'})])
        doc['color']['themes'].append({'id': 'dark', 'name': 'Dark'})
        errors, _ = v3.check_contrast(doc, [{'fg': 'fg', 'bg': 'bg'}])
        self.assertEqual(errors, ['contrast_below_min: canonical-map.json: checks.contrast[0]@dark: 1.11 < 4.5'])
        half = tok(color=[color('fg', 'rgba(0, 0, 0, 0.1)'), color('bg', '#ffffff')])
        self.assertTrue(v3.check_contrast(half, [{'fg': 'fg', 'bg': 'bg'}])[0])

    def test_contrast_via_verify_package(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            self.assertEqual(v3.verify_package(Path(directory)), ([], []))
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'][1]['value'].update(dark='#222222'))
            errors, _ = v3.verify_package(Path(directory))
            self.assertEqual(len(errors), 1)
            self.assertTrue(errors[0].startswith('contrast_below_min: canonical-map.json: checks.contrast[0]@dark: '))


class ProfileTests(unittest.TestCase):
    def test_minimal_profile_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, 'minimal')
            self.assertEqual(v3.verify_package(Path(directory)), ([], []))
            self.assertEqual(v3.verify_package(Path(directory), 'minimal'), ([], []))

    def test_minimal_profile_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, 'minimal')
            def grow(doc):
                doc['color']['tokens'] += [{'name': f'x{i}', 'value': '#abcdef', 'usage': 'u'} for i in range(4)]
                doc['color']['themes'].append({'id': 'dark', 'name': 'Dark'})
                doc['type']['groups'][0]['styles'] = doc['type']['groups'][0]['styles'][:4]
                doc['spacing']['tokens'].pop()
                doc['radius']['tokens'] += [{'name': 'r9', 'value': '9px', 'usage': 'u'}]
            edit_json(directory, 'tokens.json', grow)
            errors = v3.verify_package(Path(directory))[0]
            self.assertIn('minimal_profile_violation: tokens.json: color: 11 not in 6..10', errors)
            self.assertIn('minimal_profile_violation: tokens.json: themes: 2 != 1', errors)
            self.assertIn('minimal_profile_violation: tokens.json: text styles: 4 not in 5..7', errors)
            self.assertIn('minimal_profile_violation: tokens.json: spacing: 3 != 4', errors)
            self.assertIn('minimal_profile_violation: tokens.json: radius: 4 != 3', errors)

    def test_minimal_profile_readme_and_components(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, 'minimal', README__md='Short.\n')
            put(directory, 'components/Button/README.md', 'x')
            errors = v3.verify_package(Path(directory))[0]
            self.assertIn('minimal_profile_violation: README.md: paragraph 6 < 80 characters', errors)
            self.assertIn('minimal_profile_violation: components/Button: only Cover is allowed', errors)
            self.assertEqual([e for e in errors if e.startswith('component_')], [])

    def test_profile_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, 'minimal')
            self.assertTrue(v3.verify_package(Path(directory), 'full')[0])
            edit_json(directory, 'canonical-map.json', lambda d: d.pop('profile'))
            self.assertTrue(v3.verify_package(Path(directory))[0])
            edit_json(directory, 'canonical-map.json', lambda d: d.update(profile='huge'))
            self.assertIn('invalid_manifest: canonical-map.json: profile', v3.verify_package(Path(directory))[0])


class PackageV3Tests(unittest.TestCase):
    def test_index_version_4_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            edit_json(directory, 'design-system.json', lambda d: d.update(v=4))
            self.assertEqual(v3.verify_package(Path(directory))[0], ['unsupported_format_version: design-system.json: v: 4'])
        self.assertEqual(v3.validate_index({'v': 4}), ['unsupported_format_version: design-system.json: v: 4'])
        self.assertEqual(v3.validate_index({'v': True}), ['unsupported_format_version: design-system.json: v: True'])

    def test_index_keys_and_values(self):
        good = base_files()['design-system.json']
        self.assertEqual(v3.validate_index(good), [])
        self.assertEqual(v3.validate_index([]), ['invalid_index_value: design-system.json: <root>'])
        self.assertEqual(v3.validate_index({}), ['missing_index_key: design-system.json: v'])
        errors = v3.validate_index({'v': 3})
        self.assertEqual(errors, ['missing_index_key: design-system.json: layout', 'missing_index_key: design-system.json: title',
                                  'missing_index_key: design-system.json: namespace'])
        errors = v3.validate_index({'v': 3, 'layout': 'bundle', 'title': ' ', 'namespace': '9x'})
        self.assertEqual(errors, ['invalid_index_value: design-system.json: layout', 'invalid_index_value: design-system.json: title',
                                  'invalid_index_value: design-system.json: namespace'])
        for marker, expected in [({'v': 2, 'at': '2026-10-22T00:00:00Z'}, ['createdOnFiles.v']),
                                 ({'v': 1, 'at': 'yesterday'}, ['createdOnFiles.at']),
                                 ('x', ['createdOnFiles']), ({'v': 1}, ['createdOnFiles.at'])]:
            errors = v3.validate_index({**good, 'createdOnFiles': marker})
            self.assertEqual(errors, [f'invalid_index_value: design-system.json: {key}' for key in expected])
        self.assertEqual(v3.validate_index({**good, 'createdOnFiles': {'v': 1, 'at': '2026-10-22'}}), [])

    def test_index_marker_missing_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            edit_json(directory, 'design-system.json', lambda d: d.pop('createdOnFiles'))
            errors, warnings = v3.verify_package(Path(directory))
            self.assertEqual((errors, warnings), ([], ['index_marker_missing: design-system.json: createdOnFiles']))

    def test_required_files_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, design__system__json=None, README__md=None, tokens__json=None, canonical__map__json=None, DESIGN__md=None)
            errors = v3.verify_package(Path(directory))[0]
            for name in ('design-system.json', 'README.md', 'tokens.json', 'canonical-map.json'):
                self.assertIn(f'missing_required_file: {name}', errors)

    def test_unreadable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, design__system__json='{', tokens__json='[', canonical__map__json='nope')
            errors = v3.verify_package(Path(directory))[0]
            self.assertIn('invalid_index_value: design-system.json: json', errors)
            self.assertIn('token_shape: tokens.json: json', errors)
            self.assertIn('invalid_manifest: canonical-map.json: json', errors)

    def test_tokens_file_size_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'][0].update(usage='x' * 512000))
            errors = v3.verify_package(Path(directory))[0]
            self.assertTrue(any(e.startswith('limit_exceeded: tokens.json: file size: ') and e.endswith(' > 512000') for e in errors), errors)


class CanonicalMapTests(unittest.TestCase):
    DOC = {'schemaVersion': '1', 'system': {'id': 'a', 'version': '1', 'status': 'draft'},
           'canonical': {'brand': {'kind': 'file', 'path': 'README.md'}}}

    def test_canonical_map_file_and_repo_path_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'design-system'
            put(package, 'README.md', 'x')
            put(directory, 'src/Button.js', 'x')
            doc = json.loads(json.dumps(self.DOC))
            self.assertEqual(v3.validate_canonical_map(doc, package), [])
            doc['canonical']['code'] = {'kind': 'repo-path', 'path': 'src/Button.js'}
            self.assertEqual(v3.validate_canonical_map(doc, package), [])
            doc['canonical']['code'] = {'kind': 'file', 'path': 'src/Button.js'}
            self.assertEqual(v3.validate_canonical_map(doc, package), ['missing_path: canonical-map.json: canonical.code.path'])
            doc['canonical']['code'] = {'kind': 'repo-path', 'path': 'README.md'}
            self.assertEqual(v3.validate_canonical_map(doc, package), ['missing_path: canonical-map.json: canonical.code.path'])
            doc['canonical']['code'] = {'kind': 'repo-path', 'path': '../outside'}
            self.assertEqual(v3.validate_canonical_map(doc, package), ['invalid_path: canonical-map.json: canonical.code.path'])

    def test_canonical_map_shape_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            put(package, 'README.md', 'x')
            def check(change, expected):
                doc = json.loads(json.dumps(self.DOC))
                change(doc)
                self.assertEqual(v3.validate_canonical_map(doc, package), expected)
            self.assertEqual(v3.validate_canonical_map([], package), ['invalid_manifest: canonical-map.json: expected object'])
            check(lambda d: d.update(schemaVersion='2'), ['invalid_manifest: canonical-map.json: schemaVersion/system'])
            check(lambda d: d['system'].update(status='bad'), ['invalid_status: canonical-map.json: system'])
            check(lambda d: d.update(canonical={}), ['invalid_manifest: canonical-map.json: canonical'])
            check(lambda d: d['canonical'].update(brand={'kind': 'url', 'path': 'README.md'}), ['invalid_canonical: canonical-map.json: canonical.brand'])
            check(lambda d: d['canonical'].update(brand={'kind': 'file', 'path': 'README.md', 'url': 'https://example.com'}),
                  ['invalid_canonical: canonical-map.json: canonical.brand'])
            check(lambda d: d['canonical'].update(brand=5), ['invalid_canonical: canonical-map.json: canonical.brand'])
            check(lambda d: d['canonical'].update(brand={'kind': 'external', 'url': 'https://example.com/design'}), [])
            for url in ['http://example.com', 'https://user:pass@example.com', 'ftp://example.com/x', 'https://bad host/', 'https:///x']:
                check(lambda d: d['canonical'].update(brand={'kind': 'external', 'url': url}), ['invalid_external: canonical-map.json: canonical.brand'])
            check(lambda d: d['canonical'].update(brand={'kind': 'external', 'url': 'https://example.com', 'path': 'x'}),
                  ['invalid_external: canonical-map.json: canonical.brand'])
            check(lambda d: d.update(components=[]), ['invalid_manifest: canonical-map.json: components'])
            check(lambda d: d.update(components={'Button': {}}), ['invalid_manifest: canonical-map.json: components.Button'])
            check(lambda d: d.update(components={'Button': {'source': 'https://example.com/storybook'}}), [])
            check(lambda d: d.update(components={'Button': {'source': 'http://example.com'}}), ['invalid_external: canonical-map.json: components.Button.source'])
            check(lambda d: d.update(checks=[]), ['invalid_manifest: canonical-map.json: checks'])
            check(lambda d: d.update(checks={'contrast': 5}), ['invalid_manifest: canonical-map.json: checks.contrast'])
            check(lambda d: d.update(decisions={}), ['invalid_manifest: canonical-map.json: decisions'])
            check(lambda d: d.update(decisions=[{'id': 'D1'}, {'id': 'D1'}]), ['invalid_id: canonical-map.json: decisions'])
            check(lambda d: d.update(decisions=[{'id': 'D1', 'status': 'pending'}, 'quote']), [])
            check(lambda d: d['canonical'].update(**{'bad\nname': {'kind': 'invalid'}}), ['invalid_canonical: canonical-map.json: canonical.bad?name'])


class RefusedPathTests(unittest.TestCase):
    def test_refused_paths(self):
        paths = ['SKILL.md', 'sub/AGENTS.md', 'GEMINI.md', 'CLAUDE.md', '.hidden/x', 'PROGRA~1/a.md', 'index.html',
                 'assets/design-system.json', 'node_modules/a.js', 'package-lock.json']
        self.assertEqual(v3.check_refused(paths), [f'refused_path: {p}' for p in paths])

    def test_refused_more_names(self):
        more = ['package.json', 'a/tsconfig.json', 'deno.json', 'bunfig.toml', 'npm-shrinkwrap.json', 'yarn.lock', 'pnpm-lock.yaml',
                'bun.lock', 'bun.lockb', 'deno.lock', 'a/b/node_modules', 'artifact-type', 'artifact-type/x.json',
                'components/Button/index.html', 'sub/skill.md', 'dir/.git', 'a/NAME~12.txt']
        self.assertEqual(v3.check_refused(more), [f'refused_path: {p}' for p in more])
        fine = ['README.md', 'design-system.json', 'components/Cover/preview.html', 'a~b.md', 'tilde~x/file.md', 'index.html.bak']
        self.assertEqual(v3.check_refused(fine), [])

    def test_refused_allows_image_slots_state(self):
        self.assertEqual(v3.check_refused(['components/Cover/preview.html', '.image-slots.state.json']), [])
        self.assertEqual(v3.check_refused(['.image-slots.state.json.bak']), ['refused_path: .image-slots.state.json.bak'])

    def test_generated_files_present(self):
        paths = ['manifest.json', 'tokens.css', 'api/tokens.md', 'archived/old.md', 'migration-map.json']
        self.assertEqual(v3.check_refused(paths), [f'generated_file_present: {p}' for p in paths])
        self.assertEqual(v3.check_refused(['publish-progress.json']), ['generated_file_present: publish-progress.json'])
        self.assertEqual(v3.check_refused(['assets/manifest.json', 'docs/api/x.md', 'sub/tokens.css']), [])

    def test_package_with_adapter_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            self.assertEqual(v3.verify_package(Path(directory)), ([], []))
            put(directory, 'AGENTS.md', 'adapter\n')
            self.assertEqual(v3.verify_package(Path(directory))[0], ['refused_path: AGENTS.md'])
            code, out, err = cli('--package', directory)
            self.assertEqual((code, err.strip()), (1, 'refused_path: AGENTS.md'))
            self.assertNotIn('PASS', out)

    def test_package_refused_and_generated_walk(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, '.hidden/secret.txt', 'x')
            put(directory, 'node_modules/pkg/index.js', 'x')
            put(directory, 'api/tokens.md', 'x')
            put(directory, 'manifest.json', '{}')
            put(directory, 'index.html', '<html></html>')
            put(directory, 'components/Cover/index.html', 'x')
            put(directory, 'sub/design-system.json', '{}')
            errors = v3.verify_package(Path(directory))[0]
            for expected in ['refused_path: .hidden', 'refused_path: node_modules', 'generated_file_present: api',
                             'generated_file_present: manifest.json', 'refused_path: index.html',
                             'refused_path: components/Cover/index.html', 'refused_path: sub/design-system.json']:
                self.assertIn(expected, errors)
            self.assertFalse([e for e in errors if 'secret.txt' in e or 'pkg' in e or 'tokens.md' in e])

    def test_package_sensitive_never_read(self):
        opened = []
        real_read_text, real_read_bytes = Path.read_text, Path.read_bytes
        real_open = io.open
        def spy(real):
            def wrapper(self, *args, **kwargs):
                opened.append(Path(self).name)
                return real(self, *args, **kwargs)
            return wrapper
        def spy_open(file, *args, **kwargs):
            opened.append(Path(file).name if isinstance(file, (str, Path)) else str(file))
            return real_open(file, *args, **kwargs)
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, '.env', 'SECRET=1')
            put(directory, 'credentials.json', '{}')
            put(directory, 'assets/G/server.pem', 'x')
            put(directory, 'assets/G/README.md', 'server.pem\n')
            doc = base_files()['tokens.json']
            doc['type']['fonts'] = [{'file': '.env'}, {'file': 'server.key'}]
            put(directory, 'tokens.json', doc)
            put(directory, 'fonts/server.key', b'wOF2')
            with patch.object(Path, 'read_text', spy(real_read_text)), patch.object(Path, 'read_bytes', spy(real_read_bytes)), \
                 patch('io.open', spy_open):
                errors = v3.verify_package(Path(directory))[0]
        for name in ('.env', 'credentials.json', 'server.pem', 'server.key'):
            self.assertNotIn(name, opened)
        self.assertTrue(opened)
        for expected in ('refused_sensitive_path: .env', 'refused_sensitive_path: credentials.json',
                         'refused_sensitive_path: assets/G/server.pem', 'refused_sensitive_path: fonts/server.key'):
            self.assertIn(expected, errors)

    def test_package_linked_entries_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'linked/x.md', 'x')
            with patch.object(v3, '_is_link', lambda entry: entry.name == 'linked'):
                errors = v3.verify_package(Path(directory))[0]
            self.assertEqual(errors, ['refused_sensitive_path: linked'])


class LayoutTests(unittest.TestCase):
    def test_sections_over_limit_lists_names(self):
        paths = [f'notes/n{i:02d}.md' for i in range(1, 26)]
        expected = 'sections_over_limit: 25 > 24: ' + ', '.join(paths)
        self.assertEqual(v3.check_layout(paths), [expected])
        self.assertEqual(v3.check_layout(paths[:24]), [])
        exempt = paths[:24] + ['README.md', 'components/A/README.md', 'archived/x.md', 'notes/image.png']
        self.assertEqual(v3.check_layout(exempt), [])
        self.assertEqual(len(v3.check_layout(paths[:24] + ['x.mdx'])), 1)

    def test_legacy_layout_dir_warns(self):
        self.assertEqual(v3.check_layout(['ui-kit/a.md']), ['legacy_layout_dir: ui-kit'])
        self.assertEqual(v3.check_layout(['ui-kit', 'ui-kit/a.md', 'specimens/b.md', 'integrations', 'brand/c.md', 'foundations/d.md']),
                         ['legacy_layout_dir: brand', 'legacy_layout_dir: foundations', 'legacy_layout_dir: integrations',
                          'legacy_layout_dir: specimens', 'legacy_layout_dir: ui-kit'])
        self.assertEqual(v3.check_layout(['patterns/a.md', 'surfaces/web/rules.md']), [])

    def test_index_html_nested_warns(self):
        self.assertEqual(v3.check_layout(['index.html', 'components/A/index.html']), [])
        self.assertEqual(v3.check_layout(['docs/index.html']), ['index_html_nested: docs/index.html'])

    def test_package_layout_and_size_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            for i in range(24):
                put(directory, f'notes/n{i:02d}.md', 'x')
            put(directory, 'ui-kit/a.md', 'x')
            put(directory, 'data/big.json', ' ' * 512001)
            warnings = v3.verify_package(Path(directory))[1]
            self.assertTrue(any(w.startswith('sections_over_limit: 26 > 24: ') for w in warnings))
            self.assertIn('legacy_layout_dir: ui-kit', warnings)
            self.assertIn('kept_file_large: data/big.json: 512001 > 512000', warnings)

    def test_file_count_and_total_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            for i in range(1001):
                put(directory, f'files/f{i}.txt', '')
            warnings = v3.verify_package(Path(directory))[1]
            self.assertTrue(any(w.startswith('file_count_high: ') and w.endswith(' > 1000') for w in warnings))
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/G/README.md', 'a.bin b.bin c.bin d.bin e.bin f.bin\n')
            for name in 'abcdef':
                put(directory, f'assets/G/{name}.bin', b'\0' * 8_000_000)
            warnings = v3.verify_package(Path(directory))[1]
            self.assertTrue(any(w.startswith('package_total_large: ') and w.endswith(' > 14000000') for w in warnings), warnings)


class DesignMdTests(unittest.TestCase):
    def test_design_md_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=None)
            self.assertEqual(v3.verify_package(Path(directory))[0], ['design_md_missing: DESIGN.md'])

    def test_design_md_valid(self):
        self.assertEqual(v3.validate_design_md_structure(design_md()), [])
        withtitle = design_md().replace('---\n\n## Overview', '---\n# Sample\n\n## Overview', 1)
        self.assertEqual(v3.validate_design_md_structure(withtitle), [])
        self.assertEqual(v3.validate_design_md_structure(design_md(extra='\n## Appendix\n\nmore\n')), [])

    def test_design_md_section_missing(self):
        text = design_md([s for s in SECTIONS if s != 'Shapes'])
        self.assertEqual(v3.validate_design_md_structure(text), ['design_md_section_missing: DESIGN.md: Shapes'])
        spelled = design_md(['Overview', 'Colours', 'Typography', 'Layout', 'Elevation & Depth', 'Shapes', 'Components', "Do's and Don'ts"])
        self.assertEqual(v3.validate_design_md_structure(spelled), ['design_md_section_missing: DESIGN.md: Colors'])
        fenced = design_md() + '\n```\n## Extra\n```\n'
        self.assertEqual(v3.validate_design_md_structure(fenced), [])

    def test_design_md_section_order(self):
        swapped = SECTIONS[:1] + ['Typography', 'Colors'] + SECTIONS[3:]
        self.assertEqual(v3.validate_design_md_structure(design_md(swapped)),
                         ['design_md_section_order: DESIGN.md: Typography before Colors'])
        repeated = design_md(SECTIONS + ['Colors'])
        self.assertEqual(v3.validate_design_md_structure(repeated), ['design_md_section_order: DESIGN.md: Colors repeated'])

    def test_design_md_overview_incomplete(self):
        for missing, label in [('- Owner: x\n- Status: y\n', 'Read order'), ('- Read order: a\n- Status: y\n', 'Owner'),
                               ('- Read order: a\n- Owner: x\n', 'Status')]:
            self.assertEqual(v3.validate_design_md_structure(design_md(overview=missing)),
                             [f'design_md_overview_incomplete: DESIGN.md: {label}'])
        tolerant = '* **Read order**: a\n  - **Owner** : x\n- Status:y\n'
        self.assertEqual(v3.validate_design_md_structure(design_md(overview=tolerant)), [])
        self.assertEqual(len(v3.validate_design_md_structure(design_md(overview='nothing\n'))), 3)

    def test_design_md_broken_ref(self):
        self.assertEqual(v3.check_design_md_refs('{colors.primary-99}', {'colors.bg'}), ['design_md_broken_ref: DESIGN.md: {colors.primary-99}'])
        self.assertEqual(v3.check_design_md_refs('{colors.bg} {rounded.x} {rounded.x} {foo.bar}', {'colors.bg'}),
                         ['design_md_broken_ref: DESIGN.md: {rounded.x}'])
        text = '---\ncolors:\n  text: "{colors.ghost}"\n---\nbody {spacing.s}\n```\n{colors.fenced}\n```\n'
        self.assertEqual(v3.check_design_md_refs(text, {'spacing.s'}), [])
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=design_md(extra='\nUses {colors.ghost} and {colors.bg}.\n'))
            self.assertEqual(v3.verify_package(Path(directory))[0], ['design_md_broken_ref: DESIGN.md: {colors.ghost}'])

    def test_design_md_token_keys(self):
        tokens = {'color': {'themes': [], 'tokens': [{'name': 'bg', 'value': '#fff', 'usage': 'u'}]},
                  'type': {'groups': [{'name': 'g', 'styles': [{'name': 'body'}]}]},
                  'radius': {'tokens': [{'name': 'radius-sm', 'value': '2px', 'usage': 'u'}]},
                  'spacing': {'tokens': [{'name': 'space-1', 'value': '4px', 'usage': 'u'}]},
                  'shadow': {'tokens': [{'name': 'lift', 'value': '0', 'usage': 'u'}]}}
        self.assertEqual(v3.design_md_token_keys(tokens), {'colors.bg', 'typography.body', 'rounded.radius-sm', 'spacing.space-1'})
        self.assertEqual(v3.design_md_token_keys({}), set())
        self.assertEqual(v3.design_md_token_keys({'color': 5, 'type': {'groups': 'x'}, 'radius': {'tokens': [3]}}), set())

    def test_design_md_overview_incomplete_via_package(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=design_md(overview='- Read order: a\n- Status: y\n'))
            self.assertEqual(v3.verify_package(Path(directory))[0], ['design_md_overview_incomplete: DESIGN.md: Owner'])


class CliV3Tests(unittest.TestCase):
    def test_pass_line_lists_unchecked(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            code, out, err = cli('--package', directory)
            self.assertEqual((code, err), (0, ''))
            self.assertEqual(out.strip(), 'PASS: structural checks only; Claude Design format v3 pinned 2026-10-22 (research preview); '
                                          'unchecked: live-render, browser-display, real-import')
            put(directory, 'components/bundle.js', '/* @ds-bundle {"name":"Button"} */\n')
            code, out, err = cli('--package', directory, '--profile', 'full', '--format-version', '3')
            self.assertEqual(code, 0)
            self.assertTrue(out.strip().endswith('unchecked: live-render, browser-display, real-import, bundle'))

    def test_cli_errors_go_to_stderr_and_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=None)
            put(directory, 'notes/x.md', 'x')
            code, out, err = cli('--package', directory)
            self.assertEqual(code, 1)
            self.assertEqual(err.strip(), 'design_md_missing: DESIGN.md')
            self.assertNotIn('PASS', out)

    def test_cli_format_version_other_is_input_error(self):
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = cli('--package', directory, '--format-version', '4')
            self.assertEqual((code, out, err.strip()), (1, '', 'input_error: unsupported --format-version'))

    def test_cli_package_not_found_and_bad_profile(self):
        code, _, err = cli('--package', str(Path(tempfile.gettempdir()) / 'ds-no-such-dir-xyz'))
        self.assertEqual((code, err.startswith('input_error: package not found: ')), (1, True))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SystemExit):
                with redirect_stderr(io.StringIO()):
                    verifier.main(['--package', directory, '--profile', 'huge'])

    def test_cli_manifest_alias_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            put(directory, 'README.md', 'x')
            put(directory, 'canonical-map.json', CanonicalMapTests.DOC)
            code, out, err = cli('--root', directory, '--manifest', 'canonical-map.json')
            self.assertEqual((code, err), (0, ''))
            self.assertIn('WARN deprecated_flag: --manifest', out)
            self.assertIn('PASS:', out)
            code, out, err = cli('--root', directory, '--canonical-map', 'canonical-map.json')
            self.assertEqual((code, err), (0, ''))
            self.assertNotIn('deprecated_flag', out)
            edit_json(directory, 'canonical-map.json', lambda d: d.update(schemaVersion='9'))
            code, _, err = cli('--root', directory, '--canonical-map', 'canonical-map.json')
            self.assertEqual((code, err.strip()), (1, 'invalid_manifest: canonical-map.json: schemaVersion/system'))

    def test_cli_tokens_grammar_and_dtcg_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            put(directory, 'tokens.json', base_files()['tokens.json'])
            put(directory, 'dtcg.json', {'x': {'$type': 'number', '$value': 2}})
            self.assertEqual(cli('--root', directory, '--tokens', 'tokens.json')[:3:2], (0, ''))
            code, out, err = cli('--root', directory, '--tokens', 'dtcg.json')
            self.assertEqual((code, err.strip()), (1, 'token_shape: tokens.json: x'))
            self.assertEqual(cli('--root', directory, '--dtcg', 'dtcg.json')[0], 0)
            code, _, err = cli('--root', directory, '--dtcg', 'tokens.json')
            self.assertEqual(code, 1)
            self.assertTrue(err)

    def test_cli_tokens_with_package_checks_fonts(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = base_files()['tokens.json']
            doc['type']['fonts'] = [{'file': 'Brand.woff2'}]
            put(directory, 'tokens.json', doc)
            code, _, err = cli('--root', directory, '--tokens', 'tokens.json', '--package', directory)
            self.assertEqual(code, 1)
            self.assertIn('font_file_missing: fonts/Brand.woff2', err)

    def test_cli_unreadable_input_names_the_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            put(directory, 'tokens.json', base_files()['tokens.json'])
            put(directory, 'big.json', {'pad': 'x' * 512000})
            code, out, err = cli('--root', directory, '--tokens', str(Path(directory, 'tokens.json')))
            self.assertEqual((code, out), (1, ''))
            self.assertTrue(err.startswith('input_error: --tokens: '), err)
            self.assertNotIn('ValueError', err)
            code, out, err = cli('--root', directory, '--canonical-map', '../x.json')
            self.assertEqual((code, out, err.strip()), (1, '', 'input_error: --canonical-map: path_escape'))
            code, out, err = cli('--root', directory, '--tokens', 'big.json')
            self.assertEqual((code, out, err.strip()), (1, '', 'input_error: --tokens: file larger than 512000 bytes'))

    def test_cli_legacy_pack_still_runs_without_flags(self):
        code, out, err = cli('--root', str(Path(__file__).resolve().parents[1]))
        self.assertIn(code, (0, 1))

    def test_fixture_full_passes(self):
        self.assertTrue(FIXTURE.is_file())
        errors, _ = v3.verify_package(FIXTURE.parent, 'full')
        self.assertEqual(errors, [])

    def test_template_minimal_passes(self):
        self.assertTrue(TEMPLATE.is_file())
        errors, _ = v3.verify_package(TEMPLATE.parent, 'minimal')
        self.assertEqual(errors, [])

    def test_shipped_packages_have_no_warnings(self):
        for package, profile in ((TEMPLATE.parent, 'minimal'), (FIXTURE.parent, 'full')):
            with self.subTest(package=package.name):
                errors, warnings = v3.verify_package(package, profile)
                self.assertEqual((errors, warnings), ([], []))

    def test_shipped_packages_are_standard_trees(self):
        for package in (TEMPLATE.parent, FIXTURE.parent):
            with self.subTest(package=package.name):
                for name in ('manifest.json', 'tokens.css', 'index.html'):
                    self.assertFalse((package / name).exists(), name)
                self.assertEqual(sorted(p.name for p in (package / 'components/Cover').iterdir()), ['preview.html'])
        self.assertEqual(sorted(p.name for p in (FIXTURE.parent / 'patterns').iterdir()), ['ActionFeedback.md'])
        self.assertEqual(json.loads((TEMPLATE.parent / 'canonical-map.json').read_text(encoding='utf-8'))['profile'], 'minimal')
        self.assertEqual(json.loads((FIXTURE.parent / 'canonical-map.json').read_text(encoding='utf-8'))['profile'], 'full')

    def test_shipped_generated_files_are_current(self):
        loader_spec = importlib.util.spec_from_file_location('design_system_builder_shipped', Path(__file__).with_name('build-design-system.py'))
        builder = importlib.util.module_from_spec(loader_spec)
        loader_spec.loader.exec_module(builder)
        for package in (TEMPLATE.parent, FIXTURE.parent):
            with self.subTest(package=package.name):
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    code = builder.main(['--package', str(package), '--design-md', '--viewer', '--check'])
                self.assertEqual((code, out.getvalue().strip(), err.getvalue()), (0, 'CHECKED: design-md=ok viewer=ok', ''))

    def test_shipped_viewer_counts(self):
        # (tokens, components, assets) the page lists: components = folders under components/ except Cover; assets = files under assets/ except group READMEs.
        for package, expected in ((TEMPLATE.parent, (21, 0, 0)), (FIXTURE.parent, (23, 1, 1))):
            with self.subTest(package=package.name):
                page = (package / 'viewer.html').read_text(encoding='utf-8')
                counts = tuple(page.count(f'data-{kind}="') for kind in ('token', 'component', 'asset'))
                self.assertEqual(counts, expected)


class BoundedInputTests(unittest.TestCase):
    """Hostile input stays cheap: sizes are capped before any pattern runs, and every pattern runs in linear time."""
    BUDGET = 1.0

    def fast(self, call, label, budget=None):
        start = time.perf_counter()
        result = call()
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, budget or self.BUDGET, f'{label}: {elapsed:.2f} s')
        return result

    def test_overview_label_search_is_linear(self):
        for filler in ('\n' * 2000, ' \n' * 1000):
            errors = self.fast(lambda: v3.validate_design_md_structure('## Overview\n' + filler), 'overview blank lines')
            for label in ('Read order', 'Owner', 'Status'):
                self.assertIn(f'design_md_overview_incomplete: DESIGN.md: {label}', errors)
        valid = design_md(overview='\n' * 2000 + OVERVIEW + '\n' * 2000)
        self.assertEqual(self.fast(lambda: v3.validate_design_md_structure(valid), 'valid overview with gaps'), [])

    def test_heading_scan_is_linear(self):
        for text in ('# a' + ' ' * 2000 + 'x', '# a' + '\t ' * 1000 + 'x', '# a' + '#' * 2000 + 'x', '#' + ' ' * 2000):
            self.fast(lambda: v3._headings(text), 'headings')
            self.fast(lambda: v3.validate_readme(text, len(text), 'full', set()), 'readme headings')
            self.fast(lambda: v3.validate_design_md_structure('## Overview\n' + text), 'design headings')
        self.assertEqual(v3._headings('# a' + ' ' * 2000 + 'x'), [(1, 'a' + ' ' * 2000 + 'x')])

    def test_colour_function_split_is_linear(self):
        for value in ('rgb(' + ' ' * 2000 + 'x', 'rgb(' + ' ' * 2000, 'hsl(' + '\t' * 2000 + ')x', 'oklch(' + ' ' * 2000 + '1 2 3))'):
            self.assertEqual(self.fast(lambda: v3._classify_color(value), 'classify colour'), 'invalid')
            with self.assertRaises(ValueError) as caught:
                self.fast(lambda: v3.parse_color(value), 'parse colour')
            self.assertEqual(str(caught.exception), 'invalid_color')
        self.assertEqual(v3._classify_color('  RGB( 1 2 3 )  '), 'ok')
        self.assertEqual(v3._classify_color('rgb(1 2 3))'), 'invalid')
        self.assertEqual(v3._classify_color('rgb (1 2 3)'), 'invalid')

    def test_number_and_length_patterns_are_linear(self):
        digits = '1' * 12000
        self.assertFalse(self.fast(lambda: v3._valid_length(digits + 'x'), 'length'))
        self.assertFalse(self.fast(lambda: v3._valid_line_height(digits + 'x'), 'line height'))
        with self.assertRaises(ValueError):
            self.fast(lambda: v3.parse_color('rgb(' + digits + 'x 0 0)'), 'colour number')
        errors = self.fast(lambda: v3.validate_tokens_v3(tok(spacing=[color('s', digits + 'x')])), 'spacing token')
        self.assertEqual(errors, ['invalid_value: tokens.json: spacing.s'])
        for ok in ('12', '12.', '12.5', '.5', '+1.5px', '-3rem', 0, '0'):
            self.assertTrue(v3._valid_length(ok), ok)
        for bad in ('1..2', '.', '1e', 'px', '1 px', ''):
            self.assertFalse(v3._valid_length(bad), bad)

    def test_readme_paragraph_split_is_linear(self):
        text = 'one paragraph of words\n' + ' \n' * 20000 + 'tail'
        errors, _ = self.fast(lambda: v3.validate_readme(text, len(text), 'minimal', set()), 'minimal readme')
        self.assertEqual(errors, ['minimal_profile_violation: README.md: 2 paragraphs, expected 1'])

    def test_many_distinct_findings_stay_linear(self):
        refs = ' '.join('{colors.k%d}' % i for i in range(20000))
        errors = self.fast(lambda: v3.check_design_md_refs('---\n---\n' + refs, set()), 'broken refs')
        self.assertEqual(len(errors), 20000)
        urls = ' '.join(f'https://unpkg.com/p{i}' for i in range(9500))
        page = '<!-- @dsCard height=300 -->\n<svg></svg>\n' + urls
        found = self.fast(lambda: v3.validate_preview(page, 'components/Cover/preview.html'), 'unpinned urls')
        self.assertEqual(len([e for e in found if e.startswith('unpinned_cdn')]), 9500)
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html='<!-- @dsCard height=300 -->\n<svg></svg>\n' + urls)
            errors, _ = self.fast(lambda: v3.verify_package(Path(directory)), 'package with many findings', 2.0)
        self.assertEqual(len([e for e in errors if e.startswith('unpinned_cdn')]), 9500)

    def test_cdn_version_check_is_linear(self):
        for host in ('cdnjs.cloudflare.com', 'code.jquery.com'):
            url = f'https://{host}/' + '1' * 64000
            self.assertTrue(self.fast(lambda: v3._unpinned(url), 'cdn digits'))
            url = f'https://{host}/' + '1.' * 32000
            self.assertFalse(self.fast(lambda: v3._unpinned(url), 'cdn dotted digits'))
        page = '<!-- @dsCard height=300 -->\n<svg></svg>\nhttps://cdnjs.cloudflare.com/' + '1' * 200000
        found = self.fast(lambda: v3.validate_preview(page, 'components/Cover/preview.html'), 'preview with long digit url')
        self.assertEqual(len([e for e in found if e.startswith('unpinned_cdn')]), 1)

    def test_cdn_version_vectors(self):
        pinned = ['https://cdn.jsdelivr.net/npm/d3@7.8.5/dist/d3.min.js', 'https://unpkg.com/react@18.3.1/umd/react.js',
                  'https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js', 'https://code.jquery.com/jquery-3.7.1.min.js',
                  'https://cdn.jsdelivr.net/npm/@scope/pkg@1.2.3-beta.1/x.js', 'https://cdnjs.cloudflare.com/ajax/libs/x/10.20.30+b.1/x.js']
        loose = ['https://cdn.jsdelivr.net/npm/d3', 'https://cdn.jsdelivr.net/npm/d3@latest', 'https://cdn.jsdelivr.net/npm/@scope/pkg@1.2',
                 'https://cdnjs.cloudflare.com/ajax/libs/d3/latest/d3.js', 'https://cdnjs.cloudflare.com/ajax/libs/d3/1.2/d3.js',
                 'https://cdnjs.cloudflare.com/ajax/libs/d3/1.2.x/d3.js', 'https://code.jquery.com/jquery.min.js', 'https://cdn.tailwindcss.com']
        for url in pinned:
            self.assertFalse(v3._unpinned(url), url)
        for url in loose:
            self.assertTrue(v3._unpinned(url), url)

    def test_readme_code_spans_dedupe_is_linear(self):
        text = 'one paragraph of words\n' + ' '.join('`a%d`' % i for i in range(20000)) + ' `a1` `a1`'
        errors, warnings = self.fast(lambda: v3.validate_readme(text, len(text), 'minimal', set()), 'code spans')
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 20000)
        self.assertEqual(warnings[:2], ['readme_unknown_token: README.md: a0', 'readme_unknown_token: README.md: a1'])

    def test_long_alias_chain_does_not_crash(self):
        count = 3000
        chain = [color(f'a{i}', '{a%d}' % (i + 1)) for i in range(count)] + [color(f'a{count}', '#000000')]
        errors = self.fast(lambda: v3.validate_tokens_v3(tok(color=chain)), 'alias chain', 2.0)
        self.assertIn('limit_exceeded: tokens.json: color.tokens: 3001 > 600', errors)
        ok = [color(f'a{i}', '{a%d}' % (i + 1)) for i in range(15)] + [color('a15', '#000000')]
        self.assertEqual(v3.validate_tokens_v3(tok(color=ok)), [])

    def test_hostile_json_does_not_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, design__system__json='[' * 100000, tokens__json='{"a":' * 60000, canonical__map__json='[' * 100000)
            errors = v3.verify_package(Path(directory))[0]
        self.assertIn('invalid_index_value: design-system.json: json', errors)
        self.assertIn('token_shape: tokens.json: json', errors)
        self.assertIn('invalid_manifest: canonical-map.json: json', errors)

    def read_sizes(self, directory):
        reads = []
        real_open = io.open

        class Spy:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *exc):
                return self.handle.__exit__(*exc)

            def read(self, size=-1):
                reads.append(size)
                return self.handle.read(size)

            def __getattr__(self, name):
                return getattr(self.handle, name)

        def spy_open(file, mode='r', *args, **kwargs):
            handle = real_open(file, mode, *args, **kwargs)
            return Spy(handle) if 'b' in mode else handle

        with patch('io.open', spy_open):
            result = v3.verify_package(Path(directory))
        return result, reads

    def test_reads_are_bounded_before_any_check(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, README__md='## Content fundamentals\n' + 'x' * 300000)
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'][0].update(usage='x' * 600000))
            edit_json(directory, 'design-system.json', lambda d: d.update(pad='x' * 600000))
            edit_json(directory, 'canonical-map.json', lambda d: d.update(pad='x' * 600000))
            put(directory, 'components/Cover/preview.html', '<!-- @dsCard height=300 -->\n<svg></svg>\n' + 'x' * 300000)
            sizes = {n: os.path.getsize(Path(directory, n)) for n in
                     ('README.md', 'tokens.json', 'design-system.json', 'canonical-map.json', 'components/Cover/preview.html')}
            (errors, _warnings), reads = self.read_sizes(directory)
        self.assertTrue(reads)
        self.assertTrue(all(0 < size <= 512001 for size in reads), sorted(set(reads)))
        self.assertIn(f'readme_too_large: README.md: {sizes["README.md"]} > 200000', errors)
        self.assertIn(f'limit_exceeded: tokens.json: file size: {sizes["tokens.json"]} > 512000', errors)
        self.assertIn(f'invalid_index_value: design-system.json: size: {sizes["design-system.json"]} > 512000', errors)
        self.assertIn(f'invalid_manifest: canonical-map.json: size: {sizes["canonical-map.json"]} > 512000', errors)
        self.assertIn(f'preview_too_large: components/Cover/preview.html: {sizes["components/Cover/preview.html"]} > 256000', errors)

    def test_oversized_design_md_is_read_in_part_and_warned(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=design_md(extra='\n' + 'x' * 600000))
            size = os.path.getsize(Path(directory, 'DESIGN.md'))
            (errors, warnings), reads = self.read_sizes(directory)
        self.assertTrue(all(0 < n <= 512001 for n in reads), sorted(set(reads)))
        self.assertEqual(errors, [])
        self.assertIn(f'kept_file_large: DESIGN.md: {size} > 512000', warnings)

    def test_oversized_asset_readme_is_read_in_part(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/G/README.md', 'a.png\n' + 'x' * 600000)
            put(directory, 'assets/G/a.png', b'\x89PNG')
            (errors, _warnings), reads = self.read_sizes(directory)
        self.assertTrue(all(0 < n <= 512001 for n in reads), sorted(set(reads)))
        self.assertEqual(errors, [])


# ---------------------------------------------------------------------------
# DESIGN.md generator and build CLI (SPR-32 TK6).
# ---------------------------------------------------------------------------

INDEX = {'v': 3, 'layout': 'files', 'title': 'Sample', 'namespace': 'Sample'}
FULL_FRONT_MATTER = '''---
version: alpha
name: "Sample Studio"
colors:
  bg: "#ffffff"
  text: "#111111"
  accent: "#0057b8"
  link: "{colors.accent}"
typography:
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  radius-sm: "2px"
spacing:
  space-1: "4px"
---
'''


def two_themes(*tokens):
    doc = tok(color=list(tokens))
    doc['color']['themes'] = [{'id': 'light', 'name': 'Light'}, {'id': 'dark', 'name': 'Dark'}]
    return doc


def styled(*styles, families=None, group_family='sans'):
    doc = tok()
    doc['type'] = {'families': families or {'sans': 'Inter, sans-serif', 'mono': 'Menlo, monospace'},
                   'groups': [{'name': 'G', 'family': group_family, 'styles': list(styles)}]}
    return doc


class DesignMdBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = importlib.import_module('design_system_build')
        path = Path(__file__).with_name('build-design-system.py')
        loader_spec = importlib.util.spec_from_file_location('design_system_builder', path)
        cls.cli_module = importlib.util.module_from_spec(loader_spec)
        loader_spec.loader.exec_module(cls.cli_module)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = self.cli_module.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def front(self, tokens, index=INDEX):
        return self.build.render_front_matter(tokens, index)

    def test_front_matter_first_theme_only(self):
        tokens = two_themes(color('bg', {'light': '#ffffff', 'dark': '#000000'}), color('late', {'dark': '#123456'}),
                            color('plain', '#ABC'))
        text = self.front(tokens)
        self.assertIn('  bg: "#ffffff"\n', text)
        self.assertNotIn('#000000', text)
        self.assertIn('  late: "#123456"\n', text)  # the first theme has no entry: the first theme that has one serves it
        self.assertIn('  plain: "#aabbcc"\n', text)

    def test_alias_becomes_ref(self):
        tokens = tok(color=[color('bg', '#ffffff'), color('text', '{ink}'), color('ink', 'oklch(0 0 0)')])
        self.assertEqual(self.front(tokens), '---\nversion: alpha\nname: "Sample"\ncolors:\n  bg: "#ffffff"\n'
                                             '  text: "{colors.ink}"\n  ink: "#000000"\n---\n')

    def test_oklch_to_hex(self):
        self.assertEqual(self.build.to_hex('oklch(1 0 0)'), '#ffffff')
        self.assertEqual(self.build.to_hex('oklch(0 0 0)'), '#000000')
        self.assertIn('  ink: "#000000"\n', self.front(tok(color=[color('ink', 'oklch(0 0 0)')])))

    def test_to_hex_vectors(self):
        cases = {'#ABC': '#aabbcc', '#ABCD': '#aabbccdd', '#AABBCC': '#aabbcc', '#AABBCCDD': '#aabbccdd', ' #fff ': '#ffffff',
                 'rgb(255 0 0)': '#ff0000', 'rgb(255, 0, 0)': '#ff0000', 'rgb(100% 0% 0%)': '#ff0000',
                 'rgba(255 0 0 / 0.5)': '#ff000080', 'rgb(255 0 0 / 1)': '#ff0000', 'hsl(0 100% 50%)': '#ff0000',
                 'oklab(1 0 0)': '#ffffff'}
        for value, expected in cases.items():
            self.assertEqual(self.build.to_hex(value), expected, value)
        clamped = self.build.to_hex('oklch(0.7 0.4 30)')
        self.assertRegex(clamped, r'^#[0-9a-f]{6}$')
        for value in ('lab(50% 0 0)', 'lch(50% 0 0)', 'color(display-p3 1 0 0)', 'red', 'var(--x)', '', 12, None):
            self.assertIsNone(self.build.to_hex(value), value)

    def test_lab_passthrough_warns(self):
        tokens = tok(color=[color('mid', 'lab(50% 0 0)'), color('ink', '#000000'), color('edge', 'color(display-p3 1 0 0)')])
        self.assertIn('  mid: "lab(50% 0 0)"\n', self.front(tokens))
        self.assertEqual(self.build.design_md_warnings(tokens), ['design_md_color_passthrough: mid', 'design_md_color_passthrough: edge'])
        self.assertEqual(self.build.design_md_warnings(tok(color=[color('ink', 'oklch(0 0 0)'), color('a', '{ink}')])), [])
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'].append(color('mid', 'lab(50% 0 0)')))
            code, out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, err), (0, ''))
            self.assertIn('WARN design_md_color_passthrough: mid\n', out)
            self.assertIn('  mid: "lab(50% 0 0)"\n', Path(directory, 'DESIGN.md').read_text(encoding='utf-8'))

    def test_front_matter_key_order(self):
        files = base_files()
        text = self.build.render_front_matter(files['tokens.json'], files['design-system.json'])
        self.assertEqual(text, FULL_FRONT_MATTER)
        tops = [line.split(':')[0] for line in text.split('\n') if line and not line.startswith((' ', '-'))]
        self.assertEqual(tops, ['version', 'name', 'colors', 'typography', 'rounded', 'spacing'])
        # an empty family leaves no key at all
        self.assertEqual(self.front(tok(color=[color('bg', '#fff')])), '---\nversion: alpha\nname: "Sample"\ncolors:\n  bg: "#ffffff"\n---\n')
        self.assertEqual(self.front({}), '---\nversion: alpha\nname: "Sample"\n---\n')
        self.assertEqual(self.front(tok(), {'title': 3}), '---\nversion: alpha\nname: ""\n---\n')

    def test_typography_mapping(self):
        tokens = styled(
            {'name': 'a', 'fontSize': 16, 'fontWeight': 'bold', 'lineHeight': 1.5},
            {'name': 'b', 'fontSize': '1rem', 'fontWeight': '300 800', 'lineHeight': '24px', 'family': 'mono'},
            {'name': 'c', 'fontSize': '0.875rem', 'fontWeight': 'normal', 'lineHeight': '1.25'},
            {'name': 'd', 'fontWeight': '700', 'lineHeight': 2.0, 'fontSize': 12.5},
            {'name': 'e', 'family': 'missing'})
        self.assertEqual(self.front(tokens), '''---
version: alpha
name: "Sample"
typography:
  a:
    fontFamily: "Inter, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: 1.5
  b:
    fontFamily: "Menlo, monospace"
    fontSize: "1rem"
    fontWeight: "300 800"
    lineHeight: "24px"
  c:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.25
  d:
    fontFamily: "Inter, sans-serif"
    fontSize: "12.5px"
    fontWeight: 700
    lineHeight: 2
  e: {}
---
''')

    def test_font_stack_quotes_are_escaped(self):
        tokens = styled({'name': 'a', 'fontSize': '16px'}, families={'sans': '"Inter", sans-serif'})
        self.assertIn('    fontFamily: "\\"Inter\\", sans-serif"\n', self.front(tokens))

    def test_rounded_and_spacing(self):
        tokens = tok(radius=[color('r0', 0), color('r1', 4), color('r2', '0'), color('r3', '50%'), color('r4', '0.5rem'), color('r5', '6')],
                     spacing=[color('s1', '4px'), color('s2', 8), color('s3', 1.5)])
        text = self.front(tokens)
        self.assertIn('rounded:\n  r0: "0"\n  r1: "4px"\n  r2: "0"\n  r3: "50%"\n  r4: "0.5rem"\n  r5: "6px"\n', text)
        self.assertIn('spacing:\n  s1: "4px"\n  s2: "8px"\n  s3: "1.5px"\n', text)

    def test_escaping_follows_the_spec(self):
        title = 'a"b\\c\nd\te\rf\x08g\x0ch\x7fi\x85j k\x00lé'
        text = self.front(tok(), {'title': title})
        line = text.split('\n')[2]
        self.assertEqual(line, 'name: "a\\"b\\\\c\\nd\\te\\u000df\\u0008g\\u000ch\\u007fi\\u0085j\\u2028k\\u0000lé"')
        self.assertEqual(json.loads(line[len('name: '):]), title)
        for ch in line:
            self.assertFalse(ord(ch) < 0x20 or 0x7f <= ord(ch) <= 0x9f or ord(ch) in (0x2028, 0x2029), repr(ch))
        everything = ''.join(chr(c) for c in list(range(0, 0x300)) + [0x2028, 0x2029, 0xfffe, 0xffff, 0xdc00, 0xd800, 0x1f600])
        self.assertEqual(json.loads(self.build._quote(everything)), everything)

    def test_keys_that_need_quotes(self):
        names = ['plain', 'a-b', '_x', '1st', 'a.b', 'Yes', 'no', 'NULL', 'Off', 'n', 'Y', 'true', 'on', 'nope']
        text = self.front(tok(color=[color(name, '#000000') for name in names]))
        bare = [line.split(':')[0].strip() for line in text.split('\n')[4:-2]]
        self.assertEqual(bare, ['plain', 'a-b', '_x', '"1st"', '"a.b"', '"Yes"', '"no"', '"NULL"', '"Off"', '"n"', '"Y"', '"true"', '"on"', 'nope'])

    def test_split_front_matter(self):
        split = self.build.split_front_matter
        self.assertEqual(split('---\na: 1\n---\nbody'), ('---\na: 1\n---\n', 'body'))
        self.assertEqual(split('no block\n'), ('', 'no block\n'))
        self.assertEqual(split(''), ('', ''))
        self.assertEqual(split('---\na: 1\n---'), ('---\na: 1\n---', ''))
        self.assertEqual(split('---\r\na: 1\r\n---\r\nbody\r\n'), ('---\r\na: 1\r\n---\r\n', 'body\r\n'))
        self.assertEqual(split('---\na: 1\nbody without close\n'), ('', '---\na: 1\nbody without close\n'))
        self.assertEqual(split('---'), ('', '---'))
        self.assertEqual(split('text\n---\na\n---\nbody'), ('', 'text\n---\na\n---\nbody'))
        self.assertEqual(split('﻿---\na\n---\nbody'), ('﻿---\na\n---\n', 'body'))
        self.assertEqual(split('---\n---\nbody'), ('---\n---\n', 'body'))

    def test_split_front_matter_is_linear(self):
        for text in ('---\n' + 'a\n' * 200000, '---\n' + ' ' * 400000, '\n' * 400000):
            start = time.perf_counter()
            self.build.split_front_matter(text)
            self.assertLess(time.perf_counter() - start, 1.0)

    def test_render_keeps_body_bytes(self):
        tokens, index = base_files()['tokens.json'], base_files()['design-system.json']
        head = self.build.render_front_matter(tokens, index)
        body = '## Overview\r\n\ttabbed  \r\nCafé   text\x7f\n\n---\nnot a fence\n```\n---\n```\nno final newline'
        for existing in ('---\nold: 1\n---\n' + body, '---\r\nold: 1\r\n---\r\n' + body, '﻿---\nold: 1\n---\n' + body, body):
            result = self.build.render_design_md(existing, tokens, index)
            self.assertEqual(result, head + body)
            self.assertEqual(self.build.render_design_md(result, tokens, index), result)  # idempotent
        self.assertEqual(self.build.render_design_md('---\nold: 1\n---\n', tokens, index), head)

    def test_empty_existing_takes_the_template_body(self):
        tokens, index = base_files()['tokens.json'], base_files()['design-system.json']
        result = self.build.render_design_md('', tokens, index)
        self.assertTrue(result.startswith(FULL_FRONT_MATTER + '## Overview\n'))
        self.assertNotIn('do not edit', result)
        self.assertNotIn('\r', result)
        self.assertEqual(v3.validate_design_md_structure(result), [])
        self.assertEqual(self.build.split_front_matter(result)[0], FULL_FRONT_MATTER)

    def test_check_detects_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            before = Path(directory, 'DESIGN.md').read_bytes()
            code, out, err = self.run_cli('--package', directory, '--design-md', '--check')
            self.assertEqual((code, out, err.strip()), (1, '', 'design_md_stale: DESIGN.md'))
            self.assertEqual(Path(directory, 'DESIGN.md').read_bytes(), before)
            Path(directory, 'DESIGN.md').unlink()
            code, out, err = self.run_cli('--package', directory, '--design-md', '--check')
            self.assertEqual((code, err.strip()), (1, 'design_md_missing: DESIGN.md'))
            self.assertFalse(Path(directory, 'DESIGN.md').exists())

    def test_build_twice_same_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            path = Path(directory, 'DESIGN.md')
            code, out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, err), (0, ''))
            self.assertEqual(out.strip(), 'BUILT: design-md=written viewer=skipped adapters=0 written, 0 skipped')
            first = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertTrue(path.read_text(encoding='utf-8').startswith(FULL_FRONT_MATTER + '\n## Overview\n'))
            code, out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, err), (0, ''))
            self.assertEqual(out.strip(), 'BUILT: design-md=unchanged viewer=skipped adapters=0 written, 0 skipped')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), first)
            code, out, err = self.run_cli('--package', directory, '--design-md', '--check')
            self.assertEqual((code, out.strip(), err), (0, 'CHECKED: design-md=ok viewer=skipped', ''))
            errors, _warnings = v3.verify_package(Path(directory))
            self.assertEqual(errors, [])

    def test_build_after_token_edit_becomes_stale_then_fresh(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            self.assertEqual(self.run_cli('--package', directory, '--design-md')[0], 0)
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'][2].update(value='#0057b9'))
            code, _out, err = self.run_cli('--package', directory, '--design-md', '--check')
            self.assertEqual((code, err.strip()), (1, 'design_md_stale: DESIGN.md'))
            self.assertEqual(self.run_cli('--package', directory, '--design-md')[1].strip(),
                             'BUILT: design-md=written viewer=skipped adapters=0 written, 0 skipped')
            self.assertIn('  accent: "#0057b9"\n', Path(directory, 'DESIGN.md').read_text(encoding='utf-8'))

    def test_cli_requires_content_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            for argv in (['--package', directory], ['--package', directory, '--check'], ['--package', str(Path(directory, 'absent'))], []):
                code, out, err = self.run_cli(*argv)
                self.assertEqual((code, out, err.strip()), (1, '', 'input_error: choose --design-md/--viewer/--adapters'), argv)

    def test_cli_package_must_be_a_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = self.run_cli('--package', str(Path(directory, 'absent')), '--design-md')
            self.assertEqual((code, out), (1, ''))
            self.assertTrue(err.startswith('input_error: package not found: '), err)
            code, _out, err = self.run_cli('--design-md')
            self.assertEqual((code, err.strip()), (1, 'input_error: --package is required'))

    def test_cli_refuses_invalid_tokens_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            before = Path(directory, 'DESIGN.md').read_bytes()
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'].append(color('bad', 'red')))
            code, out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, out), (1, ''))
            self.assertIn('forbidden_color_syntax: tokens.json: color.bad', err)
            self.assertEqual(Path(directory, 'DESIGN.md').read_bytes(), before)
            make(directory, tokens__json=None)
            Path(directory, 'tokens.json').unlink()
            put(directory, 'design-system.json', '[')
            code, _out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual(code, 1)
            self.assertEqual(err.split('\n')[:2], ['missing_required_file: tokens.json', 'invalid_index_value: design-system.json: json'])
            put(directory, 'tokens.json', '{"a":')
            put(directory, 'design-system.json', {'v': 4})
            code, _out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual(err.split('\n')[:2], ['token_shape: tokens.json: json', 'unsupported_format_version: design-system.json: v: 4'])

    def test_cli_bounds_and_decodes_design_md(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md='x' * 600000)
            code, _out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, err.strip()), (1, 'limit_exceeded: DESIGN.md: file size: 600000 > 512000'))
            self.assertEqual(Path(directory, 'DESIGN.md').stat().st_size, 600000)
            put(directory, 'DESIGN.md', b'\xff\xfe## Overview\n')
            code, _out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, err.strip()), (1, 'input_error: DESIGN.md: not valid UTF-8'))

    def test_cli_never_opens_a_linked_or_sensitive_design_md(self):
        real = v3.safe_path

        def refuse_design_md(root, relative):
            if relative == 'DESIGN.md':
                raise ValueError('linked_path')
            return real(root, relative)

        with tempfile.TemporaryDirectory() as directory, patch.object(self.cli_module.v3, 'safe_path', refuse_design_md):
            make(directory)
            before = Path(directory, 'DESIGN.md').read_bytes()
            code, out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, out, err.strip()), (1, '', 'refused_sensitive_path: DESIGN.md'))
            self.assertEqual(Path(directory, 'DESIGN.md').read_bytes(), before)

    def test_cli_creates_design_md_from_the_template(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=None)
            code, out, err = self.run_cli('--package', directory, '--design-md')
            self.assertEqual((code, err), (0, ''))
            self.assertIn('design-md=written', out)
            text = Path(directory, 'DESIGN.md').read_text(encoding='utf-8')
            self.assertTrue(text.startswith(FULL_FRONT_MATTER + '## Overview\n'))

    def test_build_leaves_other_package_files_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            names = sorted(str(p.relative_to(directory)) for p in Path(directory).rglob('*') if p.is_file())
            before = {n: Path(directory, n).read_bytes() for n in names if n != 'DESIGN.md'}
            self.assertEqual(self.run_cli('--package', directory, '--design-md')[0], 0)
            after_names = sorted(str(p.relative_to(directory)) for p in Path(directory).rglob('*') if p.is_file())
            self.assertEqual(after_names, names)
            self.assertEqual({n: Path(directory, n).read_bytes() for n in names if n != 'DESIGN.md'}, before)

    # ---- TK6 fix 1 (review PS-1, NS-1, GC-1)

    def test_bom_without_front_matter_leaves_no_bom_in_the_body(self):
        existing = '\ufeff## Overview\n\n- Read order: README.md\n- Owner: A\n- Status: draft\n'
        text = self.build.render_design_md(existing, tok(color=[color('bg', '#ffffff')]), INDEX)
        self.assertNotIn('\ufeff', text)
        front, body = self.build.split_front_matter(text)
        self.assertTrue(body.startswith('## Overview\n'), body[:20])
        self.assertEqual(self.build.render_design_md(text, tok(color=[color('bg', '#ffffff')]), INDEX), text)
        # A BOM that sits in front of a front matter block is dropped with it; a BOM deeper in the body is not touched.
        deeper = '---\nversion: alpha\n---\n## Overview\n\ufeffx\n'
        self.assertIn('\ufeffx', self.build.render_design_md(deeper, tok(), INDEX))

    def test_bom_without_front_matter_through_the_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=b'\xef\xbb\xbf' + design_md().split('---\n', 2)[2].encode('utf-8'))
            self.assertEqual(self.run_cli('--package', directory, '--design-md')[0], 0)
            raw = Path(directory, 'DESIGN.md').read_bytes()
            self.assertEqual(raw.count(b'\xef\xbb\xbf'), 0)
            self.assertEqual(v3.validate_design_md_structure(raw.decode('utf-8')), [])
            self.assertEqual(self.run_cli('--package', directory, '--design-md', '--check')[0], 0)

    def test_output_larger_than_the_cap_is_refused_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md='x' * v3.CAP_KEPT)
            before = Path(directory, 'DESIGN.md').read_bytes()
            for extra in ((), ('--check',)):
                code, out, err = self.run_cli('--package', directory, '--design-md', *extra)
                self.assertEqual((code, out), (1, ''), extra)
                self.assertRegex(err.strip(), r'^limit_exceeded: DESIGN\.md: file size: \d+ > 512000$')
                self.assertEqual(Path(directory, 'DESIGN.md').read_bytes(), before)
            # One that fits after the head is added is written, and the next run leaves it alone.
            put(directory, 'DESIGN.md', 'x' * 400000)
            self.assertEqual(self.run_cli('--package', directory, '--design-md')[0], 0)
            self.assertEqual(self.run_cli('--package', directory, '--design-md')[1].strip(),
                             'BUILT: design-md=unchanged viewer=skipped adapters=0 written, 0 skipped')

    def test_small_numbers_are_plain_decimals(self):
        style = {'name': 'tiny', 'fontSize': 1e-07, 'fontWeight': 400, 'lineHeight': 1e-05, 'usage': 'u'}
        doc = styled(style)
        doc['radius'] = {'tokens': [{'name': 'r', 'value': 1e-07, 'usage': 'u'}, {'name': 'big', 'value': 2.5e-05, 'usage': 'u'}]}
        text = self.front(doc)
        self.assertNotRegex(text, r'\d[eE][+-]?\d')
        self.assertIn('lineHeight: 0.00001\n', text)
        self.assertIn('fontSize: "0.0000001px"\n', text)
        self.assertIn('  r: "0.0000001px"\n', text)
        self.assertIn('  big: "0.000025px"\n', text)
        self.assertIn('lineHeight: 1.5\n', self.front(styled({'name': 'a', 'lineHeight': 1.5, 'usage': 'u'})))
        self.assertIn('lineHeight: 2\n', self.front(styled({'name': 'a', 'lineHeight': 2.0, 'usage': 'u'})))
        self.assertIn('lineHeight: 0.00001\n', self.front(styled({'name': 'a', 'lineHeight': '0.00001', 'usage': 'u'})))


# ---------------------------------------------------------------------------
# viewer.html generator (SPR-32 TK7). Every package below is invented; hostile text is there on purpose.
# ---------------------------------------------------------------------------

PNG = b'\x89PNG\r\n\x1a\n'
EIGHT = ['overview', 'colors', 'typography', 'spacing', 'components', 'assets', 'files', 'agents']
CLEAN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10">'
             '<defs><linearGradient id="g"><stop offset="0" stop-color="#fff"/></linearGradient><path id="a" d="M0 0h5v5z"/></defs>'
             '<g style="fill:#fff;font-family:Inter"><use href="#a"/><rect width="4" height="4" fill="url(#g)"/>'
             '<text x="1" y="2">Sample <tspan>Studio</tspan></text><text>Tagline here</text></g></svg>')
COVER = '<!-- @dsCard height=300 -->\n' + CLEAN_SVG + '\n'


class ViewerBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = importlib.import_module('design_system_build')
        path = Path(__file__).with_name('build-design-system.py')
        loader_spec = importlib.util.spec_from_file_location('design_system_builder_viewer', path)
        cls.cli_module = importlib.util.module_from_spec(loader_spec)
        loader_spec.loader.exec_module(cls.cli_module)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = self.cli_module.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def page(self, directory):
        data = self.build.collect_package(Path(directory))
        return self.build.render_viewer(data), data

    def sections(self, text):
        return re.findall(r'<section id="([a-z]+)"', text)

    # ---- structure

    def test_viewer_sections_eight(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            text, _data = self.page(directory)
        self.assertEqual(self.sections(text), EIGHT)
        self.assertEqual(re.findall(r'<nav[^>]*>(.*?)</nav>', text, re.S)[0].count('href="#'), 8)
        for name in EIGHT:
            self.assertIn(f'<a href="#{name}">', text)
        self.assertEqual(len(re.findall(r'<h1[ >]', text)), 1)
        self.assertTrue(text.startswith('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">'))
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', text)
        self.assertIn('<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; '
                      'style-src \'unsafe-inline\'; script-src \'unsafe-inline\'">', text)

    def test_viewer_title_static_label(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            text, _data = self.page(directory)
            self.assertIn('<title>Sample Studio — static viewer — not a Claude Design render</title>', text)
            self.assertIn('<h1>Sample Studio</h1>', text)
            edit_json(directory, 'design-system.json', lambda d: d.update(title='<b>"Q" & co</b>\n\tx'))
            text, _data = self.page(directory)
        self.assertIn('<title>&lt;b&gt;&quot;Q&quot; &amp; co&lt;/b&gt; x — static viewer', text)
        self.assertEqual(len(re.findall(r'<title>', text)), 1)
        self.assertNotIn('<b>', text)

    def test_viewer_token_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)

            def grow(doc):
                doc['color']['tokens'].append(color('extra', '#123456'))
                doc['spacing']['tokens'].append({'name': 'space-2', 'value': '8px', 'usage': 'gap'})
                doc['shadow'] = {'tokens': [{'name': 'lift', 'value': '0 1px 2px #00000040', 'usage': 'card'},
                                            {'name': 'float', 'value': '0 8px 16px #00000040', 'usage': 'menu'}]}
                doc['type']['groups'][0]['styles'].append({'name': 'caption', 'fontSize': '12px', 'usage': 'small'})

            edit_json(directory, 'tokens.json', grow)
            text, data = self.page(directory)
        expected = 4 + 1 + 1 + 1 + 1 + 2 + 1 + 1  # colours, spacing, radius, styles, then the additions
        self.assertEqual(text.count('data-token='), expected)
        self.assertEqual(self.build.count_tokens(data['tokens']), expected)
        for name in ('bg', 'text', 'accent', 'link', 'extra', 'space-1', 'space-2', 'radius-sm', 'lift', 'float', 'body', 'caption'):
            self.assertEqual(text.count(f'data-token="{name}"'), 1, name)

    def test_viewer_component_and_asset_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'components/Button/README.md', '# Button\n\nA plain action control. It has two states.\n\n- primary\n- quiet\n')
            put(directory, 'components/Button/preview.html', '<!-- @dsCard height=120 group="Actions" -->\n<p>x</p>\n')
            put(directory, 'components/Card/preview.html', '<!-- @dsCard page group="Templates" -->\n<p>x</p>\n')
            put(directory, 'components/lib/x.js', 'x')
            put(directory, 'assets/Logos/README.md', 'a.png, b.svg, c.zip, sub/d.png\n')
            put(directory, 'assets/Logos/a.png', PNG + bytes(100))
            put(directory, 'assets/Logos/b.svg', CLEAN_SVG)
            put(directory, 'assets/Logos/c.zip', b'PK\x03\x04')
            put(directory, 'assets/Logos/sub/d.png', PNG)
            put(directory, 'assets/Loose.png', PNG)
            text, data = self.page(directory)
        self.assertEqual(text.count('data-component='), 2)
        self.assertEqual([c['name'] for c in data['components']], ['Button', 'Card'])
        self.assertEqual(text.count('data-asset='), 5)
        self.assertEqual([a['path'] for a in data['assets']],
                         ['assets/Logos/a.png', 'assets/Logos/b.svg', 'assets/Logos/c.zip', 'assets/Logos/sub/d.png', 'assets/Loose.png'])
        button = data['components'][0]
        self.assertEqual((button['group'], button['summary'], button['rel']), ('Actions', 'A plain action control.', 'components/Button/preview.html'))
        self.assertEqual(button['marker'], '@dsCard height=120 group="Actions"')
        self.assertIn('<li>primary</li>', button['readme_html'])
        self.assertEqual(data['components'][1]['group'], 'Templates')
        self.assertIn('<a href="components/Button/preview.html">', text)
        self.assertNotIn('<iframe', text)
        self.assertNotIn('<img alt="assets/Logos/c.zip"', text)
        self.assertEqual(text.count('<img '), 4)  # a.png, b.svg, sub/d.png and the ungrouped Loose.png
        self.assertIn('listed, not embedded', text)
        self.assertEqual(data['warnings'], [])

    def test_viewer_no_components_message(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            text, _data = self.page(directory)
        self.assertIn('No components', text)
        self.assertNotIn('data-component=', text)
        self.assertIn('No assets', text)

    def test_viewer_excludes_self_from_files(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'viewer.html', '<p>old</p>')
            put(directory, 'sub/viewer.html', 'kept')
            put(directory, '.hidden', 'x')
            put(directory, 'notes/.dot', 'x')
            put(directory, '.env', 'SECRET_VALUE=1')
            put(directory, 'credentials.json', 'SECRET_VALUE')
            text, data = self.page(directory)
        paths = [f['path'] for f in data['files']]
        self.assertEqual(paths, sorted(paths))
        self.assertNotIn('viewer.html', paths)
        self.assertIn('sub/viewer.html', paths)
        self.assertNotIn('.hidden', ' '.join(paths))
        self.assertNotIn('.env', ' '.join(paths))
        self.assertNotIn('credentials', ' '.join(paths))
        self.assertNotIn('SECRET_VALUE', text)
        self.assertIn('<code>tokens.json</code> <span class="mut">', text)
        self.assertEqual(dict((f['path'], f['size']) for f in data['files'])['README.md'], len(base_files()['README.md'].encode()))

    def test_viewer_script_under_4kb(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'components/Evil/README.md', '<script>alert(1)</script>\n')
            text, _data = self.page(directory)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', text)
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', text, re.S)
        self.assertEqual(len(scripts), 1)
        self.assertLessEqual(len(scripts[0].encode('utf-8')), 4096)
        self.assertNotRegex(text, r'<script\b[^>]*\bsrc\b')
        for word in ('innerHTML', 'outerHTML', 'eval(', 'fetch', 'XMLHttpRequest', 'new Function', 'WebSocket', 'serviceWorker',
                     'import(', 'document.write'):
            self.assertNotIn(word, text, word)
        self.assertNotRegex(text, r'\son[a-z]+\s*=')

    def test_viewer_no_external_ref(self):
        with tempfile.TemporaryDirectory() as directory:
            hostile = ('See [site](https://evil.example/a) and https://cdn.example/x.js or //cdn.example/y.\n\n'
                       '[proto](//evil.example) [abs](/etc/passwd) [up](../x) [js](javascript:alert(1)) ![pic](http://evil.example/i.png)\n')
            make(directory, components__Cover__preview__html=COVER,
                 DESIGN__md=design_md(overview=OVERVIEW + '\n' + hostile))
            put(directory, 'components/Doc/README.md', hostile)
            put(directory, 'assets/G/README.md', 'a.svg\n\n' + hostile)
            put(directory, 'assets/G/a.svg', CLEAN_SVG)
            text, _data = self.page(directory)
        stripped = re.sub(r'xmlns(?::[A-Za-z]+)?="[^"]*"', '', text)
        self.assertEqual(re.findall(r'https?://|//cdn', stripped), [])
        for value in re.findall(r'(?:src|href)="([^"]*)"', stripped):
            self.assertFalse(value.startswith(('http', '//', '/')), value)
        self.assertNotIn('url(http', text)
        self.assertIn('site', text)  # the label survives, the link does not
        self.assertNotIn('evil.example/a"', text)
        self.assertNotIn('javascript:', text.replace('href="#', ''))

    def test_viewer_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html=COVER)
            put(directory, 'components/Button/README.md', 'A control.\n')
            put(directory, 'assets/G/README.md', 'a.png')
            put(directory, 'assets/G/a.png', PNG + bytes(50))
            self.assertEqual(self.run_cli('--package', directory, '--design-md', '--viewer')[0], 0)
            first = [hashlib.sha256(Path(directory, n).read_bytes()).hexdigest() for n in ('DESIGN.md', 'viewer.html')]
            code, out, err = self.run_cli('--package', directory, '--design-md', '--viewer')
            second = [hashlib.sha256(Path(directory, n).read_bytes()).hexdigest() for n in ('DESIGN.md', 'viewer.html')]
            self.assertEqual((code, err), (0, ''))
            self.assertEqual(out.strip(), 'BUILT: design-md=unchanged viewer=unchanged adapters=0 written, 0 skipped')
            self.assertEqual(first, second)
            # The order the operating system lists a folder in must not matter.
            real = v3._walk

            def backwards(root):
                entries, files, dirs, links = real(root)
                return entries[::-1], dict(reversed(list(files.items()))), dirs, links

            with patch.object(v3, '_walk', backwards):
                text = self.build.render_viewer(self.build.collect_package(Path(directory)))
            self.assertEqual(text.encode('utf-8'), Path(directory, 'viewer.html').read_bytes())

    def test_viewer_check_detects_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            code, _out, err = self.run_cli('--package', directory, '--viewer', '--check')
            self.assertEqual((code, err.strip()), (1, 'viewer_missing: viewer.html'))
            self.assertFalse(Path(directory, 'viewer.html').exists())
            self.assertEqual(self.run_cli('--package', directory, '--viewer')[0], 0)
            code, out, err = self.run_cli('--package', directory, '--viewer', '--check')
            self.assertEqual((code, out.strip(), err), (0, 'CHECKED: design-md=skipped viewer=ok', ''))
            path = Path(directory, 'viewer.html')
            raw = bytearray(path.read_bytes())
            raw[len(raw) // 2] ^= 0x01
            path.write_bytes(bytes(raw))
            before = path.read_bytes()
            code, _out, err = self.run_cli('--package', directory, '--viewer', '--check')
            self.assertEqual((code, err.strip()), (1, 'viewer_stale: viewer.html'))
            self.assertEqual(path.read_bytes(), before)
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'][2].update(value='#0057b9'))
            self.assertEqual(self.run_cli('--package', directory, '--viewer')[1].strip(),
                             'BUILT: design-md=skipped viewer=written adapters=0 written, 0 skipped')
            code, out, _err = self.run_cli('--package', directory, '--design-md', '--viewer', '--check')
            self.assertEqual((code, out.strip()), (1, ''))  # DESIGN.md was not regenerated: stale before the viewer is looked at

    def test_cli_viewer_output_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            code, out, err = self.run_cli('--package', directory, '--viewer')
            self.assertEqual((code, err), (0, ''))
            self.assertEqual(out.strip(), 'BUILT: design-md=skipped viewer=written adapters=0 written, 0 skipped')
            code, out, err = self.run_cli('--package', directory, '--design-md', '--viewer')
            # The page lists DESIGN.md with its size, and the front matter just made it longer: both files are written.
            self.assertEqual(out.strip(), 'BUILT: design-md=written viewer=written adapters=0 written, 0 skipped')
            code, out, err = self.run_cli('--package', directory, '--design-md', '--viewer')
            self.assertEqual(out.strip(), 'BUILT: design-md=unchanged viewer=unchanged adapters=0 written, 0 skipped')
            code, out, err = self.run_cli('--package', directory, '--design-md', '--viewer', '--check')
            self.assertEqual((code, out.strip(), err), (0, 'CHECKED: design-md=ok viewer=ok', ''))
            Path(directory, 'viewer.html').unlink()
            self.assertEqual(self.run_cli('--package', directory, '--design-md', '--viewer')[1].strip(),
                             'BUILT: design-md=unchanged viewer=written adapters=0 written, 0 skipped')

    def test_cli_viewer_refuses_bad_input_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'].append(color('bad', 'red')))
            code, out, err = self.run_cli('--package', directory, '--viewer')
            self.assertEqual((code, out), (1, ''))
            self.assertIn('forbidden_color_syntax: tokens.json: color.bad', err)
            self.assertFalse(Path(directory, 'viewer.html').exists())
        real = v3.safe_path

        def refuse(root, relative):
            if relative == 'viewer.html':
                raise ValueError('linked_path')
            return real(root, relative)

        with tempfile.TemporaryDirectory() as directory, patch.object(self.cli_module.v3, 'safe_path', refuse):
            make(directory)
            code, out, err = self.run_cli('--package', directory, '--viewer')
            self.assertEqual((code, out, err.strip()), (1, '', 'refused_sensitive_path: viewer.html'))

    def test_cli_viewer_size_limits(self):
        words = ('lorem ipsum dolor sit amet ' * 2400)[:63900] + '\n'
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            for n in range(5):
                put(directory, f'components/C{n}/README.md', words)
            code, out, err = self.run_cli('--package', directory, '--viewer')
            size = Path(directory, 'viewer.html').stat().st_size
            self.assertEqual((code, err), (0, ''))
            self.assertTrue(300000 < size <= 512000, size)
            self.assertIn(f'WARN viewer_large: viewer.html: {size} > 300000\n', out)
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            for n in range(9):
                put(directory, f'components/C{n}/README.md', words)
            code, out, err = self.run_cli('--package', directory, '--viewer')
            self.assertEqual((code, out), (1, ''))
            self.assertRegex(err.strip(), r'^viewer_too_large: viewer\.html: \d+ > 512000$')
            self.assertFalse(Path(directory, 'viewer.html').exists())
            self.assertEqual(self.run_cli('--package', directory, '--viewer', '--check')[0], 1)

    # ---- sensitive files and bounded reads

    def test_collect_package_skips_sensitive(self):
        seen = []
        real_open = Path.open

        def spy_open(self, *args, **kwargs):
            seen.append(self.name)
            return real_open(self, *args, **kwargs)

        def forbidden(self, *args, **kwargs):
            raise AssertionError(f'unbounded read of {self.name}')

        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, '.env', 'SECRET_VALUE=1')
            put(directory, 'credentials.json', 'SECRET_VALUE')
            put(directory, 'assets/G/README.md', 'secret.pem, auth.json, x.png')
            put(directory, 'assets/G/secret.pem', 'SECRET_VALUE')
            put(directory, 'assets/G/auth.json', 'SECRET_VALUE')
            put(directory, 'assets/G/credentials.png', PNG)
            put(directory, 'assets/G/x.png', PNG)
            put(directory, 'components/.env/README.md', 'SECRET_VALUE')
            put(directory, 'components/dist/README.md', 'SECRET_VALUE')
            with patch.object(Path, 'open', spy_open), patch.object(Path, 'read_text', forbidden), patch.object(Path, 'read_bytes', forbidden):
                text, data = self.page(directory)
            self.assertEqual(self.build.inline_asset(Path(directory, 'assets/G/credentials.png')), None)
            self.assertEqual(self.build.inline_asset(Path(directory, '.env')), None)
        for name in seen:
            self.assertIsNone(v3.SENSITIVE.search(name), name)
        self.assertNotIn('SECRET_VALUE', text)
        self.assertEqual([a['path'] for a in data['assets']], ['assets/G/x.png'])
        self.assertEqual(data['components'], [])
        listed = ' '.join(f['path'] for f in data['files'])
        for word in ('.env', 'credentials', 'secret.pem', 'auth.json', 'dist'):
            self.assertNotIn(word, listed)

    def test_collect_package_goes_through_safe_path(self):
        calls = []
        real = v3.safe_path

        def spy(root, relative):
            calls.append(relative)
            return real(root, relative)

        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/G/README.md', 'x.png')
            put(directory, 'assets/G/x.png', PNG)
            with patch.object(v3, 'safe_path', spy):
                self.page(directory)
        for needed in ('design-system.json', 'tokens.json', 'canonical-map.json', 'DESIGN.md', 'README.md', 'assets/G/x.png',
                       'assets/G/README.md', 'components/Cover/preview.html'):
            self.assertIn(needed, calls)

    def test_collect_package_reads_are_bounded(self):
        sizes = []
        real_open = io.open

        class Spy:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *exc):
                return self.handle.__exit__(*exc)

            def read(self, size=-1):
                sizes.append(size)
                return self.handle.read(size)

            def __getattr__(self, name):
                return getattr(self.handle, name)

        def spy_open(file, mode='r', *args, **kwargs):
            handle = real_open(file, mode, *args, **kwargs)
            return Spy(handle) if 'b' in mode else handle

        with tempfile.TemporaryDirectory() as directory:
            make(directory, README__md='## Content fundamentals\n' + 'x' * 600000, DESIGN__md='y' * 700000)
            put(directory, 'components/Big/README.md', 'z' * 300000)
            put(directory, 'components/Big/preview.html', '<!-- @dsCard -->\n' + 'p' * 600000)
            put(directory, 'assets/G/README.md', 'w' * 300000)
            put(directory, 'assets/G/huge.png', PNG + bytes(300000))
            with patch('io.open', spy_open):
                _text, data = self.page(directory)
        self.assertTrue(sizes and all(0 < n <= 512001 for n in sizes), sorted(set(sizes)))
        self.assertTrue(len(data['readme']) <= 200000 and len(data['design_md']) <= 512000)
        self.assertIn('README cut at 64000 bytes', data['components'][0]['readme_html'])
        self.assertIn('viewer_asset_skipped: assets/G/huge.png', data['warnings'])

    def test_large_asset_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/G/README.md', 'big.png small.png')
            put(directory, 'assets/G/big.png', PNG + bytes(70000 - 8))
            put(directory, 'assets/G/small.png', PNG + bytes(2000 - 8))
            self.assertIsNone(self.build.inline_asset(Path(directory, 'assets/G/big.png')))
            self.assertIsNone(self.build.inline_asset(Path(directory, 'assets/G/small.png'), cap=1000))
            small = self.build.inline_asset(Path(directory, 'assets/G/small.png'))
            self.assertTrue(small.startswith('data:image/png;base64,'))
            text, data = self.page(directory)
            code, out, _err = self.run_cli('--package', directory, '--viewer')
        self.assertEqual(text.count('data:image/png;base64,'), 1)
        self.assertEqual(data['warnings'], ['viewer_asset_skipped: assets/G/big.png'])
        self.assertIn('70000 bytes', text)
        self.assertIn('listed, not embedded', text)
        self.assertEqual((code, out.splitlines()[0]), (0, 'WARN viewer_asset_skipped: assets/G/big.png'))

    def test_total_embedded_images_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/G/README.md', 'img')
            for n in range(10):
                put(directory, f'assets/G/i{n}.png', PNG + bytes(60000))
            opened = []
            real = self.build.inline_asset

            def counting(path, *args, **kwargs):
                opened.append(Path(path).name)
                return real(path, *args, **kwargs)

            with patch.object(self.build, 'inline_asset', counting):
                text, data = self.page(directory)
        embedded = text.count('data:image/png;base64,')
        self.assertTrue(1 <= embedded <= 4, embedded)
        self.assertLessEqual(len(opened), embedded + 1)  # once the budget is spent, no further image is even read
        self.assertEqual(len(data['warnings']), 10 - embedded)
        self.assertEqual(text.count('data-asset='), 10)

    def test_viewer_svg_with_script_skipped(self):
        evil = ['<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"><rect/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg"><rect onclick="x()" width="1" height="1"/></svg>']
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html='<!-- @dsCard height=300 -->\n' + evil[0] + '\n')
            put(directory, 'assets/G/README.md', 'bad0.svg bad1.svg bad2.svg good.svg')
            for n, svg in enumerate(evil):
                put(directory, f'assets/G/bad{n}.svg', svg)
            put(directory, 'assets/G/good.svg', CLEAN_SVG)
            text, data = self.page(directory)
        self.assertNotIn('alert(1)', text)
        self.assertNotRegex(text, r'<script>alert')
        self.assertEqual(text.count('data:image/svg+xml;base64,'), 1)
        self.assertEqual(data['warnings'], ['viewer_asset_skipped: components/Cover/preview.html']
                         + [f'viewer_asset_skipped: assets/G/bad{n}.svg' for n in range(3)])
        self.assertIsNone(data['cover_svg'])
        self.assertIn('No cover image', text)

    def test_sanitize_svg_refuses_active_content(self):
        head = '<svg xmlns="http://www.w3.org/2000/svg">'
        bad = {
            'script': head + '<script>alert(1)</script></svg>',
            'script upper': head + '<SCRIPT>alert(1)</SCRIPT></svg>',
            'script spaced': head + '<script >alert(1)</script ></svg>',
            'onload': '<svg onload="alert(1)"><rect/></svg>',
            'onload upper': '<svg ONLOAD="alert(1)"><rect/></svg>',
            'onload spaced': '<svg onload = "alert(1)"><rect/></svg>',
            'onload slash': '<svg/onload=alert(1)></svg>',
            'onclick child': head + '<rect onclick="x()"/></svg>',
            'onmouseover single': head + "<rect onmouseover='x()'/></svg>",
            'foreignObject': head + '<foreignObject><div>x</div></foreignObject></svg>',
            'iframe': head + '<iframe src="x"></iframe></svg>',
            'anchor js': head + '<a href="javascript:alert(1)"><rect/></a></svg>',
            'use external': head + '<use href="http://x.example/a.svg#b"/></svg>',
            'use data': head + '<use xlink:href="data:image/svg+xml,x"/></svg>',
            'use relative': head + '<use href="other.svg#b"/></svg>',
            'image': head + '<image href="x.png"/></svg>',
            'style element': head + '<style>@import url(http://x.example/a.css);</style></svg>',
            'fill url ext': head + '<rect fill="url(http://x.example/a)"/></svg>',
            'style url proto': head + '<rect style="background:url(//x.example/a)"/></svg>',
            'style expression': head + '<rect style="width:expression(alert(1))"/></svg>',
            'entity js': head + '<a href="&#106;avascript:alert(1)"/></svg>',
            'entity in value': head + '<rect fill="&#117;rl(x)"/></svg>',
            'backslash css': head + '<rect style="fill:\\75 rl(x)"/></svg>',
            'comment': head + '<!-- x --></svg>',
            'cdata': head + '<![CDATA[x]]></svg>',
            'doctype': '<!DOCTYPE svg><svg></svg>',
            'pi': head + '<?xml-stylesheet href="x"?></svg>',
            'breakout p': head + '<p>x</p></svg>',
            'breakout math': head + '<math><mi>x</mi></math></svg>',
            'nested svg': head + '<svg><rect/></svg></svg>',
            'two roots': head + '</svg><svg></svg>',
            'unclosed': head + '<g>',
            'mismatch': head + '<g></rect></svg>',
            'set': head + '<set attributeName="href" to="javascript:alert(1)"/></svg>',
            'animate': head + '<animate attributeName="href" values="javascript:alert(1)"/></svg>',
            'data attr': head + '<rect data-token="x"/></svg>',
            'text on=': head + '<text> onerror=alert(1) </text></svg>',
            'text url': head + '<text>see https://x.example</text></svg>',
            'bare attribute': head + '<rect hidden/></svg>',
            'unquoted': head + '<rect width=4/></svg>',
            'lt in value': head + '<rect title="a<b"/></svg>',
            'nul': head + '<rect/>\x00</svg>',
            'svg title': head + '<title>x</title></svg>',
            'not svg': '<div></div>',
            'empty': '',
            'self closing root': '<svg/>',
            'closing with attr': head + '<g></g x="1"></svg>',
        }
        for label, text in bad.items():
            self.assertIsNone(self.build.sanitize_svg(text), label)
        self.assertIsNone(self.build.sanitize_svg(None))
        self.assertEqual(self.build.sanitize_svg(CLEAN_SVG), CLEAN_SVG)
        self.assertEqual(self.build.sanitize_svg('\n  ' + CLEAN_SVG + '\n'), CLEAN_SVG)
        self.assertEqual(self.build.extract_cover_svg('<!-- @dsCard -->\n<div>' + CLEAN_SVG + '</div>'), CLEAN_SVG)
        self.assertEqual(self.build.extract_cover_svg('<SVG a="1"><g/></SVG>'), '<SVG a="1"><g/></SVG>')
        self.assertIsNone(self.build.extract_cover_svg('<p>none</p>'))
        self.assertIsNone(self.build.extract_cover_svg('<svg>never closed'))
        self.assertIsNone(self.build.extract_cover_svg(None))

    # ---- Markdown

    def test_markdown_escapes_html(self):
        out = self.build.render_markdown('<script>x</script>')
        self.assertIn('&lt;script&gt;x&lt;/script&gt;', out)
        self.assertNotIn('<script', out)
        out = self.build.render_markdown('<img src=x onerror=alert(1)>')
        self.assertNotIn('<img', out)
        self.assertNotRegex(out, r'(?i)\son[a-z]+\s*=')
        self.assertIn('&lt;img', out)
        everything = self.build.render_markdown('# <b>t</b>\n\n- <i>x</i>\n\n```\n<script>y</script>\n```\n\n| <u>h</u> |\n|---|\n| <s>c</s> |\n\n> <em>q</em>\n\n**<a>**\n\n`<code>`')
        for tag in ('<b>', '<i>', '<script>', '<u>', '<s>', '<em>', '<a>', '<img'):
            self.assertNotIn(tag, everything, tag)

    def test_markdown_blocks_and_links(self):
        out = self.build.render_markdown('# Title\n\n## Sub\n\nText with **bold** and `code` and [b](components/Button/README.md).\n\n'
                                         '- one\n- two\n  more\n\n1. first\n2. second\n\n```\nraw <x> & y\n```\n\n> quoted\n\n---\n\n'
                                         '| a | b |\n| --- | --- |\n| 1 | 2 |\n')
        self.assertIn('<h3>Title</h3>', out)
        self.assertIn('<h4>Sub</h4>', out)
        self.assertNotIn('<h1', out)
        self.assertNotIn('<h2', out)
        self.assertIn('<strong>bold</strong>', out)
        self.assertIn('<code>code</code>', out)
        self.assertIn('<a href="components/Button/README.md">b</a>', out)
        self.assertIn('<ul><li>one</li><li>two more</li></ul>', out)
        self.assertIn('<ol><li>first</li><li>second</li></ol>', out)
        self.assertIn('<pre><code>raw &lt;x&gt; &amp; y</code></pre>', out)
        self.assertIn('<blockquote><p>quoted</p></blockquote>', out)
        self.assertIn('<hr>', out)
        self.assertIn('<th scope="col">a</th>', out)
        self.assertIn('<td>2</td>', out)
        self.assertEqual(self.build.render_markdown('# T', 5), '<h5>T</h5>')
        self.assertEqual(self.build.render_markdown('###### T', 5), '<h6>T</h6>')
        self.assertEqual(self.build.render_markdown(''), '')

    def test_markdown_links_keep_only_relative_files(self):
        render = self.build.render_markdown
        self.assertEqual(render('[a](http://x.example)'), '<p>a</p>')
        self.assertEqual(render('[a](https://x.example/p)'), '<p>a</p>')
        self.assertEqual(render('[a](//x.example)'), '<p>a</p>')
        self.assertEqual(render('[a](/abs/path)'), '<p>a</p>')
        self.assertEqual(render('[a](../up/file.md)'), '<p>a</p>')
        self.assertEqual(render('[a](x/../y.md)'), '<p>a</p>')
        self.assertEqual(render('[a](javascript:alert(1))'), '<p>a</p>')
        self.assertEqual(render('[a](JaVaScRiPt:alert(1))'), '<p>a</p>')
        self.assertEqual(render('[a](data:text/html,x)'), '<p>a</p>')
        self.assertEqual(render('[a](file:' + '//' + '/etc/passwd)'), '<p>a</p>')
        self.assertEqual(render('[a](a b.md)'), '<p>a</p>')
        self.assertEqual(render('[a](x"onmouseover="y)'), '<p>a</p>')
        self.assertEqual(render('[a](x?q=1)'), '<p>a</p>')
        self.assertEqual(render('![pic](img.png)'), '<p>pic</p>')
        self.assertEqual(render('[a](notes/x.md#part)'), '<p><a href="notes/x.md#part">a</a></p>')
        self.assertEqual(render('[a](x.md) [b](y.md)'), '<p><a href="x.md">a</a> <a href="y.md">b</a></p>')
        self.assertEqual(render('[a'), '<p>[a</p>')
        self.assertEqual(render('a](b)'), '<p>a](b)</p>')

    def test_markdown_inputs_run_in_linear_time(self):
        n = 100000
        m = n // 4  # per-line constructs: the cost is per line, so fewer lines than characters
        cases = {
            'backticks': '`' * n, 'backtick pairs': '`a' * n, 'stars': '*' * n, 'bold open': '**a' * (n // 2), 'bold odd': '*a' * n,
            'open brackets': '[' * n, 'bracket then close': '[' * n + ']', 'link heads': '[a](' * (n // 4),
            'link no close': '[a](' + 'x' * n, 'close brackets': ']' * n, 'bang': '![' * n, 'bang links': '![a](b' * (n // 6),
            'many lines': 'word\n' * m, 'list': '- item\n' * m, 'ordered': '1. item\n' * m, 'quote': '> q\n' * m,
            'table': '| a | b |\n|---|---|\n' + '| 1 | 2 |\n' * m, 'table heads': '| a |\n' * m, 'fences': '```\n' * m,
            'hashes': '#' * n, 'headings': '# h\n' * m, 'rules': '---\n' * m, 'spaces': ' ' * n + 'x', 'long line': 'word ' * n,
            'nested links': '[[[[a]](b)](c)](d)' * (n // 20), 'digits': '1' * n + '.',
        }
        for label, text in cases.items():
            start = time.perf_counter()
            self.build.render_markdown(text)
            elapsed = time.perf_counter() - start
            self.assertLess(elapsed, 2.0, f'{label}: {elapsed:.2f} s')

    def test_sanitize_svg_runs_in_linear_time(self):
        head = '<svg xmlns="http://www.w3.org/2000/svg">'
        cases = {
            'unclosed tags': head + '<a ' * 50000 + '</svg>', 'attribute flood': head + '<g ' + 'a="1" ' * 100000 + '/></svg>',
            'comment flood': head + '<!--' * 50000 + '</svg>', 'deep': head + '<g>' * 100000 + '</svg>',
            'many tags': head + '<g/>' * 100000 + '</svg>', 'spaces': head + ' ' * 200000 + '</svg>',
            'long value': head + '<g a="' + 'x' * 200000 + '"/></svg>', 'unterminated value': head + '<g a="' + 'x' * 200000 + '/></svg>',
            'lt flood': head + '<' * 100000 + '</svg>', 'on run': head + '<text>' + ' on' * 60000 + '</text></svg>',
            'letters': head + '<text>' + ' on' + 'a' * 200000 + '</text></svg>', 'big clean': head + '<g>' * 1000 + '</g>' * 1000 + '</svg>',
        }
        for label, text in cases.items():
            start = time.perf_counter()
            self.build.sanitize_svg(text)
            elapsed = time.perf_counter() - start
            self.assertLess(elapsed, 2.0, f'{label}: {elapsed:.2f} s')
        start = time.perf_counter()
        self.build.extract_cover_svg('<svg ' * 200000)
        self.assertLess(time.perf_counter() - start, 2.0)

    def test_viewer_runs_in_linear_time_on_hostile_package(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, README__md='[' * 150000, DESIGN__md='---\nversion: alpha\n---\n## Overview\n' + '- Read order: ' + ',' * 100000 + '\n')
            put(directory, 'components/C/README.md', '`' * 60000)
            put(directory, 'assets/G/README.md', '*' * 60000)
            start = time.perf_counter()
            text, _data = self.page(directory)
            self.assertLess(time.perf_counter() - start, 3.0)
        self.assertEqual(self.sections(text), EIGHT)

    # ---- render_viewer on hostile data (no validation in front of it)

    def test_render_viewer_escapes_names_and_gates_css(self):
        hostile = '"><script>alert(1)</script><img src=x onerror=alert(1)>'
        data = {'index': {'title': hostile},
                'tokens': {'color': {'themes': [{'id': hostile}], 'tokens': [{'name': hostile, 'value': {hostile: 'red; background:url(//x)'}, 'usage': hostile}]},
                           'spacing': {'tokens': [{'name': 'a', 'value': '4px;background:url(//x.example/y)', 'usage': 'u'},
                                                  {'name': 'b', 'value': 'calc(1px + 2px)', 'usage': 'u'}]},
                           'radius': {'tokens': [{'name': 'c', 'value': '1px" onmouseover="x', 'usage': 'u'}]},
                           'shadow': {'tokens': [{'name': 'd', 'value': '0 0 1px url(//x.example)', 'usage': 'u'},
                                                 {'name': 'e', 'value': '0 0 1px red;}body{display:none', 'usage': 'u'},
                                                 {'name': 'f', 'value': '0 1px 2px #00000040', 'usage': 'u'}]},
                           'type': {'families': {'sans': 'Inter;}body{display:none', 'ok': '"Helvetica Neue", Arial'},
                                    'groups': [{'name': hostile, 'family': 'sans', 'styles': [
                                        {'name': hostile + '1', 'fontSize': '16px;color:red', 'fontWeight': '400;x', 'lineHeight': '1;y', 'usage': hostile},
                                        {'name': 'good', 'family': 'ok', 'fontSize': '16px', 'fontWeight': 700, 'lineHeight': 1.5, 'usage': 'u'}]}]}},
                'canonical': {'system': {'status': hostile, 'version': hostile}, 'checks': {'contrast': [{'fg': hostile, 'bg': hostile}, 'junk', {}]}},
                'design_md': '## Overview\n- Owner: ' + hostile + '\n- Read order: ' + hostile + '\n',
                'components': [{'name': hostile, 'group': hostile, 'summary': hostile, 'readme_html': '', 'marker': hostile, 'rel': hostile + '/preview.html'}],
                'assets': [{'group': hostile, 'path': 'assets/' + hostile, 'size': 1, 'inline': None}],
                'files': [{'path': 'a/' + hostile, 'size': 1}], 'cover_svg': None, 'asset_readmes': {}}
        text = self.build.render_viewer(data)
        self.assertEqual(len(re.findall(r'<script\b', text)), 1)
        self.assertNotIn('<img src=x', text)
        self.assertNotRegex(text, r'\son[a-z]+\s*=')
        self.assertNotIn('onmouseover', text.replace('onmouseover&#61;', ''))
        styles = re.findall(r'style="([^"]*)"', text)
        for value in styles:
            self.assertNotRegex(value, r'url|;\}|display:none|background:url|onmouseover|color:red')
        joined = ' '.join(styles)
        self.assertIn('box-shadow:0 1px 2px #00000040', joined)
        self.assertIn('font-family:&quot;Helvetica Neue&quot;, Arial', text)
        self.assertIn('font-size:min(16px,72px)', joined)
        self.assertIn('font-weight:700', joined)
        self.assertIn('line-height:1.5', joined)
        self.assertEqual(self.sections(text), EIGHT)
        self.assertEqual(self.build.render_viewer({}).count('<section '), 8)
        self.assertEqual(self.build.render_viewer({'tokens': [], 'index': [], 'canonical': 3}).count('<section '), 8)

    def test_render_viewer_swatches_and_contrast(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            edit_json(directory, 'tokens.json', lambda d: d['color']['tokens'].extend(
                [color('ink', 'oklch(0 0 0)'), color('mid', 'lab(50% 0 0)'), color('pale', '#777777')]))
            edit_json(directory, 'canonical-map.json', lambda d: d['checks']['contrast'].extend(
                [{'fg': 'pale', 'bg': 'bg', 'min': 4.5}, {'fg': 'mid', 'bg': 'bg'}, {'fg': 'ink', 'bg': 'bg', 'large': True}, {'fg': 'nope', 'bg': 'bg'}]))
            text, _data = self.page(directory)
        self.assertIn('background:#000000', text)  # oklch(0 0 0)
        self.assertIn('background:#0057b8', text)
        self.assertEqual(text.count('background:#0057b8'), 4)  # accent and link, two themes each
        self.assertIn('<code>lab(50% 0 0)</code>', text)
        self.assertEqual(len(re.findall(r'class="sw"', text)), 12)  # four base colours, ink and pale in two themes; lab(): none
        self.assertIn(f'<td>{v3.contrast_ratio("#111111", "#ffffff"):.2f}</td><td>4.5</td><td>Pass</td>', text)
        self.assertIn('<td>4.48</td><td>4.5</td><td>Fail</td>', text)  # #777777 on white, light theme
        self.assertIn('Not measured', text)
        self.assertIn('<th scope="row">text on bg</th><td>dark</td>', text)

    def test_overview_and_agents_come_from_the_package(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html=COVER,
                 DESIGN__md=design_md(overview='- Read order: README.md, tokens.json, `components/`\n- Owner: Sample Studio team\n'
                                               '- Status: draft\n\nThe overview paragraph is here.\n'))
            edit_json(directory, 'canonical-map.json', lambda d: d['system'].update(version='0.3.1', status='approved', id='sample-ds'))
            text, data = self.page(directory)
        overview = text.split('<section id="overview"')[1].split('</section>')[0]
        self.assertIn('<svg xmlns=', overview)
        self.assertIn('Tagline here', overview)
        self.assertIn('<dt>Status</dt><dd>approved</dd>', overview)
        self.assertIn('<dt>Version</dt><dd>0.3.1</dd>', overview)
        self.assertIn('<dt>Owner</dt><dd>Sample Studio team</dd>', overview)
        self.assertIn('The overview paragraph is here.', overview)
        self.assertIn('<details open><summary>components/', overview)
        self.assertIn('(1 file)', overview)
        agents = text.split('<section id="agents"')[1].split('</section>')[0]
        self.assertIn('<ol><li><code>README.md</code></li><li><code>tokens.json</code></li><li><code>components/</code></li></ol>', agents)
        for harness in ('Claude Design', 'Claude Code', 'Codex', 'Gemini CLI'):
            self.assertIn(harness, agents)
        self.assertEqual(data['design_md'].split('\n', 1)[0], '')  # body after the front matter
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md=None, components__Cover__preview__html='<!-- @dsCard height=300 -->\n<svg><text>Only one</text></svg>\n')
            text, _data = self.page(directory)
        self.assertIn('<p class="lead">Sample Studio <span class="mut">Plain words.</span></p>', text)  # README's first sentence
        self.assertIn('DESIGN.md has no Overview section', text)
        self.assertIn('DESIGN.md has no Read order line', text)

    def test_typography_and_spacing_screens(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            text, _data = self.page(directory)
        typography = text.split('<section id="typography"')[1].split('</section>')[0]
        self.assertIn('<code>Inter, sans-serif</code>', typography)
        self.assertIn('style="font-family:Inter, sans-serif;font-size:min(16px,72px);font-weight:400;line-height:1.5"', typography)
        self.assertIn('The quick brown fox', typography)
        spacing = text.split('<section id="spacing"')[1].split('</section>')[0]
        self.assertIn('style="width:min(4px,100%)"', spacing)
        self.assertIn('style="border-radius:2px"', spacing)
        self.assertEqual(spacing.count('data-token='), 2)

    def test_component_summary_is_plain_text(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'components/A/README.md', '# A\n\nA **bold** and `code` and [link](x.md) summary. Next sentence.\n')
            put(directory, 'components/B/README.md', '```\ncode first\n```\n\n<b>Tag</b> text without a full stop\n')
            put(directory, 'components/C/README.md', '# only a heading\n')
            _text, data = self.page(directory)
        self.assertEqual([c['summary'] for c in data['components']], ['A bold and code and link summary.', '<b>Tag</b> text without a full stop', ''])

    def test_files_screen_shows_tree_with_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            text, data = self.page(directory)
        files = text.split('<section id="files"')[1].split('</section>')[0]
        size = dict((f['path'], f['size']) for f in data['files'])['components/Cover/preview.html']
        self.assertIn('<summary>components/</summary>', files)
        self.assertIn(f'<code>preview.html</code> <span class="mut">{size} bytes</span>', files)
        self.assertIn('<details open>', files)

    # ---- fix 1 (round one review): linear links, percent-decoded targets, SVG ids, read budget, mutant-killing escapes

    def test_markdown_secondary_link_inputs_run_in_linear_time(self):
        # Quadratic before fix 1: every link head searched the closing parentheses behind it again.
        def times(unit, size):
            return unit * (size // len(unit))

        shapes = {
            'heads then pairs': lambda n: times('[a](', n * 4 // 10) + times('(x)', n * 6 // 10),
            'heads then opens': lambda n: times('[a](', n // 2) + '(' * (n // 2),
            'heads then ticks': lambda n: times('[a](', n // 2) + '`' * (n // 2),
            'bang heads then pairs': lambda n: times('![a](', n // 2) + times('(x)', n // 2),
            'double open heads': lambda n: times('[a]((', n // 2) + times('x)', n // 2),
            'heads then open pairs': lambda n: times('[a](', n // 2) + times('(x', n // 2),
            'nested brackets': lambda n: '[' * (n // 3) + '](' * (n // 6) + ')' * (n // 6),
            'ticks between heads': lambda n: times('`[a](`', n // 2) + times('(x)', n // 2),
            'stars between heads': lambda n: times('**[a](**', n // 2) + times('(x)', n // 2),
            'labels with brackets': lambda n: times('[a[b]](', n // 2) + times('(x)', n // 2),
        }
        for size in (63000, 48000):
            for label, make_text in shapes.items():
                start = time.perf_counter()
                self.build.render_markdown(make_text(size))
                elapsed = time.perf_counter() - start
                self.assertLess(elapsed, 2.0, f'{label} {size}: {elapsed:.2f} s')
        start = time.perf_counter()
        self.build.render_markdown(shapes['heads then pairs'](512000))
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0, f'DESIGN.md size: {elapsed:.2f} s')

    def test_viewer_links_hostile_readme_and_design_run_in_linear_time(self):
        hostile = '[a](' * 7000 + '(x)' * 11000
        with tempfile.TemporaryDirectory() as directory:
            make(directory, DESIGN__md='---\nversion: alpha\n---\n## Overview\n' + '[a](' * 5000 + '(x)' * 9000 + '\n')
            put(directory, 'components/C/README.md', hostile)
            put(directory, 'assets/G/README.md', hostile)
            start = time.perf_counter()
            text, _data = self.page(directory)
            elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0, f'{elapsed:.2f} s')
        self.assertEqual(self.sections(text), EIGHT)

    def test_markdown_balanced_link_targets_behave(self):
        render = self.build.render_markdown
        self.assertEqual(render('[a](x(1).md)'), '<p>a</p>')
        self.assertEqual(render('[a]((x))'), '<p>a</p>')
        self.assertEqual(render('[a](x.md'), '<p>[a](x.md</p>')
        self.assertEqual(render('[a](x.md))'), '<p><a href="x.md">a</a>)</p>')
        self.assertEqual(render('[a](q [b](c.md)'), '<p>[a](q <a href="c.md">b</a></p>')
        self.assertEqual(render('[a](x.md) (note) [b](y.md)'), '<p><a href="x.md">a</a> (note) <a href="y.md">b</a></p>')
        self.assertEqual(render('[a]( [b](c.md) )'), '<p>a</p>')  # the outer target balances, and it is not a file name
        self.assertEqual(render('text ) [a](x.md)'), '<p>text ) <a href="x.md">a</a></p>')

    def test_safe_href_decodes_percent_escapes_first(self):
        safe = self.build._safe_href
        refused = ['a/%2e%2e/b.md', 'a/%2E%2E/b.md', 'a/.%2e/b.md', 'a/%2e./b.md', 'a/%2e/b.md', 'a/%2e%2E/%2e%2e/x.md',
                   'a%2F%2Fb.md', 'a/%2F/b.md', 'a%2f%2fb.md', 'C%3A/x', 'c%3a/x', 'a%3Ab', 'a%5Cb.md', 'a%5cb.md', 'a/..%5Cb.md',
                   'a%00b', 'a%0Ab', 'a%0db.md', 'a%7Fb', 'a%1Fb', 'a%3Fq=1', 'a%23x', 'javascript%3Aalert', 'a/%252e%252e/b.md',
                   'a/%25252e%25252e/b.md', 'a/%2525252525252e%2525252525252e/b.md', 'a/%2e%2e', 'a/b/%2e%2e/%2e%2e/%2e%2e/c.md',
                   'a/%2e%2e%2fb.md', '%2e%2e/x.md']
        for target in refused:
            self.assertIsNone(safe(target), target)
            self.assertEqual(self.build.render_markdown(f'[up]({target})'), '<p>up</p>', target)
        for target in ('components/Button/README.md', 'notes/a%20b.md', 'x.md#part', 'a%C3%A9.md', 'a/b%2Bc.md', 'a%2525b.md'):
            self.assertEqual(safe(target), target, target)
        self.assertEqual(self.build.render_markdown('[b](components/Button/README.md)'),
                         '<p><a href="components/Button/README.md">b</a></p>')

    def test_cover_svg_ids_stay_out_of_the_page_ids(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10">'
               '<defs><linearGradient id="grad"><stop offset="0" stop-color="#fff"/></linearGradient></defs>'
               '<g id="colors"><rect id="q" width="4" height="4" fill="url(#grad)" style="stroke:url( #grad )"/>'
               '<use href="#colors"/><use xlink:href="#q"/></g><text id="overview">Title</text><text ID="h-colors">Tagline</text></svg>')
        with tempfile.TemporaryDirectory() as directory:
            make(directory, components__Cover__preview__html='<!-- @dsCard height=300 -->\n' + svg + '\n')
            text, data = self.page(directory)
        ids = re.findall(r'\sid="([^"]*)"', text)
        self.assertEqual(sorted(i for i in set(ids) if ids.count(i) > 1), [])
        self.assertEqual(self.sections(text), EIGHT)
        inside = text.split('<figure aria-label="Cover">')[1].split('</figure>')[0]
        self.assertEqual(sorted(re.findall(r'\sid="([^"]*)"', inside)), ['cover-colors', 'cover-grad', 'cover-h-colors', 'cover-overview', 'cover-q'])
        self.assertIn('fill="url(#cover-grad)"', inside)
        self.assertIn('stroke:url( #cover-grad )', inside)
        self.assertIn('<use href="#cover-colors"/>', inside)
        self.assertIn('<use xlink:href="#cover-q"/>', inside)
        self.assertNotIn('"#colors"', inside)
        self.assertEqual(text.count('<section id="colors"'), 1)
        self.assertEqual(text.count('id="q"'), 1)
        self.assertEqual(data['cover_svg'], svg)  # the collected data is the checked original; the page applies the prefix
        for bad in ('<svg><g id=""/></svg>', '<svg><g id="a b"/></svg>', '<svg><g id="a\'b"/></svg>', '<svg><g id="' + 'a' * 65 + '"/></svg>'):
            self.assertIsNone(self.build.sanitize_svg(bad), bad)
        self.assertEqual(self.build.sanitize_svg('<svg><g id="a"/></svg>'), '<svg><g id="a"/></svg>')

    def test_render_viewer_checks_cover_again(self):
        data = {'cover_svg': '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'}
        text = self.build.render_viewer(data)
        self.assertNotIn('alert(1)', text)
        self.assertIn('No cover image', text)

    def test_canonical_contrast_minimum_out_of_range_is_a_clean_error(self):
        for minimum in ('1' + '0' * 400, '1e999', '-1e999'):
            with tempfile.TemporaryDirectory() as directory:
                make(directory)
                edit_json(directory, 'canonical-map.json', lambda d: d['checks']['contrast'].append({'fg': 'text', 'bg': 'bg', 'min': 0}))
                path = Path(directory, 'canonical-map.json')
                path.write_text(path.read_text(encoding='utf-8').replace('"min": 0', f'"min": {minimum}'), encoding='utf-8')
                code, out, err = self.run_cli('--package', directory, '--viewer')
            self.assertEqual((code, out), (1, ''), minimum)
            self.assertEqual(len(err.strip().splitlines()), 1, err)
            self.assertTrue(err.startswith('invalid_manifest: canonical-map.json: checks.contrast'), err)
        data = {'canonical': {'checks': {'contrast': [{'fg': 'a', 'bg': 'b', 'min': 10 ** 400}]}},
                'tokens': {'color': {'tokens': [{'name': 'a', 'value': '#000000'}, {'name': 'b', 'value': '#ffffff'}]}}}
        self.assertEqual(self.build.render_viewer(data).count('<section '), 8)  # hostile data straight into the page does not raise

    def test_cli_turns_any_unexpected_error_into_one_line(self):
        for error in (ZeroDivisionError('x'), KeyError('k'), OverflowError('o'), TypeError('t'), AttributeError('a')):
            with tempfile.TemporaryDirectory() as directory:
                make(directory)
                with patch.object(self.build, 'collect_package', side_effect=error):
                    code, out, err = self.run_cli('--package', directory, '--viewer')
            self.assertEqual((code, out, err), (1, '', f'input_error: {type(error).__name__}\n'))

    def test_package_read_budget_is_total(self):
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            body = ('word ' * 12700)[:63500]
            for n in range(400):
                put(directory, f'components/C{n:03d}/README.md', body)
            reads = []
            real = self.build._text_of

            def counting(root, rel, cap):
                reads.append(rel)
                return real(root, rel, cap)

            start = time.perf_counter()
            with patch.object(self.build, '_text_of', counting):
                code, out, err = self.run_cli('--package', directory, '--viewer')
            elapsed = time.perf_counter() - start
        self.assertEqual((code, out), (1, ''))
        self.assertRegex(err, r'^viewer_too_large: viewer\.html: \d+ > 512000\n$')
        self.assertLess(elapsed, 5.0, f'{elapsed:.2f} s')
        self.assertLess(len([r for r in reads if r.endswith('/README.md')]), 40, len(reads))

    def test_markdown_code_and_alt_escapes_are_checked_individually(self):
        out = self.build.render_markdown('`<script>x</script>` and **<img onerror=x>** and [<img onerror=x>](a.md) and `<img src=x onerror=alert(1)>`')
        self.assertIn('<code>&lt;script&gt;x&lt;/script&gt;</code>', out)
        self.assertIn('<strong>&lt;img onerror&#61;x&gt;</strong>', out)
        self.assertIn('<a href="a.md">&lt;img onerror&#61;x&gt;</a>', out)
        self.assertIn('<code>&lt;img src&#61;x onerror&#61;alert(1)&gt;</code>', out)
        self.assertNotRegex(out, r'<(?!/?(?:p|code|strong|a)\b)')
        self.assertNotIn('<script', out)
        self.assertNotIn('<img', out)
        data = {'assets': [{'group': 'G', 'path': 'assets/G/a"onerror="x.png', 'size': 1, 'inline': 'data:image/png;base64,AAAA'},
                           {'group': 'G', 'path': "assets/G/b'x<y>.png", 'size': 1, 'inline': 'data:image/png;base64,AAAA'}]}
        text = self.build.render_viewer(data)
        self.assertIn('<img alt="assets/G/a&quot;onerror&#61;&quot;x.png"', text)
        self.assertIn('<img alt="assets/G/b&#x27;x&lt;y&gt;.png"', text)
        self.assertNotIn('alt="assets/G/a"', text)

    def test_cover_extraction_ignores_length_changing_case_folds(self):
        padding = '<p>' + 'İ' * 5 + '</p>'
        self.assertEqual(self.build.extract_cover_svg(padding + CLEAN_SVG + padding), CLEAN_SVG)
        self.assertEqual(self.build.extract_cover_svg(padding + CLEAN_SVG.upper()), CLEAN_SVG.upper())
        self.assertIsNone(self.build.extract_cover_svg('<ſvg></svg>'))
        self.assertIsNone(self.build.extract_cover_svg('<svg></ſvg>'))

    def test_leading_byte_order_marks_are_all_dropped(self):
        two = '﻿﻿'
        self.assertEqual(self.build.split_front_matter(two + '---\nversion: alpha\n---\n## Overview\n'),
                         (two + '---\nversion: alpha\n---\n', '## Overview\n'))
        text = self.build.render_design_md(two + '## Overview\n', tok(), INDEX)
        self.assertNotIn('﻿', text)
        self.assertTrue(text.endswith('---\n## Overview\n'))
        text = self.build.render_design_md(two + '---\nversion: alpha\n---\n## Overview\n', tok(), INDEX)
        self.assertNotIn('﻿', text)

    def test_key_and_vault_file_names_are_sensitive(self):
        names = ['id_rsa', 'id_ed25519', 'id_ecdsa', 'id_dsa', 'ID_RSA', 'id_rsa.pub', 'work.p12', 'work.pfx', 'vault.kdbx', 'vault.KDBX', 'key.ppk']
        for name in names:
            self.assertTrue(v3.SENSITIVE.search(name), name)
        for name in ('identity.png', 'valid_rsa.md', 'rsa.md', 'kdbx.md', 'idea.png'):
            self.assertFalse(v3.SENSITIVE.search(name), name)
        with tempfile.TemporaryDirectory() as directory:
            make(directory)
            put(directory, 'assets/G/README.md', 'a.png')
            put(directory, 'assets/G/id_rsa', 'SECRET_VALUE')
            put(directory, 'assets/G/vault.kdbx', 'SECRET_VALUE')
            put(directory, 'components/Button/id_ed25519', 'SECRET_VALUE')
            text, data = self.page(directory)
        self.assertNotIn('SECRET_VALUE', text)
        for name in ('id_rsa', 'kdbx', 'id_ed25519'):
            self.assertNotIn(name, text)
        self.assertTrue(all('id_' not in f['path'] for f in data['files']))

    def test_count_tokens(self):
        self.assertEqual(self.build.count_tokens({}), 0)
        self.assertEqual(self.build.count_tokens(None), 0)
        self.assertEqual(self.build.count_tokens({'color': {'tokens': [{'name': 'a'}, {'x': 1}, 3]}, 'type': {'groups': [{'styles': [{'name': 's'}, {}]}, 5]},
                                                  'spacing': {'tokens': 'no'}, 'other': 4}), 2)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'skills/design-system/tests/fixture/design-system/design-system.json'
TEMPLATE = ROOT / 'skills/design-system/templates/brand-v3/design-system.json'


if __name__ == '__main__':
    unittest.main()
