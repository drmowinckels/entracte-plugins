# entracte-plugins

Signed content plugins for [Entracte](https://github.com/drmowinckels/entracte) —
gentle, guided break content you install from a single file. No store, no account,
no network: a plugin is just a file you download and pick from disk.

## Packs

| Pack                 | Plugin id                           | What it adds                                                                                                               |
| -------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Breathing Studio** | `com.drmowinckels.breathing-studio` | Box, 4-7-8, coherent, and calming-exhale patterns that pulse the break ring, with in/out/hold tones to follow eyes-closed. |
| **Desk Yoga**        | `com.drmowinckels.desk-yoga`        | Three gentle desk-friendly flows (neck & shoulder, spine, wrist) with a pose image and a chime as each pose begins.        |
| **Eye Care**         | `com.drmowinckels.eye-care`         | Short screen-break eye relief — 20-20-20, palming, and near/far focus shifts.                                              |

Every pack is signed by one Ed25519 publisher key, so Entracte's install dialog
shows a stable fingerprint — **`AsA2XTlMP1eAqVJE…`** — for all three.

## Install

1. Download the `.plugin.json` files you want from the
   [latest release](https://github.com/drmowinckels/entracte-plugins/releases/latest).
2. In Entracte, go to **Settings → System → Plugins → Install plugin…** and pick a file.
3. The confirmation dialog shows the name, author, signing-key fingerprint, and how
   many ideas and routines it will add. Nothing is installed until you click **Install**.

Content plugins are **pure data** — they run no code. Installing one merges its
routines into your active profile; uninstalling removes exactly what it added and
nothing you created yourself. See Entracte's
[plugin docs](https://github.com/drmowinckels/entracte/blob/main/docs/PLUGINS.md)
for the full trust model.

## Build from source

Each pack lives in `packs/<name>/`:

- `manifest.json` — the plugin manifest (no `signature`/`assets`; assets are added at build time)
- `assets/` — images (`<id>.png|gif|webp|svg`) and sounds (`<id>.ogg|wav|mp3`) named by the id routines reference

```sh
python3 tools/sign.py keygen                 # once: writes key/seed.b64 (keep secret!)
python3 tools/sign.py build packs/breathing  # → dist/<id>.plugin.json
python3 tools/sign.py build packs/desk-yoga
python3 tools/sign.py build packs/eye-care
```

The signer reproduces Entracte's exact canonical signing form (sorted keys,
`data_base64` stripped, the per-`Manifest` null/empty fields) and self-checks
against a golden vector. One Ed25519 publisher key signs every pack so the
install dialog shows a stable fingerprint. `tools/validate_packs.py` mirrors
Entracte's asset rules (extensions, size/count caps, that every routine
reference resolves) and runs in CI.

## Releasing

Releases are cut by CI. Push a version tag and the
[release workflow](.github/workflows/release.yml) signs every pack and attaches the
installable `.plugin.json` files to a GitHub Release:

```sh
git tag v1.0.0 && git push --tags
```

It needs one repository secret, `PLUGIN_SIGNING_SEED` — the base64 Ed25519 seed
(the contents of your local `key/seed.b64`), set once with
`gh secret set PLUGIN_SIGNING_SEED < key/seed.b64`. Signing is deterministic, so a
CI build reproduces the same bytes as a local one.

## Assets

The breathing cues (`in`/`out`/`hold`/`hold_out`) and the desk-yoga / eye-care
`chime` are real singing-bowl sounds, generated procedurally with
[Mantice](https://github.com/bassimatte/mantice) and committed under each pack's
`assets/`. They are reproducible — see [`tools/make_bowl_cues.py`](tools/make_bowl_cues.py)
for the render-and-process recipe, and each pack's `CREDITS.md` for provenance.

The pose / exercise images are hand-drawn SVG line art, one per routine step,
committed alongside the sounds under each pack's `assets/`.
