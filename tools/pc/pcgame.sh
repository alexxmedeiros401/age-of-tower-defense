#!/bin/sh
# PC side (linked Linux shell): the game's map tests on the PC (Windows Godot, real GPU) instead of the cloud.
#   sh pcgame.sh setup                 once: Godot 4.7.2 (Windows console build) into AgeOfTD\godot\
#   sh pcgame.sh sync [REF]            the game (default art/stone-age-v2) into AgeOfTD\game\ (git in the shell's home,
#                                      then rsync without .git: the mounted folder can't delete git's lock files),
#                                      then queues a headless import job (pc_import_<stamp>)
#   sh pcgame.sh test NAME CAPTURE_MAP KINDS "unit ..." "map ..."
#        queues, after the newest import: one attack-capture job per unit (a 1920x1080 game window, --shoot-attacks
#        --focus --frames=40) and one headless --autowin job per map. Each job gets its own user-data folder through
#        APPDATA, so its screenshots land in AgeOfTD\ud\NAME_<job>\Godot\app_userdata\Age of Tower Defense\.
#        Results: logs\<job>.log (grep AUTOWIN / SCRIPT ERROR), screenshots as above.
set -e
R=$HOME/mnt/Documents/AgeOfTD
V=4.7.2
case "$1" in
setup)
  mkdir -p "$R/godot"
  # (the console build is a small wrapper that starts the main exe beside it BY NAME: keep both names as shipped)
  if [ ! -f "$R/godot/Godot_v$V-stable_win64_console.exe" ]; then
    cd $HOME && curl -sSL -o g.zip https://github.com/godotengine/godot/releases/download/$V-stable/Godot_v$V-stable_win64.exe.zip
    unzip -q -o g.zip -d gw && cp gw/Godot_v$V-stable_win64_console.exe gw/Godot_v$V-stable_win64.exe "$R/godot/" && rm -rf g.zip gw
  fi
  ls -la "$R/godot" ;;
sync)
  REF=${2:-art/stone-age-v2}
  G=$HOME/game
  if [ -d $G/.git ]; then git -C $G fetch -q --depth 1 origin "$REF" && git -C $G reset -q --hard FETCH_HEAD
  else git clone -q --depth 1 --branch "$REF" https://github.com/alexxmedeiros401/age-of-tower-defense $G; fi
  git -C $G log --oneline -1
  mkdir -p "$R/game"
  rsync -rt --exclude .git --exclude .godot $G/ "$R/game/"
  ST=$(date +%H%M%S)
  python3 - "$ST" <<'PY'
import json, os, sys
R = os.path.expanduser("~/mnt/Documents/AgeOfTD")
st = sys.argv[1]
spec = dict(name="pc_import_" + st, cwd="{ROOT}/game", mem_gb=3,
            cmd=["{ROOT}/godot/Godot_v4.7.2-stable_win64_console.exe", "--headless", "--path", "{ROOT}/game", "--import"])
p = os.path.join(R, "queue", "%s_000_%s.json" % (st, spec["name"]))
json.dump(spec, open(p + ".tmp", "w"), indent=1); os.replace(p + ".tmp", p)
open(os.path.join(R, "game_import.txt"), "w").write(spec["name"])
print("queued", spec["name"])
PY
  ;;
test)
  N=$2; CM=$3; K=$4; UNITS=$5; MAPS=$6
  python3 - "$N" "$CM" "$K" "$UNITS" "$MAPS" <<'PY'
import json, os, sys, time
R = os.path.expanduser("~/mnt/Documents/AgeOfTD")
n, cm, kinds, units, maps = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(), sys.argv[5].split()
imp = open(os.path.join(R, "game_import.txt")).read().strip()
st = time.strftime("%H%M%S")
G = "{ROOT}/godot/Godot_v4.7.2-stable_win64_console.exe"
jobs = []
for u in units:
    j = "%s_att_%s" % (n, u)
    jobs.append(dict(name=j, cwd="{ROOT}/game", mem_gb=3, after=[imp], env={"APPDATA": "{ROOT}/ud/" + j},
                     mkdirs=["{ROOT}/ud/" + j],
                     cmd=[G, "--path", "{ROOT}/game", "--resolution", "1920x1080", "--fixed-fps", "30", "--",
                          "--demo", "--map=" + cm, "--shoot-attacks", "--unit=" + u, "--focus", "--frames=40", "--skip=1",
                          "--kinds=" + kinds]))
for m in maps:
    j = "%s_aw_%s" % (n, m)
    jobs.append(dict(name=j, cwd="{ROOT}/game", mem_gb=2, after=[imp], env={"APPDATA": "{ROOT}/ud/" + j},
                     mkdirs=["{ROOT}/ud/" + j],
                     cmd=[G, "--headless", "--path", "{ROOT}/game", "--", "--autowin", "--map=" + m]))
for i, s in enumerate(jobs):
    p = os.path.join(R, "queue", "%s_%03d_%s.json" % (st, i, s["name"]))
    json.dump(s, open(p + ".tmp", "w"), indent=1); os.replace(p + ".tmp", p)
    print("queued", s["name"])
PY
  ;;
esac
