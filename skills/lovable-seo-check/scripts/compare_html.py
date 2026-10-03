#!/usr/bin/env python3
"""Compare saved raw HTML and rendered DOM. No network, telemetry or file writes."""
import argparse,json,re,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlsplit
LIMIT=5*1024*1024
def display_url(value):
    # Userinfo is never useful SEO evidence, and may contain credentials.
    return re.sub(r'(//)[^/?#]*@',r'\1[redacted]@',value)
class Signals(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.in_head=False;self.capture=None;self.buffer=[]
        self.data={'titles':[],'descriptions':[],'canonicals':[],'robots':[],'h1':[],'links':[]}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='head':self.in_head=True
        if (tag=='title' and self.in_head) or tag=='h1':self.capture=tag;self.buffer=[]
        if tag=='meta' and self.in_head:
            name=a.get('name','').lower()
            if name=='description':self.data['descriptions'].append(a.get('content',''))
            if name in ('robots','googlebot'):self.data['robots'].append({'agent':name,'value':a.get('content','')})
        if tag=='link' and self.in_head and 'canonical'in a.get('rel','').lower().split():self.data['canonicals'].append(a.get('href',''))
        if tag=='a' and a.get('href'):self.data['links'].append(a['href'])
    def handle_endtag(self,tag):
        if tag==self.capture:
            self.data['titles' if tag=='title' else 'h1'].append(' '.join(''.join(self.buffer).split()));self.capture=None;self.buffer=[]
        if tag=='head':self.in_head=False
    def handle_data(self,text):
        if self.capture:self.buffer.append(text)
def parse(text):
    p=Signals();p.feed(text);return p.data
def compare(url,raw,rendered):
    u=urlsplit(url)
    if u.scheme not in ('https','http') or not u.hostname or u.username or u.password or u.fragment:raise ValueError('Expected public page URL must be HTTP(S), without credentials or fragment.')
    result={'expected_url':url,'raw':parse(raw),'rendered':parse(rendered),'findings':[],'indexing_verified':False,'http_headers_checked':False}
    def add(stage,code,evidence):result['findings'].append({'stage':stage,'code':code,'evidence':evidence})
    for stage in ('raw','rendered'):
        data=result[stage]
        if len(data['titles'])!=1 or not data['titles'][0].strip():add(stage,'title_missing_or_multiple',data['titles'])
        if len(data['descriptions'])!=1 or not data['descriptions'][0].strip():add(stage,'description_missing_or_multiple',data['descriptions'])
        if len(data['canonicals'])!=1:add(stage,'canonical_missing_or_multiple',data['canonicals'])
        else:
            c=data['canonicals'][0]
            try:
                absolute=urljoin(url,c);target=urlsplit(absolute)
                if not c.strip() or target.scheme not in ('https','http') or not target.hostname or target.username or target.password or target.fragment:add(stage,'canonical_invalid',display_url(c))
                elif absolute!=url:add(stage,'canonical_differs_from_expected',display_url(absolute))
                if not urlsplit(c).scheme:add(stage,'canonical_is_relative',display_url(c))
            except ValueError:
                add(stage,'canonical_invalid',display_url(c))
        for directive in data['robots']:
            tokens=set(re.split(r'[\s,]+',directive['value'].lower()))
            if tokens & {'noindex','none'}:add(stage,'noindex_present',directive)
        if not data['h1']:add(stage,'h1_missing',[])
    for key in ('titles','descriptions','canonicals','robots','h1','links'):
        if result['raw'][key]!=result['rendered'][key]:add('comparison','changes_after_javascript',key)
    for stage in ('raw','rendered'):
        for key in ('canonicals','links'):
            result[stage][key]=[display_url(value) for value in result[stage][key]]
    for finding in result['findings']:
        if isinstance(finding['evidence'],list):
            finding['evidence']=[display_url(value) if isinstance(value,str) else value for value in finding['evidence']]
    return result
def read(path):
    if path.stat().st_size>LIMIT:raise ValueError('Capture exceeds 5 MiB.')
    return path.read_text(encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--rendered',type=Path,required=True);a=p.parse_args()
    try:r=compare(a.url,read(a.raw),read(a.rendered))
    except (OSError,ValueError) as e:print(json.dumps({'error':str(e)}));return 2
    print(json.dumps(r,indent=2,ensure_ascii=False));return 1 if r['findings'] else 0
if __name__=='__main__':sys.exit(main())
