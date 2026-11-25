#!/usr/bin/env python3
"""The colour-scheme themes: well-known palettes as static blxshell themes.

    python3 tools/schemes.py            writes every scheme theme's manifest.json
    python3 tools/wallpaper.py <name>   draws its wallpaper, in the same palette

A static theme pins all 21 roles, so the shell (and Ghostty, which follows
the shell) looks exactly like the scheme whatever the wallpaper is. Each
palette below is the scheme's own; `roles()` maps it onto the shell's roles:
surfaces from its background layers, accents from its three main colours, and
containers as the accent tinted into the surface, which `text` reads on.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mix(a, b, t):
    """`a` blended toward `b` by t (0 is a, 1 is b)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


# Each scheme: its background layers from the deepest to the most raised,
# text, muted text, a grey for outlines, accents, and the wallpaper it gets.
# "credit" names where the palette comes from (all MIT licensed).
SCHEMES = {
    "catppuccin-mocha": {
        "name": "Catppuccin Mocha", "credit": "Catppuccin (github.com/catppuccin)", "mode": "dark",
        "layers": ["#11111b", "#181825", "#1e1e2e", "#313244", "#45475a", "#585b70"],
        "text": "#cdd6f4", "muted": "#a6adc8", "grey": "#7f849c",
        "primary": "#cba6f7", "secondary": "#89b4fa", "tertiary": "#f5c2e7", "error": "#f38ba8",
        "tags": ["pastel", "purple"],
        "wallpaper": {"design": "shapes", "colours": ["#cba6f7", "#f5c2e7", "#89b4fa", "#b4befe", "#313244", "#45475a"]},
    },
    "catppuccin-latte": {
        "name": "Catppuccin Latte", "credit": "Catppuccin (github.com/catppuccin)", "mode": "light",
        "layers": ["#dce0e8", "#e6e9ef", "#eff1f5", "#e6e9ef", "#dce0e8", "#ccd0da"],
        "text": "#4c4f69", "muted": "#6c6f85", "grey": "#8c8fa1",
        "primary": "#8839ef", "secondary": "#1e66f5", "tertiary": "#ea76cb", "error": "#d20f39",
        "tags": ["pastel", "purple"],
        "wallpaper": {"design": "shapes", "colours": ["#8839ef", "#ea76cb", "#1e66f5", "#7287fd", "#ccd0da", "#bcc0cc"]},
    },
    "gruvbox": {
        "name": "Gruvbox", "credit": "Gruvbox by Pavel Pertsev (github.com/morhetz/gruvbox)", "mode": "dark",
        "layers": ["#1d2021", "#1d2021", "#282828", "#3c3836", "#504945", "#665c54"],
        "text": "#ebdbb2", "muted": "#bdae93", "grey": "#928374",
        "primary": "#fabd2f", "secondary": "#8ec07c", "tertiary": "#fe8019", "error": "#fb4934",
        "tags": ["retro", "warm", "yellow"],
        "wallpaper": {"design": "landscape", "sky": ["#1d2021", "#504945"], "sun": "#fabd2f",
                      "far": "#7c6f64", "near": "#1d2021"},
    },
    "nord": {
        "name": "Nord", "credit": "Nord by Arctic Ice Studio (nordtheme.com)", "mode": "dark",
        "layers": ["#242933", "#2a303c", "#2e3440", "#3b4252", "#434c5e", "#4c566a"],
        "text": "#eceff4", "muted": "#d8dee9", "grey": "#7b88a1",
        "primary": "#88c0d0", "secondary": "#81a1c1", "tertiary": "#b48ead", "error": "#bf616a",
        "tags": ["cool", "blue", "arctic"],
        "wallpaper": {"design": "sea", "sky": ["#242933", "#434c5e"], "sun": "#eceff4",
                      "far": "#88c0d0", "near": "#2e3440"},
    },
    "tokyo-night": {
        "name": "Tokyo Night", "credit": "Tokyo Night by enkia (github.com/enkia/tokyo-night-vscode-theme)",
        "mode": "dark",
        "layers": ["#16161e", "#16161e", "#1a1b26", "#24283b", "#292e42", "#414868"],
        "text": "#c0caf5", "muted": "#a9b1d6", "grey": "#565f89",
        "primary": "#7aa2f7", "secondary": "#7dcfff", "tertiary": "#bb9af7", "error": "#f7768e",
        "tags": ["neon", "blue", "night"],
        "wallpaper": {"design": "landscape", "sky": ["#16161e", "#3d2a55"], "sun": "#bb9af7",
                      "far": "#414868", "near": "#16161e"},
    },
    "rose-pine": {
        "name": "Rosé Pine", "credit": "Rosé Pine (rosepinetheme.com)", "mode": "dark",
        "layers": ["#13111e", "#191724", "#191724", "#1f1d2e", "#26233a", "#403d52"],
        "text": "#e0def4", "muted": "#908caa", "grey": "#6e6a86",
        "primary": "#ebbcba", "secondary": "#9ccfd8", "tertiary": "#c4a7e7", "error": "#eb6f92",
        "tags": ["soft", "pink", "muted"],
        "wallpaper": {"design": "shapes", "colours": ["#ebbcba", "#c4a7e7", "#9ccfd8", "#31748f", "#26233a", "#403d52"]},
    },
    "everforest": {
        "name": "Everforest", "credit": "Everforest by sainnhe (github.com/sainnhe/everforest)", "mode": "dark",
        "layers": ["#1e2326", "#232a2e", "#2d353b", "#343f44", "#3d484d", "#475258"],
        "text": "#d3c6aa", "muted": "#9da9a0", "grey": "#7a8478",
        "primary": "#a7c080", "secondary": "#83c092", "tertiary": "#dbbc7f", "error": "#e67e80",
        "tint": 0.2, "tags": ["green", "forest", "soft"],
        "wallpaper": {"design": "landscape", "sky": ["#1e2326", "#475258"], "sun": "#dbbc7f",
                      "far": "#5c6a4e", "near": "#1e2326"},
    },
    "dracula": {
        "name": "Dracula", "credit": "Dracula (draculatheme.com)", "mode": "dark",
        "layers": ["#191a21", "#21222c", "#282a36", "#343746", "#44475a", "#565970"],
        "text": "#f8f8f2", "muted": "#bfbfbf", "grey": "#6272a4",
        "primary": "#bd93f9", "secondary": "#ff79c6", "tertiary": "#8be9fd", "error": "#ff5555",
        "tags": ["vivid", "purple"],
        "wallpaper": {"design": "shapes", "colours": ["#bd93f9", "#ff79c6", "#8be9fd", "#50fa7b", "#343746", "#44475a"]},
    },
    "kanagawa": {
        "name": "Kanagawa", "credit": "Kanagawa by rebelot (github.com/rebelot/kanagawa.nvim)", "mode": "dark",
        "layers": ["#16161d", "#1a1a22", "#1f1f28", "#2a2a37", "#363646", "#54546d"],
        "text": "#dcd7ba", "muted": "#c8c093", "grey": "#727169",
        "primary": "#7e9cd8", "secondary": "#7aa89f", "tertiary": "#957fb8", "error": "#e46876",
        "tags": ["ink", "blue", "japanese"],
        "wallpaper": {"design": "sea", "sky": ["#16161d", "#2d4f67"], "sun": "#e6c384",
                      "far": "#7e9cd8", "near": "#1f1f28"},
    },
}


