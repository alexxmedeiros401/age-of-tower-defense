"""Tunes each era map with the balance bots (tests/balance.gd --quick), in two stages:

1. hp_mult (all robots) from the lives lost in waves 1-19:
     Normal: the competent build WITHOUT a hero loses ~12 lives before the boss.
     Hard:   with an era hero, ~10 lives lost on average.   Brutal: ~20.
2. boss_hp_mult: the largest boss multiplier the reference build still beats (Normal: no hero,
   Hard/Brutal: best era hero), then backed off a little so the boss is beatable but tense.

Writes hp_mult / boss_hp_mult into data/map_<id>.json.
Run: python3 tools/tune_hp.py [map_id ...]   (default: every era map from era_spec)"""
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import era_spec as S  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
G = "/home/claude/tools/godot/Godot_v4.7.2-stable_linux.x86_64"
PRE_TARGET = {"Normal": 12, "Hard": 10, "Brutal": 20}
BOSS_BACKOFF = {"Normal": 0.8, "Hard": 0.85, "Brutal": 0.95}


def run(mid, hp, boss):
    out = subprocess.run([G, "--headless", "--path", ROOT, "--script", "res://tests/balance.gd", "--", mid, "--quick",
                          "--hp=%.4f" % hp, "--boss=%.4f" % boss], capture_output=True, text=True, timeout=900).stdout
    res = {}
    for line in out.splitlines():
        if line.startswith("RUN|"):
            _, name, state, wave, lives, pre, bleak = line.split("|")
            res[name] = {"won": state == "won", "wave": int(wave), "lives": int(lives), "pre": int(pre), "boss_leak": int(bleak)}
    return res


def pre_metric(diff, res):
    if diff == "Normal":
        r = res["balanced"]
        return r["pre"] if r["wave"] >= 20 else 100
    hs = [v for k, v in res.items() if k != "balanced"]
    return sum((v["pre"] if v["wave"] >= 20 else 100) for v in hs) / len(hs)


def boss_ok(diff, res):
    if diff == "Normal":
        return res["balanced"]["boss_leak"] == 0 and res["balanced"]["won"]
    return any(v["boss_leak"] == 0 and v["won"] for k, v in res.items() if k != "balanced")


def tune(entry):
    mid, diff = entry
    path = os.path.join(ROOT, "data", "map_%s.json" % mid)
    m = json.load(open(path))
    hp0 = float(m["hp_mult"])
    # stage 1: robot HP from the pre-boss waves (boss weakened so it doesn't end the run early)
    lo, hi = math.log(hp0 * 0.4), math.log(hp0 * 3.0)
    hp = hp0
    for i in range(7):
        hp = math.exp((lo + hi) / 2)
        v = pre_metric(diff, run(mid, hp, 0.05))
        if abs(v - PRE_TARGET[diff]) <= 3:
            break
        if v < PRE_TARGET[diff]:
            lo = math.log(hp)
        else:
            hi = math.log(hp)
    # stage 2: boss multiplier
    blo, bhi = math.log(0.2), math.log(5.0)
    best_ok = 0.2
    for i in range(7):
        b = math.exp((blo + bhi) / 2)
        if boss_ok(diff, run(mid, hp, b)):
            best_ok = max(best_ok, b)
            blo = math.log(b)
        else:
            bhi = math.log(b)
    boss = round(best_ok * BOSS_BACKOFF[diff], 3)
    final = run(mid, hp, boss)
    m = json.load(open(path))
    m["hp_mult"] = round(hp, 3)
    m["boss_hp_mult"] = boss
    json.dump(m, open(path, "w"), indent=1)
    summary = {k: ("W%d" % v["lives"] if v["won"] else "L%d" % v["wave"]) for k, v in final.items()}
    print("%-18s %-6s hp %.2f -> %.2f  boss x%.2f  %s" % (mid, diff, hp0, hp, boss, summary), flush=True)


def tune_starter(mid):
    """Normal maps open each era with only the free starter towers (Ranged + Control).
    Lower robot HP until 'starter kit + era hero' keeps ~55 lives on average (never raises HP)."""
    path = os.path.join(ROOT, "data", "map_%s.json" % mid)
    m = json.load(open(path))
    hp0 = float(m.get("hp_mult", 1.0))
    boss = float(m.get("boss_hp_mult", 1.0))

    def score(hp):
        out = subprocess.run([G, "--headless", "--path", ROOT, "--script", "res://tests/balance.gd", "--", mid, "--quick", "--ranged",
                              "--hp=%.4f" % hp, "--boss=%.4f" % boss], capture_output=True, text=True, timeout=900).stdout
        vals = []
        for line in out.splitlines():
            if line.startswith("RUN|starter kit + "):
                p = line.split("|")
                vals.append(int(p[4]) if p[2] == "won" else -(20 - int(p[3])) * 5)
        return sum(vals) / max(1, len(vals))

    v0 = score(hp0)
    if v0 >= 50:
        print("%-18s starter ok at hp %.2f (%.0f)" % (mid, hp0, v0), flush=True)
        return
    lo, hi = math.log(hp0 * 0.45), math.log(hp0)
    best = hp0 * 0.45
    for i in range(6):
        hp = math.exp((lo + hi) / 2)
        v = score(hp)
        if v >= 55:
            best = max(best, hp)
            lo = math.log(hp)
        else:
            hi = math.log(hp)
    m = json.load(open(path))
    m["hp_mult"] = round(best, 3)
    json.dump(m, open(path, "w"), indent=1)
    print("%-18s starter hp %.2f -> %.2f" % (mid, hp0, best), flush=True)


if __name__ == "__main__" and "--starter" in sys.argv:
    normals = ["mammoth_valley", "river_delta"] + [x[0] for x in S.MAPS if x[3] == "Normal"]
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(tune_starter, normals))
    sys.exit(0)

if __name__ == "__main__":
    want = set(sys.argv[1:])
    todo = [(x[0], x[3]) for x in S.MAPS if not want or x[0] in want]
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(tune, todo))
