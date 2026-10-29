"""v0.9.92: the shared UI kit for every screen past the main menu, rendered in the main menu's style (navy enamel and
polished gold, glossy gem buttons):

    python3 tools/blender/ui/ui_art.py [--only btn,panel,card,close,knob,track,divider,tab] [--samples 64]

Writes assets/ui/ui_*.png. game.gd draws them as 9-patches at 1:1 (StyleBoxTexture), so each texture is made at the size
it shows on a 1080p-tall screen and its margins (listed below, also in game.gd UI_NINE) are the round corners:
  ui_btn_<colour>.png   160x64   margins 22     gem buttons: green, blue, red, gold, purple, navy, grey (pewter rim)
  ui_tab_on/off.png     160x56   margins 20     tabs and segmented choices (gold face / dark glass); tab_off is also the stat chip
  ui_panel.png          320x320  margins 72     dialog frame: navy enamel, a gold tube frame, corner studs
  ui_card*.png          128x128  margins 30     cards inside dialogs: card (navy), card_hi (selected), card_dim (locked)
  ui_track.png          160x40   margins 18     slider / bar groove
  ui_knob.png, ui_close.png                     a gold slider knob; the red gem close button with its X
  ui_divider.png        480x28                  a gold rule with a diamond, under section headings
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_argv = sys.argv[:]
sys.argv = [sys.argv[0], "--only", "__none__"]
import menu_art as M                     # (its helpers; "--only __none__" renders none of its own jobs)
sys.argv = _argv
import bpy
import ui_kit as K

A = sys.argv
ONLY = A[A.index("--only") + 1].split(",") if "--only" in A else None
SAMPLES = int(A[A.index("--samples") + 1]) if "--samples" in A else 64
TMP = M.TMP
GOLD_COL = (1.0, 0.76, 0.33)
PEWTER_COL = (0.62, 0.64, 0.68)


def base(w_px, h_px):
    K.reset(0, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2, w=w_px, h=h_px)


def frame_mats(pewter=False):
    gold = K.gold("Gold", GOLD_COL, 0.2) if not pewter else K.metal("Pewter", PEWTER_COL, 0.3)
    dark = K.matte("Outline", (0.04, 0.03, 0.06))
    return gold, dark


def gem_rect(name, face_col, w, h, r, frame=0.04, pewter=False, coat=1.0, rough=0.12, studs=False, outline=0.06):
    """A rounded rectangle of glossy enamel in a round metal frame, on a dark outline: the kit's one shape."""
    gold, dark = frame_mats(pewter)
    M.slab("Out", w + 2 * outline, h + 2 * outline, r + outline, -0.08, -0.02, dark, 0.01)
    M.dome_face("Face", w, h, r, -0.04, 0.05, K.paint("Enamel", face_col, rough, coat=coat))
    M.tube_frame("Frame", w, h, r, frame, gold, 0.02)
    if studs:
        for sx in (-1, 1):
            for sy in (-1, 1):
                K.sphere("Stud", frame * 1.5, gold, loc=(sx * (w / 2 - r * 0.42), sy * (h / 2 - r * 0.42), 0.065),
                         scale=(1, 1, 0.7), seg=24, rings=12)


def shot(name, w_px, h_px, scale_w, size):
    cam = M.top_camera(scale_w, w_px, h_px)
    M.flat_lights()
    raw = K.render(os.path.join(TMP, name + ".png"))
    M.out(name, raw, size)


JOBS = []


def job(fn):
    JOBS.append(fn)
    return fn


BTN = {"green": (0.2, 0.64, 0.16), "blue": (0.15, 0.4, 0.84), "red": (0.85, 0.15, 0.11), "gold": (1.0, 0.64, 0.1),
       "purple": (0.56, 0.26, 0.86), "navy": (0.13, 0.19, 0.36), "grey": (0.3, 0.33, 0.4)}


@job
def btn():
    # 2.5 x 1.0 units on a 2.6-wide camera, rendered 640x256 -> 160x64 (1 unit = 61.5 px): corners r 0.3 = 18 px
    for k, col in BTN.items():
        base(640, 256)
        gem_rect("Btn", col, 2.44, 0.84, 0.3, frame=0.04, pewter=(k == "grey"))
        shot("ui_btn_" + k, 640, 256, 2.6, (160, 64))


@job
def tab():
    base(640, 224)
    gem_rect("Tab", (1.0, 0.7, 0.16), 2.44, 0.7, 0.28, frame=0.035)
    shot("ui_tab_on", 640, 224, 2.6, (160, 56))
    base(640, 224)
    gem_rect("Tab", (0.06, 0.08, 0.15), 2.44, 0.7, 0.28, frame=0.032, coat=1.0)
    shot("ui_tab_off", 640, 224, 2.6, (160, 56))


