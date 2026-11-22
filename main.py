#!/usr/bin/env python3
"""news-image-20261122 -- "Baltic Blaze".

Renders a one-page newspaper front page summing up Sunday 22 November
2026 world news. Pure Python standard library, no network, no clock, no
randomness: two runs write byte-identical PNGs.

Usage: MAKEFUN_OUTPUT_DIR=out python3 main.py   (writes out/entry.png)
       python3 main.py                          (writes /output/entry.png)
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (248, 244, 233)
INK = (24, 24, 24)
RED = (168, 28, 28)
BLUE = (30, 58, 96)
GREY = (118, 114, 106)
LIGHT = (233, 227, 213)
DARK = (30, 30, 30)
GOLD = (178, 126, 22)
TEAL = (18, 96, 92)

# 5x7 bitmap font. Every glyph is seven row bitmasks, bit 4 = leftmost
# column, bit 0 = rightmost. A set bit paints one cell.
FONT = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ".": (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ",": (0, 0, 0, 0, 0b01100, 0b01000, 0b10000),
    ":": (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ";": (0, 0b01100, 0b01100, 0, 0b01100, 0b01000, 0b10000),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    "-": (0, 0, 0, 0b01110, 0, 0, 0),
    "!": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    "?": (0b01110, 0b10001, 0b00001, 0b00100, 0b00100, 0, 0b00100),
    "%": (0b11001, 0b11010, 0b00001, 0b00100, 0b00100, 0b01010, 0b10011),
    "(": (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ")": (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    "/": (0b00001, 0b00100, 0b00100, 0b00100, 0b01000, 0b01000, 0b10000),
    "&": (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "+": (0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    "=": (0, 0, 0b11111, 0, 0b11111, 0, 0),
    '"': (0b01010, 0b01010, 0, 0, 0, 0, 0),
    "$": (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    "#": (0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010),
    "*": (0, 0b10101, 0b01110, 0b10101, 0, 0, 0),
    "_": (0, 0, 0, 0, 0, 0, 0b11111),
    "@": (0b01110, 0b10001, 0b10111, 0b10101, 0b10110, 0b10000, 0b01110),
    " ": (0, 0, 0, 0, 0, 0, 0),
}


class Sheet:
    """Tiny RGB rasteriser: dots, boxes, segments, discs, bitmap text."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def dot(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(col)

    def box(self, ax, ay, bx, by, col):
        ax, ay = max(0, ax), max(0, ay)
        bx, by = min(self.w, bx), min(self.h, by)
        for yy in range(ay, by):
            start = (yy * self.w + ax) * 3
            span = bytes(col) * (bx - ax)
            self.buf[start:start + len(span)] = span

    def frame(self, ax, ay, bx, by, col, t=1):
        self.box(ax, ay, bx, ay + t, col)
        self.box(ax, by - t, bx, by, col)
        self.box(ax, ay, ax + t, by, col)
        self.box(bx - t, ay, bx, by, col)

    def hline(self, ax, bx, y, col, t=1):
        self.box(ax, y, bx, y + t, col)

    def vline(self, x, ay, by, col, t=1):
        self.box(x, ay, x + t, by, col)

    def seg(self, ax, ay, bx, by, col):
        # Bresenham.
        dx = abs(bx - ax)
        dy = -abs(by - ay)
        sx = 1 if ax < bx else -1
        sy = 1 if ay < by else -1
        err = dx + dy
        while True:
            self.dot(ax, ay, col)
            if ax == bx and ay == by:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                ax += sx
            if e2 <= dx:
                err += dx
                ay += sy

    def disc(self, cx, cy, r, col, solid=False):
        if solid:
            for yy in range(-r, r + 1):
                half = int((r * r - yy * yy) ** 0.5)
                self.box(cx - half, cy + yy, cx + half + 1, cy + yy + 1, col)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                           (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.dot(px, py, col)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def arc(self, cx, cy, r, a0, a1, col):
        n = max(8, int(r * 1.2))
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            self.dot(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), col)

    def glyph(self, x, y, ch, col, s=1):
        rows = FONT.get(ch, FONT[" "])
        for gy, bits in enumerate(rows):
            for gx in range(5):
                if (bits >> (4 - gx)) & 1:
                    self.box(x + gx * s, y + gy * s,
                             x + (gx + 1) * s, y + (gy + 1) * s, col)

    def text(self, x, y, s, col, scale=1):
        s = s.upper()
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, col, scale)
            cx += 6 * scale
        return cx

    def measure(self, s, scale=1):
        return len(s) * 6 * scale - scale

    def centred(self, y, s, col, scale=1, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        w = self.measure(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, col, scale)

    def wrap(self, s, maxw, scale=1):
        words = s.upper().split(" ")
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.measure(trial, scale) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, col, scale, maxw, leading=None):
        if leading is None:
            leading = 9 * scale + 2
        for line in self.wrap(s, maxw, scale):
            self.text(x, y, line, col, scale)
            y += leading
        return y


