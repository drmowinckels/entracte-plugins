# Desk Yoga — credits

## Sounds

The `chime` (a struck singing bowl played at each pose start) is generated with
**[Mantice](https://github.com/bassimatte/mantice)**, a procedural ambient-drone
synthesizer by **Matteo Bassi**
([freesound.org/people/bassimat](https://freesound.org/people/bassimat/)).

- Rendered from the FM preset [`tools/bowls/chime-bowl.yaml`](../../tools/bowls/chime-bowl.yaml)
  (Mantice commit `1896be8`, `--duration 10 --seed 3`) — a clean, noise-free,
  reverb-free bowl so the strike rings without an airy wash.
- Struck and warmed into the cue by [`tools/make_bowl_cues.py`](../../tools/make_bowl_cues.py)
  (this pack's chime is pitched a little lower than eye-care's).
- Pure FM synthesis — no third-party audio samples are embedded.

Mantice ships without an explicit licence at the time of writing; attributed here
as a courtesy.
