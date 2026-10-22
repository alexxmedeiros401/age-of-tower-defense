"""Queue a quick preview (coarse sculpt, quick rigged build, frames of its clips), as prev.sh / rprev.sh did:
    python3 addprev.py char ORDER NAME CHARACTER BASEMODULE|none OUTREL CAM POSES...
    python3 addprev.py robot ORDER NAME ROBOT OUTREL CAM POSES...
CAM = tx,ty,tz,dist,az,el ; POSES = Action:range:step (range like 0,24)"""
import json, os, sys
R = os.path.expanduser("~/mnt/Documents/AgeOfTD")
HQ = "{REPO}/tools/blender/hq"
env = {"AOTD_GPU": "CUDA"}
kind, order, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]
jobs = []
def job(nm, cmd, after, mkdirs=(), expect=(), mem=3):
    jobs.append(dict(name=nm, cmd=["{PY}"] + cmd, cwd=HQ, mem_gb=mem, after=list(after), mkdirs=list(mkdirs), expect=list(expect), env=env))
if kind == "char":
    ch, bm, rel, cam = sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]
    poses = sys.argv[8:]
    W = "{OUT}/" + rel
    job(name + "_q", ["sculpt_char.py", "--character", ch, "--out", W + "/q/char_q.blend", "--shots", W + "/q/views"], [], [W + "/q"], [W + "/q/char_q.blend"])
    if bm != "none":
        job(name + "_qbase", ["sculpt_base.py", "--module", bm, "--out", W + "/qbase/base_q.blend", "--shots", W + "/qbase/shots"], [], [W + "/qbase"], [W + "/qbase/base_q.blend"])
    job(name + "_qb", ["build_game.py", "--", "--character", ch, "--char", W + "/q/char_q.blend", "--base", "none", "--out", W + "/qb", "--tex", "512", "--ao", "6",
                       "--stage", "char"], [name + "_q"], [W + "/qb"], [W + "/qb/char_game.blend"])
    blend, last = W + "/qb/char_game.blend", name + "_qb"
else:
    rb, rel, cam = sys.argv[4], sys.argv[5], sys.argv[6]
    poses = sys.argv[7:]
    W = "{OUT}/" + rel
    job(name + "_sculpt", ["robot_build.py", "--", "--robot", rb, "--out", W, "--stage", "sculpt", "--shots", W + "/shots"], [], [W])
    job(name + "_game", ["robot_build.py", "--", "--robot", rb, "--out", W, "--stage", "game", "--tex", "512", "--ao", "4"], [name + "_sculpt"])
    blend, last = W + "/robot_game.blend", name + "_game"
tx, ty, tz, dist, az, el = cam.split(",")
for c in poses:
    act, rng, st = c.split(":")
    job(name + "_pose_" + act, ["render_asset.py", "--", "--blend", blend, "--out", W + "/poses", "--mode", "frames", "--action", act, "--range", rng,
                                "--step", st, "--spp", "8", "--res", "500", "--tx", tx, "--ty", ty, "--tz", tz, "--dist", dist, "--az", az, "--el", el],
        [last], [W + "/poses"])
for i, spec in enumerate(jobs):
    p = os.path.join(R, "queue", "%02d_%02d_%s.json" % (order, i, spec["name"]))
    json.dump(spec, open(p + ".tmp", "w"), indent=1)
    os.replace(p + ".tmp", p)
    print("queued", os.path.basename(p))
