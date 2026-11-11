#!/bin/sh
# PC side (linked Linux shell): the game's map tests on the PC (Windows Godot, real GPU) instead of the cloud.
#   sh pcgame.sh setup                 once: Godot 4.7.2 (Windows console build) into AgeOfTD\godot\
#   sh pcgame.sh sync [REF]            the game at REF (GitHub's archive download) into AgeOfTD\game\, then queues a
#                                      headless import job (pc_import_<stamp>); run it again until it prints synced
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
  # The game at REF (a branch or a commit; default art/stone-age-v2) from GitHub's archive download (about 75 s for the
  # 0.9 GB archive), unpacked in the shell's home, then copied over AgeOfTD\game with checksums: only changed files are
  # written, nothing is deleted. Each linked-shell call lasts at most 3 minutes: run "sync" again until it prints
  # "synced" (it resumes where it stopped).
  REF=${2:-art/stone-age-v2}
  K=$(echo "$REF" | tr '/' '_')
  P=$HOME/pack; mkdir -p $P
  if [ ! -f $P/$K.x ]; then
    if [ ! -f $P/$K.dl ]; then
      rm -f $P/*.tar.gz $P/*.dl $P/*.x
      timeout 165 curl -sSL --fail -o $P/$K.tar.gz https://codeload.github.com/alexxmedeiros401/age-of-tower-defense/tar.gz/$REF \
        && touch $P/$K.dl || { echo "download incomplete (run again)"; exit 0; }
      echo "downloaded"; exit 0
    fi
    rm -rf $P/g && mkdir -p $P/g && tar xzf $P/$K.tar.gz -C $P/g --strip-components=1 && rm -f $P/$K.tar.gz && touch $P/$K.x
    echo "unpacked"; exit 0
  fi
  mkdir -p "$R/game"
  timeout 110 rsync -rc --exclude .godot --exclude .github $P/g/ "$R/game/" || { echo "copying (run again)"; exit 0; }
  echo "synced $REF"
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
