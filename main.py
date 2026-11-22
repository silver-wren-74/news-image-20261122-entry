#!/usr/bin/env python3
"""news-image-20261122 -- "Baltic Blaze".

Draws a one-page newspaper front page summing up Sunday 22 November
2026 world news, using only the Python standard library. The render is
deterministic (no clock, no randomness, no network): two runs produce
byte-identical output.

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

# 5x7 bitmap font: 7 rows of 5 bits, '#' = on.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".#...", "#...."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".#...", "#...."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.#.", "#..##"),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "*": (".....", "#.#.#", ".###.", "#.#.#", ".....", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.##.", "#....", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


class Canvas:
    """Minimal RGB rasteriser: pixels, rects, lines, circles, bitmap text."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            row = bytes(color) * (x1 - x0)
            self.px[base:base + len(row)] = row

    def rect(self, x0, y0, x1, y1, color, t=1):
        self.fill(x0, y0, x1, y0 + t, color)
        self.fill(x0, y1 - t, x1, y1, color)
        self.fill(x0, y0, x0 + t, y1, color)
        self.fill(x1 - t, y0, x1, y1, color)

    def hline(self, x0, x1, y, color, t=1):
        self.fill(x0, y, x1, y + t, color)

    def vline(self, x, y0, y1, color, t=1):
        self.fill(x, y0, x + t, y1, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        if fill:
            for y in range(-r, r + 1):
                half = int((r * r - y * y) ** 0.5)
                self.fill(cx - half, cy + y, cx + half + 1, cy + y + 1, color)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                           (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.put(px, py, color)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def arc(self, cx, cy, r, a0, a1, color):
        steps = max(8, int(r * 1.2))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.put(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), color)

    def text(self, x, y, s, color, scale=1):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit in ("1", "#"):
                        self.fill(cx + gx * scale, y + gy * scale,
                                  cx + (gx + 1) * scale, y + (gy + 1) * scale,
                                  color)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale=1):
        return len(s) * 6 * scale - scale

    def text_center(self, y, s, color, scale=1, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, color, scale)

    def wrap(self, s, max_w, scale=1):
        words = s.upper().split(" ")
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, color, scale, max_w, leading=None):
        if leading is None:
            leading = 9 * scale + 2
        for line in self.wrap(s, max_w, scale):
            self.text(x, y, line, color, scale)
            y += leading
        return y


