#!/usr/bin/env python3
"""
Encourager (PyQt6) - a pixel friend walks across the bottom of your screen
every 30 minutes, gives a thumbs up, tells you you're doing amazing, waits,
and walks back out.

macOS. Requires Python 3 and PyQt6.

    pip3 install PyQt6
    python3 encourager_qt.py

Quit: Ctrl+C in the Terminal, or click her and press Escape.
"""

import os
import sys

from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import (QPixmap, QPainter, QColor, QFont, QPainterPath,
                         QTransform, QRegion, QFontMetrics)
from PyQt6.QtWidgets import QApplication, QWidget


# ------------------------------------------------------------------ config
INTERVAL_MIN   = 30                       # minutes between visits
MESSAGE        = "You are doing amazing"

STAY_SECONDS   = 25                       # how long she stands there
BODY_HEIGHT    = 130                      # her height on screen, in points
STOP_AT        = 0.25                     # where she stops, as a fraction of
                                          # screen width. 0.25 = one quarter in.
WALK_MS        = 90                       # ms per walk frame
WALK_PX_FRAME  = 36                       # px moved per frame. Keeps her stride
                                          # natural no matter where she stops.
FLOOR_OFFSET   = 100                      # px above the bottom of the screen
VERBOSE        = True                     # print what she's doing to the Terminal

HERE    = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(HERE, "sprites")
WALK_CYCLE = ["walk_contact", "walk_down", "walk_passing", "walk_up"]

BUBBLE_FONT_PT = 15
BUBBLE_PAD     = 12
BUBBLE_GAP     = 14                       # space between her head and the bubble


