"""Buff badges: a small round portrait of each hero in a gold ring with a green "boosted" pip.

    python3 tools/gen_badges.py          (from the repo root)

Writes assets/ui/badge_<hero>.png (128 px). The game shows it over a tower the hero is boosting (its aura
or its ability), while that tower is selected.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
S = 4                       # supersampling
N = 128 * S


def disc(r, cx=N / 2, cy=N / 2):
    y, x = np.mgrid[0:N, 0:N] + 0.5
    return np.sqrt((x - cx) ** 2 + (y - cy) ** 2) <= r


def badge(hid, col):
    y, x = (np.mgrid[0:N, 0:N] + 0.5) / N
    out = np.zeros((N, N, 4), np.float32)
    c = np.array(col, np.float32)
    # outline, gold ring (lit from the top), dark inner line, hero-coloured disc
    m_out = disc(0.495 * N)
    out[m_out] = [0.03, 0.05, 0.11, 1.0]
    m_ring = disc(0.465 * N)
    gold_top = np.array([1.0, 0.93, 0.55])
    gold_bot = np.array([0.72, 0.42, 0.08])
    t = np.clip((y - 0.05) / 0.9, 0, 1)[..., None]
    ring = gold_top * (1 - t) + gold_bot * t
    out[m_ring, :3] = ring[m_ring]
    out[disc(0.375 * N)] = [0.05, 0.07, 0.12, 1.0]
    m_in = disc(0.36 * N)
    rr = np.sqrt((x - 0.5) ** 2 + (y - 0.42) ** 2)[..., None]
    fill = np.clip(c * 1.25 + 0.12, 0, 1) * (1 - np.clip(rr / 0.42, 0, 1)) + c * 0.55 * np.clip(rr / 0.42, 0, 1)
    out[m_in, :3] = fill[m_in]
    # the face, scaled to the inner disc and clipped to it
    face = Image.open(os.path.join(ROOT, "assets", "ui", "face_%s.png" % hid)).convert("RGBA")
    fs = int(0.78 * N)
    face = face.resize((fs, fs), Image.LANCZOS)
    layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    layer.alpha_composite(face, ((N - fs) // 2, int(0.135 * N)))
    f = np.asarray(layer).astype(np.float32) / 255.0
    fa = f[..., 3:4] * m_in[..., None]
    out[..., :3] = out[..., :3] * (1 - fa) + f[..., :3] * fa
    # a glossy highlight across the top of the ring and disc
    hl = np.clip(1 - np.sqrt(((x - 0.5) / 0.34) ** 2 + ((y - 0.2) / 0.12) ** 2), 0, 1) ** 1.5 * 0.35
    out[..., :3] = np.clip(out[..., :3] + hl[..., None] * m_ring[..., None], 0, 1)
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")
    # the "boosted" pip: green disc with a white up arrow, bottom right
    d = ImageDraw.Draw(img)
    px, py, pr = 0.79 * N, 0.79 * N, 0.19 * N
    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(8, 14, 28, 255))
    pr2 = pr - 0.035 * N
    d.ellipse([px - pr2, py - pr2, px + pr2, py + pr2], fill=(70, 200, 60, 255))
    d.ellipse([px - pr2 * 0.8, py - pr2 * 0.95, px + pr2 * 0.8, py - pr2 * 0.1], fill=(130, 235, 110, 255))
    a = pr2 * 0.62
    d.polygon([(px, py - a), (px + a * 0.9, py + a * 0.05), (px + a * 0.35, py + a * 0.05), (px + a * 0.35, py + a * 0.8),
               (px - a * 0.35, py + a * 0.8), (px - a * 0.35, py + a * 0.05), (px - a * 0.9, py + a * 0.05)],
              fill=(255, 255, 255, 255), outline=(8, 14, 28, 255), width=int(0.012 * N))
    return img.resize((128, 128), Image.LANCZOS)


def main():
    heroes = json.load(open(os.path.join(ROOT, "data", "heroes.json")))["heroes"]
    for hid, h in heroes.items():
        badge(hid, h.get("color", [0.5, 0.5, 0.5])).save(os.path.join(ROOT, "assets", "ui", "badge_%s.png" % hid))
    print("wrote %d badges" % len(heroes))


main()
