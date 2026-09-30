import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('migration', ROOT / 'skills/lovable-seo-check/scripts/check_migration.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Migration(unittest.TestCase):
    def setUp(self):
        self.old = 'https://example.com/old'
        self.new = 'https://example.com/new'
        self.neighbor = 'https://example.com/about'
        self.data = {
            self.old: {'status': 301, 'location': '/new'},
            self.new: {'status': 200, 'canonical': self.new, 'title': 'Service',
                       'description': 'Service details', 'robots': '', 'x_robots_tag': ''},
            self.neighbor: {'status': 200, 'canonical': self.neighbor, 'title': 'About',
                            'description': 'Our team', 'robots': '', 'x_robots_tag': ''}}

    def check(self, mapping=None, baseline=None):
        return m.audit({self.old, self.neighbor}, {self.new, self.neighbor}, self.data,
                       {self.old: self.new} if mapping is None else mapping, baseline)

    def codes(self, **kwargs):
        return {f['code'] for f in self.check(**kwargs)['findings']}

    def test_correct_move_preserves_neighbor_and_input(self):
        before = copy.deepcopy(self.data)
        self.assertEqual(self.check()['findings'], [])
        self.assertEqual(self.data, before)
        self.assertFalse(self.check()['indexing_verified'])

    def test_detects_defects_then_repair(self):
        good = copy.deepcopy(self.data)
        self.data[self.old] = {'status': 302, 'location': '/about'}
        self.data[self.new].update(canonical=self.neighbor, title='', robots='NOINDEX')
        self.assertTrue({'temporary_redirect', 'wrong_destination', 'canonical_mismatch',
                         'title_missing', 'noindex'} <= self.codes())
        self.data = good
        self.assertEqual(self.codes(), set())

    def test_removed_page_requires_editorial_mapping(self):
        self.assertIn('replacement_undecided', self.codes(mapping={}))

    def test_loop(self):
        self.data[self.new] = {'status': 301, 'location': '/old'}
        self.assertIn('redirect_loop', self.codes())

    def test_chain(self):
        self.data[self.old]['location'] = '/intermediate'
        self.data['https://example.com/intermediate'] = {'status': 308, 'location': '/new'}
        self.assertIn('redirect_chain', self.codes())

    def test_redirect_location_missing(self):
        del self.data[self.old]['location']
        self.assertIn('redirect_location_missing', self.codes())

    def test_missing_capture_is_not_success(self):
        del self.data[self.old]
        self.assertIn('missing_http_evidence', self.codes())

    def test_error_status(self):
        self.data[self.new]['status'] = 404
        self.assertTrue({'destination_not_200', 'sitemap_target_not_200'} <= self.codes())

    def test_http_header_noindex(self):
        self.data[self.new]['x_robots_tag'] = 'googlebot: noindex, follow'
        self.assertIn('noindex', self.codes())

    def test_robots_evidence_required(self):
        del self.data[self.new]['x_robots_tag']
        self.assertIn('robots_evidence_missing', self.codes())

    def test_baseline_metadata_changes_need_review(self):
        self.assertIn('metadata_changed_review', self.codes(baseline={self.old: {'status': 200, 'title': 'Previous title'}}))

    def test_invalid_mapping(self):
        with self.assertRaises(ValueError):
            self.check(mapping={self.old: 'https://unrelated.example/'})

    def test_credentials_never_echoed(self):
        with self.assertRaisesRegex(ValueError, '^URLs must'):
            m.audit({'https://user:private@example.com/'}, {self.new}, self.data)

    def test_invalid_types(self):
        for bad in ({self.old: {'status': True}}, {self.old: {'status': 200, 'robots': []}}):
            with self.assertRaises(ValueError):
                m.captures(bad)

    def test_namespaced_sitemap(self):
        self.assertEqual(m.sitemap('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/a?a=1&amp;b=2</loc></url></urlset>'), {'https://example.com/a?a=1&b=2'})

    def test_malformed_sitemaps(self):
        for bad in ('<sitemapindex/>', '<urlset/>', '<!DOCTYPE x><urlset/>',
                    '<urlset><url><loc>https://example.com/a</loc></url><url><loc>https://example.com/a</loc></url></urlset>'):
            with self.assertRaises(ValueError):
                m.sitemap(bad)


if __name__ == '__main__':
    unittest.main()
