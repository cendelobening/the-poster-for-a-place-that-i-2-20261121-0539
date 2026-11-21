#!/usr/bin/env python3
"""AETHERIA - The Floating Isles. A travel poster for a place that isn't there.

Pure-stdlib Python 3.13: the picture is painted pixel by pixel into a
bytearray, the letters come from a hand-built 5x7 bitmap alphabet, and the
PNG bytes are assembled with struct + zlib. No randomness, no timestamps,
no network: every run writes identical bytes.

The place: Aetheria, an archipelago of islands that drift above a sea of
clouds. Its one landmark is the white beacon lighthouse on the great
island, whose waterfall pours off the island's edge into the clouds below.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
INK_SKY = (22, 26, 68)      # deep indigo, top of sky + bottom band
VIOLET = (96, 72, 138)      # mid-sky violet
PEACH = (255, 176, 118)     # horizon peach
SUN = (255, 214, 120)       # low sun
SUN_CORE = (255, 232, 170)  # sun heart
GOLD = (232, 180, 90)       # rules and accents
GOLD_LIGHT = (250, 216, 132)
CREAM = (252, 240, 220)     # name text, cloud tops
CLOUD = (250, 236, 218)     # cloud sea
CLOUD_SHADE = (243, 222, 200)
ISLE_GREEN = (58, 122, 78)  # island tops
ISLE_DARK = (34, 90, 56)    # trees
ROCK = (96, 74, 62)         # island undersides
ROCK_DARK = (70, 52, 44)    # strata
TOWER = (248, 244, 232)     # lighthouse white
TOWER_RED = (198, 62, 58)   # lighthouse bands + balloon
NAVY = (30, 38, 84)         # lighthouse gallery
FALL = (196, 228, 242)      # waterfall
FALL_HI = (238, 248, 250)   # waterfall highlight
BEAM = (255, 232, 150)      # lighthouse beams
BIRD = (40, 40, 80)
BASKET = (110, 76, 50)


# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is seven rows of five cells; '#' is ink, '.' is blank.
# Shapes drawn from memory of ordinary block capitals.
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#....", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "....#", "####."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
}


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


# ------------------------------------------------------------------ canvas
class Poster:
    """A 1024x1024 RGB canvas painted with simple filled shapes."""

    def __init__(self):
        self.pixels = bytearray(W * H * 3)

    def dot(self, x, y, colour):
        if 0 <= x < W and 0 <= y < H:
            off = (y * W + x) * 3
            self.pixels[off] = colour[0]
            self.pixels[off + 1] = colour[1]
            self.pixels[off + 2] = colour[2]

    def block(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                off = base + (xx - x0) * 3
                self.pixels[off] = colour[0]
                self.pixels[off + 1] = colour[1]
                self.pixels[off + 2] = colour[2]

    def disc(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            span = math.isqrt(max(0, r * r - dy * dy))
            for dx in range(-span, span + 1):
                self.dot(cx + dx, cy + dy, colour)

    def stroke(self, x0, y0, x1, y1, colour, width=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            if width <= 1:
                self.dot(x, y, colour)
            else:
                self.disc(x, y, width // 2, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def fill_poly(self, points, colour):
        if len(points) < 3:
            return
        top = min(p[1] for p in points)
        bottom = max(p[1] for p in points)
        for yy in range(top, bottom + 1):
            crossings = []
            for i in range(len(points)):
                ax, ay = points[i]
                bx, by = points[(i + 1) % len(points)]
                if ay == by:
                    continue
                if (ay <= yy < by) or (by <= yy < ay):
                    t = (yy - ay) / (by - ay)
                    crossings.append(ax + t * (bx - ax))
            crossings.sort()
            for j in range(0, len(crossings) - 1, 2):
                xa = int(math.ceil(crossings[j]))
                xb = int(math.floor(crossings[j + 1]))
                for xx in range(xa, xb + 1):
                    self.dot(xx, yy, colour)

    # -- text ------------------------------------------------------------
    def glyph(self, x, y, char, scale, colour):
        rows = GLYPHS.get(char.upper(), GLYPHS["?"] if "?" in GLYPHS else GLYPHS[" "])
        for row_i, row in enumerate(rows):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    self.block(x + col_i * scale, y + row_i * scale,
                               scale, scale, colour)

    def write(self, x, y, text, scale, colour, align="left"):
        width = text_width(text, scale)
        if align == "center":
            x = x - width // 2
        elif align == "right":
            x = x - width
        assert x >= 0 and x + width <= W, "text overflows page: %r" % text
        cursor = x
        for char in text:
            self.glyph(cursor, y, char, scale, colour)
            cursor += 6 * scale
        return width


# ------------------------------------------------------------ deterministic
def lcg(seed):
    """Tiny deterministic generator; same sequence on every run."""
    state = seed
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield state


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------- sky
def draw_sky(page):
    """Vertical gradient: deep indigo at the top, violet, then peach
    at the horizon where the cloud sea begins."""
    stops = [(0, INK_SKY), (300, VIOLET), (520, (214, 120, 120)),
             (640, PEACH)]
    for y in range(0, 641):
        for i in range(len(stops) - 1):
            y0, c0 = stops[i]
            y1, c1 = stops[i + 1]
            if y0 <= y <= y1:
                page.block(0, y, W, 1, lerp(c0, c1, (y - y0) / (y1 - y0)))
                break


def draw_stars(page):
    """Fixed-seed stars in the upper sky, clear of the sun."""
    rng = lcg(20261121)
    for _ in range(34):
        x = 30 + next(rng) % 640
        y = 24 + next(rng) % 210
        page.block(x, y, 2, 2, CREAM)
    # A few four-point stars.
    for cx, cy in ((150, 90), (420, 60), (560, 130), (90, 210), (640, 60)):
        page.block(cx - 1, cy - 4, 2, 9, CREAM)
        page.block(cx - 4, cy - 1, 9, 2, CREAM)


def draw_sun(page):
    """Low sun, right of centre, with stepped glow rings."""
    cx, cy = 795, 285
    page.disc(cx, cy, 140, (255, 168, 118))
    page.disc(cx, cy, 108, (255, 186, 112))
    page.disc(cx, cy, 84, (255, 202, 108))
    page.disc(cx, cy, 62, SUN)
    page.disc(cx, cy, 40, SUN_CORE)


def draw_birds(page):
    for cx, cy, s in ((300, 220, 9), (352, 262, 7), (620, 178, 8),
                      (430, 148, 7), (690, 330, 8)):
        page.stroke(cx - s, cy - 4, cx, cy, BIRD, 3)
        page.stroke(cx, cy, cx + s, cy - 4, BIRD, 3)


def draw_balloon(page):
    """One red hot-air balloon drifting right of the great island."""
    cx, cy = 905, 430
    page.disc(cx, cy, 36, TOWER_RED)
    page.disc(cx - 12, cy - 12, 13, (226, 96, 88))
    page.stroke(cx - 16, cy + 30, cx - 8, cy + 48, BASKET, 2)
    page.stroke(cx + 16, cy + 30, cx + 8, cy + 48, BASKET, 2)
    page.block(cx - 9, cy + 48, 18, 13, BASKET)


# --------------------------------------------------------------- islands
def draw_tree(page, x, y, r):
    page.block(x - 2, y, 4, 10, ROCK_DARK)
    page.disc(x, y - 6, r, ISLE_DARK)
    page.disc(x - r // 2, y - 2, r // 2 + 2, ISLE_DARK)


def draw_house(page, x, y):
    """Small white house with a red roof, sitting on an island top."""
    page.block(x, y, 20, 14, TOWER)
    page.fill_poly([(x - 3, y), (x + 10, y - 11), (x + 23, y)], TOWER_RED)
    page.block(x + 8, y + 7, 5, 7, NAVY)


def draw_island(page, cx, top_y, half_w, depth, big=False):
    """A floating island: green top, rocky cone underside, strata lines."""
    page.fill_poly([(cx - half_w, top_y), (cx + half_w, top_y),
                    (cx + half_w - 18, top_y + 26),
                    (cx - half_w + 18, top_y + 26)], ISLE_GREEN)
    # Sunlit grass edge along the top of the island.
    page.fill_poly([(cx - half_w, top_y), (cx + half_w, top_y),
                    (cx + half_w - 6, top_y + 7),
                    (cx - half_w + 6, top_y + 7)], (86, 150, 100))
    page.fill_poly([(cx - half_w + 18, top_y + 26),
                    (cx + half_w - 18, top_y + 26),
                    (cx, top_y + depth)], ROCK)
    # Lighter rock facet on the sunlit left slope of the cone.
    page.fill_poly([(cx - half_w + 18, top_y + 26),
                    (cx - half_w + 44, top_y + 26),
                    (cx - 12, top_y + depth - 8)], (118, 92, 76))
    # Strata: short dark bands narrowing down the cone.
    for frac, wfrac in ((0.35, 0.62), (0.55, 0.44), (0.75, 0.26)):
        yy = top_y + 26 + int((depth - 26) * frac)
        hw = int(half_w * wfrac)
        page.stroke(cx - hw, yy, cx + hw, yy, ROCK_DARK, 4)


def draw_lighthouse(page, cx, base_y):
    """The beacon: white tower with red bands, navy gallery, gold lamp,
    and two light beams sweeping across the sky."""
    # Beams first, so the tower paints over their roots.
    page.fill_poly([(cx, base_y - 92), (cx, base_y - 76),
                    (cx - 250, base_y - 128), (cx - 250, base_y - 96)], BEAM)
    page.fill_poly([(cx, base_y - 92), (cx, base_y - 76),
                    (cx + 250, base_y - 128), (cx + 250, base_y - 96)], BEAM)
    page.fill_poly([(cx - 20, base_y), (cx + 20, base_y),
                    (cx + 14, base_y - 98), (cx - 14, base_y - 98)], TOWER)
    page.block(cx - 18, base_y - 34, 36, 10, TOWER_RED)
    page.block(cx - 17, base_y - 66, 34, 10, TOWER_RED)
    # Halo glow, then the navy gallery on top of it, then the lamp.
    page.disc(cx, base_y - 106, 16, (255, 232, 150))
    page.block(cx - 18, base_y - 116, 36, 18, NAVY)
    page.disc(cx, base_y - 107, 7, GOLD)


def draw_waterfall(page, x0, top_y, bottom_y):
    """Water pouring off the great island's edge into the clouds."""
    page.fill_poly([(x0, top_y), (x0 + 32, top_y),
                    (x0 + 28, bottom_y), (x0 - 4, bottom_y)], FALL)
    page.fill_poly([(x0 + 10, top_y), (x0 + 20, top_y),
                    (x0 + 18, bottom_y), (x0 + 8, bottom_y)], FALL_HI)


