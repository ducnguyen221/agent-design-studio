"""Original, anonymous contract fixtures; no external assets or runtime claims."""
import importlib.util
import tempfile
import unittest
import json
import io
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch
from pathlib import Path

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
                self.assertEqual(verifier.main(['--root', directory, '--tokens', 'tokens.json']), 0)
                self.assertEqual(verifier.main(['--root', directory, '--legacy-tokens', 'tokens.json']), 0)
                self.assertEqual(verifier.main(['--root', directory, '--tokens', '.env']), 1)
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


if __name__ == '__main__':
    unittest.main()
