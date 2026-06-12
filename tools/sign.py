#!/usr/bin/env python3
"""Sign Entracte content plugins.

Reproduces Entracte's canonical signing form byte-for-byte (see
`src-tauri/src/plugins/signature.rs::signing_payload` and the `Manifest` serde
shape): keys sorted at every level, compact separators, UTF-8; the `signature`
and every asset's `data_base64` removed; the per-`Manifest` defaults made
explicit (`module`/`abi_version`/`detect`/`export` -> null, `imports` -> [],
all five hint pools present, breath `hold`/`hold_out` -> 0). A golden vector
(`--selftest`) pins that form against the real Rust output.

    python3 tools/sign.py keygen
    python3 tools/sign.py build packs/<name>
    python3 tools/sign.py selftest
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

from nacl.signing import SigningKey

ROOT = Path(__file__).resolve().parent.parent
KEY_PATH = ROOT / "key" / "seed.b64"
DIST = ROOT / "dist"

IMAGE_EXT = {"png", "gif", "webp"}
SOUND_EXT = {"ogg", "wav", "mp3"}

# Golden canonical bytes emitted by Entracte's `signing_payload` for DEMO below.
GOLDEN = '{"abi_version":null,"assets":[{"id":"pic","sha256":"aa"},{"id":"chime","sha256":"bb"}],"author":"Me","content":{"hints":{"long_social":[],"long_solo":[],"micro_physical":["roll shoulders"],"micro_psychological":[],"sleep":[]},"name":"Demo","routines":[{"category":"desk_yoga","difficulty":"gentle","id":"r1","kind":"long","label":"R1","max_step_secs":60,"pacing":"fill","steps":[{"asset":"pic","seconds":30,"sound":"chime","text":"twist"}]},{"breath":{"cycles":6,"exhale":8,"hold":0,"hold_out":0,"inhale":4,"sounds":{"exhale":"out","inhale":"in"},"then":"rest"},"category":"breathing","difficulty":"gentle","id":"b1","kind":"long","label":"478","steps":[]}],"version":1},"description":"d","detect":null,"export":null,"id":"com.example.demo","imports":[],"kind":"content","manifest_version":1,"module":null,"name":"Demo","version":"1.0.0"}'

DEMO = {
    "manifest_version": 1, "id": "com.example.demo", "name": "Demo",
    "version": "1.0.0", "author": "Me", "description": "d", "kind": "content",
    "content": {"version": 1, "name": "Demo",
                "hints": {"micro_physical": ["roll shoulders"]},
                "routines": [
                    {"id": "r1", "label": "R1", "kind": "long",
                     "category": "desk_yoga", "difficulty": "gentle",
                     "pacing": "fill", "max_step_secs": 60,
                     "steps": [{"text": "twist", "seconds": 30,
                                "asset": "pic", "sound": "chime"}]},
                    {"id": "b1", "label": "478", "kind": "long",
                     "category": "breathing", "difficulty": "gentle",
                     "steps": [],
                     "breath": {"inhale": 4, "exhale": 8, "cycles": 6,
                                "then": "rest",
                                "sounds": {"inhale": "in", "exhale": "out"}}}]},
    "assets": [{"id": "pic", "sha256": "aa", "data_base64": "AAAA"},
               {"id": "chime", "sha256": "bb", "data_base64": "BBBB"}],
}


def _step(s):
    out = {"text": s["text"], "seconds": s["seconds"]}
    if s.get("asset") is not None:
        out["asset"] = s["asset"]
    if s.get("sound") is not None:
        out["sound"] = s["sound"]
    return out


def _breath(b):
    out = {"inhale": b["inhale"], "exhale": b["exhale"],
           "hold": b.get("hold", 0), "hold_out": b.get("hold_out", 0)}
    if b.get("cycles") is not None:
        out["cycles"] = b["cycles"]
    if b.get("then") is not None:
        out["then"] = b["then"]
    if b.get("sounds") is not None:
        snd = {k: b["sounds"][k] for k in ("inhale", "hold", "exhale", "hold_out")
               if b["sounds"].get(k) is not None}
        out["sounds"] = snd
    return out


def _routine(r):
    out = {"id": r["id"], "label": r["label"], "kind": r["kind"],
           "category": r["category"], "difficulty": r["difficulty"],
           "steps": [_step(s) for s in r.get("steps", [])]}
    if r.get("pacing") is not None:
        out["pacing"] = r["pacing"]
    if r.get("max_step_secs") is not None:
        out["max_step_secs"] = r["max_step_secs"]
    if r.get("breath") is not None:
        out["breath"] = _breath(r["breath"])
    return out


def _content(c):
    h = c.get("hints", {})
    return {"version": c["version"], "name": c["name"],
            "hints": {k: h.get(k, []) for k in
                      ("micro_physical", "micro_psychological",
                       "long_solo", "long_social", "sleep")},
            "routines": [_routine(r) for r in c.get("routines", [])]}


def canonical(m):
    """The exact dict Entracte signs over (data_base64 + signature stripped)."""
    out = {
        "manifest_version": m["manifest_version"], "id": m["id"],
        "name": m["name"], "version": m["version"],
        "author": m.get("author", ""), "description": m.get("description", ""),
        "kind": m["kind"],
        "module": m.get("module"), "abi_version": m.get("abi_version"),
        "imports": m.get("imports", []),
        "detect": m.get("detect"), "export": m.get("export"),
        "content": _content(m["content"]) if m.get("content") is not None else None,
    }
    assets = m.get("assets", [])
    if assets:  # omitted when empty (skip_serializing_if = Vec::is_empty)
        out["assets"] = [{"id": a["id"], "sha256": a["sha256"]} for a in assets]
    return out


def canonical_bytes(m):
    return json.dumps(canonical(m), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def selftest():
    got = json.dumps(canonical(DEMO), sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False)
    if got != GOLDEN:
        print("SELFTEST FAILED — canonical form drifted from Entracte's.")
        print("got:    ", got)
        print("golden: ", GOLDEN)
        sys.exit(1)
    print("selftest OK — canonical form matches Entracte's signing_payload.")


def keygen():
    if KEY_PATH.exists():
        sys.exit(f"refusing to overwrite existing key at {KEY_PATH}")
    KEY_PATH.parent.mkdir(exist_ok=True)
    key = SigningKey.generate()
    KEY_PATH.write_text(base64.standard_b64encode(bytes(key)).decode())
    pub = base64.standard_b64encode(bytes(key.verify_key)).decode()
    print(f"wrote {KEY_PATH} (keep it secret!)")
    print(f"public key fingerprint: {pub[:16]}…")


def load_assets(pack_dir, manifest):
    """Read pack_dir/assets/<id>.<ext>, returning the manifest `assets` array."""
    adir = pack_dir / "assets"
    if not adir.is_dir():
        return []
    assets = []
    for f in sorted(adir.iterdir()):
        if f.name.startswith(".") or not f.is_file():
            continue
        ext = f.suffix.lstrip(".").lower()
        if ext not in IMAGE_EXT and ext not in SOUND_EXT:
            continue
        data = f.read_bytes()
        assets.append({
            "id": f.stem,
            "sha256": hashlib.sha256(data).hexdigest(),
            "data_base64": base64.standard_b64encode(data).decode(),
        })
    return assets


def build(pack_dir):
    pack_dir = Path(pack_dir)
    manifest = json.loads((pack_dir / "manifest.json").read_text())
    manifest.pop("signature", None)
    manifest["assets"] = load_assets(pack_dir, manifest)

    if not KEY_PATH.exists():
        sys.exit("no signing key — run: python3 tools/sign.py keygen")
    key = SigningKey(base64.standard_b64decode(KEY_PATH.read_text().strip()))

    payload = canonical_bytes(manifest)
    sig = key.sign(payload).signature
    manifest["signature"] = {
        "alg": "ed25519",
        "public_key": base64.standard_b64encode(bytes(key.verify_key)).decode(),
        "sig": base64.standard_b64encode(sig).decode(),
    }
    # Self-verify the signature we just produced.
    key.verify_key.verify(payload, sig)

    DIST.mkdir(exist_ok=True)
    out = DIST / f"{manifest['id']}.plugin.json"
    out.write_text(json.dumps(manifest))
    imgs = sum(1 for a in manifest["assets"]
               if a["id"] and Path(a["id"]).suffix == "")
    print(f"wrote {out}  ({len(manifest['assets'])} asset(s), "
          f"{out.stat().st_size // 1024} KiB)")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "keygen":
        keygen()
    elif cmd == "selftest":
        selftest()
    elif cmd == "build":
        if len(sys.argv) < 3:
            sys.exit("usage: sign.py build packs/<name>")
        selftest()
        build(sys.argv[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
