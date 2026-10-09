"""HUD icons drawn at 4x and downsampled for clean edges. Run: python3 gen_icons.py assets/ui"""
import sys, math
from PIL import Image, ImageDraw
OUT = sys.argv[1]
S = 512

def canvas():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

def save(im, name, size=128):
    im.resize((size, size), Image.LANCZOS).save(f"{OUT}/{name}.png"); print(name)

# coin
im, d = canvas()
d.ellipse((40, 52, 472, 484), fill=(120, 70, 10))
d.ellipse((40, 30, 472, 462), fill=(255, 196, 40), outline=(150, 90, 10), width=26)
d.ellipse((120, 110, 392, 382), outline=(220, 150, 20), width=22)
d.polygon([(256, 150), (290, 230), (370, 246), (310, 300), (326, 380), (256, 338), (186, 380), (202, 300), (142, 246), (222, 230)], fill=(230, 160, 25))
d.ellipse((90, 70, 200, 150), fill=(255, 240, 170))
save(im, "icon_gold")
# heart
im, d = canvas()
def heart(d, off, col, sc=1.0):
    pts = []
    for i in range(200):
        t = i / 200 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((256 + x * 14 * sc + off[0], 240 - y * 14 * sc + off[1]))
    d.polygon(pts, fill=col)
heart(d, (0, 20), (110, 10, 20))
heart(d, (0, 0), (235, 50, 60))
heart(d, (0, -10), (255, 110, 110), 0.55)
heart(d, (0, -4), (235, 50, 60), 0.5)
d.ellipse((140, 120, 220, 180), fill=(255, 200, 200))
save(im, "icon_lives")
# robot head (waves)
im, d = canvas()
d.rounded_rectangle((70, 120, 442, 450), 70, fill=(60, 64, 76))
d.rounded_rectangle((70, 100, 442, 430), 70, fill=(215, 220, 230), outline=(60, 64, 76), width=22)
d.rounded_rectangle((130, 220, 382, 300), 30, fill=(30, 32, 40))
d.rounded_rectangle((155, 240, 357, 280), 18, fill=(255, 50, 30))
d.rectangle((246, 30, 266, 110), fill=(60, 64, 76))
d.ellipse((226, 10, 286, 70), fill=(255, 50, 30))
save(im, "icon_wave")
# play / fast-forward
im, d = canvas()
d.polygon([(150, 90), (430, 256), (150, 422)], fill=(255, 255, 255))
save(im, "icon_play", 96)

# stars (earned / empty) and lock for the map select screen
def star(d, fill, outline):
    pts = []
    for k in range(10):
        r = 230 if k % 2 == 0 else 100
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((256 + r * math.cos(a), 270 + r * math.sin(a)))
    d.polygon(pts, fill=outline)
    inner = [(256 + (x - 256) * 0.8, 270 + (y - 270) * 0.8) for x, y in pts]
    d.polygon(inner, fill=fill)

im, d = canvas(); star(d, (255, 205, 40), (150, 90, 10)); d.ellipse((190, 130, 250, 180), fill=(255, 245, 190)); save(im, "icon_star")
im, d = canvas(); star(d, (70, 52, 38), (40, 28, 20)); save(im, "icon_star_empty")
im, d = canvas()
d.rounded_rectangle((150, 60, 362, 300), 100, outline=(170, 170, 180), width=46)
d.rounded_rectangle((100, 230, 412, 470), 40, fill=(120, 120, 130))
d.rounded_rectangle((100, 210, 412, 450), 40, fill=(200, 200, 210))
d.ellipse((226, 290, 286, 350), fill=(70, 70, 80)); d.rectangle((246, 330, 266, 400), fill=(70, 70, 80))
save(im, "icon_lock")
