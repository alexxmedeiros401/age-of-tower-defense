"""Main-menu button icons (drawn at 4x, downsampled). Run: python3 tools/gen_menu_icons.py [--all]

Since v0.9.18 the main menu's buttons, plaques and icons are rendered in Blender by tools/blender/ui/menu_art.py
(assets/ui/mm_*.png). Only menu_portal (the NEW TIMELINE medallion) is still used from here; --all also writes the
retired gear / map / upgrade / door / plus / star icons.
"""
import math
import sys
from PIL import Image, ImageDraw, ImageFilter
OUT = "assets/ui"
S = 512


def canvas():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, name, size=192):
    if name != "menu_portal" and "--all" not in sys.argv:
        return
    # soft drop shadow under every icon
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: int(v * 0.45))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    base = Image.new("RGBA", im.size, (0, 0, 0, 0))
    base.alpha_composite(sh, (8, 14))
    base.alpha_composite(im)
    base.resize((size, size), Image.LANCZOS).save(f"{OUT}/{name}.png")
    print(name)


# gear (settings)
im, d = canvas()
pts = []
for k in range(80):
    a = k / 80 * math.tau
    tooth = 1.0 if (k // 5) % 2 == 0 else 0.0
    r = 190 + 42 * tooth
    pts.append((256 + r * math.cos(a), 256 + r * math.sin(a)))
d.polygon(pts, fill=(70, 90, 110))
pts2 = [(256 + (x - 256) * 0.9, 250 + (y - 256) * 0.9) for x, y in pts]
d.polygon(pts2, fill=(170, 205, 230))
d.ellipse((150, 144, 362, 356), fill=(110, 140, 170))
d.ellipse((196, 190, 316, 310), fill=(40, 52, 66))
d.ellipse((150, 120, 250, 170), fill=(230, 245, 255))
save(im, "menu_gear")

# map (scroll with route)
im, d = canvas()
d.polygon([(70, 120), (190, 80), (320, 120), (442, 80), (442, 400), (320, 440), (190, 400), (70, 440)], fill=(120, 80, 30))
d.polygon([(80, 128), (190, 92), (320, 128), (432, 92), (432, 388), (320, 424), (190, 388), (80, 424)], fill=(245, 222, 160))
d.polygon([(190, 92), (320, 128), (320, 424), (190, 388)], fill=(230, 200, 130))
for i, (x, y) in enumerate([(120, 360), (170, 300), (220, 320), (270, 250), (320, 270), (360, 200)]):
    d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(200, 60, 40))
d.line([(380, 140), (410, 170)], fill=(220, 40, 30), width=22)
d.line([(410, 140), (380, 170)], fill=(220, 40, 30), width=22)
save(im, "menu_map")

# upgrades (glowing up-arrow in a star burst)
im, d = canvas()
for k in range(16):
    a = k / 16 * math.tau
    d.polygon([(256, 256), (256 + 240 * math.cos(a - 0.08), 256 + 240 * math.sin(a - 0.08)),
               (256 + 240 * math.cos(a + 0.08), 256 + 240 * math.sin(a + 0.08))], fill=(120, 200, 255, 120))
d.polygon([(256, 50), (430, 250), (330, 250), (330, 460), (182, 460), (182, 250), (82, 250)], fill=(20, 70, 140))
d.polygon([(256, 80), (396, 236), (306, 236), (306, 436), (206, 436), (206, 236), (116, 236)], fill=(90, 200, 255))
d.polygon([(256, 80), (396, 236), (306, 236), (256, 120)], fill=(190, 240, 255))
save(im, "menu_upgrade")

# portal (new timeline)
im, d = canvas()
for i in range(10):
    r = 230 - i * 20
    c = (int(80 + 15 * i), int(40 + 20 * i), 255, 255)
    d.ellipse((256 - r, 256 - r, 256 + r, 256 + r), outline=c, width=18)
d.ellipse((216, 216, 296, 296), fill=(240, 250, 255))
save(im, "menu_portal")

# door (quit)
im, d = canvas()
d.rectangle((130, 60, 382, 470), fill=(70, 40, 20))
d.rectangle((150, 80, 362, 470), fill=(150, 95, 45))
d.rectangle((170, 100, 342, 260), fill=(175, 115, 60))
d.rectangle((170, 280, 342, 450), fill=(175, 115, 60))
d.ellipse((300, 260, 336, 296), fill=(255, 210, 60))
save(im, "menu_door")

# plus (add currency)
im, d = canvas()
d.ellipse((30, 30, 482, 482), fill=(30, 110, 20))
d.ellipse((40, 30, 472, 462), fill=(90, 210, 50))
d.rounded_rectangle((216, 110, 296, 402), 30, fill=(255, 255, 255))
d.rounded_rectangle((110, 216, 402, 296), 30, fill=(255, 255, 255))
save(im, "menu_plus", 96)

# level star badge
im, d = canvas()
pts = []
for k in range(10):
    r = 250 if k % 2 == 0 else 130
    a = -math.pi / 2 + k * math.pi / 5
    pts.append((256 + r * math.cos(a), 270 + r * math.sin(a)))
d.polygon(pts, fill=(170, 100, 10))
d.polygon([(256 + (x - 256) * 0.86, 270 + (y - 270) * 0.86) for x, y in pts], fill=(255, 205, 40))
d.polygon([(256 + (x - 256) * 0.6, 270 + (y - 270) * 0.6) for x, y in pts], fill=(255, 230, 120))
save(im, "menu_star", 192)
