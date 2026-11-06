"""Shared hero geometry for SVG and raster output; no third-party imports."""
from pathlib import Path
from html import escape
import base64

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
BG, INK, MUTED, LINE, BLUE = '#141517', '#f2efe7', '#acafb7', '#363941', '#638aff'


def scene(mobile=False):
    w,h = (480,896) if mobile else (1000,618)
    commands = [('rect',0,0,w,h,BG)]
    def t(x,y,s,size=18,color=INK,weight=400,family='sans',tracking=0):
        commands.append(('text',x,y,s,size,color,weight,family,tracking))
    def ln(x,y,xx,yy,color=LINE,width=1):
        commands.append(('line',x,y,xx,yy,color,width))
    for a in [(30,28,58,28),(58,28,58,56),(58,56,30,56),(30,56,30,28),(30,56,58,28),(44,28,44,56)]:
        ln(*a,BLUE,2)
    t(72,48,'AKSHAT / THE BUILD LAB',15,INK,600,'mono')
    ln(30,77,w-30,77)
    t(30,116,'DEVELOPER. EXPERIMENTER. BUILDER.',12,BLUE,400,'mono',1)
    t(26,202,'Akshat',88,INK,700,'sans',-5)
    t(26,285,'Jain.',88,INK,700,'sans',-5)
    t(32,325,'@akshat-j1',18,MUTED,400,'mono')
    t(30,369 if mobile else 377,'Useful software.',27 if mobile else 31,INK,400,'serif')
    t(30,404 if mobile else 416,'Unexpected possibilities.',27 if mobile else 31,INK,400,'serif')
    if mobile:
        box=(80,435,320,382); image=(98,442,284,350)
    else:
        box=(574,104,396,440); image=(590,113,364,405)
        t(32,471,'WEB / AI / EXPERIMENTS',14,MUTED,400,'mono')
        t(574,95,'FIG. 00 / HUMAN → ASCII',12,MUTED,400,'mono')
    x,y,bw,bh=box
    commands.append(('rect',x,y,bw,bh,BG))
    for cx,cy,dx,dy in [(x,y,1,1),(x+bw,y,-1,1),(x,y+bh,1,-1),(x+bw,y+bh,-1,-1)]:
        ln(cx,cy+dy*15,cx,cy,BLUE,2);ln(cx,cy,cx+dx*15,cy,BLUE,2)
    commands.append(('portrait',*image))
    commands.append(('status',x+16,y+bh-12,13))
    ln(30,h-52,w-30,h-52)
    t(30,h-23,'> next: make it work',14 if mobile else 16,INK,400,'mono')
    if not mobile:
        t(580,h-23,'A LITTLE CURIOSITY. A LOT OF BUILDING.',12,MUTED,400,'mono')
    return w,h,commands


def write_svgs(mobile=False):
    w,h,commands=scene(mobile)
    body=[]
    for op,*a in commands:
        if op=='rect':
            x,y,rw,rh,fill=a;body.append(f'<rect x="{x}" y="{y}" width="{rw}" height="{rh}" fill="{fill}"/>')
        elif op=='line':
            x,y,xx,yy,color,sw=a;body.append(f'<path d="M{x} {y}L{xx} {yy}" fill="none" stroke="{color}" stroke-width="{sw}"/>')
        elif op=='text':
            x,y,s,size,color,weight,family,tracking=a
            font={'sans':'Arial, Helvetica, sans-serif','serif':'Georgia, serif','mono':'Consolas, Menlo, monospace'}[family]
            body.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{color}" font-weight="{weight}" letter-spacing="{tracking}"'+(' font-style="italic"' if family=='serif' else '')+f'>{escape(s)}</text>')
        elif op=='portrait':
            p=ASSETS/'portrait-ascii.png'
            if p.exists():
                x,y,rw,rh=a;data=base64.b64encode(p.read_bytes()).decode()
                body.append(f'<image x="{x}" y="{y}" width="{rw}" height="{rh}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')
        elif op=='status':
            x,y,size=a;body.append(f'<text x="{x}" y="{y}" font-family="monospace" font-size="{size}" fill="{BLUE}">identity / loaded</text>')
    data=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">Akshat Jain / The Build Lab</title><desc id="desc">Original character-art portrait derived from Akshat’s illustration, with cobalt glasses. Static hero edition.</desc>'+''.join(body)+'</svg>\n'
    name='hero-mobile' if mobile else 'hero'
    for suffix in ['', '-static']:
        (ASSETS/f'{name}{suffix}.svg').write_text(data)