def luminance(colour):
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    a, b = luminance(a), luminance(b)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def on(colour, dark_text):
    """Text for a filled accent: the scheme's darkest layer or white, whichever reads better."""
    return max((dark_text, "#ffffff"), key=lambda text: contrast(text, colour))


def roles(s):
    """The 21 shell roles from a scheme's palette."""
    dark = s["mode"] == "dark"
    deep, low, surface, container, high, highest = s["layers"]
    # Containers: the accent tinted into the surface, so `text` reads on it.
    # A scheme with dim text ("tint") takes a lighter tint.
    tint = s.get("tint", 0.32 if dark else 0.22)
    return {
        "primary": s["primary"], "primaryText": on(s["primary"], deep), "primaryContainer": mix(surface, s["primary"], tint),
        "secondary": s["secondary"], "secondaryContainer": mix(surface, s["secondary"], tint),
        "tertiary": s["tertiary"], "tertiaryContainer": mix(surface, s["tertiary"], tint),
        "error": s["error"], "errorText": on(s["error"], deep),
        "errorContainer": mix(surface, s["error"], tint),
        "errorContainerText": mix(s["error"], s["text"], 0.7),
        "surface": surface, "surfaceContainerLow": low if dark else mix(surface, container, 0.5),
        "surfaceContainer": container, "surfaceContainerHigh": high, "surfaceContainerHighest": highest,
        "surfaceVariant": highest, "text": s["text"], "textMuted": s["muted"],
        "outline": s["grey"], "outlineVariant": highest if dark else mix(highest, s["grey"], 0.4),
    }


def manifest(key, s):
    return {
        "$schema": "https://raw.githubusercontent.com/binarylinuxx/dots/main/schemas/manifest.schema.json",
        "schema": 1,
        "type": "theme",
        "id": f"dev.blxshell.{key}",
        "name": s["name"],
        "version": "1.0.0",
        "description": f"The {s['name']} colour scheme for the whole shell and Ghostty, with a wallpaper "
                       f"in its palette. Palette: {s['credit']}.",
        "authors": [{"name": "binarylinuxx", "url": "https://github.com/binarylinuxx"}],
        "license": "MIT",
        "repository": "https://github.com/binarylinuxx/dots-themes",
        "tags": [s["mode"], "colour scheme"] + s["tags"] + ["wallpaper"],
        "previews": ["preview.jpg"],
        "project": "blxshell",
        "blxshell": ">=0.1.0",
        "compositors": ["any"],
        "wallpaper": "wallpaper.png",
        "colours": {"kind": "static", "roles": roles(s)},
    }


def main():
    for key, s in SCHEMES.items():
        folder = os.path.join(ROOT, "themes", f"dev.blxshell.{key}")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(manifest(key, s), indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {key}")


if __name__ == "__main__":
    main()
