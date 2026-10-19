"""Lava mask for a map's painted ground (v0.9.21): every glowing crack and molten pool the ground render painted, as a
soft grey mask the ground shader animates (heat pulsing and flowing through the cracks).

    python3 tools/lava_mask.py volcano_ridge      -> assets/textures/ground_volcano_ridge_lava.png (half resolution)

A pixel is lava when it is bright, strongly saturated and red-dominant (the painted lava is orange to yellow; basalt,
ash and the road are dull browns and greys). Re-run it whenever the ground is re-rendered."""
import sys
import numpy as np
from PIL import Image, ImageFilter

mid = sys.argv[1] if len(sys.argv) > 1 else "volcano_ridge"
src = "assets/textures/ground_%s.png" % mid
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255.0
R, G, B = im[..., 0], im[..., 1], im[..., 2]
mx = im.max(-1)
mn = im.min(-1)
sat = (mx - mn) / np.maximum(mx, 1e-3)
m = np.clip((R - 0.32) / 0.35, 0, 1) * np.clip((sat - 0.42) / 0.25, 0, 1) * np.clip((R / (G + 0.02) - 1.12) / 0.35, 0, 1)
img = Image.fromarray((m * 255).astype(np.uint8), "L")
img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
out = "assets/textures/ground_%s_lava.png" % mid
img.save(out)
print(out, img.size, "lava %.1f%%" % (100.0 * float((np.asarray(img) > 20).mean())))
