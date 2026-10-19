"""Menu effects textures: the sunburst behind the PLAY button. Run: python3 tools/gen_menu_fx.py"""
import math
import numpy as np
from PIL import Image

N = 512
y, x = (np.mgrid[0:N, 0:N] + 0.5 - N / 2) / (N / 2)
r = np.sqrt(x * x + y * y)
a = np.arctan2(y, x)
rays = 16
wedge = 0.5 + 0.5 * np.cos(a * rays)
wedge = np.clip((wedge - 0.35) / 0.3, 0, 1)
fall = np.clip(1.0 - r, 0, 1) ** 1.4
core = np.clip(1.0 - r / 0.55, 0, 1) ** 2 * 0.5
alpha = np.clip(wedge * fall * 0.85 + core, 0, 1)
col = np.zeros((N, N, 4), np.float32)
col[..., 0] = 1.0
col[..., 1] = 0.93 - 0.2 * r
col[..., 2] = 0.55 - 0.35 * r
col[..., 3] = alpha
Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), "RGBA").save("assets/ui/mm_rays.png")
print("wrote assets/ui/mm_rays.png")
