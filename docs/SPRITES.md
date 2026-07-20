# Making your own character

You need six PNGs in `sprites/`. This guide covers how to get them and the
things that will go wrong.

## The six frames

| File | Pose |
|---|---|
| `walk_contact.png` | Front foot planted, legs apart |
| `walk_down.png` | Body at its lowest point |
| `walk_passing.png` | Legs together, body at its highest |
| `walk_up.png` | Pushing off, rising |
| `turn.png` | 3/4 view, mid-turn toward the viewer |
| `thumb.png` | Facing the viewer, thumbs up |

The four walk poses are a standard cycle. Search "walk cycle contact down
passing up" for reference — the names are universal in animation.

The script mirrors the walk frames itself for the walk-out, so you don't need
left-facing versions.

## Requirements

**Facing right.** The script assumes it and mirrors for the return trip.

**Same height, feet on the same row.** All six PNGs must be the same pixel
height, with the character's lowest opaque pixel on the same row in each. If
the feet don't line up, she bobs and slides. The script scales all frames by
one factor, so any misalignment survives.

**Real transparency.** A genuine alpha channel. Not a checkerboard pattern
drawn into the pixels — see below, this is the big one.

**Padding is fine.** Empty rows above the head are fine; the script measures
her actual body (via the alpha mask) and scales from that, ignoring padding.

## If you generate sprites with AI

Every image generator I've tried will hand you a PNG with a **fake
checkerboard** — the grey-and-white "transparency" pattern drawn in as actual
pixels, with no alpha channel at all. It looks transparent. It isn't.

Check before you do anything else:

```python
from PIL import Image
im = Image.open("your_sprite.png")
print(im.mode)   # want "RGBA". "RGB" means no alpha channel: fake.
```

If you get `RGB`, you have to key the checkerboard out, and it's fiddlier than
it looks:

- **The checker is enclosed by the character.** The gap between her legs, the
  space under an arm. Flood-filling from the image border never reaches those.
  You have to find enclosed regions too.
- **The character's own highlights look like checker.** Eye whites, teeth,
  glasses shine — all bright and low-saturation, same as the checker. Deleting
  every bright pixel eats her face. What distinguishes them: checker blobs
  contain *both* tones (white and grey); a highlight is one tone.
- **There may be more than two tones.** If the image was ever resized or
  re-compressed, the checkerboard blends into extra intermediate greys. Ours
  had three: 255, 204, and a blended ~188 tier. Histogram the low-saturation
  pixels inside the character — real art shows peaks, checker shows a flat
  plateau across dozens of luminance levels.
- **Hard edges leave a halo.** Cutting a binary alpha out of a light background
  leaves a bright rim. Estimate partial coverage at the edges and un-blend the
  background colour back out of those pixels.

**Save yourself all of it: ask for a real transparent PNG, and verify `mode`
is `RGBA` before you start.** Everything above is reconstructing information
that was destroyed when the checkerboard got flattened.

## Sheet layout

If you generate a sheet with several poses in a row, **leave generous space
between them**. If the figures touch — even just hair overlapping — they form
one connected blob and can't be cut apart without slicing someone's hair off.

Labels under the poses are fine; they're small enough to filter out by area.

## Sanity check

Before wiring them in:

```python
from PIL import Image
import numpy as np

names = ["walk_contact", "walk_down", "walk_passing", "walk_up", "turn", "thumb"]
feet, heights = set(), set()
for n in names:
    a = np.array(Image.open(f"sprites/{n}.png").convert("RGBA"))
    m = a[:, :, 3] > 0
    feet.add(np.where(m.any(1))[0].max())
    heights.add(a.shape[0])
    print(f"{n:14s} {a.shape[1]}x{a.shape[0]}  opaque={m.sum()}")

print("foot rows:", feet, "(want one value)")
print("heights  :", heights, "(want one value)")
```

Both sets should have exactly one value. If not, re-anchor: crop each frame to
its content, then paste onto a shared canvas with the feet on a fixed row.
