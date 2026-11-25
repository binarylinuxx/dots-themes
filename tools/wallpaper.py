#!/usr/bin/env python3
"""Draws the themes' wallpapers, so each one can be redrawn exactly.

    python3 tools/wallpaper.py [name …] [--size 3840x2160]

With no names it draws them all. Each theme folder gets wallpaper.png at the
full size and preview.jpg (960x540) for the store. Needs Pillow and numpy.

The first five themes generate their colours from the wallpaper. The
colour-scheme themes (tools/schemes.py) are the other way round: their
wallpaper is drawn from the scheme's palette by the generic designs below.
"""
import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from schemes import SCHEMES, mix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 2  # drawn at twice the size, then reduced: smooth edges


def hex_rgb(text):
    text = text.lstrip("#")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


def sky(w, h, top, bottom, horizon=1.0):
    """A vertical blend from `top` to `bottom`, reaching it at `horizon`."""
    t = np.clip(np.linspace(0, 1, h) / horizon, 0, 1)[:, None, None]
    a, b = np.array(hex_rgb(top), float), np.array(hex_rgb(bottom), float)
    rows = a + (b - a) * t
    # A little ordered dither keeps a wide blend from banding.
    rng = np.random.default_rng(7)
    pixels = np.broadcast_to(rows, (h, w, 3)) + rng.uniform(-0.5, 0.5, (h, w, 1))
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "RGB")


def ridge(w, h, base, waves, step=8):
    """A filled band under a curve: base + sum(amplitude * sin(freq * x + phase))."""
    points = []
    for x in range(0, w + step, step):
        u = x / w
        y = base + sum(a * math.sin(f * u * 2 * math.pi + p) for a, f, p in waves)
        points.append((x, y * h))
    return points + [(w, h), (0, h)]


def disc(draw, cx, cy, r, colour):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


def polar(cx, cy, radius, wave, rotation=0.0, steps=720):
    points = []
    for step in range(steps):
        angle = 2 * math.pi * step / steps
        r = radius * wave(angle)
        points.append((cx + r * math.cos(angle + rotation), cy + r * math.sin(angle + rotation)))
    return points


def cookie(lobes, depth):
    return lambda angle: 1 + depth * math.cos(lobes * angle)


def pill(image, cx, cy, length, thickness, degrees, colour):
    w, h = image.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [cx - length / 2, cy - thickness / 2, cx + length / 2, cy + thickness / 2], radius=thickness / 2, fill=255)
    mask = mask.rotate(degrees, center=(cx, cy), resample=Image.BICUBIC)
    image.paste(Image.new("RGB", (w, h), hex_rgb(colour)), mask=mask)


# --- The wallpapers ----------------------------------------------------------


def dune(w, h):
    """Dusk over the desert: a low sun and dunes in layers, back to front."""
    image = sky(w, h, "#24162b", "#a35c55", horizon=0.62)
    draw = ImageDraw.Draw(image)
    disc(draw, 0.68 * w, 0.47 * h, 0.115 * h, hex_rgb("#f4c58e"))
    layers = [
        ("#c07a5c", 0.56, [(0.035, 1, 0.4), (0.015, 3, 1.3)]),
        ("#9c5a4a", 0.63, [(0.045, 1, 2.2), (0.012, 4, 0.2)]),
        ("#76403d", 0.71, [(0.05, 1, 4.0), (0.016, 2.5, 1.0)]),
        ("#522b30", 0.80, [(0.045, 1.2, 0.9), (0.014, 3.5, 2.7)]),
        ("#311a22", 0.90, [(0.04, 0.8, 3.1), (0.012, 3, 0.5)]),
    ]
    for colour, base, waves in layers:
        draw.polygon(ridge(w, h, base, waves), fill=hex_rgb(colour))
    return image


def tide(w, h):
    """Night sea: a moon, a few stars and waves rolling in."""
    image = sky(w, h, "#081226", "#1f4466", horizon=0.6)
    draw = ImageDraw.Draw(image)
    disc(draw, 0.24 * w, 0.24 * h, 0.075 * h, hex_rgb("#e3edf4"))
    for x, y, r in [(0.42, 0.12, 4), (0.55, 0.22, 3), (0.71, 0.09, 5), (0.83, 0.28, 3), (0.9, 0.14, 4),
                    (0.1, 0.4, 3), (0.62, 0.36, 3), (0.35, 0.33, 2.5)]:
        disc(draw, x * w, y * h, r * h / 2160 * 2, hex_rgb("#c9d9e6"))
    layers = [
        ("#2f7593", 0.58, [(0.012, 3, 0.3), (0.006, 9, 1.0)]),
        ("#215c7c", 0.65, [(0.016, 2.5, 1.7), (0.007, 8, 2.1)]),
        ("#174565", 0.73, [(0.02, 2, 0.6), (0.008, 7, 3.0)]),
        ("#0f304b", 0.82, [(0.024, 1.6, 2.4), (0.009, 6, 0.4)]),
        ("#081d31", 0.91, [(0.026, 1.3, 4.1), (0.01, 5, 1.6)]),
    ]
    for colour, base, waves in layers:
        draw.polygon(ridge(w, h, base, waves), fill=hex_rgb(colour))
    return image


