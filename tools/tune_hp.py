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


def kit_score(mid, k, hp, boss):
    out = subprocess.run([G, "--headless", "--path", ROOT, "--script", "res://tests/balance.gd", "--", mid, "--kit=%d" % k,
                          "--hp=%.4f" % hp, "--boss=%.4f" % boss], capture_output=True, text=True, timeout=900).stdout
    best = -100
    for line in out.splitlines():
        if line.startswith("RUN|kit"):
            p = line.split("|")
            v = int(p[4]) if p[2] == "won" else -(20 - int(p[3])) * 5 - 5
            best = max(best, v)
    return best


def tune_kit(entry):
    """Progression tuning (towers unlock weakest-first, one more per map):
    map #i of an era must be WON with i+2 towers + the best era hero (~45 lives)
    and LOST with i+1 towers, whatever the hero."""
    mid, idx = entry
    path = os.path.join(ROOT, "data", "map_%s.json" % mid)
    m = json.load(open(path))
    hp0 = float(m.get("hp_mult", 1.0))
    boss = float(m.get("boss_hp_mult", 1.0))
    wk, lk = min(4, idx + 2), idx + 1
    lo, hi = math.log(hp0 * 0.4), math.log(hp0 * 4.0)
    hp = hp0
    for i in range(7):
        hp = math.exp((lo + hi) / 2)
        v = kit_score(mid, wk, hp, boss)
        if abs(v - 45) <= 8:
            break
        if v > 45:
            lo = math.log(hp)
        else:
            hi = math.log(hp)
    win = kit_score(mid, wk, hp, boss)
    lose = kit_score(mid, lk, hp, boss)
    steps = 0
    while lose >= 0 and steps < 8:      # the smaller kit still wins: push HP up while the full kit can still win
        trial = hp * 1.1
        w2 = kit_score(mid, wk, trial, boss)
        if w2 < 10:
            break
        hp, win = trial, w2
        lose = kit_score(mid, lk, hp, boss)
        steps += 1
    m = json.load(open(path))
    m["hp_mult"] = round(hp, 3)
    json.dump(m, open(path, "w"), indent=1)
    flag = "" if lose < 0 else "   <-- smaller kit can still win"
    print("%-18s map#%d hp %.2f -> %.2f  kit%d best %d   kit%d best %d%s" % (mid, idx + 1, hp0, hp, wk, win, lk, lose, flag), flush=True)


if __name__ == "__main__" and "--kit" in sys.argv:
    maps = json.load(open(os.path.join(ROOT, "data", "maps.json")))["maps"]
    seen = {}
    todo = []
    for mm in maps:
        seen[mm["era"]] = seen.get(mm["era"], -1) + 1
        if len(sys.argv) <= 2 or mm["id"] in sys.argv:
            todo.append((mm["id"], seen[mm["era"]]))
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(tune_kit, todo))
    sys.exit(0)

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