class Encourager(QWidget):
    def __init__(self):
        super().__init__()

        # ---- frameless, always on top, genuinely translucent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool                 # no Dock icon, no Space switching
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # A Qt.Tool window on macOS hides when its app loses focus. This keeps
        # her on screen when you click into another app.
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

        self.frames = self._load()
        self.sprite_w = max(p.width() for p in self.frames.values())
        self.sprite_h = self.frames["turn"].height()

        screen = QApplication.primaryScreen().geometry()
        self.sw, self.sh = screen.width(), screen.height()
        self.home_x = int(self.sw * STOP_AT)

        # the window holds the sprite plus the bubble above it
        self._measure_bubble()
        self.win_w = max(self.sprite_w, self.bubble_w) + 20
        self.win_h = self.sprite_h + self.bubble_h + BUBBLE_GAP + 10

        self.resize(self.win_w, self.win_h)

        self.current = "turn"
        self.show_bubble = False
        distance = self.home_x + self.win_w        # from offscreen to home
        self.steps = max(8, int(round(distance / float(WALK_PX_FRAME))))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        self.next_timer = QTimer(self)
        self.next_timer.setSingleShot(True)
        self.next_timer.timeout.connect(self.visit)

        self.stay_timer = QTimer(self)
        self.stay_timer.setSingleShot(True)
        self.stay_timer.timeout.connect(self._start_walk_out)

        self.hide()

    # ------------------------------------------------------------ sprites
    def _load(self):
        if not os.path.isdir(SPRITES):
            sys.exit("Can't find sprites_soft next to this script:\n  %s" % SPRITES)

        raw = {}
        for name in WALK_CYCLE + ["turn", "thumb"]:
            path = os.path.join(SPRITES, name + ".png")
            if not os.path.exists(path):
                sys.exit("Missing sprite: %s" % path)
            pm = QPixmap(path)
            if pm.isNull():
                sys.exit("Could not read sprite: %s" % path)
            raw[name] = pm

        # scale so her BODY (not the padded canvas) is BODY_HEIGHT tall.
        # The PNG canvas has empty rows above her head and below her feet;
        # scaling by canvas height would render her noticeably short.
        body_px = QRegion(raw["thumb"].mask()).boundingRect().height()
        if body_px <= 0:
            body_px = raw["thumb"].height()
        factor = BODY_HEIGHT / float(body_px)

        frames = {}
        for name, pm in raw.items():
            w = max(1, int(round(pm.width() * factor)))
            h = max(1, int(round(pm.height() * factor)))
            frames[name] = pm.scaled(
                w, h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation)

        for name in WALK_CYCLE:
            frames[name + "_flip"] = frames[name].transformed(
                QTransform().scale(-1, 1))
        return frames

    # ------------------------------------------------------------ bubble
    def _measure_bubble(self):
        f = QFont("Helvetica", BUBBLE_FONT_PT)
        f.setBold(True)
        self.bubble_font = f
        fm = QFontMetrics(f)
        r = fm.boundingRect(MESSAGE)
        self.text_w, self.text_h = r.width(), r.height()
        self.bubble_w = self.text_w + BUBBLE_PAD * 2 + 6
        self.bubble_h = self.text_h + BUBBLE_PAD * 2 + 12   # +tail

    # ------------------------------------------------------------ paint
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pm = self.frames[self.current]
        sx = (self.win_w - pm.width()) // 2
        sy = self.win_h - pm.height()
        p.drawPixmap(sx, sy, pm)

        if self.show_bubble:
            self._paint_bubble(p)
        p.end()

    def _paint_bubble(self, p):
        bw, bh = self.bubble_w, self.bubble_h - 12
        bx = (self.win_w - bw) // 2
        by = 4

        path = QPainterPath()
        path.addRoundedRect(QRectF(bx, by, bw, bh), 10, 10)

        cx = self.win_w // 2
        tail = QPainterPath()
        tail.moveTo(cx - 9, by + bh)
        tail.lineTo(cx + 9, by + bh)
        tail.lineTo(cx, by + bh + 12)
        tail.closeSubpath()
        path = path.united(tail)

        p.setPen(QColor("#1c1c1c"))
        p.setBrush(QColor("#ffffff"))
        p.drawPath(path)

        p.setFont(self.bubble_font)
        p.setPen(QColor("#1c1c1c"))
        p.drawText(QRectF(bx, by, bw, bh),
                   Qt.AlignmentFlag.AlignCenter, MESSAGE)

    # ------------------------------------------------------------ motion
    def _place(self, cx):
        """Move the WINDOW, so nothing ever needs repainting behind her."""
        x = int(cx - self.win_w / 2)
        y = self.sh - FLOOR_OFFSET - self.win_h + 10
        self.move(QPoint(x, y))

    def _log(self, msg):
        if VERBOSE:
            print("[encourager] %s" % msg, flush=True)

    def _schedule_next(self):
        # QTimer.start() requires an int. INTERVAL_MIN = 1.0 or 0.5 would
        # otherwise raise TypeError and she would never come back.
        ms = int(round(INTERVAL_MIN * 60 * 1000))
        self.next_timer.start(ms)
        self._log("gone. next visit in %.2f min (%d ms)" % (INTERVAL_MIN, ms))

    def visit(self):
        self._log("walking in")
        self.phase = "in"
        self.step = 0
        self.show_bubble = False
        self.show()
        self.raise_()
        self.timer.start(int(WALK_MS))

    def _tick(self):
        start = -self.win_w
        home = self.home_x

        if self.phase == "in":
            if self.step >= self.steps:
                self.timer.stop()
                self.current = "turn"
                self._place(home)
                self.update()
                QTimer.singleShot(220, self._arrive)
                return
            t = self.step / float(self.steps - 1)
            cx = start + t * (home - start)
            self.current = WALK_CYCLE[self.step % 4]
            self._place(cx)
            self.update()
            self.step += 1

        elif self.phase == "out":
            if self.step >= self.steps:
                self.timer.stop()
                self.hide()
                self._schedule_next()
                return
            t = self.step / float(self.steps - 1)
            cx = home + t * (start - home)
            self.current = WALK_CYCLE[self.step % 4] + "_flip"
            self._place(cx)
            self.update()
            self.step += 1

    def _arrive(self):
        self._log("arrived, staying %s s" % STAY_SECONDS)
        self.current = "thumb"
        self.show_bubble = True
        self.update()
        self.stay_timer.start(int(round(STAY_SECONDS * 1000)))

    def _start_walk_out(self):
        self._log("walking out")
        self.show_bubble = False
        self.current = "turn"
        self.update()
        self.phase = "out"
        self.step = 0
        QTimer.singleShot(220, lambda: self.timer.start(int(WALK_MS)))

    # ------------------------------------------------------------ misc
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            QApplication.quit()


def _set_accessory_policy():
    """Make this an 'accessory' app on macOS.

    A normal app's Tool windows hide when the app is deactivated (i.e. when you
    click another app) - that's what made her vanish. Accessory apps (like
    menu-bar utilities) have no such behaviour and stay on screen. Needs pyobjc,
    which is why we try/except: if it's missing she still runs, just with the
    old hide-on-click behaviour.
    """
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory)
        return True
    except Exception:
        return False


def main():
    global INTERVAL_MIN, STAY_SECONDS
    args = sys.argv[1:]
    for flag, name in (("--every", "INTERVAL_MIN"), ("--stay", "STAY_SECONDS")):
        if flag in args:
            try:
                globals()[name] = float(args[args.index(flag) + 1])
            except (IndexError, ValueError):
                sys.exit("%s needs a number, e.g. %s 1" % (flag, flag))

    print("[encourager] running: %s" % os.path.abspath(__file__), flush=True)
    print("[encourager] every %.2f min, stays %.0f s"
          % (INTERVAL_MIN, STAY_SECONDS), flush=True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if _set_accessory_policy():
        print("[encourager] accessory mode on - stays visible when you click away",
              flush=True)
    else:
        print("[encourager] NOTE: pyobjc not found, she'll hide when you click "
              "another app.\n"
              "             Fix:  pip3 install pyobjc-framework-Cocoa",
              flush=True)

    w = Encourager()
    QTimer.singleShot(600, w.visit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
