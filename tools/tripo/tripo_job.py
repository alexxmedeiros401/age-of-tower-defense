"""Runs one Tripo API pipeline on a GitHub runner (the dev container can't reach Tripo; the runner can).

    TRIPO_API_KEY=... python3 tools/tripo/tripo_job.py tripo_job.json OUT_DIR

tripo_job.json is a list of steps; each step's results land in OUT_DIR (images and models downloaded right away: Tripo's
links expire in minutes) and in OUT_DIR/log.json. Step kinds:
  {"kind": "upload", "name": "ref", "file": "path/in/repo.png"}                          -> a file_token
  {"kind": "text_to_image", "name": "c1", "prompt": "...", "model": "seedream_v5", "size": "2K"}
  {"kind": "image_to_image", "name": "c1", "inputs": ["@ref", ...], "prompt": "...", "model": "seedream_v5", "size": "2K"}
  {"kind": "image_to_multiview", "name": "mv", "input": "@c1"}
  {"kind": "multiview_to_model", "name": "m1", "mv": "@mv", "params": {...}}               (or "views": {"front": "@c1", ...})
  {"kind": "image_to_model", "name": "m1", "input": "@c1", "params": {...}}
"@name" means an earlier step's output: a file token, an image URL or a task id. Steps run in order; independent steps
can be marked "parallel": true to start before the previous one finishes (polled together)."""
import json, os, sys, time, urllib.request, urllib.error, mimetypes, uuid

BASE = "https://openapi.tripo3d.com/v3"
KEY = os.environ.get("TRIPO_API_KEY", "").strip()
if not KEY:
    sys.exit("TRIPO_API_KEY is not set")
JOB = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
LOG = {"steps": []}
VAL = {}


def req(method, path, body=None, files=None):
    url = BASE + path
    headers = {"Authorization": "Bearer " + KEY}
    data = None
    if files:
        b = uuid.uuid4().hex
        parts = []
        for field, (fname, blob) in files.items():
            ct = mimetypes.guess_type(fname)[0] or "application/octet-stream"
            parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                          % (b, field, os.path.basename(fname), ct)).encode() + blob + b"\r\n")
        data = b"".join(parts) + ("--%s--\r\n" % b).encode()
        headers["Content-Type"] = "multipart/form-data; boundary=" + b
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    for attempt in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=120)
            return json.loads(r.read())
        except urllib.error.HTTPError as e:
            txt = e.read().decode(errors="replace")
            if e.code == 429 or e.code >= 500:
                time.sleep(5 * (attempt + 1))
                continue
            raise SystemExit("HTTP %d on %s %s: %s" % (e.code, method, path, txt[:800]))
        except urllib.error.URLError:
            time.sleep(5 * (attempt + 1))
    raise SystemExit("gave up on %s %s" % (method, path))


def ref(v):
    if isinstance(v, str) and v.startswith("@"):
        return VAL[v[1:]]["ref"]
    if isinstance(v, list):
        return [ref(x) for x in v]
    if isinstance(v, dict):
        return {k: ref(x) for k, x in v.items()}
    return v


def download(url, name):
    ext = os.path.splitext(url.split("?")[0])[1] or ".bin"
    p = os.path.join(OUT, name + ext)
    with urllib.request.urlopen(url, timeout=300) as r, open(p, "wb") as f:
        f.write(r.read())
    return p


def wait(task_id, name):
    t0 = time.time()
    while True:
        r = req("GET", "/tasks/" + task_id)
        d = r.get("data", {})
        st = d.get("status")
        if st == "success":
            print("[%s] success in %ds, credits %s" % (name, time.time() - t0, d.get("credits_consumed")), flush=True)
            return d
        if st in ("failed", "cancelled", "banned", "expired", "unknown"):
            raise SystemExit("[%s] task %s %s: %s" % (name, task_id, st, json.dumps(d)[:800]))
        if time.time() - t0 > 1800:
            raise SystemExit("[%s] timed out" % name)
        time.sleep(4)


def start(st):
    k = st["kind"]
    if k == "upload":
        blob = open(st["file"], "rb").read()
        r = req("POST", "/files", files={"file": (st["file"], blob)})
        tok = r["data"]["file_token"]
        VAL[st["name"]] = {"ref": tok}
        LOG["steps"].append({"name": st["name"], "kind": k, "file_token": tok})
        print("[%s] uploaded %s" % (st["name"], st["file"]), flush=True)
        return None
    if k == "text_to_image":
        body = {x: st[x] for x in ("prompt", "model", "size", "aspect_ratio", "quality", "background", "template", "output_format") if x in st}
        path = "/generation/text-to-image"
    elif k == "image_to_image":
        body = {x: st[x] for x in ("prompt", "model", "size", "aspect_ratio", "quality", "template") if x in st}
        ins = ref(st["inputs"])
        if len(ins) == 1:
            body["input"] = ins[0]
        else:
            body["inputs"] = ins
        path = "/generation/image-to-image"
    elif k == "image_to_multiview":
        body = {"input": ref(st["input"])}
        path = "/generation/image-to-multiview"
    elif k == "multiview_to_model":
        if "mv" in st:
            body = {"inputs": [{"task_id": VAL[st["mv"][1:]]["task_id"]}]}
        else:
            body = {"inputs": [{v: ref(u)} for v, u in st["views"].items()]}
        body.update(st.get("params", {}))
        path = "/generation/multiview-to-model"
    elif k == "image_to_model":
        body = {"input": ref(st["input"])}
        body.update(st.get("params", {}))
        path = "/generation/image-to-model"
    else:
        raise SystemExit("unknown step kind " + k)
    r = req("POST", path, body)
    tid = r["data"]["task_id"]
    print("[%s] started %s task %s" % (st["name"], k, tid), flush=True)
    return tid


def finish(st, tid):
    d = wait(tid, st["name"])
    out = d.get("output", {}) or {}
    files = {}
    for key, url in out.items():
        if isinstance(url, str) and url.startswith("http"):
            files[key] = os.path.basename(download(url, "%s_%s" % (st["name"], key.replace("_url", ""))))
    refv = out.get("generated_image_url") or out.get("front_view_url") or tid
    VAL[st["name"]] = {"ref": refv, "task_id": tid}
    LOG["steps"].append({"name": st["name"], "kind": st["kind"], "task_id": tid, "credits": d.get("credits_consumed"), "files": files})
    json.dump(LOG, open(os.path.join(OUT, "log.json"), "w"), indent=1)


pending = []
for st in JOB:
    if not st.get("parallel"):
        for s2, t2 in pending:
            finish(s2, t2)
        pending = []
    tid = start(st)
    if tid:
        pending.append((st, tid))
for s2, t2 in pending:
    finish(s2, t2)
try:
    bal = req("GET", "/account/balance")
    LOG["balance_after"] = bal.get("data")
    print("balance", json.dumps(bal.get("data")), flush=True)
except SystemExit as e:
    print("balance query failed:", e)
json.dump(LOG, open(os.path.join(OUT, "log.json"), "w"), indent=1)
print("TRIPO JOB DONE", flush=True)
