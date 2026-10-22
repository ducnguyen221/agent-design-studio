"""Original, anonymous contract fixtures; no external assets or runtime claims."""
import importlib.util
import tempfile
import unittest
import json
import io
import sys
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
            self.assertEqual(errors.getvalue().strip(), 'input_error: ValueError')
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
        required = {'design-system/brand/identity.md', 'design-system/foundations/colors.md',
                    'design-system/components/button.md', 'design-system/patterns/action-feedback.md',
                    'design-system/surfaces/web/screens/index.md', 'design-system/assets/manifest.md'}
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
        manifest = json.loads((root / 'design-system/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(verifier.validate_manifest(manifest, root), [])

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
            self.assertIn('font_file_missing: fonts/../escape.woff2', errors)
            self.assertIn('font_file_missing: fonts/.env', errors)

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


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'skills/design-system/tests/fixture/design-system/design-system.json'
TEMPLATE = ROOT / 'skills/design-system/templates/brand-v3/design-system.json'
# Dropped at TK8, when the v3 fixture and template exist.
CliV3Tests.test_fixture_full_passes = unittest.skipUnless(FIXTURE.is_file(), 'v3 fixture arrives in TK8')(CliV3Tests.test_fixture_full_passes)
CliV3Tests.test_template_minimal_passes = unittest.skipUnless(TEMPLATE.is_file(), 'v3 template arrives in TK8')(CliV3Tests.test_template_minimal_passes)


if __name__ == '__main__':
    unittest.main()