def bloom(w, h):
    """Material shapes in pinks on dark plum."""
    image = Image.new("RGB", (w, h), hex_rgb("#1d1118"))
    draw = ImageDraw.Draw(image)
    u = h / 2160
    draw.polygon(polar(0.70 * w, 0.58 * h, 560 * u, cookie(9, 0.075), 0.3), fill=hex_rgb("#4a2238"))
    draw.polygon(polar(0.70 * w, 0.58 * h, 410 * u, cookie(9, 0.075), 0.3), fill=hex_rgb("#7d3559"))
    draw.polygon(polar(0.22 * w, 0.30 * h, 330 * u, cookie(4, 0.2), math.pi / 4), fill=hex_rgb("#3a1a2c"))
    draw.polygon(polar(0.33 * w, 0.72 * h, 160 * u, cookie(12, 0.09)), fill=hex_rgb("#ff8fbf"))
    pill(image, 0.42 * w, 0.42 * h, 880 * u, 210 * u, 24, "#f3b3d0")
    draw = ImageDraw.Draw(image)
    for x, y, r, colour in [(0.54, 0.18, 44, "#ff8fbf"), (0.12, 0.62, 66, "#4a2238"),
                            (0.88, 0.22, 34, "#f3b3d0"), (0.9, 0.86, 52, "#7d3559")]:
        disc(draw, x * w, y * h, r * u, hex_rgb(colour))
    return image


def graphite(w, h):
    """Grey Material shapes on true black, for OLED screens."""
    image = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    u = h / 2160
    draw.polygon(polar(0.74 * w, 0.36 * h, 540 * u, cookie(7, 0.09), 0.5), fill=hex_rgb("#161616"))
    draw.polygon(polar(0.74 * w, 0.36 * h, 380 * u, cookie(7, 0.09), 0.5), fill=hex_rgb("#262626"))
    draw.polygon(polar(0.20 * w, 0.70 * h, 300 * u, cookie(4, 0.2), 0), fill=hex_rgb("#1c1c1c"))
    draw.polygon(polar(0.46 * w, 0.24 * h, 120 * u, cookie(10, 0.1)), fill=hex_rgb("#8c8c8c"))
    pill(image, 0.40 * w, 0.66 * h, 820 * u, 190 * u, -18, "#3d3d3d")
    draw = ImageDraw.Draw(image)
    for x, y, r, colour in [(0.92, 0.78, 58, "#262626"), (0.1, 0.2, 40, "#3d3d3d"),
                            (0.6, 0.84, 30, "#8c8c8c"), (0.56, 0.5, 22, "#5a5a5a")]:
        disc(draw, x * w, y * h, r * u, hex_rgb(colour))
    return image


def meadow(w, h):
    """A light morning: soft sun over green hills, for the light mode."""
    image = sky(w, h, "#f6f3e8", "#e3ecdb", horizon=0.6)
    draw = ImageDraw.Draw(image)
    disc(draw, 0.30 * w, 0.32 * h, 0.1 * h, hex_rgb("#f5d27f"))
    layers = [
        ("#c6dcbd", 0.55, [(0.04, 1, 1.0), (0.012, 3, 0.4)]),
        ("#a3c99f", 0.63, [(0.05, 1, 3.0), (0.014, 2.5, 1.8)]),
        ("#80b184", 0.72, [(0.05, 1.3, 0.2), (0.012, 3.5, 2.6)]),
        ("#5f966b", 0.81, [(0.045, 1, 2.0), (0.014, 3, 0.9)]),
        ("#437a54", 0.91, [(0.04, 0.9, 4.4), (0.012, 3, 1.2)]),
    ]
    for colour, base, waves in layers:
        draw.polygon(ridge(w, h, base, waves), fill=hex_rgb(colour))
    return image


# --- Generic designs, for the colour-scheme themes ---------------------------

HILLS = [[(0.035, 1, 0.4), (0.015, 3, 1.3)], [(0.045, 1, 2.2), (0.012, 4, 0.2)], [(0.05, 1, 4.0), (0.016, 2.5, 1.0)],
         [(0.045, 1.2, 0.9), (0.014, 3.5, 2.7)], [(0.04, 0.8, 3.1), (0.012, 3, 0.5)]]