def write_png(path, canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------------------
# Pictograms: small geometric drawings, one per story.
# ---------------------------------------------------------------------------

def pic_ship(c, x, y, color):
    # Hull, bridge, mast, and flame tongues above the deck.
    c.line(x, y + 34, x + 66, y + 34, color)
    c.line(x, y + 34, x + 8, y + 46, color)
    c.line(x + 66, y + 34, x + 58, y + 46, color)
    c.line(x + 8, y + 46, x + 58, y + 46, color)
    c.fill(x + 40, y + 16, x + 56, y + 34, color)
    c.vline(x + 18, y + 6, y + 34, color, 2)
    c.fill(x + 20, y + 8, x + 34, y + 14, RED)
    for dx, hgt in ((-6, 12), (0, 18), (6, 12)):
        c.line(x + 48 + dx, y + 12, x + 48 + dx, y + 12 - hgt, RED)
    c.line(x - 4, y + 54, x + 70, y + 54, BLUE)
    c.line(x + 2, y + 60, x + 64, y + 60, BLUE)


def pic_globe(c, x, y, r, color):
    c.circle(x, y, r, color)
    c.arc(x, y, r - 2, -1.2, 1.2, color)
    c.arc(x, y, r - 2, 1.9, 4.3, color)
    c.hline(x - r, x + r, y, color)
    c.arc(x, y, r // 2, -1.57, 1.57, color)
    c.arc(x, y, r // 2, 1.57, 4.71, color)
    c.line(x - r + 6, y - r + 8, x + r - 8, y + r - 6, color)


def pic_tanker(c, x, y, color):
    c.fill(x, y + 26, x + 66, y + 40, color)
    c.fill(x + 46, y + 12, x + 58, y + 26, color)
    c.line(x + 8, y + 8, x + 20, y + 20, RED)
    c.line(x + 20, y + 8, x + 8, y + 20, RED)
    c.line(x + 28, y + 8, x + 40, y + 20, RED)
    c.line(x + 40, y + 8, x + 28, y + 20, RED)
    for k in range(3):
        yy = y + 48 + k * 6
        c.line(x + k * 8, yy, x + 22 + k * 8, yy, BLUE)
        c.line(x + 34 + k * 6, yy, x + 56 + k * 6, yy, BLUE)


def pic_flags(c, x, y, color):
    # Two crossed flagpoles with small pennants.
    c.line(x + 8, y + 44, x + 30, y + 4, color)
    c.line(x + 58, y + 44, x + 36, y + 4, color)
    c.fill(x + 30, y + 4, x + 52, y + 14, RED)
    c.fill(x + 14, y + 4, x + 36, y + 14, BLUE)
    c.hline(x + 4, x + 62, y + 46, color, 2)


def pic_target(c, x, y, r, color):
    c.circle(x, y, r, color)
    c.circle(x, y, r - 10, color)
    c.circle(x, y, r - 20, RED, fill=True)
    c.line(x - r - 8, y, x + r + 8, y, color)
    c.line(x, y - r - 8, x, y + r + 8, color)


def pic_mic(c, x, y, color):
    c.circle(x + 20, y + 14, 12, color)
    c.fill(x + 14, y + 12, x + 26, y + 30, color)
    c.arc(x + 20, y + 22, 16, 0.3, 2.8, color)
    c.vline(x + 20, y + 38, y + 48, color, 2)
    c.hline(x + 10, x + 30, y + 48, color, 2)


def pic_ballot(c, x, y, color):
    c.fill(x + 6, y + 18, x + 60, y + 52, color)
    c.fill(x + 6, y + 18, x + 60, y + 26, LIGHT)
    c.rect(x + 6, y + 18, x + 60, y + 52, color, 2)
    c.fill(x + 28, y + 10, x + 38, y + 18, PAPER)
    c.line(x + 18, y + 2, x + 30, y + 16, RED)
    c.line(x + 30, y + 16, x + 48, y - 6, RED)
    c.text(x + 14, y + 32, "VOTE", PAPER, 1)


def pic_bridge(c, x, y, color):
    c.line(x, y + 40, x + 66, y + 40, color)
    c.line(x + 6, y + 40, x + 20, y + 8, color)
    c.line(x + 60, y + 40, x + 46, y + 8, color)
    c.vline(x + 20, y + 8, y + 40, color, 2)
    c.vline(x + 46, y + 8, y + 40, color, 2)
    c.line(x + 20, y + 8, x + 46, y + 8, color)
    for bx in (26, 33, 40):
        c.vline(x + bx, y + 14, y + 40, color, 1)
    c.line(x + 2, y + 50, x + 64, y + 50, TEAL)
    c.line(x + 8, y + 56, x + 58, y + 56, TEAL)


PICS = {"ship": pic_ship, "globe": pic_globe, "tanker": pic_tanker,
        "flags": pic_flags, "target": pic_target, "mic": pic_mic,
        "ballot": pic_ballot, "bridge": pic_bridge}


def draw_pic(c, kind, x, y, color):
    if kind == "ship":
        pic_ship(c, x, y, color)
    elif kind == "globe":
        pic_globe(c, x + 30, y + 30, 28, color)
    elif kind == "tanker":
        pic_tanker(c, x, y, color)
    elif kind == "flags":
        pic_flags(c, x, y, color)
    elif kind == "target":
        pic_target(c, x + 32, y + 30, 26, color)
    elif kind == "mic":
        pic_mic(c, x + 12, y + 6, color)
    elif kind == "ballot":
        pic_ballot(c, x, y + 4, color)
    elif kind == "bridge":
        pic_bridge(c, x, y + 6, color)


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


def draw_panel(c, x0, y0, x1, y1, story, hscale=2, dscale=1):
    kicker, headline, deck, pic = story
    c.rect(x0, y0, x1, y1, GREY)
    ix = x1 - 92
    iy = y0 + 14
    draw_pic(c, pic, ix, iy, BLUE)
    text_w = (ix - 8) - (x0 + 12)
    y = y0 + 12
    c.text(x0 + 12, y, kicker, RED, 1)
    y += 14
    for line in c.wrap(headline, text_w, hscale):
        c.text(x0 + 12, y, line, INK, hscale)
        y += 9 * hscale + 2
    y += 4
    y = c.para(x0 + 12, y, deck, INK, dscale, text_w)


def draw_page():
    c = Canvas(W, H, PAPER)
    # Masthead.
    c.text_center(26, "THE WORLD IN ONE PAGE", INK, 4)
    c.hline(24, 1000, 78, INK, 2)
    c.text_center(88, "SUNDAY, 22 NOVEMBER 2026", RED, 2)
    c.text_center(112, "THE DAY'S NEWS - AS REPORTED TODAY", GREY, 1)
    c.hline(24, 1000, 134, RED, 3)
    # Lead story, full width.
    draw_panel(c, 24, 146, 1000, 322, STORIES[0], hscale=3, dscale=2)
    # Row two: two panels.
    draw_panel(c, 24, 334, 506, 514, STORIES[1])
    draw_panel(c, 518, 334, 1000, 514, STORIES[2])
    # Row three: two panels.
    draw_panel(c, 24, 526, 506, 706, STORIES[3])
    draw_panel(c, 518, 526, 1000, 706, STORIES[4])
    # Row four: three panels.
    draw_panel(c, 24, 718, 348, 884, STORIES[5])
    draw_panel(c, 360, 718, 684, 884, STORIES[6])
    draw_panel(c, 696, 718, 1000, 884, STORIES[7])
    # Tonight strip.
    c.fill(24, 896, 1000, 950, DARK)
    c.text(40, 912, "TONIGHT: LAS VEGAS GP UNDER THE LIGHTS - NORRIS ON POLE, "
            "VERSTAPPEN 2ND", PAPER, 1)
    c.text(40, 928, "AUSTRALIA END ENGLAND'S SEVEN-MATCH T20 WINNING STREAK",
            PAPER, 1)
    # Footer.
    c.hline(24, 1000, 962, GREY)
    c.text_center(972, "SOURCES: REUTERS, CNN, BBC, TIMES OF INDIA - "
                  "ALL STORIES AS REPORTED ON 22 NOVEMBER 2026", GREY, 1)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, draw_page())
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
