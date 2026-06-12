#!/usr/bin/env python3
"""Synthesize the placeholder assets each pack references.

Pure Python — no ffmpeg/PIL. Tones are real mono 16-bit WAV (a valid `RIFF…
WAVE` Entracte accepts); images are solid-colour PNGs (valid headers Entracte
can size-check). They are intentionally minimal placeholders: swap them for
real recordings/artwork before publishing.
"""
import math
import struct
import wave
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tone(path, freq, dur=0.5, vol=0.45, rate=22050):
    n = int(dur * rate)
    fade = int(0.3 * n)
    frames = bytearray()
    for i in range(n):
        env = 1.0 if i < n - fade else max(0.0, (n - i) / fade)
        # tiny attack so it doesn't click
        if i < 200:
            env *= i / 200
        s = vol * env * math.sin(2 * math.pi * freq * i / rate)
        frames += struct.pack("<h", int(s * 32767))
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


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


# pack dir -> tones {id: freq} and images {id: rgb}
PACKS = {
    "breathing": {
        "tones": {"in": 196.0, "out": 261.6, "hold": 174.6},
        "images": {},
    },
    "desk-yoga": {
        "tones": {"chime": 659.3},
        "images": {
            "neck-rolls": (45, 92, 110), "ear-to-shoulder": (52, 104, 122),
            "shoulder-squeeze": (60, 116, 134), "cat-cow": (70, 110, 90),
            "seated-twist": (96, 120, 70), "side-bend": (120, 116, 64),
            "wrist-circles": (120, 88, 70), "wrist-stretch": (130, 76, 84),
            "prayer-stretch": (110, 70, 100),
        },
    },
    "eye-care": {
        "tones": {"chime": 587.3},
        "images": {
            "look-far": (40, 80, 120), "palming": (60, 60, 90),
            "focus-shift": (50, 100, 110), "figure-eight": (80, 70, 120),
        },
    },
}


def main():
    for pack, spec in PACKS.items():
        adir = ROOT / "packs" / pack / "assets"
        adir.mkdir(parents=True, exist_ok=True)
        for tid, freq in spec["tones"].items():
            tone(adir / f"{tid}.wav", freq, dur=0.45 if tid != "chime" else 0.6)
        for iid, rgb in spec["images"].items():
            png_solid(adir / f"{iid}.png", rgb)
        n = len(spec["tones"]) + len(spec["images"])
        print(f"{pack}: {n} asset(s) -> {adir}")


if __name__ == "__main__":
    main()
