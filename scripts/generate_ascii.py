#!/usr/bin/env python3
"""Portrait → character grid → genuine looping GIFs. No generated face frames.

Requires Pillow 12.2.0. Run from any directory: python3 scripts/generate_ascii.py
Font paths can be fixed with --mono, --sans, --bold, --serif for exact reproduction.
"""
import argparse
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence, ImageFilter
import PIL
from hero_art import scene, write_svgs, ASSETS, BG, INK, MUTED, BLUE

COLS, ROWS, CW, CH = 72, 62, 7, 12
# A 12% tighter view of the same illustration enlarges the face inside the
# unchanged portrait slot; no hero geometry or text alignment is moved.
CROP = (298,236,785,961)
RAMP = '.:+*%#@'
BLUSH_REGIONS = ((399,652,451,690),(624,635,672,670))
EYE_REGIONS = ((391,543,499,609),(568,530,675,596))
DECOR_REGIONS = ((274,735,332,819),(748,716,817,795))


def prepare_face(original):
    """Clean only a working copy. Never save over or otherwise write the source.

    Cheek strokes are colour-selected inside two narrowly bounded regions. Each
    masked pixel is reconstructed from nearby unmasked skin; no blank cutouts.
    """
    source=original.copy()
    mask=Image.new('L',source.size)
    mp=mask.load();pixels=original.load()
    for x0,y0,x1,y1 in BLUSH_REGIONS:
        for y in range(y0,y1):
            for x in range(x0,x1):
                r,g,b=pixels[x,y]
                if r>115 and g<140 and r>1.65*g and r-g>65:
                    mp[x,y]=255
    # Include antialiased stroke edges, without touching glasses, nose or beard.
    mask=mask.filter(ImageFilter.MaxFilter(7))
    mp=mask.load();out=source.load()
    changed=0
    for y in range(630,695):
        for x in range(395,677):
            if not mp[x,y]:continue
            samples=[]
            for dy in range(-18,19,3):
                for dx in range(-18,19,3):
                    xx,yy=x+dx,y+dy
                    if mp[xx,yy] or dx*dx+dy*dy<16:continue
                    r,g,b=pixels[xx,yy]
                    if r>180 and g>115 and b>60 and 15<r-g<95 and g>b+10:
                        samples.append(((r,g,b),1/(dx*dx+dy*dy)))
            if not samples:
                raise ValueError('Blush mask has no surrounding skin samples')
            weights=sum(weight for _,weight in samples)
            out[x,y]=tuple(round(sum(rgb[c]*weight for rgb,weight in samples)/weights) for c in range(3))
            changed+=1
    return source,changed


def find_font(explicit, candidates):
    for path in [explicit,*candidates]:
        if path and Path(path).is_file():
            return str(Path(path).resolve())
    raise SystemExit('Font unavailable. Supply --mono, --sans, --bold and --serif paths.')


def fonts(args):
    return {
        'mono':find_font(args.mono,['/System/Library/Fonts/Menlo.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']),
        'sans':find_font(args.sans,['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']),
        'bold':find_font(args.bold,['/System/Library/Fonts/Supplemental/Arial Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']),
        'serif':find_font(args.serif,['/System/Library/Fonts/Supplemental/Georgia Italic.ttf','/usr/share/fonts/truetype/liberation2/LiberationSerif-Italic.ttf']),
    }


