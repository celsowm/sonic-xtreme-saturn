#!/usr/bin/env python3
"""Bake real CC0 source PNG textures into eight 64x64 VDP1 indexed8 materials.

The input PNGs are unmodified Kenney Retro Textures Fantasy artwork, tracked
in assets/textures/jade-gully. The source files remain inspectable and
replaceable. No procedurally generated or invented texture pixels are used.

Only 8-bit non-interlaced indexed PNG is supported by the strict stdlib
decoder. Quantize *each* material to 31 colors, in 8 bands of a shared
256-entry RGB555 palette (bank 7). Retains a flat-color fallback for clipped
faces and fits in exactly 32KiB of permanent VDP1 VRAM. Deterministic.
"""
import argparse
from collections import Counter
import struct
from pathlib import Path
import zlib

NAMES=(
    "grass-path", "sand-path", "rock-grey", "forest-leaves",
    "sandstone", "waterfall", "meadow-grass", "moss-bank"
)
WIDTH=HEIGHT=64
PALETTE_COLORS_PER_TEXTURE=31
# Art direction: grade the ACTUAL Kenney texels so they read as a vibrant,
# tropical action-adventure stage rather than a dark fantasy dungeon.
# RGB gains are not new generated texture sources.
GRADE=(
    (1.26,1.72,0.90),
    (1.30,1.17,0.94),
    (1.45,1.40,1.23),
    (1.26,1.76,0.93),
    (1.38,1.25,0.94),
    (0.86,1.22,1.38),
    (1.24,1.86,0.93),
    (1.12,1.52,0.96),
)
UNDERLAY=(
    (34,84,27),(120,93,54),(70,68,58),(32,106,40),
    (122,103,71),(28,106,140),(45,115,28),(77,87,49)
)

def read_png(data):
    if data[:8]!=b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    chunks=[]
    off=8
    while off<len(data):
        if off+12>len(data):raise ValueError("truncated PNG chunk")
        size=struct.unpack_from(">I",data,off)[0]
        tag=data[off+4:off+8]
        end=off+12+size
        if end>len(data):raise ValueError("truncated PNG payload")
        content=data[off+8:off+8+size]
        crc=struct.unpack_from(">I",data,off+8+size)[0]
        if zlib.crc32(tag+content)&0xffffffff!=crc:
            raise ValueError(f"bad PNG CRC {tag!r}")
        chunks.append((tag,content))
        off=end
        if tag==b"IEND":break
    parts={k:v for k,v in chunks if k!=b"IDAT"}
    if b"IHDR" not in parts or b"PLTE" not in parts:
        raise ValueError("requires indexed PNG with a palette")
    width,height,depth,kind,comp,filt,interlace=struct.unpack(">IIBBBBB",parts[b"IHDR"])
    if depth!=8 or kind!=3 or interlace or comp or filt:
        raise ValueError("only 8-bit non-interlaced indexed PNG supported")
    if width!=64 or height not in (64,128):
        raise ValueError("Kenney input expected 64x64 or 64x128")
    colors=parts[b"PLTE"]
    if len(colors)%3:raise ValueError("invalid palette")
    alpha=parts.get(b"tRNS",b"")
    palettes=[tuple(colors[i:i+3]) for i in range(0,len(colors),3)]
    raw=zlib.decompress(b"".join(payload for tag,payload in chunks if tag==b"IDAT"))
    out=[]
    prev=bytearray(width)
    offset=0
    for y in range(height):
        if offset+width+1>len(raw):raise ValueError("truncated PNG rows")
        mode=raw[offset]
        data=raw[offset+1:offset+1+width]
        offset+=1+width
        row=bytearray(width)
        if mode not in range(5):raise ValueError("bad PNG filter")
        for x in range(width):
            a=row[x-1] if x else 0
            b=prev[x]
            c=prev[x-1] if x else 0
            if mode==0:predictor=0
            elif mode==1:predictor=a
            elif mode==2:predictor=b
            elif mode==3:predictor=(a+b)//2
            else:
                p=a+b-c;pa=abs(p-a);pb=abs(p-b);pc=abs(p-c)
                predictor=a if pa<=pb and pa<=pc else b if pb<=pc else c
            row[x]=(data[x]+predictor)&255
        if height==64 or y%2==0:
            for idx in row:
                if idx>=len(palettes):raise ValueError("invalid PNG palette index")
                rgb=palettes[idx]
                opacity=alpha[idx] if idx<len(alpha) else 255
                out.append((*rgb,opacity))
        prev=row
    if offset!=len(raw) or len(out)!=WIDTH*HEIGHT:
        raise ValueError("unexpected indexed PNG data size")
    return out

