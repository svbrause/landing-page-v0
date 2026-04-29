from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "hybrid_overlay_frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FRAME_W, FRAME_H = 720, 1280
SCREEN_W, SCREEN_H = 390, 844
FPS = 24
DURATION = 6
TOTAL = FPS * DURATION

# Approximate phone-screen corners from the floating-phone Veo clip.
DEST = [(219, 613), (506, 613), (503, 1090), (218, 1084)]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def find_coeffs(pa, pb):
    # Coefficients for PIL perspective transform from rectangle to quadrilateral.
    import numpy as np

    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    A = np.matrix(matrix, dtype=float)
    B = np.array(pb).reshape(8)
    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)


COEFFS = find_coeffs(DEST, [(0, 0), (SCREEN_W, 0), (SCREEN_W, SCREEN_H), (0, SCREEN_H)])


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pill(draw, x, y, text, fill, stroke=None):
    f = font(18, True)
    bbox = draw.textbbox((0, 0), text, font=f)
    w = bbox[2] - bbox[0] + 34
    h = 34
    rounded(draw, (x, y, x + w, y + h), 17, fill, stroke or fill)
    draw.text((x + 17, y + 7), text, fill=(52, 38, 34, 255), font=f)
    return w


def base_overlay() -> Image.Image:
    return Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 0))


def draw_header(draw: ImageDraw.ImageDraw, title: str):
    rounded(draw, (0, 0, SCREEN_W, 88), 0, (255, 252, 249, 245))
    draw.text((142, 42), title, fill=(33, 28, 26, 255), font=font(22, True))
    draw.text((24, 42), "<", fill=(33, 28, 26, 255), font=font(26, True))


def draw_scan(t: float) -> Image.Image:
    im = base_overlay()
    draw = ImageDraw.Draw(im)
    draw_header(draw, "Ponce AI")
    draw.text((94, 104), "Center your face", fill=(72, 58, 54, 255), font=font(22, True))
    draw.text((110, 133), "Scanning...", fill=(154, 111, 102, 255), font=font(18))
    # Face guide.
    alpha = int(145 + 55 * math.sin(t * math.tau * 2))
    draw.ellipse((73, 178, 317, 486), outline=(232, 179, 164, alpha), width=4)
    y = 180 + int((300 * ((t * 1.4) % 1)))
    draw.line((82, y, 308, y), fill=(255, 255, 255, 175), width=3)
    rounded(draw, (120, 706, 270, 752), 23, (255, 252, 249, 235), (232, 210, 202, 255), 2)
    draw.text((154, 719), "Scan Face", fill=(64, 45, 41, 255), font=font(18, True))
    return im


def draw_results(t: float) -> Image.Image:
    im = base_overlay()
    draw = ImageDraw.Draw(im)
    draw_header(draw, "Assessment")
    # Highlight zones.
    zones = [
        (118, 214, 270, 250, "Forehead"),
        (112, 314, 172, 348, "Under eyes"),
        (216, 314, 278, 348, ""),
        (92, 390, 173, 452, "Cheeks"),
        (217, 392, 300, 454, ""),
        (123, 500, 268, 552, "Jawline"),
    ]
    for i, (x1, y1, x2, y2, label) in enumerate(zones):
        draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=(236, 164, 146, 60), outline=(222, 123, 105, 210), width=3)
        if label:
            draw.text((x1, y1 - 26), label, fill=(88, 58, 52, 235), font=font(15, True))
    y0 = 604
    cards = [("Botox", "Forehead lines"), ("Filler", "Cheek contour"), ("Microneedling", "Skin texture")]
    for i, (name, sub) in enumerate(cards):
        y = y0 + i * 58
        rounded(draw, (28, y, 362, y + 48), 17, (255, 252, 249, 242), (236, 214, 207, 255), 2)
        draw.text((50, y + 9), name, fill=(45, 35, 31, 255), font=font(18, True))
        draw.text((210, y + 12), sub, fill=(122, 92, 84, 255), font=font(15))
        draw.text((330, y + 12), "+", fill=(188, 98, 84, 255), font=font(22, True))
    return im


def draw_saved(t: float) -> Image.Image:
    im = Image.new("RGBA", (SCREEN_W, SCREEN_H), (255, 252, 249, 248))
    draw = ImageDraw.Draw(im)
    draw_header(draw, "Ponce AI")
    draw.text((34, 124), "Your interests", fill=(42, 32, 29, 255), font=font(30, True))
    draw.text((34, 161), "Saved to discuss later", fill=(128, 96, 88, 255), font=font(18))
    items = [("Botox", "Forehead lines"), ("Filler", "Cheek contour"), ("Microneedling", "Skin texture")]
    for i, (name, sub) in enumerate(items):
        y = 220 + i * 100
        rounded(draw, (30, y, 360, y + 76), 18, (255, 255, 255, 255), (235, 217, 211, 255), 2)
        draw.ellipse((50, y + 24, 78, y + 52), fill=(207, 139, 124, 255))
        draw.text((58, y + 27), "✓", fill=(255, 255, 255, 255), font=font(18, True))
        draw.text((96, y + 15), name, fill=(45, 35, 31, 255), font=font(21, True))
        draw.text((96, y + 44), sub, fill=(126, 94, 86, 255), font=font(16))
    rounded(draw, (52, 620, 338, 672), 26, (53, 38, 34, 255))
    draw.text((92, 636), "Discuss at consult", fill=(255, 255, 255, 255), font=font(19, True))
    return im


def screen_for_frame(i: int) -> Image.Image:
    t = i / FPS
    if t < 2:
        return draw_scan(t / 2)
    if t < 4:
        return draw_results((t - 2) / 2)
    return draw_saved((t - 4) / 2)


for i in range(TOTAL):
    full = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    screen = screen_for_frame(i)
    warped = screen.transform((FRAME_W, FRAME_H), Image.Transform.PERSPECTIVE, COEFFS, Image.Resampling.BICUBIC)
    full.alpha_composite(warped)
    full.save(OUT_DIR / f"overlay_{i:04d}.png")

print(f"Wrote {TOTAL} overlay frames to {OUT_DIR}")