def ascii_portrait(paths):
    original=ImageOps.exif_transpose(Image.open(ASSETS/'portrait.jpeg')).convert('RGB')
    if original.size != (1086,1448):
        raise ValueError('Source dimensions changed; review the documented portrait crop before regenerating')
    cleaned,removed_blush=prepare_face(original)
    if removed_blush<100:
        raise ValueError('Expected cheek strokes were not detected; review preprocessing')
    source=cleaned.crop(CROP)
    # A tiny native-resolution median filter suppresses brush-grain noise.
    # No warping, tracing, eye templates, or geometric replacement is used.
    sampled=source.filter(ImageFilter.MedianFilter(3))
    small=sampled.resize((COLS,ROWS),Image.Resampling.BOX)
    blue=Image.new('L',source.size)
    bp=blue.load();sp=source.load()
    for y in range(source.height):
        if not 480 <= y+CROP[1] <= 665:continue
        for x in range(source.width):
            r,g,b=sp[x,y]
            if b-r>14 and b-g>5 and r<115:bp[x,y]=255
    # Preserve the real rim's area and asymmetry; never skeletonize or redraw it.
    blue=blue.resize((COLS,ROWS),Image.Resampling.BOX)
    luminance=small.convert('L')
    canvas=Image.new('RGB',(COLS*CW,ROWS*CH),BG)
    draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(paths['mono'],12)
    lines=[]
    for y in range(ROWS):
        chars=[]
        for x in range(COLS):
            r,g,b=small.getpixel((x,y))
            sx=CROP[0]+(x+.5)*(CROP[2]-CROP[0])/COLS
            sy=CROP[1]+(y+.5)*(CROP[3]-CROP[1])/ROWS
            if (min(r,g,b)>231 and max(r,g,b)-min(r,g,b)<22) or any(x0<=sx<x1 and y0<=sy<y1 for x0,y0,x1,y1 in DECOR_REGIONS):
                chars.append(' ');continue
            lum=.2126*r+.7152*g+.0722*b
            ink=min(1,max(0,(255-lum)/225))
            neighbours=[luminance.getpixel((xx,yy)) for xx,yy in
                        [(max(0,x-1),y),(min(COLS-1,x+1),y),(x,max(0,y-1)),(x,min(ROWS-1,y+1))]]
            edge=max(0,sum(neighbours)/len(neighbours)-lum)
            is_eye=any(x0<=sx<x1 and y0<=sy<y1 for x0,y0,x1,y1 in EYE_REGIONS)
            is_beard=375<sx<705 and 685<sy<915
            # Eye pixels use continuous source luminance, without binary pupil
            # masks or contour overrides. Quiet midtones, retain real dark ink.
            detail=ink if is_eye else min(1,ink+min(.04 if is_beard else .08,edge/400 if is_beard else edge/300))
            gamma=1.85 if is_eye else 1.8 if is_beard else 1.55
            edge_fade=min(1,(ROWS-1-y)/3) if y>ROWS-4 else 1
            detail*=max(0,edge_fade)
            ramp='.:+*@' if is_eye else RAMP
            ch=ramp[min(len(ramp)-1,int(detail**gamma*(len(ramp)-1)))]
            if detail<.32 and edge<8:ch='.' if (x+y)%2==0 else ' '
            shade=round(125+(100 if is_beard else 120)*detail**.7)
            if edge_fade<1:shade=round(21+(shade-21)*edge_fade)
            color=(shade,round(shade*.985),round(shade*.95))
            # The cobalt accent occupies only genuine blue source pixels.
            if blue.getpixel((x,y))>15:
                ch='#' if blue.getpixel((x,y))>80 else '+'
                color=(99,138,255)
            draw.text((x*CW,y*CH-2),ch,font=font,fill=color,anchor='lt',stroke_width=0)
            chars.append(ch)
        lines.append(''.join(chars))
    canvas.save(ASSETS/'portrait-ascii.png',optimize=True)
    (ASSETS/'portrait-ascii.txt').write_text('\n'.join(lines)+'\n')
    return canvas


def draw_text(draw, command, paths):
    x,y,s,size,color,weight,family,tracking=command
    key='bold' if family=='sans' and weight>=600 else family
    font=ImageFont.truetype(paths[key],size)
    if not tracking:
        draw.text((x,y),s,font=font,fill=color,anchor='ls')
    else:
        for ch in s:
            draw.text((x,y),ch,font=font,fill=color,anchor='ls')
            x+=draw.textlength(ch,font=font)+tracking


