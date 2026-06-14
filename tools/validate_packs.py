#!/usr/bin/env python3
"""Validate every pack against Entracte's asset rules — a pre-flight that fails
in CI rather than at install time.

Mirrors `src-tauri/src/plugins/asset.rs` + `manifest.rs` in the Entracte app:
the accepted image/sound extensions, the per-asset size caps, the asset-count
cap, the filename-safe id, and — the high-value check — that every routine
`asset` reference resolves to an existing *image* and every `sound` /
breath-phase cue to an existing *audio* asset of the right kind.

Pure stdlib. Run with no args to check every pack under packs/.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IMAGE_EXT = {"png", "gif", "webp", "svg"}
SOUND_EXT = {"ogg", "wav", "mp3"}
MAX_ASSETS = 64
MAX_IMAGE_BYTES = 512 * 1024
MAX_SOUND_BYTES = 256 * 1024
ID_RE = re.compile(r"^[a-z0-9._-]{1,128}$")


def scan_assets(adir, errors):
    """Map asset id (file stem) -> "image" | "audio" for every valid file."""
    kinds = {}
    if not adir.is_dir():
        return kinds
    for f in sorted(adir.iterdir()):
        if f.name.startswith(".") or not f.is_file():
            continue
        ext = f.suffix.lstrip(".").lower()
        kind = "image" if ext in IMAGE_EXT else "audio" if ext in SOUND_EXT else None
        if kind is None:
            continue
        if not ID_RE.match(f.stem):
            errors.append(f"asset id '{f.stem}' must be 1..=128 chars of [a-z0-9._-]")
            continue
        cap = MAX_IMAGE_BYTES if kind == "image" else MAX_SOUND_BYTES
        if f.stat().st_size > cap:
            errors.append(f"{kind} '{f.stem}' is {f.stat().st_size} bytes, over the {cap}-byte cap")
        if f.stem in kinds:
            errors.append(f"duplicate asset id '{f.stem}'")
        kinds[f.stem] = kind
    if len(kinds) > MAX_ASSETS:
        errors.append(f"pack carries {len(kinds)} assets, over the {MAX_ASSETS} cap")
    return kinds


def want(kinds, rid, ref, expect, errors):
    if ref is None:
        return
    if ref not in kinds:
        errors.append(f"routine '{rid}' references unknown asset '{ref}'")
    elif kinds[ref] != expect:
        errors.append(f"routine '{rid}' references '{ref}' as {expect} but it is {kinds[ref]}")


def validate_pack(pack_dir):
    errors = []
    manifest_path = pack_dir / "manifest.json"
    try:
        m = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return [f"manifest.json could not be read/parsed: {e}"]

    content = m.get("content")
    kinds = scan_assets(pack_dir / "assets", errors)
    if m.get("kind") != "content":
        if kinds:
            errors.append(f"a {m.get('kind')!r} plugin must not carry assets")
        return errors

    for r in (content or {}).get("routines", []):
        rid = r.get("id", "?")
        for step in r.get("steps", []):
            want(kinds, rid, step.get("asset"), "image", errors)
            want(kinds, rid, step.get("sound"), "audio", errors)
        snd = (r.get("breath") or {}).get("sounds") or {}
        for phase in ("inhale", "hold", "exhale", "hold_out"):
            want(kinds, rid, snd.get(phase), "audio", errors)
    return errors


def main():
    packs = sorted(p for p in (ROOT / "packs").iterdir() if (p / "manifest.json").is_file())
    failed = 0
    for pack in packs:
        errors = validate_pack(pack)
        if errors:
            failed += 1
            print(f"✗ {pack.name}")
            for e in errors:
                print(f"    - {e}")
        else:
            print(f"✓ {pack.name}")
    if failed:
        print(f"\n{failed} pack(s) failed validation")
        sys.exit(1)
    print(f"\nall {len(packs)} pack(s) valid")


if __name__ == "__main__":
    main()
