#!/usr/bin/env python3
"""Draw Wednesday 18 November 2026's world news as one poster image.

Pure Python 3.13 standard library: no network, no clock, no randomness, so
every run writes byte-identical PNG output to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png when set).

The poster is a broadsheet front page: a masthead naming the day, one lead
story (Trump flies from Manila to Shenzhen for the APEC summit and talks
with Xi), four more stories from four regions and beats, and an overnight
strip - all events first reported on Wednesday 18 November 2026, as
reported by Reuters, BBC, AP, the Guardian and the India Meteorological
Department.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)   # warm newsprint
CARD = (255, 253, 248)    # story card white
INK = (24, 23, 20)        # headline ink
NAVY = (20, 32, 58)       # masthead / footer band
NAVY_LT = (36, 52, 86)
GOLD = (219, 166, 66)     # masthead date
RED = (178, 38, 28)       # accent / lead rule
BLUE = (45, 89, 134)      # sea / story accents
TEAL = (29, 120, 105)
GRAY = (106, 100, 90)     # secondary text
LINE = (202, 194, 177)    # hairlines
SKY = (168, 198, 222)     # illustration sky
SKY_DK = (122, 158, 190)
ORANGE = (213, 105, 24)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ------------------------------------------------------- 5x8 bitmap font
# Each glyph: 8 rows of 5 cells, '#' = ink. Uppercase only; all copy is
# written in capitals, which suits a broadsheet poster. Advance is 6 cells.
GLYPHS = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#",
          "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "#...#",
          "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", "#....",
          ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#",
          "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#....",
          "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#....",
          "#...."),
    'G': (".####", "#....", "#....", "#..##", "#...#", "#...#", "#...#",
          ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#",
          "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..",
          "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "...#.", "#..#.",
          ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#..#.",
          "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#....",
          "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#",
          "#...#"),
}

GLYPHS.update({
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#",
          "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#",
          ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#....",
          "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#...#", "#.#.#", "#..#.",
          ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#..#.",
          "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "....#",
          "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..",
          "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#",
          ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.",
          "..#.."),
    'W': ("#...#", "#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##",
          "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#",
          "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..",
          "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#....",
          "#####"),
    '0': (".###.", "#..##", "#.#.#", "#.#.#", "##..#", "#...#", "#...#",
          ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "..#..",
          ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#....",
          "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "#...#",
          ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#.",
          "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "....#", "#...#",
          ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", "#...#",
          ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#..",
          "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", "#...#",
          ".###."),
    '9': (".###.", "#...#", "#...#", "#...#", ".####", "....#", "....#",
          ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", ".....",
          "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".....", ".##..",
          ".##.."),
    ',': (".....", ".....", ".....", ".....", ".....", ".##..", ".##..",
          ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", ".....",
          "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#..",
          "....."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", ".....",
          "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", ".....",
          "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", ".....",
          "....."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", ".#...", "..#..",
          "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "...#.", "..#..",
          "##..."),
    '/': ("....#", "....#", "...#.", "...#.", "..#..", "..#..", ".#...",
          ".#..."),
    '&': (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", "#..#.",
          ".##.#"),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##",
          "....."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", ".....",
          "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#..",
          "....."),
    ';': (".....", ".##..", ".....", ".##..", ".##..", ".##..", ".#...",
          "....."),
    ':': (".....", ".##..", ".....", ".....", ".....", ".##..", ".....",
          "....."),
    '*': (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", ".....",
          "....."),
    '#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#.",
          "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", ".....",
          "....."),
    '[': (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".#...",
          ".###."),
    ']': (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", "...#.",
          ".###."),
    '<': ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#",
          "....."),
    '>': ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#....",
          "....."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", ".....",
          "#####"),
})


def text_width(text, scale):
    """Pixel width of text at the given scale (6 units per char)."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
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


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.px[o:o + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.px[o:o + (x1 - x0) * 3] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line with square thickness t."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        half = t // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                elif (r - 1) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, color)

    def triangle(self, p0, p1, p2, color):
        """Filled triangle via scanline fill."""
        pts = sorted([p0, p1, p2], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        for y in range(ay, cy + 1):
            t1 = (y - ay) / (cy - ay) if cy != ay else 0
            xl = ax + (cx - ax) * t1
            if y < by:
                t2 = (y - ay) / (by - ay) if by != ay else 0
                xr = ax + (bx - ax) * t2
            else:
                t2 = (y - by) / (cy - by) if cy != by else 0
                xr = bx + (cx - bx) * t2
            xa, xb = sorted([int(round(xl)), int(round(xr))])
            self.fill_rect(xa, y, xb - xa + 1, 1, color)

    def burst(self, cx, cy, r_out, r_in, points, color):
        """Spiky starburst polygon."""
        verts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / points - math.pi / 2
            verts.append((cx + int(r * math.cos(a)),
                          cy + int(r * math.sin(a))))
        for i in range(1, len(verts) - 1):
            self.triangle(verts[0], verts[i], verts[i + 1], color)

    # ------------------------------------------------------------ text
    def glyph(self, x, y, ch, scale, color):
        rows = GLYPHS.get(ch)
        if rows is None:
            rows = GLYPHS['?']
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == '#':
                    self.fill_rect(x + rx * scale, y + ry * scale,
                                   scale, scale, color)

    def text(self, x, y, s, scale, color):
        s = s.upper()
        for ch in s:
            self.glyph(x, y, ch, scale, color)
            x += 6 * scale
        return x

    def text_center(self, cx, y, s, scale, color):
        x = cx - text_width(s.upper(), scale) // 2
        return self.text(x, y, s, scale, color)

    def para(self, x, y, s, scale, color, max_width, leading=None):
        """Wrapped paragraph; returns y just below the last line."""
        lh = leading if leading is not None else 8 * scale + 4
        for line in wrap_text(s, scale, max_width):
            self.text(x, y, line, scale, color)
            y += lh
        return y


# --------------------------------------------------------------------- PNG
def encode_png(canvas):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


# ------------------------------------------------------------------- icons
# Small flat pictograms, drawn with the same primitives as the text.

def draw_globe(cv, cx, cy, r):
    """Small globe for the masthead: ring, meridians, land blobs."""
    cv.disc(cx, cy, r, GOLD, fill=False)
    cv.disc(cx, cy, r - 2, GOLD, fill=False)
    for dx in (-r // 2, 0, r // 2):
        half = int((r * r - dx * dx) ** 0.5)
        cv.line(cx + dx, cy - half, cx + dx, cy + half, GOLD, 1)
    cv.line(cx - r, cy, cx + r, cy, GOLD, 1)
    cv.disc(cx - r // 3, cy - r // 4, r // 4, GOLD)
    cv.disc(cx + r // 3, cy + r // 5, r // 5, GOLD)
    cv.disc(cx + r // 4, cy - r // 2, r // 6, GOLD)


def draw_plane_route(cv, x, y, w, h):
    """Air Force One on a Manila-to-Shenzhen arc over sky and sea."""
    cv.fill_rect(x, y, w, h, SKY)
    # sun and clouds
    cv.disc(x + w - 52, y + 34, 20, GOLD)
    for cx, cy, r in ((x + 52, y + 42, 14), (x + 74, y + 48, 18),
                      (x + 96, y + 42, 13)):
        cv.disc(cx, cy, r, WHITE)
    for cx, cy, r in ((x + w - 130, y + 96, 12), (x + w - 110, y + 102, 15),
                      (x + w - 92, y + 96, 11)):
        cv.disc(cx, cy, r, WHITE)
    # sea at the bottom
    cv.fill_rect(x, y + h - 64, w, 64, BLUE)
    for i, wy in enumerate((y + h - 46, y + h - 30, y + h - 14)):
        cv.line(x + 14 + i * 46, wy, x + 66 + i * 46, wy, SKY, 3)
        cv.line(x + w - 80 - i * 46, wy, x + w - 28 - i * 46, wy, SKY, 3)
    # flight arc, Manila (left) to Shenzhen (right)
    mx, my = x + 52, y + h - 88
    sx, sy = x + w - 52, y + h - 88
    top_y = y + 92
    for t in range(0, 101, 2):
        f = t / 100.0
        px = int(mx + (sx - mx) * f)
        # arc point: quadratic blend between the two cities
        py = int(my * (1 - f) * (1 - f) + 2 * top_y * f * (1 - f)
                 + sy * f * f)
        cv.disc(px, py, 2, NAVY)
    # city markers
    for cx, cy, label in ((mx, my, "MANILA"), (sx, sy, "SHENZHEN")):
        cv.disc(cx, cy, 7, RED)
        cv.disc(cx, cy, 3, WHITE)
        cv.text_center(cx, cy + 14, label, 2, INK)
    # plane on the arc, nose right, sitting on the arc apex
    px, py = x + w // 2, y + 142
    cv.triangle((px - 46, py + 4), (px + 48, py - 10), (px + 48, py - 2),
                NAVY)
    cv.triangle((px - 46, py + 4), (px - 26, py + 14), (px + 48, py - 2),
                NAVY)
    cv.triangle((px + 48, py - 10), (px + 60, py - 6), (px + 48, py - 2),
                RED)
    cv.triangle((px - 4, py - 4), (px + 12, py - 4), (px - 28, py + 28),
                NAVY_LT)
    cv.triangle((px - 4, py - 4), (px - 28, py + 28), (px - 38, py + 28),
                NAVY_LT)
    cv.triangle((px - 30, py), (px - 16, py), (px - 38, py - 24), NAVY_LT)
    cv.disc(px + 30, py - 7, 4, (182, 212, 236))
    cv.disc(px - 2, py + 1, 6, WHITE)
    cv.disc(px - 2, py + 1, 4, RED)
    for i, ly in enumerate((py + 22, py + 30, py + 38)):
        cv.line(px - 56, ly, px - 56 + 24 - i * 6, ly, GRAY, 2)


def draw_cyclone(cv, x, y, w, h):
    """Cyclone Akvan: spiral bands over a coastline."""
    cx, cy = x + w // 2, y + h // 2 - 10
    cv.fill_rect(x, y + h - 26, w, 26, BLUE)
    cv.line(x + 8, y + h - 12, x + 40, y + h - 12, SKY, 3)
    cv.line(x + w - 44, y + h - 12, x + w - 12, y + h - 12, SKY, 3)
    # spiral: offset rings read as a rotating storm
    for r, dx, dy in ((46, 0, 0), (36, 6, -4), (26, 10, -2), (16, 6, 2)):
        cv.disc(cx + dx, cy + dy, r, TEAL, fill=False)
        cv.disc(cx + dx, cy + dy, r - 2, TEAL, fill=False)
    cv.disc(cx + 6, cy + 2, 8, TEAL)
    cv.disc(cx + 6, cy + 2, 4, WHITE)
    # rain slashes
    for rx, ry in ((x + 6, y + 18), (x + 22, y + 30), (x + w - 26, y + 22),
                   (x + w - 10, y + 36)):
        cv.line(rx, ry, rx - 6, ry + 12, BLUE, 2)


def draw_boat(cv, x, y, w, h):
    """Small boat crowded on waves: the Canary Islands crossing."""
    cx, cy = x + w // 2, y + h // 2 + 6
    # waves
    for wy in (y + h - 30, y + h - 18, y + h - 6):
        cv.line(x + 6, wy, x + 34, wy, BLUE, 3)
        cv.line(x + w - 36, wy, x + w - 8, wy, BLUE, 3)
        cv.line(x + w // 2 - 12, wy + 6, x + w // 2 + 14, wy + 6, BLUE, 3)
    # hull
    cv.triangle((cx - 44, cy - 6), (cx + 44, cy - 6), (cx + 30, cy + 16),
                ORANGE)
    cv.triangle((cx - 44, cy - 6), (cx + 30, cy + 16), (cx - 30, cy + 16),
                ORANGE)
    cv.fill_rect(cx - 44, cy - 10, 88, 5, RED)
    # mast and sail
    cv.line(cx, cy - 10, cx, cy - 48, INK, 3)
    cv.triangle((cx + 2, cy - 48), (cx + 2, cy - 12), (cx + 30, cy - 12),
                WHITE)
    cv.triangle((cx - 2, cy - 46), (cx - 2, cy - 12), (cx - 24, cy - 12),
                SKY_DK)
    # passengers: small heads above the gunwale
    for hx in (cx - 30, cx - 14, cx + 2, cx + 18, cx + 32):
        cv.disc(hx, cy - 14, 5, INK)


def draw_medal(cv, x, y, w, h):
    """A medal on a ribbon: the Lviv visit."""
    cx, cy = x + w // 2, y + h // 2 + 12
    # ribbon
    cv.triangle((cx - 26, y + 8), (cx - 4, y + 8), (cx - 16, cy - 22), RED)
    cv.triangle((cx + 4, y + 8), (cx + 26, y + 8), (cx + 16, cy - 22),
                NAVY)
    cv.triangle((cx - 16, cy - 22), (cx + 16, cy - 22), (cx, cy - 8),
                GOLD)
    # medal
    cv.disc(cx, cy, 30, GOLD)
    cv.disc(cx, cy, 24, GOLD, fill=False)
    cv.disc(cx, cy, 22, (240, 196, 110), fill=False)
    cv.burst(cx, cy, 14, 6, 5, RED)
    cv.disc(cx, cy, 4, WHITE)


def draw_tanker(cv, x, y, w, h):
    """LPG tanker MT Tara Gas on the Strait of Hormuz."""
    cx, cy = x + w // 2, y + h // 2 + 8
    # sea
    cv.fill_rect(x, y + h - 30, w, 30, BLUE)
    for wy in (y + h - 20, y + h - 10):
        cv.line(x + 8, wy, x + 40, wy, SKY, 3)
        cv.line(x + w - 42, wy, x + w - 10, wy, SKY, 3)
    # hull
    cv.fill_rect(cx - 46, cy - 4, 92, 18, RED)
    cv.triangle((cx + 46, cy - 4), (cx + 46, cy + 14), (cx + 58, cy + 14),
                RED)
    cv.fill_rect(cx - 46, cy + 14, 104, 4, INK)
    # three LPG domes
    for dx in (-28, 0, 28):
        cv.disc(cx + dx, cy - 4, 13, WHITE)
        cv.rect(cx + dx - 13, cy - 17, 26, 14, INK, 1)
        cv.fill_rect(cx + dx - 13, cy - 4, 26, 2, INK)
    # bridge tower
    cv.fill_rect(cx + 34, cy - 34, 16, 30, NAVY)
    cv.fill_rect(cx + 36, cy - 30, 12, 6, SKY)
    cv.fill_rect(cx + 36, cy - 20, 12, 6, SKY)
    # funnel smoke above the bridge tower
    for sx, sy, sr in ((cx + 40, cy - 44, 7), (cx + 46, cy - 56, 9),
                       (cx + 36, cy - 64, 6)):
        cv.disc(sx, sy, sr, GRAY)


# ------------------------------------------------------------------ poster
def draw_card(cv, x0, y0, accent, tag, headline, body, icon):
    cv.fill_rect(x0, y0, 488, 196, CARD)
    cv.rect(x0, y0, 488, 196, LINE, 1)
    cv.fill_rect(x0, y0, 488, 6, accent)
    icon(cv, x0 + 10, y0 + 46, 100, 110)
    tx = x0 + 122
    tw = 488 - 122 - 14
    cv.text(tx, y0 + 16, tag, 2, accent)
    cv.para(tx, y0 + 38, headline, 3, INK, tw, leading=25)
    cv.para(tx, y0 + 120, body, 2, GRAY, tw, leading=18)


def draw_poster():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ---------------------------------------------------
    cv.fill_rect(0, 0, W, 108, NAVY)
    draw_globe(cv, 62, 54, 30)
    cv.text_center(560, 12, "THE WORLD TODAY", 6, WHITE)
    cv.text_center(560, 64, "WEDNESDAY 18 NOVEMBER 2026", 3, GOLD)
    cv.fill_rect(0, 108, W, 4, RED)

    # ---- lead story: Trump to Shenzhen ------------------------------
    cv.text(28, 128, "LEAD STORY - ASIA", 2, RED)
    cv.text(28, 152, "TRUMP FLIES TO", 4, INK)
    cv.text(28, 186, "SHENZHEN TO MEET XI", 4, INK)
    cv.fill_rect(28, 222, 200, 4, RED)
    cv.para(28, 238, "AFTER A DAY OF TALKS IN MANILA, THE PRESIDENT "
           "HEADS TO CHINA FOR THE APEC SUMMIT. A BILATERAL WITH XI "
           "JINPING IS ON THE SCHEDULE, WITH TRADE, AI AND UKRAINE ON "
           "THE TABLE.", 2, INK, 560, leading=19)
    cv.rect(28, 332, 560, 52, LINE, 1)
    cv.fill_rect(28, 332, 6, 52, RED)
    cv.text(44, 350, "TRUMP SAYS HE IS OPEN TO A ONE-ON-ONE", 2, NAVY)
    cv.text(44, 368, "WITH PUTIN TOO", 2, NAVY)
    draw_plane_route(cv, 620, 124, 376, 280)
    cv.text_center(808, 410, "THE ROUTE: MANILA TO SHENZHEN", 2, GRAY)

    # ---- four more stories ------------------------------------------
    draw_card(cv, 16, 444, TEAL, "ASIA - WEATHER",
              "CYCLONE AKVAN TURNS SEVERE OFF INDIA",
              "WINDS OF 110 KM/H AS THE STORM HEADS FOR ANDHRA "
              "PRADESH. HEAVY RAIN FROM TODAY; LANDFALL DUE FRIDAY.",
              draw_cyclone)
    draw_card(cv, 520, 444, BLUE, "EUROPE - MIGRATION",
              "RECORD DAY FOR CANARY MIGRANTS",
              "1,500 ARRIVE IN ONE DAY, THE MOST IN 30 YEARS, "
              "STRAINING SHELTERS ON EL HIERRO.",
              draw_boat)
    draw_card(cv, 16, 652, NAVY, "EUROPE - UKRAINE",
              "HARRY MEETS WOUNDED VETERANS IN LVIV",
              "'YOU WILL WIN THE WAR,' HE TELLS TROOPS AT A REHAB "
              "CLINIC AFTER A QUIET WEEKEND VISIT.",
              draw_medal)
    draw_card(cv, 520, 652, RED, "MIDDLE EAST - ENERGY",
              "HORMUZ TANKER ATTACK CONDEMNED",
              "INDIA SPEAKS OUT AFTER THE LPG CARRIER MT TARA GAS "
              "WAS HIT; 21 OF 24 INDIAN CREW ARE SAFE ASHORE.",
              draw_tanker)

    # ---- overnight ----------------------------------------------------
    cv.text(16, 862, "OVERNIGHT", 3, RED)
    cv.fill_rect(16, 888, 992, 2, LINE)
    items = [
        "NVIDIA POSTS BUMPER RESULTS AS EX-CHIEF JENSEN HUANG EXITS",
        "RUSSIAN MILITARY PLANE CRASHES IN SIBERIA; ALL 19 ON BOARD KILLED",
        "US SOLDIER HELD IN BRITAIN ON SUSPICION OF SPYING",
    ]
    y = 894
    for item in items:
        for line in wrap_text(item, 2, 960):
            cv.fill_rect(16, y + 4, 8, 8, RED)
            cv.text(36, y, line, 2, INK)
            y += 20

    # ---- footer -------------------------------------------------------
    cv.fill_rect(0, 960, W, 64, NAVY)
    cv.text_center(512, 972, "THE DAY'S NEWS, AS REPORTED ON WEDNESDAY "
                   "18 NOVEMBER 2026", 2, WHITE)
    cv.text_center(512, 996, "SOURCES: REUTERS - BBC - AP - GUARDIAN - "
                   "IMD", 2, GOLD)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(draw_poster())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    main()