@job
def panel():
    # 3.9 units on a 4.0 camera -> 320 px (1 unit = 80 px): frame tube 0.06 (~10 px), corners r 0.55 (44 px)
    base(1280, 1280)
    gem_rect("Panel", (0.035, 0.06, 0.14), 3.76, 3.76, 0.55, frame=0.06, coat=0.6, rough=0.3, studs=True, outline=0.07)
    shot("ui_panel", 1280, 1280, 4.0, (320, 320))


@job
def card():
    for name, col, fr, pewter in (("ui_card", (0.08, 0.12, 0.23), 0.026, False), ("ui_card_hi", (0.14, 0.25, 0.46), 0.045, False),
                                  ("ui_card_dim", (0.08, 0.09, 0.12), 0.026, True)):
        base(512, 512)
        gem_rect("Card", col, 1.5, 1.5, 0.3, frame=fr, coat=0.6, rough=0.3, pewter=pewter, outline=0.04)
        shot(name, 512, 512, 1.6, (128, 128))


@job
def track():
    base(640, 160)
    gold, dark = frame_mats()
    M.slab("Out", 3.86, 0.86, 0.43, -0.08, -0.02, dark, 0.01)
    M.slab("Groove", 3.7, 0.7, 0.35, -0.04, 0.0, K.paint("Groove", (0.03, 0.04, 0.08), 0.4), 0.01)
    M.tube_frame("Frame", 3.7, 0.7, 0.35, 0.04, gold, 0.02)
    shot("ui_track", 640, 160, 4.0, (160, 40))


@job
def knob():
    K.reset(256, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2)
    gold, dark = frame_mats()
    K.cylinder("Out", 1.0, 0.05, 96, dark, loc=(0, 0, -0.03))
    K.revolve("Knob", [(0.0, 0.42), (0.35, 0.4), (0.62, 0.32), (0.84, 0.18), (0.92, 0.06), (0.92, 0.0)], 128, gold)
    gm = K.gem("Gem", (0.3, 0.8, 1.0))
    K.sphere("Gem", 0.3, gm, loc=(0, 0, 0.38), scale=(1, 1, 0.5), seg=8, rings=4)
    M.top_camera(2.2, 256)
    M.flat_lights()
    raw = K.render(os.path.join(TMP, "knob.png"))
    M.out("ui_knob", raw, 64)


@job
def close():
    K.reset(512, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2)
    gold, dark = frame_mats()
    K.cylinder("Out", 1.06, 0.05, 96, dark, loc=(0, 0, -0.03))
    K.revolve("Rim", [(0.78, 0.0), (0.8, 0.06), (0.86, 0.1), (0.94, 0.1), (1.0, 0.06), (1.0, 0.0)], 128, gold)
    K.revolve("Dome", [(0.0, 0.32), (0.3, 0.3), (0.55, 0.24), (0.72, 0.15), (0.8, 0.07), (0.8, 0.0)], 128,
              K.paint("Enamel", (0.88, 0.12, 0.1), 0.12, coat=1.0))
    w = K.paint("Glyph", (1, 1, 1), 0.2, coat=0.6)
    a, b = 0.42, 0.11
    pts = [(b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b), (-b, -a), (b, -a), (b, -b), (a, -b), (a, b), (b, b)]
    x = K.prism("X", pts, 0.0, 0.12, w, loc=(0, 0, 0.27), rot=(0, 0, math.radians(45)))
    K.bevel(x, 0.04, 4, 30)
    M.top_camera(2.2, 512)
    M.flat_lights()
    raw = K.render(os.path.join(TMP, "close.png"))
    M.out("ui_close", raw, 112)


@job
def divider():
    base(1920, 112)
    gold, dark = frame_mats()
    for sx in (-1, 1):
        pts = [(sx * 0.32, 0.0, 0.02), (sx * 7.6, 0.0, 0.02)]
        K.curve_tube("Line%d" % sx, pts, 0.08, gold, res=8)
        K.sphere("Dot", 0.09, gold, loc=(sx * 7.75, 0, 0.03), scale=(1, 1, 0.6), seg=24, rings=12)
    d = K.prism("Diamond", [(0.0, 0.3), (0.3, 0.0), (0.0, -0.3), (-0.3, 0.0)], 0.0, 0.08, gold)
    K.bevel(d, 0.05, 3, 30)
    K.sphere("Gem", 0.13, K.gem("Gem", (0.3, 0.8, 1.0)), loc=(0, 0, 0.1), scale=(1, 1, 0.5), seg=8, rings=4)
    shot("ui_divider", 1920, 112, 16.0, (480, 28))


for fn in JOBS:
    if ONLY and fn.__name__ not in ONLY:
        continue
    fn()