WAVES = [[(0.012, 3, 0.3), (0.006, 9, 1.0)], [(0.016, 2.5, 1.7), (0.007, 8, 2.1)], [(0.02, 2, 0.6), (0.008, 7, 3.0)],
         [(0.024, 1.6, 2.4), (0.009, 6, 0.4)], [(0.026, 1.3, 4.1), (0.01, 5, 1.6)]]


def layered(w, h, p, shapes, bases, sun_at, sun_size, stars=False):
    """Sky, a sun or moon, then five bands blending from p["far"] to p["near"]."""
    image = sky(w, h, p["sky"][0], p["sky"][1], horizon=0.62)
    draw = ImageDraw.Draw(image)
    disc(draw, sun_at[0] * w, sun_at[1] * h, sun_size * h, hex_rgb(p["sun"]))
    if stars:
        star = mix(p["sun"], p["sky"][0], 0.2)
        for x, y, r in [(0.42, 0.12, 4), (0.55, 0.22, 3), (0.71, 0.09, 5), (0.83, 0.28, 3), (0.9, 0.14, 4),
                        (0.1, 0.4, 3), (0.62, 0.36, 3), (0.35, 0.33, 2.5)]:
            disc(draw, x * w, y * h, r * h / 1080, hex_rgb(star))
    for index, (waves, base) in enumerate(zip(shapes, bases)):
        draw.polygon(ridge(w, h, base, waves), fill=hex_rgb(mix(p["far"], p["near"], index / 4)))
    return image


def landscape(w, h, p):
    return layered(w, h, p, HILLS, [0.56, 0.63, 0.71, 0.80, 0.90], (0.68, 0.47), 0.115)


def sea(w, h, p):
    return layered(w, h, p, WAVES, [0.58, 0.65, 0.73, 0.82, 0.91], (0.24, 0.24), 0.075, stars=True)


def shapes(w, h, p, background):
    """Material shapes: accents c0..c3, quiet shapes c4 and c5."""
    c = p["colours"]
    image = Image.new("RGB", (w, h), hex_rgb(background))
    draw = ImageDraw.Draw(image)
    u = h / 2160
    draw.polygon(polar(0.70 * w, 0.58 * h, 560 * u, cookie(9, 0.075), 0.3), fill=hex_rgb(c[4]))
    draw.polygon(polar(0.70 * w, 0.58 * h, 410 * u, cookie(9, 0.075), 0.3), fill=hex_rgb(mix(c[0], c[4], 0.35)))
    draw.polygon(polar(0.22 * w, 0.30 * h, 330 * u, cookie(4, 0.2), math.pi / 4), fill=hex_rgb(c[5]))
    draw.polygon(polar(0.33 * w, 0.72 * h, 160 * u, cookie(12, 0.09)), fill=hex_rgb(c[1]))
    pill(image, 0.42 * w, 0.42 * h, 880 * u, 210 * u, 24, c[2])
    draw = ImageDraw.Draw(image)
    for x, y, r, colour in [(0.54, 0.18, 44, c[3]), (0.12, 0.62, 66, c[4]), (0.88, 0.22, 34, c[1]),
                            (0.9, 0.86, 52, c[0])]:
        disc(draw, x * w, y * h, r * u, hex_rgb(colour))
    return image


def scheme_design(scheme):
    p = scheme["wallpaper"]
    if p["design"] == "shapes":
        return lambda w, h: shapes(w, h, p, scheme["layers"][2])
    return lambda w, h: {"landscape": landscape, "sea": sea}[p["design"]](w, h, p)


DESIGNS = {"dune": dune, "tide": tide, "bloom": bloom, "graphite": graphite, "meadow": meadow}
DESIGNS.update({key: scheme_design(scheme) for key, scheme in SCHEMES.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("names", nargs="*", choices=[[]] + list(DESIGNS), default=[])
    parser.add_argument("--size", default="3840x2160")
    args = parser.parse_args()
    width, height = (int(n) for n in args.size.split("x"))
    for name in args.names or DESIGNS:
        folder = os.path.join(ROOT, "themes", f"dev.blxshell.{name}")
        os.makedirs(folder, exist_ok=True)
        image = DESIGNS[name](width * SCALE, height * SCALE).resize((width, height), Image.LANCZOS)
        image.save(os.path.join(folder, "wallpaper.png"), optimize=True)
        image.resize((960, 540), Image.LANCZOS).save(os.path.join(folder, "preview.jpg"), quality=88)
        print(f"drew {name}")


if __name__ == "__main__":
    main()
