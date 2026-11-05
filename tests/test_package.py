"""Offline checks of the distribution itself; no HA or crypto dependency."""
import ast
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).parents[1]
COMP=ROOT/'custom_components/myhouse_pro'

class Package(unittest.TestCase):
    def test_manifest(self):
        m=json.loads((COMP/'manifest.json').read_text())
        self.assertEqual(m['domain'],'myhouse_pro')
        self.assertEqual(m['version'],'0.2.3')
        self.assertEqual(m['codeowners'],['@ignaziogiannossi'])
        for key in ['documentation','issue_tracker']:
            self.assertTrue(m[key].startswith('https://github.com/ignaziogiannossi/home-assistant-myhouse-pro'))
        self.assertEqual(json.loads((ROOT/'hacs.json').read_text())['name'],m['name'])

    def test_translation_keys_match(self):
        def keys(obj):
            return {k:keys(v) if isinstance(v,dict) else None for k,v in obj.items()}
        en=json.loads((COMP/'translations/en.json').read_text())
        it=json.loads((COMP/'translations/it.json').read_text())
        self.assertEqual(keys(en),keys(it))
        for language in [en,it]:
            self.assertIn('HTTPS',language['config']['step']['user']['description'])

    def test_all_python_parses(self):
        for path in COMP.glob('*.py'): ast.parse(path.read_text())

    def test_diagnostics_allowlist(self):
        tree=ast.parse((COMP/'diagnostics.py').read_text())
        output=next(n for n in ast.walk(tree) if isinstance(n,ast.Return))
        self.assertEqual({k.value for k in output.value.keys},{'version','last_update_success','state','temperature_c','target_c','humidity','source'})

    def test_distribution_excludes_home_files(self):
        self.assertFalse((ROOT/'configuration.yaml').exists())
        self.assertFalse((ROOT/'secrets.yaml').exists())
        self.assertFalse((ROOT/'.storage').exists())
        self.assertEqual({p.name for p in (ROOT/'custom_components').iterdir() if p.is_dir()},{'myhouse_pro'})

    def test_original_png_icon(self):
        data=(COMP/'brand/icon.png').read_bytes()
        self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(int.from_bytes(data[16:20],'big'),256)
        self.assertEqual(int.from_bytes(data[20:24],'big'),256)
