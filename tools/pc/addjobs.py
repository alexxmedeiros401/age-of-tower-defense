"""Queue the standard HQ unit builds: python3 addjobs.py ORDER SHORT CHARACTER BASE_MODULE [after...]"""
import json, os, sys
R = os.path.expanduser("~/mnt/Documents/AgeOfTD")
o, short, ch, base = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
after0 = sys.argv[5:]
d = "{OUT}/medieval/%sf" % short
HQ = "{REPO}/tools/blender/hq"
env = {"AOTD_GPU": "CUDA"}
jobs = [
    (o, dict(name=short + "_char", cmd=["{PY}", "sculpt_char.py", "--character", ch, "--fine", "--out", d + "/hi/%s_hi.blend" % ch, "--shots", d + "/hi/shots_fine"],
             cwd=HQ, mem_gb=5, after=after0, mkdirs=[d + "/hi"], expect=[d + "/hi/%s_hi.blend" % ch], env=env)),
    (o + 1, dict(name=short + "_base", cmd=["{PY}", "sculpt_base.py", "--module", base, "--fine", "--out", d + "/hi/%s_hi.blend" % base, "--shots", d + "/hi/base_shots_fine"],
                 cwd=HQ, mem_gb=3, after=after0, mkdirs=[d + "/hi"], expect=[d + "/hi/%s_hi.blend" % base], env=env)),
    (o + 2, dict(name=short + "_bake", cmd=["{PY}", "build_game.py", "--", "--character", ch, "--char", d + "/hi/%s_hi.blend" % ch, "--base", d + "/hi/%s_hi.blend" % base,
                                          "--out", d + "/final", "--tex", "2048", "--ao", "40"],
                 cwd=HQ, mem_gb=6, after=[short + "_char", short + "_base"], mkdirs=[d + "/final"], expect=[d + "/final/%s.glb" % ch], env=env)),
]
for oo, spec in jobs:
    p = os.path.join(R, "queue", "%02d_%s.json" % (oo, spec["name"]))
    json.dump(spec, open(p + ".tmp", "w"), indent=1)
    os.replace(p + ".tmp", p)
    print("queued", os.path.basename(p))
