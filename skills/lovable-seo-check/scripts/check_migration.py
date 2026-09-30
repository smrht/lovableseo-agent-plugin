#!/usr/bin/env python3
"""Audit saved sitemaps and HTTP evidence. Reads local files; makes no requests."""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlsplit

LIMIT = 5 * 1024 * 1024
MAX_URLS = 5000
REDIRECTS = {301, 302, 303, 307, 308}


def url(value):
    if not isinstance(value, str) or len(value) > 4096 or any(c.isspace() for c in value):
        raise ValueError('Expected an absolute HTTP(S) URL without whitespace.')
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('URLs must be HTTP(S), without credentials or fragments.')
    return value


def read(path):
    with Path(path).open('rb') as handle:
        data = handle.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError('Input exceeds 5 MiB.')
    return data.decode('utf-8-sig')


def sitemap(text):
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('Sitemap declarations and entities are not supported.')
    root = ET.fromstring(text)
    if any(element.tag.startswith('{http://www.w3.org/2001/XInclude}') for element in root.iter()):
        raise ValueError('Sitemap XInclude is not supported.')
    if root.tag.rsplit('}', 1)[-1] != 'urlset':
        raise ValueError('Supply a URL sitemap, not a sitemap index. Combine its child URL sets first.')
    values = []
    for entry in root:
        if entry.tag.rsplit('}', 1)[-1] != 'url':
            continue
        locations = [child for child in entry if child.tag.rsplit('}', 1)[-1] == 'loc']
        if len(locations) != 1:
            raise ValueError('Each sitemap URL needs exactly one loc.')
        values.append(url((locations[0].text or '').strip()))
    if not values or len(values) > MAX_URLS or len(set(values)) != len(values):
        raise ValueError('Sitemap must contain 1–5000 unique URLs.')
    return set(values)


def load_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Conflicting duplicate JSON keys; supply one unambiguous capture per URL.')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique)


def captures(data):
    if not isinstance(data, dict) or len(data) > MAX_URLS * 3:
        raise ValueError('HTTP evidence must be an object keyed by URL, up to 15000 entries.')
    for key, record in data.items():
        url(key)
        if not isinstance(record, dict) or type(record.get('status')) is not int or not 100 <= record['status'] <= 599:
            raise ValueError('Every captured response needs an integer HTTP status.')
        for field in ('location', 'canonical', 'title', 'description', 'robots', 'x_robots_tag'):
            if field in record and not isinstance(record[field], str):
                raise ValueError('Captured text fields must be strings.')
        if record.get('location'):
            url(urljoin(key, record['location']))
        if record.get('canonical'):
            url(urljoin(key, record['canonical']))
    return data


def audit(old, new, evidence, mapping=None, baseline=None):
    """Mappings are explicit editorial decisions; never infer a replacement page."""
    old = {url(item) for item in old}
    new = {url(item) for item in new}
    if not old or not new or max(len(old), len(new)) > MAX_URLS:
        raise ValueError('Supply non-empty old/new inventories of at most 5000 URLs each.')
    evidence = captures(evidence)
    mapping = {} if mapping is None else mapping
    baseline = captures({} if baseline is None else baseline)
    if not isinstance(mapping, dict):
        raise ValueError('Mapping must be an object from old URL to intended new URL.')
    for source, target in mapping.items():
        if url(source) not in old or url(target) not in new:
            raise ValueError('Mappings must connect an old inventory URL to a new inventory URL.')
    findings = []

    def add(code, source, **details):
        findings.append(dict(code=code, url=source, **details))

    def follow(source):
        chain = []
        current = source
        while True:
            if current in chain:
                add('redirect_loop', source, chain=chain + [current])
                return None
            if len(chain) >= 11:
                add('too_many_redirects', source, chain=chain)
                return None
            chain.append(current)
            response = evidence.get(current)
            if response is None:
                add('missing_http_evidence', source, missing_url=current)
                return None
            if response['status'] not in REDIRECTS:
                if response['status'] != 200:
                    add('destination_not_200', source, destination=current, status=response['status'])
                    return None
                if len(chain) > 2:
                    add('redirect_chain', source, chain=chain)
                return current
            if response['status'] not in (301, 308):
                add('temporary_redirect', source, at=current, status=response['status'])
            if not response.get('location'):
                add('redirect_location_missing', source, at=current)
                return None
            current = urljoin(current, response['location'])

    for target in sorted(new):
        response = evidence.get(target)
        if response is None:
            add('missing_http_evidence', target, missing_url=target)
            continue
        if response['status'] != 200:
            add('sitemap_target_not_200', target, status=response['status'])
            continue
        for field in ('title', 'description'):
            if not response.get(field, '').strip():
                add(field + '_missing', target)
        canonical = response.get('canonical', '')
        if not canonical:
            add('canonical_missing', target)
        elif urljoin(target, canonical) != target:
            add('canonical_mismatch', target, canonical=urljoin(target, canonical))
        for field in ('robots', 'x_robots_tag'):
            if field not in response:
                add('robots_evidence_missing', target, field=field)
            elif {'noindex', 'none'} & set(re.split(r'[\s,:;]+', response[field].lower())):
                add('noindex', target, field=field)

    for source in sorted(old):
        expected = mapping.get(source, source if source in new else None)
        if expected is None:
            add('replacement_undecided', source)
            continue
        destination = follow(source)
        if destination is not None and destination != expected:
            add('wrong_destination', source, expected=expected, actual=destination)
        if destination is not None and destination == expected:
            for field in ('title', 'description'):
                previous = baseline.get(source, {}).get(field, '').strip()
                current = evidence.get(destination, {}).get(field, '').strip()
                if previous and current and previous != current:
                    add('metadata_changed_review', source, field=field)

    return {'old_urls': len(old), 'new_urls': len(new), 'findings': findings,
            'scope': 'Saved URL inventories and supplied response captures only; no live fetches.',
            'indexing_verified': False, 'content_equivalence_verified': False,
            'baseline_metadata_supplied': bool(baseline)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', required=True, type=Path)
    parser.add_argument('--new', required=True, type=Path)
    parser.add_argument('--responses', required=True, type=Path)
    parser.add_argument('--mapping', type=Path)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(sitemap(read(args.old)), sitemap(read(args.new)),
                       load_json(read(args.responses)),
                       load_json(read(args.mapping)) if args.mapping else None,
                       load_json(read(args.baseline)) if args.baseline else None)
    except (ValueError, OSError, ET.ParseError) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 1 if result['findings'] else 0


if __name__ == '__main__':
    sys.exit(main())
