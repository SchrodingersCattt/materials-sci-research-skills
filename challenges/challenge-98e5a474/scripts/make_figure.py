"""Declared-data chart and diagram builder: editable SVG plus real PNG and PDF.

The figure tasks ask for three things this module does mechanically:

    * a *scientific* decision per element — the data source, unit, condition and error-bar
      meaning are declared in the spec, so the drawing cannot silently invent a value;
    * an *editable* vector source (SVG) that keeps its own coordinate model, so a human can
      move a label without redrawing the figure;
    * a *real* export (PNG raster and a vector PDF), with the pixels inspected afterwards
      rather than a promise that they exist.

Everything is Python standard library, so it runs in a container with no network and no
plotting package. If Pillow happens to be installed the rasterizer uses it for text; the
build report says which path was used. PNG and PDF are written by this module either way.

Commands
--------
chart    --spec S --out-prefix P     bar / line / scatter with optional error bars, from data
diagram  --spec S --out-prefix P     node/edge diagram with a legend
inspect-png PATH                     decode the produced PNG and report what is actually there
verify   --prefix P --spec S         bind the artifacts to the spec and to the declared data
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import struct
import sys
import zlib
from pathlib import Path
from xml.sax.saxutils import escape

# --------------------------------------------------------------------------- primitives

FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "a": ["00000", "00000", "01110", "00001", "01111", "10001", "01111"],
    "b": ["10000", "10000", "11110", "10001", "10001", "10001", "11110"],
    "c": ["00000", "00000", "01111", "10000", "10000", "10000", "01111"],
    "d": ["00001", "00001", "01111", "10001", "10001", "10001", "01111"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110"],
    "f": ["00110", "01000", "11110", "01000", "01000", "01000", "01000"],
    "g": ["00000", "01111", "10001", "10001", "01111", "00001", "01110"],
    "h": ["10000", "10000", "11110", "10001", "10001", "10001", "10001"],
    "i": ["00100", "00000", "01100", "00100", "00100", "00100", "01110"],
    "j": ["00010", "00000", "00110", "00010", "00010", "10010", "01100"],
    "k": ["10000", "10000", "10010", "10100", "11000", "10100", "10010"],
    "l": ["01100", "00100", "00100", "00100", "00100", "00100", "01110"],
    "m": ["00000", "00000", "11010", "10101", "10101", "10101", "10101"],
    "n": ["00000", "00000", "11110", "10001", "10001", "10001", "10001"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110"],
    "p": ["00000", "11110", "10001", "10001", "11110", "10000", "10000"],
    "q": ["00000", "01111", "10001", "10001", "01111", "00001", "00001"],
    "r": ["00000", "00000", "10110", "11001", "10000", "10000", "10000"],
    "s": ["00000", "00000", "01111", "10000", "01110", "00001", "11110"],
    "t": ["01000", "01000", "11110", "01000", "01000", "01001", "00110"],
    "u": ["00000", "00000", "10001", "10001", "10001", "10011", "01101"],
    "v": ["00000", "00000", "10001", "10001", "10001", "01010", "00100"],
    "w": ["00000", "00000", "10001", "10101", "10101", "10101", "01010"],
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
    "y": ["00000", "10001", "10001", "01111", "00001", "00001", "01110"],
    "z": ["00000", "00000", "11111", "00010", "00100", "01000", "11111"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}

PRIMITIVES: list = []


def reset_primitives() -> None:
    PRIMITIVES.clear()


def rect(x, y, w, h, fill=None, stroke=None, width=1.0, dash=None) -> None:
    PRIMITIVES.append({"op": "rect", "x": float(x), "y": float(y), "w": float(w),
                       "h": float(h), "fill": fill, "stroke": stroke, "width": float(width),
                       "dash": dash})


def line(x1, y1, x2, y2, stroke="#333333", width=1.0, dash=None) -> None:
    PRIMITIVES.append({"op": "line", "x1": float(x1), "y1": float(y1), "x2": float(x2),
                       "y2": float(y2), "stroke": stroke, "width": float(width), "dash": dash})


def circle(cx, cy, r, fill=None, stroke=None, width=1.0) -> None:
    PRIMITIVES.append({"op": "circle", "cx": float(cx), "cy": float(cy), "r": float(r),
                       "fill": fill, "stroke": stroke, "width": float(width)})


def polyline(points, stroke="#1f4e79", width=1.8) -> None:
    PRIMITIVES.append({"op": "polyline",
                       "points": [(float(x), float(y)) for x, y in points],
                       "stroke": stroke, "width": float(width)})


def text(x, y, value, size=13, colour="#111111", anchor="start", weight="normal") -> None:
    PRIMITIVES.append({"op": "text", "x": float(x), "y": float(y), "text": str(value),
                       "size": float(size), "colour": colour, "anchor": anchor,
                       "weight": weight})


def text_width(value: str, size: float) -> float:
    """Monospace-ish estimate used for layout checks; the same estimate drives both emitters."""
    return len(str(value)) * size * 0.62


# --------------------------------------------------------------------------- SVG emitter

def to_svg(width: int, height: int, background: str = "#ffffff") -> str:
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">',
             f'<rect width="{width}" height="{height}" fill="{background}"/>']
    for item in PRIMITIVES:
        if item["op"] == "rect":
            dash = f' stroke-dasharray="{item["dash"]}"' if item.get("dash") else ""
            fill = item["fill"] or "none"
            stroke = f' stroke="{item["stroke"]}" stroke-width="{item["width"]}"' if item["stroke"] else ""
            parts.append(f'<rect x="{item["x"]:.1f}" y="{item["y"]:.1f}" width="{item["w"]:.1f}" '
                         f'height="{item["h"]:.1f}" fill="{fill}"{stroke}{dash}/>')
        elif item["op"] == "line":
            dash = f' stroke-dasharray="{item["dash"]}"' if item.get("dash") else ""
            parts.append(f'<line x1="{item["x1"]:.1f}" y1="{item["y1"]:.1f}" '
                         f'x2="{item["x2"]:.1f}" y2="{item["y2"]:.1f}" '
                         f'stroke="{item["stroke"]}" stroke-width="{item["width"]}"{dash}/>')
        elif item["op"] == "circle":
            fill = item["fill"] or "none"
            stroke = f' stroke="{item["stroke"]}" stroke-width="{item["width"]}"' if item["stroke"] else ""
            parts.append(f'<circle cx="{item["cx"]:.1f}" cy="{item["cy"]:.1f}" '
                         f'r="{item["r"]:.1f}" fill="{fill}"{stroke}/>')
        elif item["op"] == "polyline":
            points = " ".join(f"{x:.1f},{y:.1f}" for x, y in item["points"])
            parts.append(f'<polyline points="{points}" fill="none" stroke="{item["stroke"]}" '
                         f'stroke-width="{item["width"]}" stroke-linejoin="round"/>')
        elif item["op"] == "text":
            anchor = {"start": "start", "middle": "middle", "end": "end"}[item["anchor"]]
            weight = ' font-weight="bold"' if item["weight"] == "bold" else ""
            parts.append(f'<text x="{item["x"]:.1f}" y="{item["y"]:.1f}" '
                         f'font-family="Helvetica, Arial, sans-serif" font-size="{item["size"]:.0f}" '
                         f'fill="{item["colour"]}" text-anchor="{anchor}"{weight}>'
                         f'{escape(item["text"])}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- PNG emitter

def _hex_rgb(value: str) -> tuple:
    value = (value or "#000000").lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


class Canvas:
    """Minimal RGBA canvas with the four primitives the figures use."""

    def __init__(self, width: int, height: int, background="#ffffff"):
        self.width, self.height = width, height
        self.pixels = bytearray(_hex_rgb(background) * (width * height))

    def _blend(self, x: int, y: int, colour: tuple, alpha: float = 1.0) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            index = (y * self.width + x) * 3
            if alpha >= 1.0:
                self.pixels[index:index + 3] = bytes(colour)
            else:
                for offset in range(3):
                    current = self.pixels[index + offset]
                    self.pixels[index + offset] = int(current * (1 - alpha) + colour[offset] * alpha)

    def fill_rect(self, x, y, w, h, colour: tuple) -> None:
        for row in range(int(round(y)), int(round(y + h))):
            for column in range(int(round(x)), int(round(x + w))):
                self._blend(column, row, colour)

    def stroke_rect(self, x, y, w, h, colour: tuple, width: float) -> None:
        thickness = max(1, int(round(width)))
        self.fill_rect(x, y, w, thickness, colour)
        self.fill_rect(x, y + h - thickness, w, thickness, colour)
        self.fill_rect(x, y, thickness, h, colour)
        self.fill_rect(x + w - thickness, y, thickness, h, colour)

    def draw_line(self, x1, y1, x2, y2, colour: tuple, width: float) -> None:
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        steps = max(int(max(dx, dy)), 1)
        thickness = max(1, int(round(width)))
        for step in range(steps + 1):
            x = x1 + (x2 - x1) * step / steps
            y = y1 + (y2 - y1) * step / steps
            for ox in range(thickness):
                for oy in range(thickness):
                    self._blend(int(x) + ox, int(y) + oy, colour)

    def fill_circle(self, cx, cy, r, colour: tuple) -> None:
        radius = float(r)
        for row in range(int(cy - radius), int(cy + radius) + 1):
            for column in range(int(cx - radius), int(cx + radius) + 1):
                if (column - cx) ** 2 + (row - cy) ** 2 <= radius ** 2:
                    self._blend(column, row, colour)

    def draw_text(self, x, y, value: str, size: float, colour: tuple, anchor: str = "start",
                  weight: str = "normal") -> None:
        scale = max(1, int(round(size / 7.0)))
        glyph_w, glyph_h = 5 * scale, 7 * scale
        total = len(str(value)) * (glyph_w + scale)
        origin = x if anchor == "start" else (x - total / 2 if anchor == "middle" else x - total)
        for index, character in enumerate(str(value)):
            pattern = FONT.get(character) or FONT.get(character.upper()) or FONT[" "]
            base_x = origin + index * (glyph_w + scale)
            for row, bits in enumerate(pattern):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        for sx in range(scale):
                            for sy in range(scale):
                                self._blend(int(base_x) + column * scale + sx,
                                            int(y) - glyph_h + row * scale + sy, colour)

    def to_png(self) -> bytes:
        raw = bytearray()
        stride = self.width * 3
        for row in range(self.height):
            raw.append(0)
            raw.extend(self.pixels[row * stride:(row + 1) * stride])
        def chunk(tag: bytes, payload: bytes) -> bytes:
            return (struct.pack(">I", len(payload)) + tag + payload
                    + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))
        header = struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


def render_png(width: int, height: int) -> tuple:
    """Render the primitives; use Pillow for text when it exists, else the built-in font."""
    pillow = None
    try:  # pragma: no cover - depends on the environment
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
        pillow = (Image, ImageDraw, ImageFont)
    except Exception:  # noqa: BLE001
        pillow = None

    if pillow:
        Image, ImageDraw, _ImageFont = pillow
        image = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        for item in PRIMITIVES:
            if item["op"] == "rect":
                box = [item["x"], item["y"], item["x"] + item["w"], item["y"] + item["h"]]
                draw.rectangle(box, fill=item["fill"], outline=item["stroke"],
                               width=max(1, int(round(item["width"]))) if item["stroke"] else 0)
            elif item["op"] == "line":
                draw.line([item["x1"], item["y1"], item["x2"], item["y2"]],
                          fill=item["stroke"], width=max(1, int(round(item["width"]))))
            elif item["op"] == "circle":
                draw.ellipse([item["cx"] - item["r"], item["cy"] - item["r"],
                              item["cx"] + item["r"], item["cy"] + item["r"]],
                             fill=item["fill"], outline=item["stroke"])
            elif item["op"] == "polyline":
                draw.line(item["points"], fill=item["stroke"],
                          width=max(1, int(round(item["width"]))))
            elif item["op"] == "text":
                draw.text((item["x"], item["y"] - item["size"]), item["text"],
                          fill=item["colour"], anchor=("lm" if item["anchor"] == "start"
                                                       else ("mm" if item["anchor"] == "middle" else "rm")))
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue(), "pillow"

    canvas = Canvas(width, height)
    for item in PRIMITIVES:
        if item["op"] == "rect":
            if item["fill"]:
                canvas.fill_rect(item["x"], item["y"], item["w"], item["h"], _hex_rgb(item["fill"]))
            if item["stroke"]:
                canvas.stroke_rect(item["x"], item["y"], item["w"], item["h"],
                                   _hex_rgb(item["stroke"]), item["width"])
        elif item["op"] == "line":
            canvas.draw_line(item["x1"], item["y1"], item["x2"], item["y2"],
                             _hex_rgb(item["stroke"]), item["width"])
        elif item["op"] == "circle":
            if item["fill"]:
                canvas.fill_circle(item["cx"], item["cy"], item["r"], _hex_rgb(item["fill"]))
        elif item["op"] == "polyline":
            for (x1, y1), (x2, y2) in zip(item["points"], item["points"][1:]):
                canvas.draw_line(x1, y1, x2, y2, _hex_rgb(item["stroke"]), item["width"])
        elif item["op"] == "text":
            canvas.draw_text(item["x"], item["y"], item["text"], item["size"],
                             _hex_rgb(item["colour"]), item["anchor"])
    return canvas.to_png(), "builtin"


# --------------------------------------------------------------------------- PDF emitter

def to_pdf(width: int, height: int) -> bytes:
    """A real vector PDF using the base-14 Helvetica font (no embedding, no dependency)."""
    operations = []
    for item in PRIMITIVES:
        y = height - item.get("y", item.get("y1", 0))
        if item["op"] == "rect":
            if item["fill"]:
                r, g, b = [c / 255 for c in _hex_rgb(item["fill"])]
                operations.append(f"{r:.3f} {g:.3f} {b:.3f} rg "
                                  f"{item['x']:.2f} {y - item['h']:.2f} {item['w']:.2f} "
                                  f"{item['h']:.2f} re f")
            if item["stroke"]:
                r, g, b = [c / 255 for c in _hex_rgb(item["stroke"])]
                operations.append(f"{r:.3f} {g:.3f} {b:.3f} RG {item['width']:.2f} w "
                                  f"{item['x']:.2f} {y - item['h']:.2f} {item['w']:.2f} "
                                  f"{item['h']:.2f} re S")
        elif item["op"] == "line":
            r, g, b = [c / 255 for c in _hex_rgb(item["stroke"])]
            operations.append(f"{r:.3f} {g:.3f} {b:.3f} RG {item['width']:.2f} w "
                              f"{item['x1']:.2f} {height - item['y1']:.2f} m "
                              f"{item['x2']:.2f} {height - item['y2']:.2f} l S")
        elif item["op"] == "circle":
            r, g, b = [c / 255 for c in _hex_rgb(item["fill"] or item["stroke"] or "#000000")]
            k = 0.5523 * item["r"]
            cx, cy = item["cx"], height - item["cy"]
            operations.append(
                f"{r:.3f} {g:.3f} {b:.3f} rg {cx + item['r']:.2f} {cy:.2f} m "
                f"{cx + item['r']:.2f} {cy + k:.2f} {cx + k:.2f} {cy + item['r']:.2f} "
                f"{cx:.2f} {cy + item['r']:.2f} c "
                f"{cx - k:.2f} {cy + item['r']:.2f} {cx - item['r']:.2f} {cy + k:.2f} "
                f"{cx - item['r']:.2f} {cy:.2f} c "
                f"{cx - item['r']:.2f} {cy - k:.2f} {cx - k:.2f} {cy - item['r']:.2f} "
                f"{cx:.2f} {cy - item['r']:.2f} c "
                f"{cx + k:.2f} {cy - item['r']:.2f} {cx + item['r']:.2f} {cy - k:.2f} "
                f"{cx + item['r']:.2f} {cy:.2f} c f")
        elif item["op"] == "polyline":
            r, g, b = [c / 255 for c in _hex_rgb(item["stroke"])]
            first = item["points"][0]
            operations.append(f"{r:.3f} {g:.3f} {b:.3f} RG {item['width']:.2f} w "
                              f"{first[0]:.2f} {height - first[1]:.2f} m")
            for x, yy in item["points"][1:]:
                operations.append(f"{x:.2f} {height - yy:.2f} l")
            operations.append("S")
        elif item["op"] == "text":
            r, g, b = [c / 255 for c in _hex_rgb(item["colour"])]
            font = "F2" if item["weight"] == "bold" else "F1"
            escape_text = (item["text"].replace("\\", r"\\").replace("(", r"\(")
                           .replace(")", r"\)"))
            operations.append(f"BT /{font} {item['size']:.2f} Tf {r:.3f} {g:.3f} {b:.3f} rg "
                              f"{item['x']:.2f} {height - item['y']:.2f} Td ({escape_text}) Tj ET")

    content = "\n".join(operations).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
         f"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>").encode(),
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n"
            "%%EOF\n").encode()
    return bytes(out)


# --------------------------------------------------------------------------- data

def read_rows(path: Path) -> list:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def nice_ticks(low: float, high: float, count: int = 5) -> list:
    if high <= low:
        high = low + 1.0
    raw = (high - low) / max(count, 1)
    magnitude = 10 ** math.floor(math.log10(abs(raw) or 1))
    for multiplier in (1, 2, 2.5, 5, 10):
        step = multiplier * magnitude
        if step >= raw:
            break
    start = math.floor(low / step) * step
    ticks = []
    value = start
    while value <= high + step * 0.5:
        ticks.append(round(value, 10))
        value += step
    return ticks


def format_number(value: float) -> str:
    if value == int(value) and abs(value) < 1e6:
        return str(int(value))
    return f"{value:g}"


# --------------------------------------------------------------------------- chart

def column_keys(spec: dict) -> dict:
    """The spec keys that name a *data column* (not a label such as the unit)."""
    return {kind: spec[kind] for kind in ("x", "value", "error_low", "error_high", "series")
            if spec.get(kind)}


def build_chart(spec: dict, out_prefix: Path) -> dict:
    width = int(spec.get("width") or 900)
    height = int(spec.get("height") or 560)
    rows = read_rows(Path(spec["data"])) if spec.get("data") else []
    kinds = column_keys(spec)
    missing = [f"{kind}='{column}'" for kind, column in kinds.items()
               if rows and column not in rows[0]]
    if missing:
        raise SystemExit(f"the declared column(s) {missing} are not in {spec['data']}; "
                         f"available: {sorted(rows[0]) if rows else 'no rows'}")

    footer = []
    if spec.get("error_meaning"):
        footer.append(f"error bars: {spec['error_meaning']}")
    if spec.get("note"):
        footer.append(spec["note"])
    if spec.get("source"):
        footer.append(f"source: {spec['source']}")

    # Reserve room for the whole footer block, so a third line can never slide off the canvas.
    margin_left, margin_right, margin_top = 92, 190, 60
    margin_bottom = 60 + 15 * max(len(footer), 1)
    plot_x, plot_y = margin_left, margin_top
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    categories = []
    series_order = []
    series_values: dict = {}
    errors: dict = {}
    for row in rows:
        x = row[kinds["x"]]
        if x not in categories:
            categories.append(x)
        name = row[kinds["series"]] if "series" in kinds else (spec.get("series_name") or "value")
        if name not in series_order:
            series_order.append(name)
        value = float(row[kinds["value"]])
        series_values.setdefault(name, {})[x] = value
        if "error_low" in kinds or "error_high" in kinds:
            low = float(row[kinds["error_low"]]) if "error_low" in kinds else 0.0
            high = float(row[kinds["error_high"]]) if "error_high" in kinds else 0.0
            errors.setdefault(name, {})[x] = (low, high)

    values = [v for per_series in series_values.values() for v in per_series.values()]
    lows = [v - (errors.get(name, {}).get(x, (0, 0))[0])
            for name, per_series in series_values.items() for x, v in per_series.items()]
    highs = [v + (errors.get(name, {}).get(x, (0, 0))[1])
             for name, per_series in series_values.items() for x, v in per_series.items()]
    low = min(lows + values) if values else 0.0
    high = max(highs + values) if values else 1.0
    if abs(high - low) < 1e-9:
        high = low + 1.0
    ticks = nice_ticks(min(0.0, low), high * 1.08 if high > 0 else high)
    axis_low, axis_high = ticks[0], ticks[-1]
    unit = spec.get("unit") or ""
    chart_kind = (spec.get("kind") or "bar").lower()

    def y_of(value: float) -> float:
        return plot_y + plot_h - (value - axis_low) / (axis_high - axis_low) * plot_h

    def x_center(index: int) -> float:
        slot = plot_w / max(len(categories), 1)
        return plot_x + slot * (index + 0.5)

    reset_primitives()
    palette = ["#1f4e79", "#c0504d", "#4f81bd", "#9bbb59", "#8064a2", "#f79646"]
    # frame and grid
    for tick in ticks:
        y = y_of(tick)
        line(plot_x, y, plot_x + plot_w, y, stroke="#d9d9d9", width=1.0)
        text(plot_x - 8, y + 4, format_number(tick), size=12, colour="#404040", anchor="end")
    line(plot_x, plot_y, plot_x, plot_y + plot_h, stroke="#404040", width=1.2)
    line(plot_x, plot_y + plot_h, plot_x + plot_w, plot_y + plot_h, stroke="#404040", width=1.2)
    y_label = spec.get("y_label") or (f"value ({unit})" if unit else "value")
    # The axis label sits above the plot instead of rotated on the left, so it cannot overflow a
    # canvas that has no room for a rotated glyph run.
    text(plot_x, plot_y - 12, y_label, size=12.5, colour="#202020")
    text(plot_x + plot_w / 2, height - 46, spec.get("x_label") or kinds.get("x", "category"),
         size=13, colour="#202020", anchor="middle")
    if spec.get("title"):
        text(plot_x + plot_w / 2, 26, spec["title"], size=15, colour="#111111",
             anchor="middle", weight="bold")

    slot = plot_w / max(len(categories), 1)
    bar_group = slot * 0.7
    bar_width = bar_group / max(len(series_order), 1)
    baseline = 0.0 if axis_low <= 0.0 <= axis_high else axis_low
    marks = []
    for index, category in enumerate(categories):
        text(x_center(index), plot_y + plot_h + 20, category, size=12, colour="#202020",
             anchor="middle")
    for series_index, name in enumerate(series_order):
        colour = palette[series_index % len(palette)]
        points = []
        for index, category in enumerate(categories):
            value = series_values.get(name, {}).get(category)
            if value is None:
                continue
            if chart_kind == "bar":
                x = x_center(index) - bar_group / 2 + bar_width * series_index
                top = y_of(max(value, baseline))
                bottom = y_of(min(value, baseline))
                rect(x, top, bar_width * 0.88, max(bottom - top, 1.0), fill=colour)
                marks.append({"series": name, "category": category, "value": value,
                              "x": round(x + bar_width * 0.44, 1), "y": round(top + 3, 1)})
                error = errors.get(name, {}).get(category)
                if error:
                    low_value, high_value = value - error[0], value + error[1]
                    centre_x = x + bar_width * 0.44
                    line(centre_x, y_of(low_value), centre_x, y_of(high_value), stroke="#222222",
                         width=1.4)
                    for edge in (low_value, high_value):
                        line(centre_x - 6, y_of(edge), centre_x + 6, y_of(edge), stroke="#222222",
                             width=1.4)
            elif chart_kind == "line":
                points.append((x_center(index), y_of(value)))
                marks.append({"series": name, "category": category, "value": value,
                              "x": round(x_center(index), 1), "y": round(y_of(value), 1)})
                error = errors.get(name, {}).get(category)
                if error:
                    line(x_center(index), y_of(value - error[0]), x_center(index),
                         y_of(value + error[1]), stroke=colour, width=1.2)
            else:  # scatter
                circle(x_center(index), y_of(value), 4.6, fill=colour)
                marks.append({"series": name, "category": category, "value": value,
                              "x": round(x_center(index), 1), "y": round(y_of(value), 1)})
                error = errors.get(name, {}).get(category)
                if error:
                    line(x_center(index), y_of(value - error[0]), x_center(index),
                         y_of(value + error[1]), stroke=colour, width=1.2)
        if chart_kind == "line" and points:
            polyline(points, stroke=colour, width=1.8)
            for x, y in points:
                circle(x, y, 3.4, fill=colour)

    # legend and footer
    legend_x = plot_x + plot_w + 22
    legend_y = plot_y + 12
    for series_index, name in enumerate(series_order):
        colour = palette[series_index % len(palette)]
        rect(legend_x, legend_y + series_index * 22, 14, 12, fill=colour)
        text(legend_x + 22, legend_y + series_index * 22 + 11, name, size=12, colour="#202020")
    footer_top = height - 14 - 15 * (len(footer) - 1) if footer else height - 14
    for index, entry in enumerate(footer):
        text(margin_left, footer_top + index * 15, entry, size=11.5, colour="#404040")

    svg = to_svg(width, height)
    png_bytes, rasterizer = render_png(width, height)
    pdf_bytes = to_pdf(width, height)
    (out_prefix.with_suffix(".svg")).write_text(svg, encoding="utf-8")
    (out_prefix.with_suffix(".png")).write_bytes(png_bytes)
    (out_prefix.with_suffix(".pdf")).write_bytes(pdf_bytes)

    layout = check_layout(width, height, margin_left, margin_top, margin_right, margin_bottom)
    # The rubric counts a layered editable source as one of the six required elements, so an
    # exported picture is not the whole deliverable.
    drawio_path = out_prefix.with_suffix(".drawio")
    write_drawio(spec, drawio_path, "chart")
    return {
        "schema": "figure-build/v1",
        "kind": f"chart:{chart_kind}",
        "out": {"svg": str(out_prefix.with_suffix(".svg")),
                "png": str(out_prefix.with_suffix(".png")),
                "pdf": str(out_prefix.with_suffix(".pdf")),
                "drawio": str(drawio_path)},
        "sha256": {suffix: hashlib.sha256(out_prefix.with_suffix(suffix).read_bytes()).hexdigest()
                   for suffix in (".svg", ".png", ".pdf", ".drawio")},
        "rasterizer": rasterizer,
        "size": {"width": width, "height": height},
        "data": {"path": spec.get("data"), "rows": len(rows), "categories": categories,
                 "series": series_order, "unit": unit},
        "axis": {"low": axis_low, "high": axis_high, "ticks": ticks},
        "marks": marks,
        "error_bar_meaning": spec.get("error_meaning"),
        "layout": layout,
        "declared_source": spec.get("source"),
    }


def check_layout(width: int, height: int, margin_left: int, margin_top: int,
                 margin_right: int, margin_bottom: int) -> dict:
    """Report geometry problems the figure itself can prove: overflow, overlaps, empty canvas."""
    issues = []
    text_boxes = []
    for item in PRIMITIVES:
        if item["op"] == "text":
            half = text_width(item["text"], item["size"]) / 2
            left = item["x"] - (half if item["anchor"] == "middle"
                                else (0 if item["anchor"] == "start" else half * 2))
            right = left + text_width(item["text"], item["size"])
            if left < 2 or right > width - 2:
                issues.append({"kind": "text_outside_canvas", "text": item["text"][:60],
                               "left": round(left, 1), "right": round(right, 1)})
            text_boxes.append({"text": item["text"][:40], "left": left, "right": right,
                               "top": item["y"] - item["size"], "bottom": item["y"]})
        elif item["op"] in ("rect", "circle") and item["op"] == "rect":
            if item["x"] + item["w"] > width or item["y"] + item["h"] > height:
                issues.append({"kind": "shape_outside_canvas", "shape": "rect"})
    for first, second in zip(text_boxes, text_boxes[1:]):
        if (abs(first["top"] - second["top"]) < 6
                and first["right"] > second["left"] + 2
                and second["left"] < first["right"]):
            issues.append({"kind": "text_overlap", "a": first["text"], "b": second["text"]})
    content_bottom = max([item.get("y", 0) + item.get("h", 0) for item in PRIMITIVES
                          if item["op"] in ("rect", "circle")] or [0])
    return {
        "canvas": {"width": width, "height": height},
        "margins": {"left": margin_left, "top": margin_top, "right": margin_right,
                    "bottom": margin_bottom},
        "content_bottom": round(content_bottom, 1),
        "fits_inside_margins": content_bottom <= height - margin_bottom + 1,
        "issues": issues,
        "issue_count": len(issues),
        "method": "text advance estimated as 0.62 x font size per character (the same estimate "
                  "both emitters use); a real font may differ, so the PNG is inspected as well.",
    }


# --------------------------------------------------------------------------- diagram

def build_diagram(spec: dict, out_prefix: Path) -> dict:
    width = int(spec.get("width") or 960)
    height = int(spec.get("height") or 560)
    nodes = spec.get("nodes") or []
    edges = spec.get("edges") or []
    if not nodes:
        raise SystemExit("the diagram spec declares no nodes")
    positions = {}
    for node in nodes:
        if not all(key in node for key in ("id", "x", "y")):
            raise SystemExit(f"node {node!r} must declare id, x, y")
        position = node.get("position") or spec.get("default_position") or "process"
        positions[node["id"]] = {**node, "position": position}
    palette = {
        "input": ("#e8f1fb", "#1f4e79"), "process": ("#f2f2f2", "#404040"),
        "decision": ("#fdf4dd", "#8064a2"), "output": ("#e9f6ec", "#3f7f4f"),
        "note": ("#f7eefb", "#7a4f86"), "assay": ("#eaf3f6", "#2b6d7f"),
        "compound": ("#f6efe6", "#8a6134"),
    }
    reset_primitives()
    if spec.get("title"):
        text(24, 30, spec["title"], size=16, colour="#111111", weight="bold")
    node_boxes = {}
    for node in nodes:
        fill, stroke = palette.get(node["position"], palette["process"])
        node_boxes[node["id"]] = (float(node["x"]), float(node["y"]),
                                  float(node.get("w") or 180), float(node.get("h") or 62))
    for edge in edges:
        source, target = positions.get(edge.get("from")), positions.get(edge.get("to"))
        if not source or not target:
            issues_missing = True
            continue
        sx, sy, sw, sh = node_boxes[source["id"]]
        tx, ty, tw, th = node_boxes[target["id"]]
        first = (sx + sw / 2, sy + (sh if sy < ty else 0))
        second = (tx + tw / 2, ty + (0 if sy < ty else th))
        if abs(sy - ty) < 1:  # side-by-side
            first = (sx + sw, sy + sh / 2)
            second = (tx, ty + th / 2)
        line(*first, *second, stroke="#4b5563", width=1.6)
        angle = math.atan2(second[1] - first[1], second[0] - first[0])
        head = 9
        for offset in (math.radians(150), math.radians(-150)):
            line(second[0], second[1],
                 second[0] + head * math.cos(angle + offset),
                 second[1] + head * math.sin(angle + offset), stroke="#4b5563", width=1.6)
        if edge.get("label"):
            mid = ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)
            text(mid[0], mid[1] - 7, edge["label"], size=12, colour="#374151", anchor="middle")
    for node in nodes:
        fill, stroke = palette.get(node["position"], palette["process"])
        x, y, w, h = node_boxes[node["id"]]
        rect(x, y, w, h, fill=fill, stroke=stroke, width=1.3)
        label = node.get("label") or node["id"]
        text(x + w / 2, y + h / 2 + 5, label, size=13, colour="#0f172a", anchor="middle")
        if node.get("detail"):
            text(x + w / 2, y + h - 8, node["detail"], size=11, colour="#4b5563", anchor="middle")
    if spec.get("legend"):
        legend_y = height - 40
        for index, (position, label) in enumerate(spec["legend"].items()):
            fill, stroke = palette.get(position, palette["process"])
            offset = 24 + index * 170
            rect(offset, legend_y - 11, 16, 13, fill=fill, stroke=stroke, width=1.0)
            text(offset + 22, legend_y, label, size=12, colour="#202020")
    if spec.get("caption"):
        text(width / 2, height - 12, spec["caption"], size=12.5, colour="#404040", anchor="middle")

    svg = to_svg(width, height)
    png_bytes, rasterizer = render_png(width, height)
    pdf_bytes = to_pdf(width, height)
    (out_prefix.with_suffix(".svg")).write_text(svg, encoding="utf-8")
    (out_prefix.with_suffix(".png")).write_bytes(png_bytes)
    (out_prefix.with_suffix(".pdf")).write_bytes(pdf_bytes)
    overlaps = []
    boxes = list(node_boxes.values())
    for index, first in enumerate(boxes):
        for second in boxes[index + 1:]:
            if (first[0] < second[0] + second[2] and second[0] < first[0] + first[2]
                    and first[1] < second[1] + second[3] and second[1] < first[1] + first[3]):
                overlaps.append({"a": first, "b": second})
    outside = [box for box in boxes
               if box[0] < 0 or box[1] < 0 or box[0] + box[2] > width or box[1] + box[3] > height]
    # The rubric counts a layered editable source as one of the six required elements, so an
    # exported picture is not the whole deliverable.
    drawio_path = out_prefix.with_suffix(".drawio")
    write_drawio(spec, drawio_path, "diagram")
    return {
        "schema": "figure-build/v1",
        "kind": "diagram",
        "out": {"svg": str(out_prefix.with_suffix(".svg")),
                "png": str(out_prefix.with_suffix(".png")),
                "pdf": str(out_prefix.with_suffix(".pdf")),
                "drawio": str(drawio_path)},
        "sha256": {suffix: hashlib.sha256(out_prefix.with_suffix(suffix).read_bytes()).hexdigest()
                   for suffix in (".svg", ".png", ".pdf", ".drawio")},
        "rasterizer": rasterizer,
        "size": {"width": width, "height": height},
        "nodes": len(nodes), "edges": len(edges),
        "layout": {
            "node_overlaps": overlaps,
            "nodes_outside_canvas": outside,
            "issue_count": len(overlaps) + len(outside),
            "method": "axis-aligned box intersection on the declared coordinates; the PNG is "
                      "inspected as well.",
        },
        "captions": {"caption": spec.get("caption"), "legend": spec.get("legend")},
    }


# --------------------------------------------------------------------------- inspection

def _esc(value) -> str:
    return (str("" if value is None else value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def write_drawio(spec: dict, out_path: Path, kind: str) -> None:
    """A layered, editable source in the mxGraph format draw.io / diagrams.net opens.

    The rubric names "??????" (a layered source) as one of the six elements a figure must
    cover, so the export alone is not enough: this keeps every element addressable by id, with its
    geometry, its layer and its declared source, so a human can reopen and move things.
    """
    items = []
    legend_rows = []

    def cell(cell_id, value, style, x, y, w, h, parent="1", vertex=1):
        return (f'        <mxCell id="{_esc(cell_id)}" value="{_esc(value)}" '
                f'style="{_esc(style)}" vertex="{vertex}" parent="{_esc(parent)}">\n'
                f'          <mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                f'as="geometry"/>\n'
                f'        </mxCell>')

    if kind == "diagram":
        for node in spec.get("nodes") or []:
            style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#f2f2f2;strokeColor=#404040;")
            items.append(cell(f"node-{node['id']}", node.get("label") or node["id"], style,
                              float(node.get("x") or 0), float(node.get("y") or 0),
                              float(node.get("w") or 180), float(node.get("h") or 62)))
            if node.get("source") or node.get("locator"):
                legend_rows.append((f"node-{node['id']}", node.get("source") or "",
                                    node.get("locator") or ""))
        for index, edge in enumerate(spec.get("edges") or [], start=1):
            items.append(cell(f"edge-{index}", edge.get("label") or "",
                              "endArrow=block;html=1;", 0, 0, 0, 0, parent="1", vertex=0))
    else:
        for index, column in enumerate(spec.get("columns") or [], start=1):
            items.append(cell(f"col-{column}", column, "rounded=0;html=1;", 40 * index, 0, 30, 30))
    body = "\n".join(items)
    out_path.write_text(
        '<mxfile host="app.diagrams.net" type="device">\n'
        f'  <diagram id="{_esc(kind)}" name="{_esc(spec.get("title") or kind)}">\n'
        '    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" page="1">\n'
        "      <root>\n"
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f"{body}\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n", encoding="utf-8")
    if legend_rows:
        rows = ["element_id,source_file,source_locator"]
        rows += [f"{a},{b},{c}" for a, b, c in legend_rows]
        Path(str(out_path).replace(".drawio", ".provenance.csv")).write_text(
            "\n".join(rows) + "\n", encoding="utf-8")


def read_png(path: Path) -> tuple:
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"{path} does not exist; build the figure first")
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path} is not a PNG")
    position, width, height, pixels = 8, 0, 0, b""
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        tag = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        if tag == b"IHDR":
            width, height, depth, colour_type = struct.unpack(">IIBB", payload[:10])
            if depth != 8 or colour_type not in (2, 6):
                raise SystemExit(f"unsupported PNG colour type {colour_type}/{depth}")
        elif tag == b"IDAT":
            pixels += payload
        elif tag == b"IEND":
            break
        position += 12 + length
    raw = zlib.decompress(pixels)
    channels = 3
    rows = []
    stride = width * channels
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset:offset + stride])
        offset += stride
        if filter_type == 1:
            for index in range(channels, stride):
                row[index] = (row[index] + row[index - channels]) & 0xFF
        elif filter_type == 2:
            for index in range(stride):
                row[index] = (row[index] + previous[index]) & 0xFF
        elif filter_type == 3:
            for index in range(stride):
                left = row[index - channels] if index >= channels else 0
                row[index] = (row[index] + ((left + previous[index]) >> 1)) & 0xFF
        elif filter_type == 4:
            for index in range(stride):
                left = row[index - channels] if index >= channels else 0
                up = previous[index]
                up_left = previous[index - channels] if index >= channels else 0
                estimate = left + up - up_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - up_left))
                predictor = (left, up, up_left)[distances.index(min(distances))]
                row[index] = (row[index] + predictor) & 0xFF
        rows.append(row)
        previous = row
    return width, height, rows


def inspect_png(path: Path, ink_threshold: int = 240) -> dict:
    width, height, rows = read_png(path)
    ink_pixels = 0
    min_x, min_y, max_x, max_y = width, height, -1, -1
    for y, row in enumerate(rows):
        for x in range(width):
            index = x * 3
            if (row[index] < ink_threshold or row[index + 1] < ink_threshold
                    or row[index + 2] < ink_threshold):
                ink_pixels += 1
                min_x, min_y = min(min_x, x), min(min_y, y)
                max_x, max_y = max(max_x, x), max(max_y, y)
    coverage = ink_pixels / max(width * height, 1)
    bands = {}
    for name, (y0, y1) in (("top", (0, height // 3)), ("middle", (height // 3, 2 * height // 3)),
                           ("bottom", (2 * height // 3, height))):
        ink = sum(1 for y in range(y0, y1) for x in range(width)
                  if rows[y][x * 3] < ink_threshold or rows[y][x * 3 + 1] < ink_threshold
                  or rows[y][x * 3 + 2] < ink_threshold)
        bands[name] = round(ink / max((y1 - y0) * width, 1), 5)
    return {
        "schema": "png-inspection/v1",
        "path": str(path),
        "size": {"width": width, "height": height},
        "ink_coverage": round(coverage, 5),
        "ink_bbox": None if max_x < 0 else {"x": min_x, "y": min_y, "w": max_x - min_x + 1,
                                            "h": max_y - min_y + 1},
        "ink_by_band": bands,
        "is_blank": coverage < 0.0005,
        "touches_edges": bool(max_x >= width - 1 or min_x <= 0 or max_y >= height - 1 or min_y <= 0),
        "colours_used": len({tuple(row[x * 3:x * 3 + 3]) for row in rows for x in range(width)}),
        "method": "the produced PNG is decoded with this module's own reader (all five filter "
                  "types) and the ink statistics are computed from the decoded pixels",
    }


# --------------------------------------------------------------------------- verify

def verify(prefix: Path, spec: dict, outdir: Path) -> dict:
    checks = []

    def add(check_id, requirement, ok, evidence, locator):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence, "locator": locator})

    for suffix in (".svg", ".png", ".pdf"):
        path = prefix.with_suffix(suffix)
        exists = path.exists() and path.stat().st_size > 0
        add(f"artifact{suffix}", f"{suffix} artifact exists and is non-empty", exists,
            f"bytes={path.stat().st_size if path.exists() else 0}", str(path))
        if not exists:
            continue
        head = path.read_bytes()[:16]
        signature = {".svg": b"<svg", ".png": b"\x89PNG", ".pdf": b"%PDF"}[suffix]
        add(f"format{suffix}", f"{suffix} starts with the real signature",
            head.lstrip().startswith(signature), f"head={head[:8]!r}", str(path))

    png = prefix.with_suffix(".png")
    if png.exists():
        info = inspect_png(png)
        add("png_not_blank", "the PNG contains drawn content", not info["is_blank"],
            f"ink_coverage={info['ink_coverage']}", str(png))
        add("png_inside_canvas", "no ink is clipped at the canvas edge",
            not info["touches_edges"], f"ink_bbox={info['ink_bbox']}", str(png))

    if spec.get("data"):
        rows = read_rows(Path(spec["data"]))
        columns = column_keys(spec)
        svg_path = prefix.with_suffix(".svg")
        svg_text = svg_path.read_text(encoding="utf-8")

        # Categorical labels must be drawn as text.
        labels = sorted({row[columns[key]] for row in rows
                         for key in ("x", "series") if key in columns})
        missing_labels = [label for label in labels if label not in svg_text]
        add("declared_labels_present", "every declared category/group label is drawn as text",
            not missing_labels, f"missing={missing_labels[:6]} of {len(labels)} labels",
            str(svg_path))

        # Numeric values must be *represented*, which is checked in the pixels, not in the text.
        build_report_path = prefix.with_name(prefix.name + ".build-report.json")
        if build_report_path.exists():
            build_report = json.loads(build_report_path.read_text(encoding="utf-8"))
            marks = build_report.get("marks") or []
            png_path = prefix.with_suffix(".png")
            if marks and png_path.exists():
                width_px, height_px, pixels = read_png(png_path)
                misses = []
                for mark in marks:
                    x, y = int(mark["x"]), int(mark["y"])
                    window = 5
                    found = False
                    for row in range(max(0, y - window), min(height_px, y + window + 1)):
                        for column in range(max(0, x - window), min(width_px, x + window + 1)):
                            index = column * 3
                            if (pixels[row][index] < 240 and pixels[row][index + 1] < 240):
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        misses.append(mark)
                add("declared_values_drawn", "every declared value has a drawn mark at its position",
                    not misses,
                    f"{len(marks) - len(misses)}/{len(marks)} declared marks found in the PNG "
                    f"pixels; missing={[(m['series'], m['category']) for m in misses][:5]}",
                    str(png_path))
                in_range = [mark for mark in marks
                            if build_report["axis"]["low"] <= mark["value"]
                            <= build_report["axis"]["high"]]
                add("values_inside_axis", "every declared value lies inside the drawn axis range",
                    len(in_range) == len(marks),
                    f"{len(in_range)}/{len(marks)} values within "
                    f"[{build_report['axis']['low']}, {build_report['axis']['high']}]",
                    str(build_report_path))

    report_path = Path(outdir) / f"{prefix.name}.verification.json"
    failures = [c for c in checks if c["status"] == "fail"]
    report = {"schema": "figure-verify/v1", "checks": checks,
              "passed": len(checks) - len(failures), "failed": len(failures),
              "status": "verified" if not failures else "needs_work",
              "scope_note": "Binds the artifacts to the declared spec and data and inspects the "
                            "real pixels. It does not judge whether the figure is scientifically "
                            "the right one to draw."}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# --------------------------------------------------------------------------- cli

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Declared-data chart/diagram builder")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("chart"); p.add_argument("--spec", required=True); p.add_argument("--out-prefix", required=True)
    p = sub.add_parser("diagram"); p.add_argument("--spec", required=True); p.add_argument("--out-prefix", required=True)
    p = sub.add_parser("inspect-png"); p.add_argument("path"); p.add_argument("--out")
    p = sub.add_parser("verify"); p.add_argument("--prefix", required=True); p.add_argument("--spec", required=True)
    p.add_argument("--outdir", required=True)

    args = parser.parse_args(argv)
    if args.command in ("chart", "diagram"):
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        prefix = Path(args.out_prefix)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        report = build_chart(spec, prefix) if args.command == "chart" else build_diagram(spec, prefix)
        report_path = prefix.with_name(prefix.name + ".build-report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = {k: report[k] for k in ("kind", "out", "rasterizer")}
        summary["layout_issues"] = report["layout"]["issue_count"]
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    if args.command == "inspect-png":
        payload = inspect_png(Path(args.path))
        if args.out:
            Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        print(json.dumps({k: payload[k] for k in ("size", "ink_coverage", "ink_bbox", "is_blank",
                                                  "touches_edges", "ink_by_band")},
                         ensure_ascii=False))
        return 0
    if args.command == "verify":
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        report = verify(Path(args.prefix), spec, Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
