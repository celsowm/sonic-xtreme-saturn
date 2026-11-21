#!/usr/bin/env python3
"""Bake user-supplied X-Treme Ring Sprites mod data to Saturn VDP1 INDEX8.

The tracked .b64 is an offline, losslessly packed 4bpp rendition of the 16
32x32 world-ring frames from Mr. Malfunction's SADX texture mod. Pixel alpha
is thresholded at 128 to the Saturn transparent index 0. Only the 14 fully
visible source RGB colors are used; their 8-bit RGB components are preserved
until the RGB555 hardware quantization. No network, PIL, 7z or SADX runtime.
"""
import argparse
import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path

FRAME_COUNT=16
WIDTH=HEIGHT=32
PALETTE_BANK=6
COMPRESSED_SHA256="bf368a4131af2a9c2710d422b90fac12b94577f5892c2763debf1d48d729de1c"
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/rings/xtreme-ring-frames.b64"
META=ROOT/"assets/rings/metadata.json"

def rgb555(rgb):
    r,g,b=rgb
    return 0x8000|((b>>3)<<10)|((g>>3)<<5)|(r>>3)

def load(source=SOURCE,metadata=META):
    payload=base64.b64decode("".join(source.read_text().split()),validate=True)
    if hashlib.sha256(payload).hexdigest()!=COMPRESSED_SHA256:
        raise ValueError("ring source checksum mismatch")
    packed=zlib.decompress(payload)
    if len(packed)!=FRAME_COUNT*WIDTH*HEIGHT//2:
        raise ValueError("invalid packed ring frame length")
    meta=json.loads(metadata.read_text())
    colors=meta["opaque_rgb"]
    if len(colors)!=14 or len({tuple(c) for c in colors})!=14:
        raise ValueError("expected 14 unique original ring colors")
    if any(len(c)!=3 or any(type(v)!=int or not 0<=v<=255 for v in c)
           for c in colors):
        raise ValueError("invalid RGB palette")
    palette=[0]*256
    for idx,rgb in enumerate(colors,1):
        palette[idx]=rgb555(rgb)
    indices=bytearray()
    for byte in packed:
        indices.append(byte>>4)
        indices.append(byte&15)
    if max(indices)>len(colors) or min(indices)!=0:
        raise ValueError("invalid palette indices")
    frames=[indices[i*WIDTH*HEIGHT:(i+1)*WIDTH*HEIGHT]
            for i in range(FRAME_COUNT)]
    if any(not any(frame) or 0 not in frame for frame in frames):
        raise ValueError("frames need visible gold and transparent background")
    return palette,frames

def emit(palette,frames):
    out=[
      "/* Generated from user-supplied X-Treme Ring Sprites SADX mod.",
      " * Mr. Malfunction, GameBanana #537401, no CC0 claim.",
      " * INDEX8, 16 x 32x32 frames, transparent code 0, CRAM bank 6. */",
      "#ifndef XTREME_GENERATED_RING_TEXTURE_DATA_H",
      "#define XTREME_GENERATED_RING_TEXTURE_DATA_H",
      "static const uint16_t xtreme_ring_palette[256] = {"
    ]
    for start in range(0,256,8):
        out.append("    "+", ".join(f"0x{v:04X}u" for v in palette[start:start+8])+",")
    out += ["};", "static const uint8_t xtreme_ring_pixels[16][1024] = {"]
    for idx,frame in enumerate(frames):
        out.append(f"    {{ /* source ring{idx+1}.png */")
        for start in range(0,1024,16):
            out.append("        "+", ".join(f"0x{v:02X}u" for v in frame[start:start+16])+",")
        out.append("    },")
    out += ["};","#endif",""]
    return "\n".join(out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    palette,frames=load()
    output=emit(palette,frames)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(output,encoding="ascii")
    print(f"[rings] {len(frames)} source frames 32x32, {sum(any(x for x in f) for f in frames)} visible")
    print("[rings] VDP1 resident: 16 x 1024 = 16384 bytes; CRAM bank 6, code 0 transparent")

if __name__=="__main__":main()
