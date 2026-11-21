#!/usr/bin/env python3
"""AERLITH -- a travel poster for a place that isn't there.

Pure-stdlib Python 3.13. Renders a 1024x1024 travel poster and writes it
to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png when set, for local
testing). No network, no third-party packages, fully deterministic.

Scene: golden-hour sky over a calm sea, one floating island with a
waterfall spilling off its edge, a low sun, a small sailboat, birds.
The place name AERLITH is set big into the picture, top centre.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT_PATH = os.path.join(OUT_DIR, "entry.png")

# ---------------------------------------------------------------- canvas
# rows[y] is a bytearray of W*3 RGB bytes.
rows = [bytearray(W * 3) for _ in range(H)]


def lerp(a, b, t):
    return int(a + (b - a) * t + 0.5)


def lerp_color(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def gradient_fill(y0, y1, stops):
    """Vertical multi-stop gradient between rows y0..y1 (inclusive)."""
    span = max(1, y1 - y0)
    for y in range(y0, y1 + 1):
        t = (y - y0) / span
        # find surrounding stops
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if t <= p1 or i == len(stops) - 2:
                tt = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                tt = max(0.0, min(1.0, tt))
                col = lerp_color(c0, c1, tt)
                break
        rows[y] = bytearray(bytes(col) * W)


def blend_px(x, y, color, alpha):
    """Alpha-blend one pixel. alpha 0..1."""
    if x < 0 or x >= W or y < 0 or y >= H:
        return
    if alpha >= 1.0:
        i = x * 3
        rows[y][i] = color[0]
        rows[y][i + 1] = color[1]
        rows[y][i + 2] = color[2]
        return
    if alpha <= 0.0:
        return
    i = x * 3
    r = rows[y]
    r[i] = int(r[i] + (color[0] - r[i]) * alpha + 0.5)
    r[i + 1] = int(r[i + 1] + (color[1] - r[i + 1]) * alpha + 0.5)
    r[i + 2] = int(r[i + 2] + (color[2] - r[i + 2]) * alpha + 0.5)


def fill_rect(x0, y0, x1, y1, color, alpha=1.0):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W - 1, x1)
    y1 = min(H - 1, y1)
    if x0 > x1 or y0 > y1:
        return
    if alpha >= 1.0:
        span = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            rows[y][x0 * 3:(x1 + 1) * 3] = span
    else:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                blend_px(x, y, color, alpha)


def fill_ellipse(cx, cy, rx, ry, color, alpha=1.0):
    for dy in range(-ry, ry + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        t = 1.0 - (dy * dy) / float(ry * ry)
        if t < 0:
            continue
        dx = int(rx * math.sqrt(t))
        x0 = max(0, cx - dx)
        x1 = min(W - 1, cx + dx)
        if alpha >= 1.0:
            span = bytes(color) * (x1 - x0 + 1)
            rows[y][x0 * 3:(x1 + 1) * 3] = span
        else:
            for x in range(x0, x1 + 1):
                blend_px(x, y, color, alpha)


def fill_circle(cx, cy, r, color, alpha=1.0):
    fill_ellipse(cx, cy, r, r, color, alpha)


def fill_polygon(points, color, alpha=1.0):
    """Scanline polygon fill."""
    ys = [p[1] for p in points]
    y0 = max(0, min(ys))
    y1 = min(H - 1, max(ys))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                t = (y - y1p) / float(y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(xs[i]))
            xb = min(W - 1, int(xs[i + 1]))
            if alpha >= 1.0:
                span = bytes(color) * (xb - xa + 1)
                rows[y][xa * 3:(xb + 1) * 3] = span
            else:
                for x in range(xa, xb + 1):
                    blend_px(x, y, color, alpha)


def draw_line(x0, y0, x1, y1, color, width=1, alpha=1.0):
    """DDA line with square brush."""
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    half = width // 2
    for s in range(steps + 1):
        x = int(x0 + dx * s / steps)
        y = int(y0 + dy * s / steps)
        for oy in range(-half, half + 1):
            for ox in range(-half, half + 1):
                blend_px(x + ox, y + oy, color, alpha)


# ---------------------------------------------------------------- 5x7 font
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10110", "10011"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
}


def text_width(text, scale, spacing):
    return len(text) * 5 * scale + (len(text) - 1) * spacing


def draw_text(text, cx, y, scale, color, outline, spacing=None):
    """Draw text centred on cx, top edge at y. Outline pass then main pass,
    plus a soft drop shadow for legibility against the sky."""
    if spacing is None:
        spacing = scale
    total = text_width(text, scale, spacing)
    x = cx - total // 2
    pad = max(2, scale // 4)
    shadow_dx, shadow_dy = scale // 3, scale // 3
    # shadow pass
    for ch_i, ch in enumerate(text):
        glyph = FONT[ch]
        gx = x + ch_i * (5 * scale + spacing)
        for r in range(7):
            for c in range(5):
                if glyph[r][c] == "1":
                    fill_rect(gx + c * scale + shadow_dx,
                              y + r * scale + shadow_dy,
                              gx + c * scale + scale - 1 + shadow_dx,
                              y + r * scale + scale - 1 + shadow_dy,
                              (20, 16, 48), alpha=0.35)
    # outline pass (expanded rects)
    for ch_i, ch in enumerate(text):
        glyph = FONT[ch]
        gx = x + ch_i * (5 * scale + spacing)
        for r in range(7):
            for c in range(5):
                if glyph[r][c] == "1":
                    fill_rect(gx + c * scale - pad, y + r * scale - pad,
                              gx + c * scale + scale - 1 + pad,
                              y + r * scale + scale - 1 + pad, outline)
    # main pass
    for ch_i, ch in enumerate(text):
        glyph = FONT[ch]
        gx = x + ch_i * (5 * scale + spacing)
        for r in range(7):
            for c in range(5):
                if glyph[r][c] == "1":
                    fill_rect(gx + c * scale, y + r * scale,
                              gx + c * scale + scale - 1,
                              y + r * scale + scale - 1, color)


# ------------------------------------------------------------------- scene
def render():
    # --- sky: deep indigo -> violet -> rose -> coral -> gold at horizon
    gradient_fill(0, 640, [
        (0.00, (26, 32, 86)),
        (0.30, (74, 60, 140)),
        (0.55, (190, 90, 130)),
        (0.75, (255, 140, 96)),
        (0.90, (255, 196, 120)),
        (1.00, (255, 214, 150)),
    ])
    # --- sea: warm horizon glow -> teal -> deep navy
    gradient_fill(641, H - 1, [
        (0.00, (232, 148, 108)),
        (0.12, (120, 90, 130)),
        (0.35, (44, 96, 138)),
        (1.00, (14, 38, 78)),
    ])

    # --- sun glow (radial, behind the island)
    sun_x, sun_y, sun_r = 760, 420, 60
    glow_r = 280
    for yy in range(sun_y - glow_r, sun_y + glow_r + 1):
        if yy < 0 or yy >= H:
            continue
        for xx in range(sun_x - glow_r, sun_x + glow_r + 1):
            if xx < 0 or xx >= W:
                continue
            d = math.hypot(xx - sun_x, yy - sun_y)
            if d < glow_r:
                a = 0.55 * (1.0 - d / glow_r) ** 2
                blend_px(xx, yy, (255, 190, 120), a)
    # --- sun disc
    fill_circle(sun_x, sun_y, sun_r, (255, 238, 186))
    fill_circle(sun_x, sun_y, sun_r - 8, (255, 246, 214))

    # --- clouds (soft, warm)
    for cx, cy, rx, ry, col, al in [
        (190, 250, 150, 26, (255, 190, 170), 0.55),
        (230, 268, 110, 20, (255, 205, 185), 0.50),
        (850, 180, 150, 24, (255, 185, 175), 0.50),
        (880, 200, 100, 18, (255, 205, 190), 0.45),
        (140, 420, 120, 20, (255, 170, 150), 0.40),
        (880, 330, 120, 20, (255, 180, 160), 0.40),
    ]:
        fill_ellipse(cx, cy, rx, ry, col, al)

    # --- birds
    bird = (40, 30, 60)
    for bx, by, s in [(250, 300, 16), (305, 282, 13), (352, 312, 11),
                      (830, 290, 14), (878, 272, 11)]:
        draw_line(bx - s, by - s // 3, bx, by, bird, width=3)
        draw_line(bx, by, bx + s, by - s // 3, bird, width=3)

    # --- sun reflection on the sea (shimmering dashes under the sun)
    for yy in range(655, 1000, 13):
        prog = (yy - 655) / 345.0
        half = int(30 + prog * 110)
        # deterministic pseudo-random dash pattern
        seed = (yy * 2654435761) % 97
        dash_w = int(half * (0.5 + (seed % 50) / 100.0))
        cx = sun_x + ((seed % 41) - 20)
        a = 0.55 * (1.0 - prog * 0.7)
        fill_rect(cx - dash_w, yy, cx + dash_w, yy + 4,
                  (255, 205, 130), alpha=a)

    # --- floating island (the landmark)
    rock = (88, 52, 72)
    island = [(280, 440), (680, 440), (650, 510), (590, 580),
              (530, 630), (470, 655), (410, 630), (350, 580), (310, 510)]
    fill_polygon(island, rock)
    # grassy cap
    fill_rect(278, 428, 682, 446, (86, 158, 110))
    fill_ellipse(480, 432, 205, 12, (110, 190, 128))
    # trees
    for tx, ty, tr in [(350, 420, 20), (415, 414, 24), (610, 418, 18)]:
        fill_rect(tx - 3, ty, tx + 3, ty + 14, (60, 40, 50))
        fill_circle(tx, ty - tr // 2, tr, (46, 120, 80))
        fill_circle(tx - tr // 3, ty - tr // 2 - tr // 3, tr // 2,
                    (110, 190, 120))
    # little white tower with a warm window
    fill_rect(545, 372, 585, 432, (255, 244, 220))
    fill_polygon([(540, 372), (590, 372), (565, 348)], (255, 140, 96))
    fill_rect(560, 392, 570, 410, (255, 205, 110))
    fill_rect(558, 420, 572, 432, (90, 60, 70))

    # --- waterfall spilling off the island's left edge into the sea
    for yy in range(448, 656):
        t = (yy - 448) / 208.0
        cx = int(332 - t * 34)
        wdt = int(13 + t * 8)
        fill_rect(cx - wdt, yy, cx + wdt, yy, (210, 238, 250), alpha=0.85)
        fill_rect(cx - wdt // 2, yy, cx + wdt // 2, yy,
                  (245, 252, 255), alpha=0.9)
    # thin second fall on the right edge
    for yy in range(448, 640):
        t = (yy - 448) / 192.0
        cx = int(645 + t * 16)
        fill_rect(cx - 5, yy, cx + 5, yy, (210, 238, 250), alpha=0.7)
    # foam where the falls meet the sea
    fill_ellipse(296, 658, 42, 10, (240, 248, 252), 0.85)
    fill_ellipse(662, 644, 22, 7, (240, 248, 252), 0.7)
    # soft shadow of the island on the water
    fill_ellipse(470, 700, 210, 16, (10, 26, 56), 0.35)

    # --- sailboat, small, for scale and invitation
    bx, by = 215, 790
    fill_polygon([(bx - 34, by), (bx + 34, by), (bx + 22, by + 16),
                  (bx - 22, by + 16)], (30, 24, 52))
    draw_line(bx, by - 58, bx, by, (30, 24, 52), width=3)
    fill_polygon([(bx + 4, by - 54), (bx + 4, by - 6), (bx + 40, by - 6)],
                 (255, 240, 210))
    fill_polygon([(bx - 4, by - 46), (bx - 4, by - 6), (bx - 30, by - 6)],
                 (255, 214, 170))
    fill_ellipse(bx, by + 18, 40, 4, (255, 220, 160), 0.4)

    # --- the place name, big, set into the sky
    draw_text("AERLITH", W // 2, 64, 16, (255, 242, 208), (30, 24, 60))
    # thin rule + diamond under the name
    fill_rect(332, 204, 692, 206, (255, 242, 208), alpha=0.85)
    fill_polygon([(512, 196), (522, 205), (512, 214), (502, 205)],
                 (255, 242, 208))

    # --- poster frame
    for inset, th in ((26, 3), (38, 1)):
        fill_rect(inset, inset, W - 1 - inset, inset + th - 1,
                  (255, 240, 210), alpha=0.75)
        fill_rect(inset, H - inset - th, W - 1 - inset, H - 1 - inset,
                  (255, 240, 210), alpha=0.75)
        fill_rect(inset, inset, inset + th - 1, H - 1 - inset,
                  (255, 240, 210), alpha=0.75)
        fill_rect(W - inset - th, inset, W - 1 - inset, H - 1 - inset,
                  (255, 240, 210), alpha=0.75)


# ---------------------------------------------------------------- PNG writer
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    # Up filter (type 2) per row: great for vertical gradients.
    raw = bytearray()
    prev = bytes(W * 3)
    for y in range(H):
        row = bytes(rows[y])
        raw.append(2)
        raw.extend((a - b) & 0xFF for a, b in zip(row, prev))
        prev = row
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    render()
    size = write_png(OUT_PATH)
    print(f"wrote {OUT_PATH}: {W}x{H}, {size} bytes")


if __name__ == "__main__":
    main()