def hero_frame(mobile,portrait,paths,progress=1,opacity=1,status='identity / loaded'):
    w,h,commands=scene(mobile)
    out=Image.new('RGB',(w,h),BG);d=ImageDraw.Draw(out)
    for op,*a in commands:
        if op=='rect':
            x,y,rw,rh,fill=a;d.rectangle((x,y,x+rw-1,y+rh-1),fill=fill)
        elif op=='line':
            x,y,xx,yy,color,sw=a;d.line((x,y,xx,yy),fill=color,width=sw)
        elif op=='text':
            draw_text(d,a,paths)
        elif op=='portrait':
            x,y,rw,rh=a
            p=portrait.copy()
            # A scan advances by rows, then by characters within the current row.
            amount=progress*ROWS;row=int(amount);fraction=amount-row
            if progress<1:
                pd=ImageDraw.Draw(p)
                pd.rectangle((0,(row+1)*CH,p.width,p.height),fill=BG)
                pd.rectangle((int(fraction*COLS)*CW,row*CH,p.width,(row+1)*CH),fill=BG)
            if opacity<1:
                p=Image.blend(Image.new('RGB',p.size,BG),p,opacity)
            p.thumbnail((rw,rh),Image.Resampling.LANCZOS)
            px=x+(rw-p.width)//2;py=y+(rh-p.height)//2
            out.paste(p,(px,py))
            if 0<progress<1:
                cy=py+int(p.height*progress)
                # A small cobalt registration tick marks the rendering row.
                d.line((x+rw-5,cy,x+rw,cy),fill=BLUE,width=2)
        elif op=='status':
            x,y,size=a;draw_text(d,[x,y,status,size,BLUE,400,'mono',0],paths)
    return out


def palette():
    # One fixed palette avoids GIF frame-to-frame colour flicker.
    colors=[(20,21,23),(242,239,231),(172,175,183),(54,57,65),(99,138,255)]
    for i in range(42):
        v=round(28+i*217/41);colors.append((v,round(v*.985),round(v*.95)))
    for i in range(16):
        t=i/15;colors.append(tuple(round(a+(b-a)*t) for a,b in zip((20,21,23),(99,138,255))))
    colors += [colors[0]]*(256-len(colors))
    p=Image.new('P',(1,1));p.putpalette([c for color in colors for c in color]);return p


def encode(mobile,portrait,paths):
    frames=[];durations=[];pal=palette()
    def add(frame,ms):
        frames.append(frame.quantize(palette=pal,dither=Image.Dither.NONE));durations.append(ms)
    add(hero_frame(mobile,portrait,paths,0,status='identity / ready'),180)
    for step in range(1,61):
        # Smooth linear terminal throughput, with a fractional last row.
        p=step/60
        add(hero_frame(mobile,portrait,paths,p,status=f'identity / {round(p*100):03d}%'),50)
    completed=hero_frame(mobile,portrait,paths)
    add(completed,3000)
    for alpha in [.86,.70,.53,.36,.20,.08]:
        add(hero_frame(mobile,portrait,paths,opacity=alpha,status='identity / replay'),50)
    name='hero-ascii-mobile' if mobile else 'hero-ascii'
    completed.save(ASSETS/f'{name}-static.png',optimize=True)
    frames[0].save(ASSETS/f'{name}.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=1,optimize=True)
    with Image.open(ASSETS/f'{name}.gif') as gif:
        assert gif.n_frames==len(frames) and gif.info.get('loop')==0
        assert sum(f.info.get('duration',0) for f in ImageSequence.Iterator(gif))==sum(durations)
    return {'file':name+'.gif','dimensions':completed.size,'frames':len(frames),'duration_ms':sum(durations),'reveal_ms':3000,'completed_hold_ms':3000,'fade_ms':300,'ready_ms':180,'bytes':(ASSETS/f'{name}.gif').stat().st_size}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['mono','sans','bold','serif']:p.add_argument('--'+name)
    args=p.parse_args();paths=fonts(args)
    portrait=ascii_portrait(paths)
    result=[encode(mobile,portrait,paths) for mobile in [False,True]]
    for mobile in [False,True]:write_svgs(mobile)
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    manifest={'source':'assets/portrait.jpeg','source_sha256':sha(ASSETS/'portrait.jpeg'),'crop':CROP,'grid':[COLS,ROWS],'cell_pixels':[CW,CH],'pillow':PIL.__version__,'fonts':{k:{'path':v,'sha256':sha(v)} for k,v in paths.items()},'outputs':result}
    manifest['processing']={'method':'source-luminance ASCII conversion','manual_eye_patterns':False,'glasses_tracing':False,'native_median_filter':3,'eye_tone_gamma':1.85,'beard_tone_gamma':1.8}
    (ASSETS/'ascii-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
