#!/usr/bin/env python3
"""Fetch public GitHub facts; preserve the last good snapshot on any source failure."""
import json
import os
import re
import ssl
import sys
from datetime import datetime, timezone, date
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT/'assets/github-data.json'
USER = 'akshat-j1'


class CalendarParser(HTMLParser):
    """Public HTML fallback for local runs without an API token."""
    def __init__(self):
        super().__init__()
        self.dates, self.counts, self.target, self.buffer = {}, {}, None, ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and a.get('data-date'):
            self.dates[a['id']] = a['data-date']
        if tag == 'tool-tip' and a.get('for') in self.dates:
            self.target, self.buffer = a['for'], ''

    def handle_data(self, data):
        if self.target:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.target:
            match = re.match(r'\s*(No|[\d,]+) contribution', self.buffer)
            if not match:
                raise ValueError('Contribution tooltip format changed')
            self.counts[self.dates[self.target]] = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
            self.target = None

    def days(self):
        today = date.today().isoformat()
        days = [{'date': d, 'count': c} for d, c in sorted(self.counts.items()) if d <= today]
        validate_days(days)
        return days


def validate_days(days):
    if not 350 <= len(days) <= 372:
        raise ValueError('Expected a full contribution calendar')
    dates = [date.fromisoformat(d['date']) for d in days]
    if len(set(dates)) != len(dates) or dates != sorted(dates):
        raise ValueError('Invalid or duplicate contribution dates')
    if any((b-a).days != 1 for a,b in zip(dates,dates[1:])):
        raise ValueError('Incomplete contribution calendar')
    if any(type(d['count']) is not int or d['count'] < 0 for d in days):
        raise ValueError('Invalid contribution counts')


def get(url, payload=None):
    headers = {'User-Agent': 'akshat-build-lab-profile', 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GH_TOKEN')
    # Never send the workflow credential to a non-API host.
    if token and url.startswith('https://api.github.com/'):
        headers['Authorization'] = f'Bearer {token}'
    if payload:
        headers['Content-Type'] = 'application/json'
    req = Request(url, data=json.dumps(payload).encode() if payload else None, headers=headers)
    context = ssl.create_default_context()
    # python.org macOS installs may lack their optional certificate symlink.
    # Use the OS trust bundle in that case, keeping certificate checks enabled.
    if ssl.get_default_verify_paths().cafile is None and Path('/etc/ssl/cert.pem').is_file():
        context.load_verify_locations('/etc/ssl/cert.pem')
    with urlopen(req, timeout=25, context=context) as response:
        return response.read().decode()


def fetch_repositories():
    items = []
    page = 1
    while True:
        batch = json.loads(get(f'https://api.github.com/users/{USER}/repos?per_page=100&page={page}'))
        if not isinstance(batch, list):
            raise ValueError('Invalid repository response')
        items.extend({k:r[k] for k in ['name','fork','language']} for r in batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 20:
            raise ValueError('Unexpected repository pagination')
    if not items:
        raise ValueError('Empty repository response')
    return {'updated_at': now(), 'source': f'https://api.github.com/users/{USER}/repos', 'items': sorted(items, key=lambda r:r['name'].lower())}


def fetch_contributions():
    if os.environ.get('GH_TOKEN'):
        query = 'query { user(login:"akshat-j1") { contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }'
        result = json.loads(get('https://api.github.com/graphql', {'query':query}))
        calendar = result['data']['user']['contributionsCollection']['contributionCalendar']
        days = [{'date':d['date'], 'count':d['contributionCount']} for w in calendar['weeks'] for d in w['contributionDays']]
        days = sorted((d for d in days if d['date'] <= date.today().isoformat()), key=lambda d:d['date'])
        validate_days(days)
        if sum(d['count'] for d in days) != calendar['totalContributions']:
            raise ValueError('Contribution calendar total mismatch')
        source = 'https://api.github.com/graphql'
    else:
        source = f'https://github.com/users/{USER}/contributions'
        parser = CalendarParser()
        parser.feed(get(source))
        days = parser.days()
    return {'updated_at':now(), 'source':source, 'days':days}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')


def main():
    data = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {'schema':1}
    failures = []
    for key, fetch in [('repositories',fetch_repositories),('contributions',fetch_contributions)]:
        try:
            data[key] = fetch()
            print(f'Updated {key}')
        except Exception as exc:
            # No response bodies, request headers or tokens in logs.
            print(f'::warning::{key}: {type(exc).__name__}; retaining dated snapshot', file=sys.stderr)
            failures.append(key)
    if any(k not in data for k in ['repositories','contributions']):
        raise SystemExit('No valid initial snapshot available')
    if len(failures) == 2:
        raise SystemExit('Both sources failed; existing assets remain unchanged')
    temporary = SNAPSHOT.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2)+'\n')
    temporary.replace(SNAPSHOT)


if __name__ == '__main__':
    main()