def save_png(path, sheet):
    rows = bytearray()
    step = sheet.w * 3
    for yy in range(sheet.h):
        rows.append(0)
        rows += sheet.buf[yy * step:(yy + 1) * step]
    blob = zlib.compress(bytes(rows), 9)

    def part(tag, payload):
        head = struct.pack(">I", len(payload)) + tag + payload
        return head + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", sheet.w, sheet.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += part(b"IHDR", ihdr)
    png += part(b"IDAT", blob)
    png += part(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------------------
# Pictograms: one small geometric drawing per story.
# ---------------------------------------------------------------------------

def draw_ship(cv, x, y, col):
    # Hull, wheelhouse, mast with pennant, flame tongues, sea lines.
    cv.seg(x, y + 34, x + 66, y + 34, col)
    cv.seg(x, y + 34, x + 8, y + 46, col)
    cv.seg(x + 66, y + 34, x + 58, y + 46, col)
    cv.seg(x + 8, y + 46, x + 58, y + 46, col)
    cv.box(x + 40, y + 16, x + 56, y + 34, col)
    cv.vline(x + 18, y + 6, y + 34, col, 2)
    cv.box(x + 20, y + 8, x + 34, y + 14, RED)
    for off, tall in ((-6, 12), (0, 18), (6, 12)):
        cv.seg(x + 48 + off, y + 12, x + 48 + off, y + 12 - tall, RED)
    cv.seg(x - 4, y + 54, x + 70, y + 54, BLUE)
    cv.seg(x + 2, y + 60, x + 64, y + 60, BLUE)


def draw_globe(cv, x, y, r, col):
    cv.disc(x, y, r, col)
    cv.arc(x, y, r - 2, -1.2, 1.2, col)
    cv.arc(x, y, r - 2, 1.9, 4.3, col)
    cv.hline(x - r, x + r, y, col)
    cv.arc(x, y, r // 2, -1.57, 1.57, col)
    cv.arc(x, y, r // 2, 1.57, 4.71, col)
    cv.seg(x - r + 6, y - r + 8, x + r - 8, y + r - 6, col)


def draw_tanker(cv, x, y, col):
    cv.box(x, y + 26, x + 66, y + 40, col)
    cv.box(x + 46, y + 12, x + 58, y + 26, col)
    for ax, ay, bx, by in ((8, 8, 20, 20), (20, 8, 8, 20),
                           (28, 8, 40, 20), (40, 8, 28, 20)):
        cv.seg(x + ax, y + ay, x + bx, y + by, RED)
    for k in range(3):
        yy = y + 48 + k * 6
        cv.seg(x + k * 8, yy, x + 22 + k * 8, yy, BLUE)
        cv.seg(x + 34 + k * 6, yy, x + 56 + k * 6, yy, BLUE)


def draw_flags(cv, x, y, col):
    # Two crossed poles with pennants, on a shared base line.
    cv.seg(x + 8, y + 44, x + 30, y + 4, col)
    cv.seg(x + 58, y + 44, x + 36, y + 4, col)
    cv.box(x + 30, y + 4, x + 52, y + 14, RED)
    cv.box(x + 14, y + 4, x + 36, y + 14, BLUE)
    cv.hline(x + 4, x + 62, y + 46, col, 2)


def draw_target(cv, x, y, r, col):
    cv.disc(x, y, r, col)
    cv.disc(x, y, r - 10, col)
    cv.disc(x, y, r - 20, RED, solid=True)
    cv.seg(x - r - 8, y, x + r + 8, y, col)
    cv.seg(x, y - r - 8, x, y + r + 8, col)


def draw_mic(cv, x, y, col):
    cv.disc(x + 20, y + 14, 12, col)
    cv.box(x + 14, y + 12, x + 26, y + 30, col)
    cv.arc(x + 20, y + 22, 16, 0.3, 2.8, col)
    cv.vline(x + 20, y + 38, y + 48, col, 2)
    cv.hline(x + 10, x + 30, y + 48, col, 2)


def draw_ballot(cv, x, y, col):
    cv.box(x + 6, y + 18, x + 60, y + 52, col)
    cv.box(x + 6, y + 18, x + 60, y + 26, LIGHT)
    cv.frame(x + 6, y + 18, x + 60, y + 52, col, 2)
    cv.box(x + 28, y + 10, x + 38, y + 18, PAPER)
    cv.seg(x + 18, y + 2, x + 30, y + 16, RED)
    cv.seg(x + 30, y + 16, x + 48, y - 6, RED)
    cv.text(x + 14, y + 32, "VOTE", PAPER, 1)


def draw_bridge(cv, x, y, col):
    cv.seg(x, y + 40, x + 66, y + 40, col)
    cv.seg(x + 6, y + 40, x + 20, y + 8, col)
    cv.seg(x + 60, y + 40, x + 46, y + 8, col)
    cv.vline(x + 20, y + 8, y + 40, col, 2)
    cv.vline(x + 46, y + 8, y + 40, col, 2)
    cv.seg(x + 20, y + 8, x + 46, y + 8, col)
    for bx in (26, 33, 40):
        cv.vline(x + bx, y + 14, y + 40, col, 1)
    cv.seg(x + 2, y + 50, x + 64, y + 50, TEAL)
    cv.seg(x + 8, y + 56, x + 58, y + 56, TEAL)


def draw_pic(cv, kind, x, y, col):
    if kind == "ship":
        draw_ship(cv, x, y, col)
    elif kind == "globe":
        draw_globe(cv, x + 30, y + 30, 28, col)
    elif kind == "tanker":
        draw_tanker(cv, x, y, col)
    elif kind == "flags":
        draw_flags(cv, x, y, col)
    elif kind == "target":
        draw_target(cv, x + 32, y + 30, 26, col)
    elif kind == "mic":
        draw_mic(cv, x + 12, y + 6, col)
    elif kind == "ballot":
        draw_ballot(cv, x, y + 4, col)
    elif kind == "bridge":
        draw_bridge(cv, x, y + 6, col)


# ---------------------------------------------------------------------------
# Stories: all verified against reporting dated 22 November 2026.
# ---------------------------------------------------------------------------

STORIES = [
    # (kicker, headline, deck, pictogram)
    ("BALTIC SEA - GULF OF FINLAND",
     "DRONES SET RUSSIAN CARGO SHIP ABLAZE; IT DRIFTS INTO FINNISH WATERS",
     "The Sparta II, bound for Kaliningrad, was hit by two drones and "
     "caught fire. Its 16 crew escaped by lifeboat as Helsinki imposed "
     "air and sea curbs and said Ukraine was likely behind the attack.",
     "ship"),
    ("CLIMATE - ANTALYA, TURKIYE",
     "COP31 STILL DEADLOCKED AS TALKS RUN INTO SUNDAY",
     "No final agreement yet as negotiators haggle over fossil fuels. "
     "The closing plenary was suspended and a third draft is due after "
     "overnight talks.",
     "globe"),
    ("GULF - STRAIT OF HORMUZ",
     "TANKERS HIT OFF OMAN AS GULF TENSIONS FLARE",
     "Multiple tankers were hit off the Oman coast. Bahrain is probing "
     "a Patriot interceptor crash amid reports of Iranian drone attacks.",
     "tanker"),
    ("DEFENCE - WASHINGTON",
     "PENTAGON CURBS US-CANADA MILITARY TIES",
     "Defence chief Hegseth set fresh boundaries, telling US service "
     "members to curb informal gatherings with Canadian counterparts.",
     "flags"),
    ("EUROPE - COPENHAGEN",
     "DENMARK ACCUSES RUSSIA OF ASSASSINATION PLOT",
     "Copenhagen says Moscow plotted to kill a US-Ukrainian rapper in "
     "Denmark. An EU leader called the allegation unacceptable.",
     "target"),
    ("WAR IN UKRAINE - KYIV",
     "ZELENSKY CALLS PUTIN A 'KILLER' AFTER TRUMP PRAISES HIM",
     "The Ukrainian president called strikes on the Crimean Bridge a "
     "fair response after Trump called the Russian leader a friend.",
     "mic"),
    ("SOUTH AFRICA",
     "ANC FIGHTS TO HOLD ITS CITIES AS SOUTH AFRICA VOTES",
     "Voters cast ballots in local elections after the ruling party's "
     "setback. Control of the big metros is on the line.",
     "ballot"),
    ("INDIA - BIHAR",
     "MODI OPENS NITISH SETU AS CYCLONE AKVAN DISRUPTS FLIGHTS",
     "The new bridge links Patna and Vaishali. The storm forced 14 "
     "flights to be cancelled at Ranchi airport.",
     "bridge"),
]


def panel(cv, ax, ay, bx, by, story, hs=2, ds=1):
    kicker, headline, deck, pic = story
    cv.frame(ax, ay, bx, by, GREY)
    ix, iy = bx - 92, ay + 14
    draw_pic(cv, pic, ix, iy, BLUE)
    col_w = (ix - 8) - (ax + 12)
    yy = ay + 12
    cv.text(ax + 12, yy, kicker, RED, 1)
    yy += 14
    for line in cv.wrap(headline, col_w, hs):
        cv.text(ax + 12, yy, line, INK, hs)
        yy += 9 * hs + 2
    yy += 4
    # The deck wraps inside the text column too, so it never runs under
    # the pictogram in the panel's top-right corner.
    cv.para(ax + 12, yy, deck, INK, ds, col_w)


def compose():
    cv = Sheet(W, H, PAPER)
    # Masthead.
    cv.centred(26, "THE WORLD IN ONE PAGE", INK, 4)
    cv.hline(24, 1000, 78, INK, 2)
    cv.centred(88, "SUNDAY, 22 NOVEMBER 2026", RED, 2)
    cv.centred(112, "THE DAY'S NEWS - AS REPORTED TODAY", GREY, 1)
    cv.hline(24, 1000, 134, RED, 3)
    # Lead story, full width.
    panel(cv, 24, 146, 1000, 322, STORIES[0], hs=3, ds=2)
    # Row two: two panels.
    panel(cv, 24, 334, 506, 514, STORIES[1])
    panel(cv, 518, 334, 1000, 514, STORIES[2])
    # Row three: two panels.
    panel(cv, 24, 526, 506, 706, STORIES[3])
    panel(cv, 518, 526, 1000, 706, STORIES[4])
    # Row four: three panels.
    panel(cv, 24, 718, 348, 884, STORIES[5])
    panel(cv, 360, 718, 684, 884, STORIES[6])
    panel(cv, 696, 718, 1000, 884, STORIES[7])
    # Tonight strip.
    cv.box(24, 896, 1000, 950, DARK)
    cv.text(40, 912, "TONIGHT: LAS VEGAS GP UNDER THE LIGHTS - NORRIS ON POLE, "
            "VERSTAPPEN 2ND", PAPER, 1)
    cv.text(40, 928, "AUSTRALIA END ENGLAND'S SEVEN-MATCH T20 WINNING STREAK",
            PAPER, 1)
    # Footer.
    cv.hline(24, 1000, 962, GREY)
    cv.centred(972, "SOURCES: REUTERS, CNN, BBC, TIMES OF INDIA - "
               "ALL STORIES AS REPORTED ON 22 NOVEMBER 2026", GREY, 1)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = save_png(path, compose())
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
