import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SKILL=ROOT/'skills/lovable-seo-check'
spec=importlib.util.spec_from_file_location('compare',SKILL/'scripts/compare_html.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Check(unittest.TestCase):
 def setUp(self):self.before=(SKILL/'assets/before.html').read_text();self.after=(SKILL/'assets/after.html').read_text();self.url='https://example.com/bike-repairs'
 def test_repair(self):self.assertTrue(m.compare(self.url,self.before,self.before)['findings']);self.assertEqual(m.compare(self.url,self.after,self.after)['findings'],[])
 def test_javascript_difference(self):r=m.compare(self.url,self.before,self.after);self.assertIn('changes_after_javascript',[x['code'] for x in r['findings']]);self.assertFalse(r['indexing_verified'])
 def test_noindex(self):s=self.after.replace('</head>','<meta name="ROBOTS" content="NOINDEX, follow"></head>');self.assertIn('noindex_present',[x['code'] for x in m.compare(self.url,s,s)['findings']])
 def test_multiple_canonicals(self):s=self.after.replace('</head>','<link rel="canonical" href="https://example.com/"></head>');self.assertIn('canonical_missing_or_multiple',[x['code'] for x in m.compare(self.url,s,s)['findings']])
 def test_relative_canonical(self):s=self.after.replace(self.url,'/bike-repairs');codes=[x['code'] for x in m.compare(self.url,s,s)['findings']];self.assertIn('canonical_is_relative',codes);self.assertNotIn('canonical_differs_from_expected',codes)
 def test_nested_h1(self):s=self.after.replace('Bike repairs</h1>','Bike <em>repairs</em></h1>');self.assertEqual(m.parse(s)['h1'],['Bike repairs'])
 def test_title_outside_head(self):s=self.after.replace('<title>Bike repairs | Demo</title>','').replace('</body>','<title>body title</title></body>');self.assertEqual(m.parse(s)['titles'],[])
 def test_credentials_rejected(self):
  with self.assertRaises(ValueError):m.compare('https://user:private@example.com/',self.after,self.after)
 def test_malformed_canonical_keeps_other_checks(self):
  s=self.after.replace(self.url,'https://[broken').replace('</head>','<meta name="robots" content="noindex"></head>')
  r=m.compare(self.url,s,s)
  self.assertIn('canonical_invalid',[x['code'] for x in r['findings']])
  self.assertIn('noindex_present',[x['code'] for x in r['findings']])
 def test_canonical_and_link_credentials_not_exposed(self):
  secret='fixture-private-password'
  s=self.after.replace(self.url,f'https://user:{secret}@example.com/bike-repairs')
  s=s.replace('</body>',f'<a href="https://other:{secret}@example.com/next">Next</a></body>')
  r=m.compare(self.url,s,s)
  self.assertIn('canonical_invalid',[x['code'] for x in r['findings']])
  self.assertNotIn(secret,str(r))
if __name__=='__main__':unittest.main()
