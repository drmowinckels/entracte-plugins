#!/usr/bin/env python3
"""Synthesize the placeholder *image* assets each pack references.

Pure Python — no PIL. Images are solid-colour PNGs (valid headers Entracte can
size-check), intentionally minimal placeholders: swap them for real artwork
before publishing.

The breathing tones and the desk-yoga/eye-care chime are no longer synthesized
here — they are real singing-bowl recordings derived once from a Mantice render
(see tools/make_bowl_cues.py) and committed under each pack's assets/.
"""
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def png_solid(path, rgb, w=480, h=320):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8-bit truecolour
    row = b"\x00" + bytes(rgb) * w
    idat = zlib.compress(row * h, 9)
    Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b""))


# pack dir -> images {id: rgb}
PACKS = {
    "desk-yoga": {
        "neck-rolls": (45, 92, 110), "ear-to-shoulder": (52, 104, 122),
        "shoulder-squeeze": (60, 116, 134), "cat-cow": (70, 110, 90),
        "seated-twist": (96, 120, 70), "side-bend": (120, 116, 64),
        "wrist-circles": (120, 88, 70), "wrist-stretch": (130, 76, 84),
        "prayer-stretch": (110, 70, 100),
    },
    "eye-care": {
        "look-far": (40, 80, 120), "palming": (60, 60, 90),
        "focus-shift": (50, 100, 110), "figure-eight": (80, 70, 120),
    },
}


def main():
    for pack, images in PACKS.items():
        adir = ROOT / "packs" / pack / "assets"
        adir.mkdir(parents=True, exist_ok=True)
        for iid, rgb in images.items():
            png_solid(adir / f"{iid}.png", rgb)
        print(f"{pack}: {len(images)} image(s) -> {adir}")


if __name__ == "__main__":
    main()
