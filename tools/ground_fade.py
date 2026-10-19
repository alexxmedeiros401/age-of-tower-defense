"""Fade a ground texture's outer band to one flat colour, so it meets the game's far-ground plane without a seam.

    python3 tools/ground_fade.py assets/textures/ground_<map>.png [--band 1.6] [--px 64]

game.gd paints the far plane (under and beyond the ground texture) with the average colour of the texture's edge rows
(_edge_color), so a busy edge (the HQ grounds' tufted forest floor) showed a hard line where it ended. The last `band`
world units (px pixels per unit) now blend into the band's own average colour, which is what the edge rows then hold.
map_ground_hq.py runs this on every render.
"""
import sys
import numpy as np
from PIL import Image


def fade(im, band_px):
    """im: float32 HxWx3 in 0..1. Returns a copy whose outer band_px pixels blend smoothly to the band's mean colour."""
    h, w, _ = im.shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)).astype(np.float32)
    flat = im[d < band_px].mean(0)
    t = np.clip(d / band_px, 0, 1)
    wgt = (t * t * (3 - 2 * t))[..., None]
    return im * wgt + flat * (1 - wgt)


if __name__ == "__main__":
    path = sys.argv[1]
    a = sys.argv
    band = float(a[a.index("--band") + 1]) if "--band" in a else 1.6
    px = float(a[a.index("--px") + 1]) if "--px" in a else 64.0
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    out = fade(im, band * px)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(path)
    print("faded", path, "band %.0f px" % (band * px))