# ----------------------------------------------------------------- clouds
def draw_cloud_sea(page):
    """The sea of clouds the islands drift above."""
    for y in range(620, H):
        t = (y - 620) / (H - 620)
        page.block(0, y, W, 1, lerp((255, 214, 178), CLOUD, t))
    # Horizon puffs: a row of overlapping discs.
    rng = lcg(777)
    x = -40
    while x < W + 40:
        r = 46 + next(rng) % 26
        page.disc(x, 648 + next(rng) % 14, r, CREAM)
        x += 62 + next(rng) % 30
    # Larger drifting puffs lower down, shadows tucked underneath.
    puffs = [(120, 760, 78), (300, 820, 96), (520, 780, 84), (700, 850, 100),
             (880, 780, 82), (60, 880, 70), (240, 900, 88), (450, 905, 92),
             (660, 905, 86), (860, 900, 90), (980, 860, 70)]
    for cx, cy, r in puffs:
        page.disc(cx, cy, r, CLOUD)
        page.disc(cx - r // 2, cy + r // 2 + 6, r // 3, CLOUD_SHADE)
        page.disc(cx + r // 2, cy + r // 2 + 8, r // 3, CLOUD)


# ------------------------------------------------------------------ build
def build():
    page = Poster()
    draw_sky(page)
    draw_stars(page)
    draw_sun(page)
    draw_birds(page)

    # Distant islands, smaller and lower, for depth.
    draw_island(page, 170, 556, 52, 76)
    draw_tree(page, 168, 552, 9)
    draw_island(page, 823, 548, 62, 104)
    draw_tree(page, 800, 544, 10)
    draw_house(page, 828, 530)

    # The great island, centre, with the beacon lighthouse.
    draw_island(page, 512, 468, 172, 232, big=True)
    draw_lighthouse(page, 512, 468)
    draw_tree(page, 400, 464, 14)
    draw_tree(page, 636, 464, 12)
    draw_house(page, 430, 448)
    draw_house(page, 580, 448)
    draw_waterfall(page, 648, 492, 668)

    draw_balloon(page)
    draw_cloud_sea(page)
    # Foam where the waterfall meets the clouds.
    page.disc(660, 668, 24, CREAM)
    page.disc(640, 672, 14, CREAM)

    # Name, set large across the top of the sky.
    page.write(W // 2, 56, "AETHERIA", 11, CREAM, align="center")
    page.block(W // 2 - 256, 147, 512, 5, GOLD)
    page.write(W // 2, 168, "THE FLOATING ISLES", 3, GOLD_LIGHT,
               align="center")

    # Bottom band with the one mood line.
    page.block(0, 932, W, 4, GOLD)
    page.block(0, 936, W, 88, INK_SKY)
    page.write(W // 2, 962, "WHERE THE ISLANDS DRIFT ABOVE THE CLOUDS",
               3, CREAM, align="center")
    return page


# --------------------------------------------------------------- PNG out
def png_bytes(page):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)  # filter: none
        start = yy * W * 3
        raw.extend(page.pixels[start:start + W * 3])

    def chunk(tag, data):
        crc = zlib.crc32(tag)
        crc = zlib.crc32(data, crc)
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", crc & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out.extend(chunk(b"IHDR", ihdr))
    out.extend(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    out.extend(chunk(b"IEND", b""))
    return bytes(out)


def main():
    page = build()
    data = png_bytes(page)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    path = os.path.join(out_dir, "entry.png")
    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)
    except OSError:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "output", "entry.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)
    os.chmod(path, 0o644)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
