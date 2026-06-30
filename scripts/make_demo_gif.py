# -*- coding: utf-8 -*-
"""Generate an illustrative animated GIF of the MatchFeature 2-step workflow.

Pure-PIL drawing (no QGIS needed). Output: assets/matchfeature_demo.gif
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 960, 520
BG = (247, 249, 250)
INK = (28, 42, 48)
TEAL = (20, 160, 160)
ORANGE = (240, 130, 40)
GRAY = (150, 162, 168)
GRAY_FILL = (224, 230, 232)
WHITE = (255, 255, 255)

FONT_DIR = "/opt/plugins-venv/lib/python3.11/site-packages/reportlab/fonts"
def font(sz, bold=True):
    p = os.path.join(FONT_DIR, "VeraBd.ttf" if bold else "Vera.ttf")
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()

F_TITLE = font(40, True)
F_STEP = font(24, True)
F_SMALL = font(20, False)

# Scene starts below the header (y >= 200) to avoid any collision.
SOURCE = [(150, 240), (300, 220), (322, 392), (162, 410)]
TARGET1 = [(560, 230), (700, 250), (690, 378), (540, 360)]
TARGET2 = [(720, 392), (862, 372), (882, 486), (732, 498)]

SRC_C = (232, 318)
T1_C = (622, 305)
T2_C = (798, 437)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def brush(draw, x, y, scale=1.0):
    draw.line([(x, y), (x + int(48 * scale), y - int(48 * scale))],
              fill=(90, 70, 60), width=int(10 * scale))
    draw.ellipse([x - int(17 * scale), y - int(17 * scale),
                  x + int(17 * scale), y + int(17 * scale)], fill=TEAL,
                 outline=WHITE, width=3)


def badge(draw, c, n, color):
    x, y = c
    r = 22
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=WHITE, width=4)
    w = draw.textlength(str(n), font=F_STEP)
    draw.text((x - w / 2, y - 14), str(n), font=F_STEP, fill=WHITE)


def base(draw, t1_fill=0.0, t2_fill=0.0, highlight_source=False):
    draw.polygon(SOURCE, fill=TEAL, outline=(12, 110, 110))
    if highlight_source:
        draw.line(SOURCE + [SOURCE[0]], fill=ORANGE, width=6, joint="curve")
    for poly, f in ((TARGET1, t1_fill), (TARGET2, t2_fill)):
        col = lerp(GRAY_FILL, TEAL, f)
        draw.polygon(poly, fill=col, outline=(12, 110, 110) if f > 0.5 else GRAY)


def header(draw, step_text, step_color):
    draw.text((40, 26), "MatchFeature", font=F_TITLE, fill=TEAL)
    draw.text((42, 78), "Copiar atributos e estilo  ·  mesma camada",
              font=F_SMALL, fill=GRAY)
    pad = 16
    tw = draw.textlength(step_text, font=F_STEP)
    x0, y0 = 40, 118
    draw.rounded_rectangle([x0, y0, x0 + tw + pad * 2, y0 + 44], radius=22,
                           fill=step_color)
    draw.text((x0 + pad, y0 + 9), step_text, font=F_STEP, fill=WHITE)


frames = []
def add(img, n=1):
    for _ in range(n):
        frames.append(img.copy())


# Phase 1: copy source
for k in range(8):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "Passo 1  ·  copiar a origem", TEAL)
    base(d, highlight_source=(k % 2 == 0))
    brush(d, SRC_C[0] + 18, SRC_C[1] + 6, 1.0)
    badge(d, (SOURCE[0][0] + 4, SOURCE[0][1] + 4), 1, ORANGE)
    add(img, 1)

# Phase 2: arrow travels
ax0, ay0 = 332, 300
ax1, ay1 = 545, 290
for k in range(10):
    t = k / 9.0
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "Copiado!  a aplicar…", ORANGE)
    base(d)
    cx = int(ax0 + (ax1 - ax0) * t)
    cy = int(ay0 + (ay1 - ay0) * t)
    d.line([(ax0, ay0), (cx, cy)], fill=ORANGE, width=8)
    d.polygon([(cx, cy), (cx - 16, cy - 9), (cx - 16, cy + 9)], fill=ORANGE)
    add(img, 1)

# Phase 3: apply to targets
for k in range(11):
    t = k / 10.0
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    header(d, "Passo 2  ·  aplicar aos destinos", TEAL)
    base(d, t1_fill=min(1.0, t * 1.3), t2_fill=max(0.0, (t - 0.25) * 1.4))
    if t > 0.15:
        badge(d, T1_C, 2, ORANGE)
    if t > 0.55:
        badge(d, T2_C, 2, ORANGE)
    add(img, 1)

# Hold final
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
header(d, "Concluido!  ·  Ctrl+Z anula", TEAL)
base(d, t1_fill=1.0, t2_fill=1.0)
d.text((40, H - 34), "Ideia & concecao: Hugo P. Teixeira   ·   GPL v2+",
       font=F_SMALL, fill=GRAY)
add(img, 16)

os.makedirs("/app/assets", exist_ok=True)
out = "/app/assets/matchfeature_demo.gif"
frames[0].save(out, save_all=True, append_images=frames[1:], duration=130,
               loop=0, optimize=True)
print("GIF written:", out, os.path.getsize(out), "bytes,", len(frames), "frames")
