"""A real local HTTP route repair, captured with redirects disabled."""
import importlib.util
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[1] / 'skills/lovable-seo-check/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migration = load('check_migration')
html = load('compare_html')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


class LiveMigration(unittest.TestCase):
    def test_http_repair_and_unchanged_neighbor(self):
        state = {'fixed': False}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == '/old':
                    self.send_response(301 if state['fixed'] else 302)
                    self.send_header('Location', '/new' if state['fixed'] else '/about')
                    self.end_headers()
                    return
                if self.path not in ('/new', '/about'):
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                broken = self.path == '/new' and not state['fixed']
                if broken:
                    self.send_header('X-Robots-Tag', 'noindex')
                self.end_headers()
                title = '' if broken else 'Service' if self.path == '/new' else 'About'
                canonical = base + ('/about' if broken else self.path)
                body = f'<html><head><title>{title}</title><meta name="description" content="Details"><link rel="canonical" href="{canonical}"></head><body><h1>{title}</h1></body></html>'
                self.wfile.write(body.encode())

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        base = 'http://127.0.0.1:' + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        opener = build_opener(NoRedirect)

        def capture():
            result = {}
            for path in ('/old', '/new', '/about', '/missing'):
                try:
                    response = opener.open(base + path, timeout=3)
                except HTTPError as exc:
                    response = exc
                with response:
                    parsed = html.parse(response.read().decode())
                    result[base + path] = {
                        'status': response.code, 'location': response.headers.get('Location', ''),
                        'canonical': next(iter(parsed['canonicals']), ''),
                        'title': next(iter(parsed['titles']), ''),
                        'description': next(iter(parsed['descriptions']), ''),
                        'robots': ','.join(r['value'] for r in parsed['robots']),
                        'x_robots_tag': response.headers.get('X-Robots-Tag', '')}
            return result

        try:
            old = {base + '/old', base + '/about'}
            new = {base + '/new', base + '/about'}
            mapping = {base + '/old': base + '/new'}
            before = capture()
            findings = migration.audit(old, new, before, mapping)['findings']
            self.assertEqual({r['code'] for r in findings}, {
                'temporary_redirect', 'wrong_destination', 'canonical_mismatch', 'title_missing', 'noindex'})
            state['fixed'] = True
            after = capture()
            self.assertEqual(migration.audit(old, new, after, mapping)['findings'], [])
            self.assertEqual(before[base + '/about'], after[base + '/about'])
            self.assertEqual(after[base + '/missing']['status'], 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)


if __name__ == '__main__':
    unittest.main()
