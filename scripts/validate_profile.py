#!/usr/bin/env python3
"""Offline integrity checks for GitHub-compatible profile assets and facts."""
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from refresh_data import validate_days

ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ['src','srcset']:
            if key in a:
                self.assets.append(a[key])
        assert tag not in ['script','iframe','style'], f'Unsupported README element: {tag}'


def main():
    readme = (ROOT/'README.md').read_text()
    refs = References(); refs.feed(readme)
    for ref in refs.assets:
        assert not ref.startswith(('http:','https:')), 'README image has an external dependency'
        assert (ROOT/ref).is_file(), f'Missing image: {ref}'
    for path in (ROOT/'assets').glob('*.svg'):
        tree = ET.fromstring(path.read_text())
        assert 'viewBox' in tree.attrib
        assert tree.find('{*}title') is not None and tree.find('{*}desc') is not None
        for el in tree.iter():
            tag = el.tag.split('}')[-1]
            assert tag not in ['script','foreignObject','iframe','animate','set'], f'Unsafe/unsupported element: {path}: {tag}'
            for k,v in el.attrib.items():
                assert not k.lower().startswith('on'), f'Event handler: {path}'
                if k.endswith('href'):
                    assert v.startswith('data:image/png;base64,'), f'External SVG resource: {path}'
        assert path.stat().st_size < 1_000_000, f'Oversized asset: {path}'
    snapshot = json.loads((ROOT/'assets/github-data.json').read_text())
    validate_days(snapshot['contributions']['days'])
    assert snapshot['schema'] == 1
    assert all(isinstance(r['fork'],bool) for r in snapshot['repositories']['items'])
    headings = re.findall(r'^## (.+)$',readme,re.M)
    anchors = {re.sub(r'[^\w\- ]','',h.lower()).replace(' ','-') for h in headings}
    for anchor in re.findall(r'href="#([^"]+)"',readme):
        assert anchor in anchors, f'Broken section anchor: {anchor}'
    print(f'PASS: {len(refs.assets)} local image references, {len(list((ROOT/"assets").glob("*.svg")))} SVGs, anchors, and dated GitHub data')


if __name__ == '__main__':
    main()
