"""Install an HQ .glb into the game: copy it in, let Godot import it (which extracts its textures), set the textures'
import options (VRAM compressed, at most 1024 px; normal maps flagged as such, the others not) and import again.
    python3 install_glb.py SRC.glb DEST.glb"""
import os, re, shutil, subprocess, sys

src, dest = sys.argv[1], sys.argv[2]
ROOT = "/home/claude/age-of-tower-defense"
shutil.copy(src, os.path.join(ROOT, dest))
def imp(tag):
    r = subprocess.run(["timeout", "900", "godot", "--headless", "--path", ROOT, "--import"], capture_output=True, text=True)
    open("/tmp/claude-0/install_%s.log" % tag, "w").write(r.stdout + r.stderr)
    errs = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l or "SCRIPT ERROR" in l]
    print(tag, "import exit", r.returncode, "errors:", len(errs))
    for l in errs[:6]:
        print("  ", l[:200])
imp("1")
d = os.path.dirname(os.path.join(ROOT, dest))
stem = os.path.splitext(os.path.basename(dest))[0]
n = 0
for f in sorted(os.listdir(d)):
    if f.startswith(stem + "_") and f.endswith(".jpg.import"):
        p = os.path.join(d, f)
        s = open(p).read()
        nm = 1 if "_normal" in f else 2
        s2 = re.sub(r"compress/mode=\d", "compress/mode=2", s)
        s2 = re.sub(r"compress/normal_map=\d", "compress/normal_map=%d" % nm, s2)
        s2 = re.sub(r"process/size_limit=\d+", "process/size_limit=1024", s2)
        if s2 != s:
            open(p, "w").write(s2)
            n += 1
        print("  ", f, "normal_map", nm)
print("fixed", n, "import files")
if n:
    imp("2")
