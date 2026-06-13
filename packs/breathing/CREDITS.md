# Breathing Studio — credits

## Sounds

The breath cues (`in`, `out`, `hold`, `hold_out`) are singing-bowl sounds generated
with **[Mantice](https://github.com/bassimatte/mantice)**, a procedural ambient-drone
synthesizer by **Matteo Bassi**
([freesound.org/people/bassimat](https://freesound.org/people/bassimat/)).

- Rendered from the FM preset [`tools/bowls/breath-bowl.yaml`](../../tools/bowls/breath-bowl.yaml)
  (Mantice commit `1896be8`, `--duration 14 --seed 7`).
- Processed into the four cues by [`tools/make_bowl_cues.py`](../../tools/make_bowl_cues.py).
- The preset is **pure FM synthesis** — no third-party audio samples are embedded;
  the output is generated mathematically.

Mantice ships without an explicit licence at the time of writing. These assets are
attributed here as a courtesy; confirm reuse terms with the author before publishing
if that matters for your distribution.
