#!/usr/bin/env python3
"""news-image-20261120, variant 6: the day, hour by hour.

A vertical timeline of Friday 20 November 2026. One spine runs down
the middle of the page and seven stories are pinned to the part of
the day they broke: the overnight missile strikes on Ukraine, the
morning cyclone landfall in India, the Shenzhen summit aftermath,
Trump's Iran remarks, Myanmar's reply to the genocide ruling, the
afternoon market rout, and the evening earthquake in Peru.

Every story was checked against reporting dated 20 November 2026
before it was drawn. The program is pure Python stdlib, draws the
whole image procedurally, uses no network, and is deterministic.

Writes entry.png into MAKEFUN_OUTPUT_DIR (default /output).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
INK = (13, 20, 36)        # deep navy page
PANEL = (27, 39, 63)      # story card
PANEL_EDGE = (92, 104, 138)
CREAM = (244, 238, 220)   # main text
GOLD = (214, 178, 94)     # spine, rules, tags
RED = (206, 74, 60)       # lead accent
MUTE = (170, 180, 198)    # detail text
FAINT = (120, 130, 155)

# ------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, written as strings for readability.
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
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
}

BLANK = ("00000",) * 7


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px per char cell)."""
    return len(text) * 6 * scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns lines that fit max_width pixels."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    """A plain RGB pixel buffer with small shape helpers."""

    def __init__(self, w, h, color):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, color)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def rect(self, x, y, w, h, color, thick=1):
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line, with a square brush of the given thickness."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        half = thick // 2
        while True:
            self.fill_rect(x - half, y - half, thick, thick, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def polyline(self, points, color, thick=1):
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            self.line(ax, ay, bx, by, color, thick)

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.fill_rect(cx - half, yy, half * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            outer = int((r * r - dy * dy) ** 0.5)
            inner_sq = (r - thick) ** 2 - dy * dy
            inner = int(inner_sq ** 0.5) if inner_sq > 0 else 0
            self.fill_rect(cx - outer, yy, outer - inner, 1, color)
            self.fill_rect(cx + inner + 1, yy, outer - inner, 1, color)

    def draw_char(self, x, y, ch, scale, color):
        glyph = FONT.get(ch, BLANK)
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, color)

    def draw_text(self, x, y, text, scale, color, align="left"):
        if align == "center":
            x -= text_width(text, scale) // 2
        elif align == "right":
            x -= text_width(text, scale)
        for ch in text:
            self.draw_char(x, y, ch, scale, color)
            x += 6 * scale


# ------------------------------------------------------------------- PNG
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        start = y * cv.w * 3
        raw += cv.buf[start:start + cv.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ------------------------------------------------------------ node icons
# Small pictograms drawn inside the gold discs on the timeline spine.
# Each takes the canvas, the disc centre and the ink colour.

def icon_burst(cv, cx, cy, color):
    for k in range(8):
        ang = k * 3.14159265 / 4
        x2 = cx + int(13 * _cos(ang))
        y2 = cy + int(13 * _sin(ang))
        cv.line(cx, cy, x2, y2, color, 2)
    cv.disc(cx, cy, 4, color)


def _cos(a):
    # cos(a) = sin(a + 90 degrees), using the table below.
    return _SIN[(int(a * 180 / 3.14159265) + 90) % 360]


def _sin(a):
    return _SIN[int(a * 180 / 3.14159265) % 360]


# sine table, one entry per degree, built once at import time.
_SIN = []
for _deg in range(360):
    _rad = _deg * 3.141592653589793 / 180.0
    _s, _term, _n = 0.0, _rad, 1
    while abs(_term) > 1e-12:
        _s += _term
        _term *= -_rad * _rad / ((2 * _n) * (2 * _n + 1))
        _n += 1
    _SIN.append(_s)


def icon_cyclone(cv, cx, cy, color):
    for r in (4, 8, 12):
        cv.ring(cx, cy, r, color, 2)
    cv.line(cx - 12, cy, cx + 12, cy, color, 2)
    cv.line(cx, cy - 12, cx, cy + 12, color, 2)


def icon_summit(cv, cx, cy, color):
    pts = [(cx - 11, cy + 8), (cx, cy - 10), (cx + 11, cy + 8)]
    for px, py in pts:
        cv.disc(px, py, 4, color)
    cv.polyline([pts[0], pts[1], pts[2], pts[0]], color, 2)


def icon_clock(cv, cx, cy, color):
    cv.ring(cx, cy, 12, color, 2)
    cv.line(cx, cy, cx, cy - 8, color, 2)
    cv.line(cx, cy, cx + 7, cy + 3, color, 2)
    cv.disc(cx, cy, 2, color)


def icon_scales(cv, cx, cy, color):
    cv.line(cx, cy - 12, cx, cy + 11, color, 2)
    cv.line(cx - 11, cy - 8, cx + 11, cy - 8, color, 2)
    cv.line(cx - 11, cy - 8, cx - 13, cy + 2, color, 2)
    cv.line(cx - 11, cy - 8, cx - 9, cy + 2, color, 2)
    cv.line(cx - 14, cy + 2, cx - 8, cy + 2, color, 2)
    cv.line(cx + 11, cy - 8, cx + 13, cy + 2, color, 2)
    cv.line(cx + 11, cy - 8, cx + 9, cy + 2, color, 2)
    cv.line(cx + 8, cy + 2, cx + 14, cy + 2, color, 2)
    cv.line(cx - 6, cy + 11, cx + 6, cy + 11, color, 2)


def icon_chart(cv, cx, cy, color):
    cv.polyline([(cx - 12, cy - 9), (cx - 4, cy - 2), (cx + 2, cy - 5),
                 (cx + 12, cy + 9)], color, 3)
    cv.line(cx + 12, cy + 9, cx + 5, cy + 9, color, 3)
    cv.line(cx + 12, cy + 9, cx + 12, cy + 2, color, 3)


def icon_quake(cv, cx, cy, color):
    cv.polyline([(cx - 13, cy), (cx - 8, cy - 9), (cx - 3, cy + 8),
                 (cx + 3, cy - 9), (cx + 8, cy + 8), (cx + 13, cy)],
                color, 3)


# -------------------------------------------------------------- stories
# (day-part, headline, detail, icon). All seven were verified against
# reporting dated Friday 20 November 2026: CNN (strikes, Poland,
# Shenzhen), The Hindu BusinessLine / IMD (Akvan), Reuters via
# BusinessWorld (Iran), Reuters / UN News (Myanmar reply, 20 Nov),
# One Turn (markets), AP / USGS (Peru quake, 7:09 PM local).
STORIES = [
    ("OVERNIGHT",
     "RUSSIA'S BIGGEST STRIKE OF THE YEAR",
     "400+ drones, 110 missiles; 8+ killed. Two land in Poland.",
     icon_burst),
    ("MORNING",
     "CYCLONE AKVAN HITS ODISHA",
     "Landfall near Gopalpur. 300,000+ evacuated; no major damage.",
     icon_cyclone),
    ("MORNING",
     "SHENZHEN SUMMIT ENDS WITHOUT A DEAL",
     "First three-way talks end with no breakthrough on Ukraine.",
     icon_summit),
    ("MIDDAY",
     "TRUMP: NO RUSH ON IRAN",
     "Any decision on new strikes waits until after 1 January 2027.",
     icon_clock),
    ("AFTERNOON",
     "MYANMAR REJECTS GENOCIDE RULING",
     "A day after the world court verdict, Myanmar calls it unfair.",
     icon_scales),
    ("AFTERNOON",
     "AI ROUT DRAGS MARKETS DOWN",
     "S&P 500 falls 3.7% into correction; Nikkei drops 5.1%.",
     icon_chart),
    ("EVENING",
     "6.7 QUAKE SHAKES PERU",
     "7:09 PM: strong tremor hits the Andes. No casualties reported.",
     icon_quake),
]

CARD_W = 452
CARD_H = 106
SLOT = 108
TOP_Y = 166
SPINE_X = 512


def draw_card(cv, story, y, left):
    tag, headline, detail, _icon = story
    x = 20 if left else 552
    cv.fill_rect(x, y, CARD_W, CARD_H, PANEL)
    cv.rect(x, y, CARD_W, CARD_H, PANEL_EDGE, 2)
    # red edge on the side facing the spine: the lead story's side
    if left:
        cv.fill_rect(x + CARD_W - 5, y, 5, CARD_H, RED)
    else:
        cv.fill_rect(x, y, 5, CARD_H, RED)
    inner = x + 16
    cv.draw_text(inner, y + 10, tag, 2, GOLD)
    lines = wrap_text(headline, CARD_W - 32, 3)
    hy = y + 30
    for line in lines[:2]:
        cv.draw_text(inner, hy, line, 3, CREAM)
        hy += 21
    dlines = wrap_text(detail.upper(), CARD_W - 32, 2)
    dy = y + 76
    for line in dlines[:2]:
        cv.draw_text(inner, dy, line, 2, MUTE)
        dy += 15


def compose():
    cv = Canvas(W, H, INK)
    # faint horizontal banding for depth
    for y in range(0, H, 4):
        if (y // 4) % 2 == 0:
            cv.fill_rect(0, y, W, 1, (16, 24, 42))

    # ---------------------------------------------------------- masthead
    cv.draw_text(512, 16, "FRIDAY 20 NOVEMBER 2026", 5, CREAM, "center")
    cv.fill_rect(212, 66, 600, 3, GOLD)
    cv.draw_text(512, 82, "THE DAY, HOUR BY HOUR", 3, GOLD, "center")
    cv.draw_text(512, 112, "SEVEN STORIES FROM AROUND THE WORLD",
                 2, MUTE, "center")
    cv.fill_rect(20, 146, 984, 3, RED)
    cv.fill_rect(20, 152, 984, 2, GOLD)

    # ---------------------------------------------------------- timeline
    cv.fill_rect(SPINE_X - 2, TOP_Y, 4, 7 * SLOT - 2, FAINT)
    for i, story in enumerate(STORIES):
        y = TOP_Y + i * SLOT
        cy = y + CARD_H // 2
        left = (i % 2 == 0)
        draw_card(cv, story, y, left)
        # connector from the card to the spine node
        if left:
            cv.fill_rect(20 + CARD_W, cy - 2, SPINE_X - 19 - (20 + CARD_W),
                         4, GOLD)
        else:
            cv.fill_rect(SPINE_X + 19, cy - 2, 552 - SPINE_X - 19, 4, GOLD)
        cv.disc(SPINE_X, cy, 19, GOLD)
        cv.ring(SPINE_X, cy, 19, CREAM, 2)
        story[3](cv, SPINE_X, cy, INK)

    # ------------------------------------------------------------ footer
    fy = 936
    cv.fill_rect(20, fy - 6, 984, 2, GOLD)
    cv.draw_text(512, fy + 8,
                 "ALSO TODAY: WORLD CHILDREN'S DAY - UNICEF SAYS CHILD",
                 2, CREAM, "center")
    cv.draw_text(512, fy + 26,
                 "CASUALTIES IN UKRAINE ARE AT THEIR HIGHEST IN ALMOST FOUR YEARS",
                 2, CREAM, "center")
    cv.draw_text(512, fy + 44,
                 "HOUTHI MISSILES AIMED AT RIYADH SHOT DOWN",
                 2, GOLD, "center")
    cv.draw_text(512, fy + 66,
                 "SOURCES: CNN | REUTERS | THE HINDU BUSINESSLINE | UN NEWS | AP",
                 2, FAINT, "center")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, compose())
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
