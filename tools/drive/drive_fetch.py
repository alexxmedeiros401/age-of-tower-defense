"""Downloads link-shared Google Drive files on a GitHub runner (the dev container can't reach Google; the runner can).

    python3 tools/drive/drive_fetch.py drive_job.json OUT_DIR

drive_job.json maps an output file name to a Drive file id: {"ada.glb": "15ck...", ...}. The files must be shared
"anyone with the link". A .glb is checked (magic b'glTF', header length == file size)."""
import json, os, struct, sys, time, urllib.request

JOB = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
bad = []
for name, fid in JOB.items():
    url = "https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t" % fid
    p = os.path.join(OUT, name)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=600) as r, open(p, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            break
        except Exception as e:
            print("retry", name, e, flush=True)
            time.sleep(5 * (attempt + 1))
    data = open(p, "rb").read(12) if os.path.exists(p) else b""
    size = os.path.getsize(p) if os.path.exists(p) else 0
    ok = True
    if name.endswith(".glb"):
        ok = len(data) == 12 and data[:4] == b"glTF" and struct.unpack("<I", data[8:12])[0] == size
    print("%-14s %10d bytes  %s" % (name, size, "ok" if ok else "BAD"), flush=True)
    if not ok:
        bad.append(name)
print("FETCH DONE, bad:", bad)
sys.exit(1 if bad else 0)
