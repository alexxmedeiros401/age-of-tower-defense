"""AgeOfTD build runner (Windows).

Runs the Blender art jobs Claude puts in queue\\ (one JSON file per job), a few at a time, at below-normal priority so
the PC stays responsive, and keeps the PC from going to sleep while jobs run. Close this window (or press Ctrl+C) to
stop it: the jobs it started stop with it, and anything unfinished goes back in the queue for next time.
Create a file named STOP in this folder to let the running jobs finish without starting new ones.

Job file fields: name, cmd (list), cwd, env, mkdirs, after (names of jobs that must be done first), mem_gb, expect
(files that must exist afterwards). {PY} {ROOT} {REPO} {OUT} in any string are replaced by this folder's paths.
"""
import os, sys, json, time, glob, ctypes, datetime, subprocess, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(ROOT, "py", "python", "python.exe")
REPO = os.path.join(ROOT, "repo")
OUT = os.path.join(ROOT, "out")
D = {k: os.path.join(ROOT, k) for k in ("queue", "running", "done", "failed", "logs")}
for _p in list(D.values()) + [OUT]:
    os.makedirs(_p, exist_ok=True)
CONF = os.path.join(ROOT, "runner_conf.json")       # optional: {"max_jobs": 3, "reserve_gb": 6}
CPUS = os.cpu_count() or 4


class MEMSTAT(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def mem():
    m = MEMSTAT()
    m.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullTotalPhys / 2 ** 30, m.ullAvailPhys / 2 ** 30


def conf():
    c = {"max_jobs": max(1, min(4, CPUS // 4)), "reserve_gb": 6.0}
    try:
        with open(CONF) as f:
            c.update(json.load(f))
    except Exception:
        pass
    return c


def now():
    return datetime.datetime.now().strftime("%H:%M:%S")


def say(*a):
    line = " ".join(str(x) for x in (now(),) + a)
    print(line, flush=True)
    try:
        with open(os.path.join(D["logs"], "runner.log"), "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def sub(x):
    return x.replace("{PY}", PY).replace("{ROOT}", ROOT).replace("{REPO}", REPO).replace("{OUT}", OUT)


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def sysinfo():
    gpus = "?"
    try:
        gpus = subprocess.run(["powershell", "-NoProfile", "-Command",
                               "(Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + ' (' + $_.DriverVersion + ')' }) -join '; '"],
                              capture_output=True, text=True, timeout=90).stdout.strip()
    except Exception as e:
        gpus = "? %s" % e
    t, a = mem()
    write_json(os.path.join(ROOT, "sysinfo.json"), {"cpus": CPUS, "mem_total_gb": round(t, 1), "mem_avail_gb": round(a, 1),
                                                    "gpus": gpus, "python": sys.version, "conf": conf()})


def keep_awake(on):
    # ES_CONTINUOUS | ES_SYSTEM_REQUIRED while jobs run (the screen may still turn off), ES_CONTINUOUS alone to release
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | (0x00000001 if on else 0))
    except Exception:
        pass


def main():
    print("=" * 78)
    print(" AgeOfTD build runner: Claude's Blender jobs for Age of Tower Defense run from here, at low priority.")
    print(" Leave this window open (minimized is fine). Close it any time to stop everything.")
    print(" Folder:", ROOT)
    print("=" * 78, flush=True)
    for rp in glob.glob(os.path.join(D["running"], "*.json")):        # (left over from a run that was closed: back in line)
        os.replace(rp, os.path.join(D["queue"], os.path.basename(rp)))
    sysinfo()
    running = {}
    last_start = 0.0
    awake = False
    while True:
        try:
            c = conf()
            for name in list(running):                                 # reap finished jobs
                p, lf, t0, spec, rp = running[name]
                rc = p.poll()
                if rc is None:
                    continue
                lf.close()
                mins = (time.time() - t0) / 60
                missing = [e for e in spec.get("expect", []) if not os.path.exists(sub(e))]
                ok = rc == 0 and not missing
                write_json(os.path.join(D["done" if ok else "failed"], name + ".json"),
                           dict(spec, rc=rc, minutes=round(mins, 1), finished=now(), missing=missing))
                try:
                    os.remove(rp)
                except OSError:
                    pass
                say("done  " if ok else "FAILED", name, "(%.1f min%s)" % (mins, "" if ok else ", rc %s %s" % (rc, missing)))
                del running[name]
            total, avail = mem()
            stop = os.path.exists(os.path.join(ROOT, "STOP"))
            queued = sorted(glob.glob(os.path.join(D["queue"], "*.json")))
            if not stop and len(running) < c["max_jobs"] and time.time() - last_start > 45:
                for qp in queued:
                    spec = load(qp)
                    if not spec or "name" not in spec:
                        continue
                    name = spec["name"]
                    if name in running:
                        continue
                    deps = spec.get("after", [])
                    bad = [d for d in deps if os.path.exists(os.path.join(D["failed"], d + ".json"))]
                    if bad:
                        write_json(os.path.join(D["failed"], name + ".json"), dict(spec, rc=None, reason="after failed: %s" % bad, finished=now()))
                        os.remove(qp)
                        say("SKIP  ", name, "(%s failed)" % bad)
                        continue
                    if not all(os.path.exists(os.path.join(D["done"], d + ".json")) for d in deps):
                        continue
                    need = float(spec.get("mem_gb", 4))
                    if running and avail - c["reserve_gb"] < need:
                        continue
                    if not running and total - c["reserve_gb"] < need * 0.6:
                        continue
                    for d in spec.get("mkdirs", []):
                        os.makedirs(sub(d), exist_ok=True)
                    rp = os.path.join(D["running"], os.path.basename(qp))
                    os.replace(qp, rp)
                    for old in ("done", "failed"):
                        try:
                            os.remove(os.path.join(D[old], name + ".json"))
                        except OSError:
                            pass
                    env = dict(os.environ)
                    env.update({k: sub(str(v)) for k, v in spec.get("env", {}).items()})
                    env["PYTHONUNBUFFERED"] = "1"
                    lf = open(os.path.join(D["logs"], name + ".log"), "w", buffering=1, encoding="utf-8", errors="replace")
                    cmd = [sub(str(x)) for x in spec["cmd"]]
                    p = subprocess.Popen(cmd, cwd=sub(spec.get("cwd", "{REPO}")), env=env, stdout=lf, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
                    running[name] = (p, lf, time.time(), spec, rp)
                    last_start = time.time()
                    say("start ", name, "(%.1f GB free)" % avail)
                    break
            if bool(running) != awake:
                awake = bool(running)
                keep_awake(awake)
            write_json(os.path.join(ROOT, "status.json"), {
                "t": now(), "mem_total_gb": round(total, 1), "mem_avail_gb": round(avail, 1), "stop": stop,
                "running": {n: round((time.time() - v[2]) / 60, 1) for n, v in running.items()},
                "queued": [os.path.basename(q)[:-5] for q in queued]})
        except KeyboardInterrupt:
            raise
        except Exception:
            say("runner error:", traceback.format_exc())
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped.")
