#!/usr/bin/env python3
"""Original Build Lab artwork. Standard library only; no remote assets or fonts."""
from pathlib import Path
from html import escape
from collections import Counter
from datetime import date, timedelta
import json

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
BG, PANEL, INK, MUTED, LINE, BLUE = '#141517', '#1c1e22', '#f2efe7', '#acafb7', '#363941', '#638aff'


def text(x, y, value, size=20, color=INK, weight=400, family='sans', extra=''):
    fonts = 'Arial, Helvetica, sans-serif' if family == 'sans' else 'Consolas, Menlo, monospace' if family == 'mono' else 'Georgia, serif'
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" font-family="{fonts}" {extra}>{escape(str(value))}</text>'


def rect(x, y, w, h, fill=PANEL, stroke='none', rx=0, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" {extra}/>'


def line(x1, y1, x2, y2, color=LINE, extra=''):
    return f'<path d="M{x1} {y1}H{x2}" stroke="{color}" {extra}/>' if y1 == y2 else f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" {extra}/>'


def svg(name, w, h, body, title, desc):
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<style>.cursor{{animation:blink 1.4s steps(2,end) infinite}}@keyframes blink{{50%{{opacity:0}}}}@media(prefers-reduced-motion:reduce){{.cursor{{animation:none}}}}</style>
{rect(0, 0, w, h, BG, rx=12)}{body}</svg>\n'''
    (ASSETS / f'{name}.svg').write_text(content)


def mark(x, y, size=28):
    return f'<g transform="translate({x} {y})" fill="none" stroke="{BLUE}" stroke-width="2"><path d="M0 0H{size}V{size}H0Z M0 {size}L{size} 0 M{size/2} 0V{size}"/></g>'


def hero(mobile=False):
    # The portrait GIF generator and these static SVGs share one layout.
    # Importing the geometry does not require Pillow in the metrics workflow.
    from hero_art import write_svgs
    write_svgs(mobile)


PROJECTS = [
    ('01', 'MEETFLIX', 'A meeting camera. A creative canvas.', 'Local computer vision turns gestures into', 'live meme effects for Google Meet.', 'TypeScript / MediaPipe / Vite', 'meetflix', 'vision'),
    ('02', 'Weather Intelligence', 'From scattered reports to a clearer picture.', 'Citizen reports and weather data meet', 'geospatial dashboards and evidence scoring.', 'Python / FastAPI / React / PostGIS', 'sih26069-weather-platform', 'weather'),
    ('03', 'LinguaCert AI', 'Exploring language assessment with AI.', 'A CEFR-aligned English testing project', 'built with Next.js, Supabase and Gemini.', 'TypeScript / Next.js / Supabase / Gemini', 'linguacert-ai', 'language'),
]


def diagram(kind, x, y, scale=1):
    p = f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="{LINE}" stroke-width="1.5">'
    if kind == 'vision':
        p += '<rect x="10" y="10" width="200" height="136" rx="8"/><path d="M25 36V24H39 M181 24H195V36 M25 118V132H39 M181 132H195V118"/>'
        p += f'<path d="M66 100L88 69L111 87L141 49L166 75" stroke="{BLUE}" stroke-width="3"/>'
        for cx, cy in [(66,100),(88,69),(111,87),(141,49),(166,75)]:
            p += f'<circle cx="{cx}" cy="{cy}" r="4" fill="{INK}" stroke="{BG}"/>'
        p += '<path d="M80 161H140 M110 146V161"/>'
    elif kind == 'weather':
        p += '<path d="M15 135Q0 55 85 22T195 55T144 148T15 135Z M33 118Q16 58 87 43T177 69T136 128T33 118Z M53 103Q38 66 93 62T157 78T125 111T53 103Z"/>'
        p += f'<path d="M0 86H220 M110 0V168" stroke-dasharray="3 7"/><circle cx="110" cy="86" r="24" stroke="{BLUE}"/><circle cx="110" cy="86" r="4" fill="{BLUE}"/>'
    else:
        for i, size in enumerate([20,36,59,90,64,40,18,46,75,104,68,36,16]):
            p += f'<path d="M{20+i*15} {85-size/2}v{size}" stroke="{BLUE if i in [3,9] else MUTED}" stroke-width="5"/>'
        p += '<path d="M12 150H215 M12 20H215" stroke-dasharray="3 7"/>'
    return p+'</g>'


def projects(mobile=False):
    for no, title, subtitle, a, c, tech, repo, kind in PROJECTS:
        w, h = (480, 435) if mobile else (1000, 280)
        b = rect(0, 0, 5, h, BLUE)
        b += text(30, 38, f'BUILD NOTE / {no}', 13, BLUE, family='mono')
        b += text(30, 91, title, 34 if mobile else 39, INK, 700, extra='letter-spacing="-1"')
        b += text(30, 125, subtitle, 18 if mobile else 21, MUTED, family='serif', extra='font-style="italic"')
        b += text(30, 170, a, 18, INK) + text(30, 198, c, 18, INK)
        if mobile:
            b += text(30, 234, tech.replace(' / Gemini', ''), 14, MUTED, family='mono')
            b += diagram(kind, 245, 258, .85)
            b += text(30, 389, 'OPEN', 13, BLUE, family='mono')
            b += text(30, 411, 'REPOSITORY ↗', 13, BLUE, family='mono')
        else:
            b += line(708, 28, 708, 252)
            b += diagram(kind, 746, 36)
            b += text(30, 248, tech, 14, MUTED, family='mono')
            b += text(746, 248, 'OPEN REPOSITORY ↗', 14, BLUE, family='mono')
        svg(f'project-{no}'+('-mobile' if mobile else ''), w, h, b, f'{title} — {subtitle}', f'{a} {c} Technologies: {tech}. Technical diagram is original artwork, not a product screenshot.')


def stack(mobile=False):
    w, h = (480, 620) if mobile else (1000, 376)
    b = text(30, 40, 'THE TOOL DRAWER', 14, BLUE, family='mono')
    b += text(30, 80, 'Different tools. Same curiosity.', 26 if mobile else 32, INK, family='serif', extra='font-style="italic"')
    groups = [
        ('01 / INTERFACES', 'React · Next.js', 'TypeScript · JavaScript', 'Tailwind CSS · Vite'),
        ('02 / SYSTEMS', 'Python · FastAPI', 'PostgreSQL · PostGIS', 'Redis · Supabase'),
        ('03 / INTELLIGENCE', 'MediaPipe', 'Gemini API', 'Vision + language experiments'),
    ]
    for i, (label, a, c, d) in enumerate(groups):
        x, y, cw, ch = (20, 106+i*164, 440, 148) if mobile else (20+i*326, 110, 308, 226)
        b += rect(x, y, cw, ch, PANEL, LINE, 5)
        b += text(x+18, y+31, label, 13, BLUE, family='mono')
        b += text(x+18, y+68, a, 24, INK, 600)
        b += text(x+18, y+98, c, 17, MUTED)
        b += text(x+18, y+124 if mobile else y+128, d, 16, MUTED)
        if not mobile:
            b += line(x+18, y+161, x+cw-18, y+161)
            b += text(x+18, y+195, ['browser → interaction','data → decisions','input → possibility'][i], 14, INK, family='mono')
    svg('stack-mobile' if mobile else 'stack', w, h, b, 'The tool drawer — verified project technologies', 'Interfaces: React, Next.js, TypeScript, JavaScript, Tailwind CSS, Vite. Systems: Python, FastAPI, PostgreSQL, PostGIS, Redis, Supabase. Intelligence: MediaPipe and Gemini API. Inclusion means project usage, not a proficiency ranking.')


def activity(mobile=False):
    data = json.loads((ASSETS/'github-data.json').read_text())
    days, repos = data['contributions']['days'], data['repositories']['items']
    total = sum(d['count'] for d in days)
    active = sum(d['count'] > 0 for d in days)
    owned = [r for r in repos if not r['fork']]
    langs = Counter(r['language'] for r in owned if r['language'])
    w, h = (480, 800) if mobile else (1000, 570)
    b = text(30, 40, 'FIELD RECORDINGS / GITHUB', 14, BLUE, family='mono')
    period = f'{days[0]["date"]} — {days[-1]["date"]}'
    b += text(30 if mobile else w-30, 63 if mobile else 40, period, 11, MUTED, family='mono', extra='' if mobile else 'text-anchor="end"')
    metrics = [(f'{total:,}', 'contributions', 'calendar window'), (str(active), 'active days', 'at least 1 contribution'), (str(len(owned)), 'public repositories', 'owned / excludes forks')]
    for i, (n, label, note) in enumerate(metrics):
        x, y = (30, 98+i*89) if mobile else (30+i*326, 112)
        b += text(x, y, n, 42 if mobile else 54, INK, 600, extra='letter-spacing="-2"')
        b += text(x+115 if mobile else x, y-10 if mobile else y+34, label, 18, INK)
        b += text(x+115 if mobile else x, y+12 if mobile else y+58, note, 12, MUTED, family='mono')
    graph_y = 350 if mobile else 233
    b += line(30, graph_y-29, w-30, graph_y-29)
    b += text(30, graph_y, '26 WEEKS / CONTRIBUTIONS PER WEEK', 12, MUTED, family='mono')
    end = date.fromisoformat(days[-1]['date'])
    monday = end-timedelta(days=end.weekday())
    starts = [monday-timedelta(weeks=i) for i in range(25,-1,-1)]
    weeks = [sum(d['count'] for d in days if s <= date.fromisoformat(d['date']) < s+timedelta(days=7)) for s in starts]
    max_count = max(weeks, default=0)
    b += text(w-30, graph_y+23, f'PEAK WEEK / {max_count}', 11, MUTED, family='mono', extra='text-anchor="end"')
    gw = w-60
    for i, (s, count) in enumerate(zip(starts,weeks)):
        bh = 96*count/max(1,max_count)
        x = 30+i*gw/26
        fill = LINE if count == 0 else BLUE if i == 25 else '#7c879f'
        b += f'<rect x="{x:.2f}" y="{graph_y+123-max(1,bh):.2f}" width="{gw/26-4:.2f}" height="{max(1,bh):.2f}" rx="0.5" fill="{fill}"><title>Week of {s}: {count} contributions</title></rect>'
    b += text(30, graph_y+146, starts[0].strftime('%d %b %Y'), 11, MUTED, family='mono')
    b += text(w-30, graph_y+146, end.strftime('%d %b %Y')+' / partial week', 11, MUTED, family='mono', extra='text-anchor="end"')
    ly = 550 if mobile else 430
    b += text(30, ly, 'REPOSITORIES BY PRIMARY LANGUAGE', 12, MUTED, family='mono')
    for i, (lang,count) in enumerate(langs.most_common(6)):
        x, y = (30, ly+32+i*29) if mobile else (30+(i%3)*326, ly+36+(i//3)*34)
        b += text(x, y, lang, 15, INK)
        b += rect(x+120, y-9, 105, 5, LINE, rx=2)
        b += rect(x+120, y-9, 105*count/max(langs.values()), 5, BLUE, rx=2)
        b += text(x+240, y, str(count), 13, MUTED, family='mono')
    stamp = min(data['contributions']['updated_at'], data['repositories']['updated_at'])[:10]
    b += line(30, h-47, w-30, h-47)
    b += text(30, h-22, f'SNAPSHOT {stamp} / PUBLIC GITHUB DATA', 11, MUTED, family='mono')
    desc = f'{total} contributions on {active} active days, {days[0]["date"]} through {days[-1]["date"]}. {len(owned)} owned public repositories. Weekly bars include the current partial week. Primary-language counts exclude forks and repositories without a detected language. Snapshots retain their timestamp on failure.'
    svg('activity-mobile' if mobile else 'activity', w, h, b, 'GitHub field recordings', desc)


def main():
    for mobile in [False, True]:
        hero(mobile)
        projects(mobile)
        stack(mobile)
        activity(mobile)
    b = mark(28, 24, 22) + text(66, 42, 'END OF PAGE. NOT OF IDEAS.', 15, INK, family='mono')
    b += text(28, 87, 'There is probably another experiment in the works.', 19, MUTED, family='serif', extra='font-style="italic"')
    svg('footer', 680, 116, b, 'End of page. Not of ideas.', 'There is probably another experiment in the works.')
    b = mark(26, 25, 22) + text(63, 43, 'END OF PAGE. NOT OF IDEAS.', 16, INK, family='mono')
    b += text(26, 87, 'There is probably another experiment', 22, MUTED, family='serif', extra='font-style="italic"')
    b += text(26, 115, 'in the works.', 22, MUTED, family='serif', extra='font-style="italic"')
    svg('footer-mobile', 480, 145, b, 'End of page. Not of ideas.', 'There is probably another experiment in the works.')


if __name__ == '__main__':
    main()
