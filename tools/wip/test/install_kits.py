"""Install HQ .glb files into the game in one pass: copy them in, let Godot import them (which extracts their textures),
set the textures' import options (VRAM compressed, at most LIMIT px; normal maps flagged as such, the others not) and
import again.
    python3 install_kits.py LIMIT SRC.glb:DEST.glb [SRC.glb:DEST.glb ...]"""
import os, re, shutil, subprocess, sys

ROOT = "/home/claude/age-of-tower-defense"
limit = int(sys.argv[1])
pairs = [a.split(":") for a in sys.argv[2:]]
for src, dest in pairs:
    shutil.copy(src, os.path.join(ROOT, dest))
    print("copied", dest, os.path.getsize(src))


def imp(tag):
    r = subprocess.run(["timeout", "1200", "godot", "--headless", "--path", ROOT, "--import"], capture_output=True, text=True)
    open("/tmp/claude-0/install_kits_%s.log" % tag, "w").write(r.stdout + r.stderr)
    errs = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l]
    print(tag, "import exit", r.returncode, "errors:", len(errs))
    for l in errs[:6]:
        print("  ", l[:200])


imp("1")
n = 0
for src, dest in pairs:
    d = os.path.dirname(os.path.join(ROOT, dest))
    stem = os.path.splitext(os.path.basename(dest))[0]
    for f in sorted(os.listdir(d)):
        if f.startswith(stem + "_") and (f.endswith(".jpg.import") or f.endswith(".png.import")):
            p = os.path.join(d, f)
            s = open(p).read()
            nm = 1 if "_normal" in f else 2
            s2 = re.sub(r"compress/mode=\d", "compress/mode=2", s)
            s2 = re.sub(r"compress/normal_map=\d", "compress/normal_map=%d" % nm, s2)
            s2 = re.sub(r"process/size_limit=\d+", "process/size_limit=%d" % limit, s2)
            if s2 != s:
                open(p, "w").write(s2)
                n += 1
            print("  ", f, "normal_map", nm)
print("fixed", n, "import files")
if n:
    imp("2")