def color_grade(p,material):
    r,g,b,a=p
    under=UNDERLAY[material]
    if a<255:
        r=(r*a+under[0]*(255-a)+127)//255
        g=(g*a+under[1]*(255-a)+127)//255
        b=(b*a+under[2]*(255-a)+127)//255
    gains=GRADE[material]
    return tuple(min(255,int(v*factor+0.5)) for v,factor in zip((r,g,b),gains))

def quantize(pixels):
    freq=Counter(pixels)
    unique=sorted(freq, key=lambda color:(-freq[color],color))
    if len(unique)<=31:
        chosen=unique
    else:
        # Deterministic popularity/coverage quantizer. Highly frequent colors
        # seed the palette; subsequent colors maximize distance from selected
        # colors times their occurrence. Preserve meaningful patterns.
        chosen=[unique[0]]
        remaining=unique[1:]
        dist={c:sum((c[i]-chosen[0][i])**2 for i in range(3)) for c in remaining}
        while len(chosen)<31:
            pick=max(remaining,key=lambda c:(dist[c]*(freq[c]+2),freq[c],c))
            chosen.append(pick)
            remaining.remove(pick)
            for c in remaining:
                n=sum((c[i]-pick[i])**2 for i in range(3))
                if n<dist[c]:dist[c]=n
    chosen=chosen[:31]
    cache={}
    def nearest(c):
        if c not in cache:
            cache[c]=min(range(len(chosen)),key=lambda i:(
                sum((c[k]-chosen[i][k])**2 for k in range(3)),i))
        return cache[c]
    slots=[nearest(c)+1 for c in pixels]
    return chosen,slots

def rgb555(color):
    r,g,b=color
    return 0x8000 | ((b>>3)<<10) | ((g>>3)<<5) | (r>>3)

def build(source):
    pixels=[]
    palette=[0x8000]*256
    summaries=[]
    fallback=[]
    for i,name in enumerate(NAMES):
        file=source/(name+".png")
        if not file.is_file():raise ValueError(f"missing real CC0 PNG: {file}")
        original=read_png(file.read_bytes())
        graded=[color_grade(p,i) for p in original]
        colors,entries=quantize(graded)
        if len(set(entries))<4:
            raise ValueError(f"texture has insufficient detail: {name}")
        for j,c in enumerate(colors):
            palette[i*32+1+j]=rgb555(c)
        pixels.append([i*32+x for x in entries])
        fallback.append(rgb555(colors[0]))
        summaries.append({"material":name,"source_unique":len(set(graded)),
                          "palette_used":len(set(entries)),
                          "width":64,"height":64})
    return palette,pixels,fallback,summaries

def as_array(values,wrap=16,hex_width=2):
    return "\n".join("    "+", ".join(
        f"0x{x:0{hex_width}X}u" for x in values[j:j+wrap])+","
        for j in range(0,len(values),wrap))

def emit(palette,pixels,fallback):
    blocks=[
        "/* AUTOGENERATED from actual Kenney CC0 texture PNGs, not placeholder art.",
        " * Run python tools/bake_stage_textures.py assets/textures/jade-gully OUT.h",
        " * Eight 64x64 indexed8 patterns / one 256-entry RGB555 palette bank. */",
        "#ifndef XTREME_GENERATED_STAGE_TEXTURE_DATA_H",
        "#define XTREME_GENERATED_STAGE_TEXTURE_DATA_H",
        "static const uint16_t stage_palette[256] = {",
        as_array(palette,8,4),
        "};",
        "static const uint16_t stage_fallback_rgb[8] = {",
        as_array(fallback,8,4),
        "};",
        "static const uint8_t stage_pixels[8][4096] = {",
    ]
    for material,values in zip(NAMES,pixels):
        blocks.extend((f"  {{ /* {material} */",as_array(values,16,2),"  },"))
    blocks.extend(("};","#endif",""))
    return "\n".join(blocks)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    a=parser.parse_args()
    palette,pixels,fallback,summary=build(a.source)
    out=emit(palette,pixels,fallback)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(out,encoding="ascii")
    for record in summary:
        print(f"[cc0] {record['material']}: {record['source_unique']} source RGB colors"
              f" => {record['palette_used']} visible INDEX8 colors")
    print("[cc0] VDP1 total: 8 x 64x64 = 32,768 bytes; one 256-color CRAM bank")

if __name__=="__main__":main()
