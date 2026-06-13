#!/usr/bin/env python3
"""Turn a Mantice bowl render into the breathing/chime cue assets.

The breathing sounds are NOT synthesized at build time (see gen_assets.py for
the placeholder images). They are derived once from a procedural singing-bowl
drone rendered with Mantice (https://github.com/bassimatte/mantice), then
committed as real WAVs. This script documents and reproduces that step.

Reproduce
---------
    git clone https://github.com/bassimatte/mantice        # rendered at commit 1896be8
    cd mantice && python3 -m venv .venv && . .venv/bin/activate
    pip install numpy scipy soundfile pyyaml
    cp /path/to/entracte-plugins/tools/bowls/breath-bowl.yaml "presets/sacred/Breath Bowl.yaml"
    python main.py --preset "presets/sacred/Breath Bowl.yaml" --duration 14 --seed 7 --format wav
    #   -> exports/breath_bowl.wav
    python /path/to/entracte-plugins/tools/make_bowl_cues.py exports/breath_bowl.wav

Design
------
Four DISTINCT steady pitches trace the breath arc (no glide):
  hold_out (C3, lowest) < out (E3) < in (Bb3) < hold (D4, highest)
in rises (volume peaks late), out falls (peaks early), the holds are even
sustains. Every cue rings out to silence so nothing hard-cuts into dead air.
The chime is a struck variant for desk-yoga / eye-care pose starts.

Requires numpy + soundfile (NOT part of the signed build — a one-off asset step).
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SR = 44100
DUR = 4.0  # cue length: fills the shortest (4s) breath phase and rings out within it

BREATHING = ROOT / "packs" / "breathing" / "assets"
CHIME_DIRS = [ROOT / "packs" / "desk-yoga" / "assets",
              ROOT / "packs" / "eye-care" / "assets"]


def load(src):
    x, sr = sf.read(str(src))
    mono = x.mean(axis=1) if x.ndim > 1 else x
    if sr != SR:
        mono = np.interp(np.arange(0, len(mono), sr / SR), np.arange(len(mono)), mono)
    return mono


def flatten(sig, win_ms=150):
    """Divide out Mantice's slow level drift so imposed envelopes are exact;
    keeps the fast shimmer/beating of the bowl."""
    w = int(win_ms / 1000 * SR)
    rms = np.sqrt(np.convolve(sig ** 2, np.ones(w) / w, mode="same")) + 1e-6
    return sig / rms * rms.mean()


def smooth(n):
    return 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))


def pitch(sig, semis):
    factor = 2 ** (semis / 12.0)
    return np.interp(np.arange(0, len(sig), factor), np.arange(len(sig)), sig)


def take(mono, start, semis, out_dur=DUR):
    seg = pitch(mono[int(start * SR):int((start + out_dur * 1.6) * SR)].copy(), semis)
    return seg[:int(out_dur * SR)]


def ring(n, attack, a0, sustain_until, floor=0.02):
    """Raised-cosine swell a0->1 over `attack`, hold to `sustain_until`, then
    exponential ring-out to `floor`, with a short fade to true zero at the end."""
    env = np.ones(n)
    na = max(1, int(attack * n))
    env[:na] = a0 + (1 - a0) * smooth(na)
    nd = int(sustain_until * n)
    env[nd:] = env[nd] * np.exp(np.linspace(0, np.log(floor), n - nd))
    f = int(0.05 * SR)
    env[-f:] *= smooth(f)[::-1]
    return env


def norm(sig, peak=0.85):
    return sig * (peak / np.abs(sig).max())


def write(path, sig):
    sf.write(str(path), norm(sig).astype(np.float32), SR, subtype="PCM_16")
    print(f"  wrote {path.relative_to(ROOT)}  ({len(sig) / SR:.2f}s)")


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("exports/breath_bowl.wav")
    if not src.exists():
        sys.exit(f"render not found: {src}\nSee the docstring to produce it with Mantice.")
    mono = flatten(load(src))
    n = int(DUR * SR)

    write(BREATHING / "in.wav",       take(mono, 3.0, +3) * ring(n, 0.72, 0.12, 0.74))  # Bb3, rising
    write(BREATHING / "hold.wav",     take(mono, 6.0, +7) * ring(n, 0.18, 0.20, 0.45))  # D4, steady (highest)
    write(BREATHING / "out.wav",      take(mono, 3.0, -3) * ring(n, 0.05, 0.00, 0.10))  # E3, falling
    write(BREATHING / "hold_out.wav", take(mono, 6.0, -7) * ring(n, 0.18, 0.20, 0.45))  # C3, steady (lowest)

    ch = take(mono, 5.0, +7, out_dur=2.6)
    atk = int(0.004 * SR)
    ch = ch * np.concatenate([np.linspace(0, 1, atk),
                              np.exp(-np.arange(len(ch) - atk) / SR / 0.9)])
    ch[-int(0.05 * SR):] *= smooth(int(0.05 * SR))[::-1]
    for d in CHIME_DIRS:
        write(d / "chime.wav", ch)
    print("done.")


if __name__ == "__main__":
    main()
