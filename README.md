# entracte-plugins

Signed content plugins for [Entracte](https://github.com/drmowinckels/entracte).

Each pack lives in `packs/<name>/`:
- `manifest.json` — the plugin manifest (no `signature`/`assets`; assets are added at build time)
- `assets/` — images (`<id>.png|gif|webp`) and sounds (`<id>.ogg|wav|mp3`) named by the id routines reference

## Build

    python3 tools/sign.py keygen                 # once: writes key/seed.b64 (keep secret!)
    python3 tools/gen_assets.py                  # synthesize the placeholder/tone assets
    python3 tools/sign.py build packs/breathing  # → dist/<id>.plugin.json
    python3 tools/sign.py build packs/desk-yoga
    python3 tools/sign.py build packs/eye-care

The signer reproduces Entracte's exact canonical signing form (sorted keys,
`data_base64` stripped, the per-`Manifest` null/empty fields) and self-checks
against a golden vector. One Ed25519 publisher key signs every pack so the
install dialog shows a stable fingerprint.

Assets in this repo are **placeholders** (synthesized tones; labelled image
boxes) — swap them for real artwork/recordings before publishing.
