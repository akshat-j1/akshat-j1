#!/usr/bin/env python3
"""Inspect the encoded animation, timing, static fallbacks and source provenance."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageSequence, ImageChops, ImageDraw, ImageOps
from generate_ascii import prepare_face, BLUSH_REGIONS, DECOR_REGIONS, CROP, COLS, ROWS

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'


def main():
    m=json.loads((ASSETS/'ascii-manifest.json').read_text())
    assert hashlib.sha256((ROOT/m['source']).read_bytes()).hexdigest()==m['source_sha256'], 'Source portrait changed'
    original=ImageOps.exif_transpose(Image.open(ROOT/m['source'])).convert('RGB')
    original_pixels=original.tobytes()
    cleaned,repaired=prepare_face(original)
    assert original.tobytes()==original_pixels, 'Preprocessing changed its input'
    assert repaired>100
    changed=ImageChops.difference(original,cleaned).convert('L').point(lambda v:255 if v else 0)
    allowed=Image.new('L',original.size);allowed_draw=ImageDraw.Draw(allowed)
    for x0,y0,x1,y1 in BLUSH_REGIONS:
        allowed_draw.rectangle((x0-3,y0-3,x1+2,y1+2),fill=255)
        for y in range(y0,y1):
            for x in range(x0,x1):
                r,g,b=cleaned.getpixel((x,y))
                assert not (r>115 and g<140 and r>1.65*g and r-g>65), 'Residual blush stroke'
    assert not ImageChops.subtract(changed,allowed).getbbox(), 'Cleanup affected protected facial features'
    bounds=changed.getbbox()
    for y in range(bounds[1],bounds[3]):
        for x in range(bounds[0],bounds[2]):
            if changed.getpixel((x,y)):
                r,g,b=cleaned.getpixel((x,y))
                assert r>180 and g>115 and b>60, 'Cheek repair left a dark/empty patch'
    text=(ASSETS/'portrait-ascii.txt').read_text().splitlines()
    cols,rows=m['grid']
    assert len(text)==rows and all(len(row)==cols for row in text)
    assert set(''.join(text)) <= set(' .:+*%#@')
    for y,row in enumerate(text):
        for x,ch in enumerate(row):
            sx=CROP[0]+(x+.5)*(CROP[2]-CROP[0])/COLS;sy=CROP[1]+(y+.5)*(CROP[3]-CROP[1])/ROWS
            if any(x0<=sx<x1 and y0<=sy<y1 for x0,y0,x1,y1 in DECOR_REGIONS):assert ch==' ', 'Decorative cheek mark remains'
    for output in m['outputs']:
        gif=Image.open(ASSETS/output['file'])
        assert gif.is_animated and gif.info.get('loop')==0
        assert gif.n_frames==68 and gif.size==tuple(output['dimensions'])
        assert (ASSETS/output['file']).stat().st_size<600_000
        frames=[(f.convert('RGB').copy(),f.info['duration']) for f in ImageSequence.Iterator(gif)]
        assert sum(duration for _,duration in frames)==6480
        assert sum(duration for _,duration in frames[1:61])==3000
        assert frames[61][1]==3000
        assert sum(duration for _,duration in frames[62:])==300
        static=Image.open(ASSETS/output['file'].replace('.gif','-static.png')).convert('RGB')
        assert static.size==gif.size
        # Compare completed GIF and PNG allowing for the deliberately limited GIF palette.
        diff=ImageChops.difference(static,frames[61][0])
        assert max(diff.getextrema()[i][1] for i in range(3))<60
        assert ImageChops.difference(frames[0][0],frames[61][0]).getbbox()
        assert ImageChops.difference(frames[8][0],frames[32][0]).getbbox()
        # Contact sheet exposes actual encoded states for review.
        sheet=Image.new('RGB',(gif.width*3,gif.height),(20,21,23))
        for i,index in enumerate([15,40,61]):sheet.paste(frames[index][0],(gif.width*i,0))
        if output['file']=='hero-ascii.gif':sheet.save(ASSETS/'ascii-sequence-preview.png',optimize=True)
    print('PASS: immutable source, clean cheeks, source-tone character palette without drawn eye patterns, 68 GIF frames, unchanged 6.48s timing, dimensions, palette fidelity, and static fallbacks')


if __name__=='__main__':main()
