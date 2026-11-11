"""Tripo's international API (api.tripo3d.ai/v2/openapi, keys from platform.tripo3d.ai). tripo_job.py hands over to
this when tripo_job.json is {"api": "v2", "models": [...]}:
  {"api": "v2", "model_versions": ["v3.1-20260211", "v3.0-20250812"],
   "params": {"texture": true, "pbr": true, "texture_quality": "detailed", "geometry_quality": "detailed"},
   "models": [{"name": "axewarrior", "file": "tools/tripo/in/x/axewarrior.png"}, ...]}
The balance is checked first (a bad key fails before anything is spent). Every model starts at once; each finished
model is downloaded as OUT/<name>.glb (pbr_model, else model, else base_model) with its preview image, and the
credits each task froze or used, plus the balance before and after, go to OUT/log.json."""
import json, os, sys, time, urllib.request, urllib.error, mimetypes, uuid
# Tripo sits behind Cloudflare, which now refuses Python-urllib's default User-Agent (HTTP 403, error 1010):
# send a named client instead, on every request including the model downloads.
_op = urllib.request.build_opener()
_op.addheaders = [("User-Agent", "AgeOfTowerDefense-art-pipeline/1.0 (+https://github.com/alexxmedeiros401/age-of-tower-defense)")]
urllib.request.install_opener(_op)

BASE = "https://api.tripo3d.ai/v2/openapi"


class ApiError(Exception):
    def __init__(self, code, txt):
        super().__init__("HTTP %d: %s" % (code, txt[:600]))
        self.code, self.txt = code, txt


def req(key, method, path, body=None, files=None):
    headers = {"Authorization": "Bearer " + key}
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
            r = urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, headers=headers, method=method), timeout=180)
            return json.loads(r.read())
        except urllib.error.HTTPError as e:
            txt = e.read().decode(errors="replace")
            if e.code == 429 or e.code >= 500:
                time.sleep(5 * (attempt + 1))
                continue
            raise ApiError(e.code, txt)
        except urllib.error.URLError:
            time.sleep(5 * (attempt + 1))
    raise ApiError(0, "gave up on %s %s" % (method, path))


def run(job, out, key):
    log = {"api": "v2", "models": []}
    save = lambda: json.dump(log, open(os.path.join(out, "log.json"), "w"), indent=1)
    try:
        bal = req(key, "GET", "/user/balance")
    except ApiError as e:
        sys.exit("balance check failed, nothing was started: %s" % e)
    log["balance_before"] = bal.get("data")
    print("balance before", json.dumps(bal.get("data")), flush=True)
    save()
    params = job.get("params", {})
    versions = job.get("model_versions", ["v3.0-20250812"])
    tasks = []
    for m in job["models"]:
        blob = open(m["file"], "rb").read()
        up = req(key, "POST", "/upload", files={"file": (m["file"], blob)})["data"]
        tok = up.get("image_token") or up.get("file_token")
        ext = os.path.splitext(m["file"])[1].lstrip(".").lower().replace("jpeg", "jpg")
        tid = None
        if m.get("retexture_of"):                # re-texture an earlier task's model, guided by the image
            base = {"type": "texture_model", "original_model_task_id": m["retexture_of"], "texture": True, "pbr": True,
                    "texture_quality": params.get("texture_quality", "detailed"), "texture_alignment": "original_image"}
            for extra in ({"texture_prompt": {"image": {"type": ext, "file_token": tok}}}, {}):
                try:
                    tid = req(key, "POST", "/task", dict(base, **extra))["data"]["task_id"]
                    print("[%s] started retexture %s%s" % (m["name"], tid, "" if extra else " (no image prompt)"), flush=True)
                    tasks.append((m, tid, "texture_model", []))
                    break
                except ApiError as e:
                    print("[%s] retexture refused: %s" % (m["name"], e.txt[:300]), flush=True)
                    if e.code in (401, 402, 403):
                        save()
                        sys.exit("stopping: %s" % e)
            if not tid:
                log["models"].append({"name": m["name"], "error": "retexture refused"})
                save()
            continue
        for v in versions:                       # newest first; fall back if this account doesn't offer it
            p = dict(params, **m.get("params", {}))
            for drop in ([], ["geometry_quality"]):
                body = {"type": "image_to_model", "file": {"type": ext, "file_token": tok}, "model_version": v}
                body.update({k: x for k, x in p.items() if k not in drop})
                try:
                    tid = req(key, "POST", "/task", body)["data"]["task_id"]
                    print("[%s] started %s (%s%s)" % (m["name"], tid, v, ", no geometry_quality" if drop else ""), flush=True)
                    tasks.append((m, tid, v, [k for k in drop]))
                    break
                except ApiError as e:
                    print("[%s] %s with %s%s refused: %s" % (m["name"], v, "", " (no geometry_quality)" if drop else "", e.txt[:300]), flush=True)
                    if e.code in (401, 402, 403):
                        save()
                        sys.exit("stopping: %s" % e)
            if tid:
                break
        if not tid:
            log["models"].append({"name": m["name"], "error": "no model version accepted"})
            save()
    t0 = time.time()
    left = list(tasks)
    while left and time.time() - t0 < 3000:
        time.sleep(8)
        for item in list(left):
            m, tid, v, dropped = item
            d = req(key, "GET", "/task/" + tid)["data"]
            st = d.get("status")
            if st in ("queued", "running"):
                continue
            left.remove(item)
            rec = {"name": m["name"], "task_id": tid, "model_version": v, "dropped": dropped, "status": st,
                   "credits": d.get("consumed_credit", d.get("credits_consumed"))}
            if st == "success":
                o = d.get("output", {}) or {}
                url = o.get("pbr_model") or o.get("model") or o.get("base_model")
                if url:
                    p = os.path.join(out, m["name"] + ".glb")
                    with urllib.request.urlopen(url, timeout=600) as r, open(p, "wb") as f:
                        f.write(r.read())
                    rec["glb_bytes"] = os.path.getsize(p)
                if o.get("rendered_image"):
                    try:
                        with urllib.request.urlopen(o["rendered_image"], timeout=120) as r, open(os.path.join(out, m["name"] + "_preview.webp"), "wb") as f:
                            f.write(r.read())
                    except Exception as e:
                        rec["preview_error"] = str(e)
            else:
                rec["detail"] = json.dumps(d)[:600]
            print("[%s] %s credits %s" % (m["name"], st, rec["credits"]), flush=True)
            log["models"].append(rec)
            save()
    for m, tid, v, dropped in left:
        log["models"].append({"name": m["name"], "task_id": tid, "status": "timed out here (task may still finish on Tripo)"})
    try:
        log["balance_after"] = req(key, "GET", "/user/balance").get("data")
        print("balance after", json.dumps(log["balance_after"]), flush=True)
    except ApiError as e:
        print("balance query failed:", e)
    save()
    print("TRIPO JOB DONE", flush=True)
