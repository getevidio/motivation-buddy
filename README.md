# Encourager

A pixel version of you walks in from the edge of your screen every 30 minutes,
gives a thumbs up, tells you you're doing amazing, and walks back out.

macOS. Transparent background, no window chrome, stays visible while you work.

![demo](docs/demo.gif)

---

## Install

You need Python 3. If `python3 --version` in Terminal doesn't print `3.10` or
higher, get it from [python.org/downloads](https://www.python.org/downloads/).

```sh
git clone https://github.com/YOUR-USERNAME/encourager.git
cd encourager
pip3 install -r requirements.txt
python3 encourager.py
```

She should walk in within a second.

**Both packages matter.** `PyQt6` draws her. `pyobjc-framework-Cocoa` is what
keeps her on screen when you click into another app — without it she vanishes
the moment the Terminal loses focus. The app tells you at startup which mode
it's in:

```
[encourager] accessory mode on - stays visible when you click away
```

If you instead see a `NOTE: pyobjc not found`, install that second package.

Quit with `Ctrl+C` in the Terminal.

---

## Start her automatically

Right now she only runs while that Terminal window is open. To have her start
when your Mac does:

```sh
sh install.sh
```

That detects your Python path and folder location, and writes a `start.command`
launcher. Then:

1. Double-click `start.command` in Finder to test it
2. **System Settings → General → Login Items**
3. Click **＋** under "Open at Login"
4. Pick `start.command` from this folder

Done. She starts on her own from now on.

Two caveats:

- A small Terminal window opens in the background and stays open while she
  runs. That's what keeps her alive. Minimise and ignore it.
- If you move or rename this folder, the login item breaks. Remove the old
  entry, run `sh install.sh` again, and re-add it.

---

## Settings

All at the top of `encourager.py`:

| Setting | Default | What it does |
|---|---|---|
| `INTERVAL_MIN` | `30` | Minutes between visits |
| `MESSAGE` | `"You are doing amazing"` | What the speech bubble says |
| `STAY_SECONDS` | `25` | How long she stands there |
| `BODY_HEIGHT` | `130` | Her height on screen, in points. Dock icons are ~64 |
| `STOP_AT` | `0.25` | Where she stops, as a fraction of screen width |
| `WALK_PX_FRAME` | `36` | Her stride. Higher = faster |
| `FLOOR_OFFSET` | `100` | How far above the bottom of the screen she stands |
| `VERBOSE` | `True` | Print what she's doing to the Terminal |

To test without editing the file:

```sh
python3 encourager.py --every 1 --stay 5
```

---

## Use your own character

See **[docs/SPRITES.md](docs/SPRITES.md)** for the full guide, including the
gotchas that will bite you if you generate sprites with AI.

Short version: you need six PNGs in `sprites/`, all the same height, with the
character's feet on the same row in every one:

```
sprites/
  walk_contact.png    foot planted, legs apart
  walk_down.png       body at its lowest
  walk_passing.png    legs together, body highest
  walk_up.png         pushing off
  turn.png            3/4 view, mid-turn
  thumb.png           facing viewer, thumbs up
```

Facing **right**. Real transparency (an actual alpha channel — not a
checkerboard pattern drawn into the pixels). The script mirrors the walk frames
itself for the walk-out.

---

## How it works

- **Transparency**: PyQt6's `WA_TranslucentBackground` gives real per-pixel
  alpha on macOS. Tkinter can't do this — its `-transparentcolor` is
  Windows-only and silently does nothing on a Mac.
- **No ghost trail**: the window is only as big as she is, and *the window
  itself moves* across the screen. Nothing needs repainting behind her.
- **Staying visible**: the app sets its macOS activation policy to
  `accessory` (the category menu-bar utilities use), so it has no
  hide-on-deactivate behaviour.

---

## Licence

MIT. The sprite art is mine — swap in your own.
