#!/bin/sh
# PC side (run in the linked Linux shell, which sees Documents under ~/mnt): fetch a pc-jobs branch made by push_pc.sh
# and queue, for each unit, a rig job and then a review job on the Windows runner (GPU renders: AOTD_GPU=OPTIX).
#   sh pcrig.sh pc-jobs/TAG-RUN ID [ID ...] [-- REVIEW ARGS]     e.g. ... -- --only clips --frames Attack@8,Attack@12
# Outputs: Documents\AgeOfTD\out\pc\TAG-RUN\ID\ (ID.glb, ID_hq.blend, rig_report.json, the review sheets); job logs in
# logs\, state in status.json. Git runs in the shell's own home (the mounted folder can't delete git's lock files);
# only the branch's tools/ and pcin/ are copied into jobs\TAG-RUN\.
set -e
BR=$1; shift
N=${BR#pc-jobs/}
IDS=""; while [ $# -gt 0 ] && [ "$1" != "--" ]; do IDS="$IDS $1"; shift; done
[ "$1" = "--" ] && shift
R=$HOME/mnt/Documents/AgeOfTD
G=$HOME/pcgit/$N
rm -rf "$G"
git clone -q --depth 1 --filter=blob:none --sparse --branch "$BR" https://github.com/alexxmedeiros401/age-of-tower-defense "$G"
git -C "$G" sparse-checkout set --no-cone /tools/ /pcin/
J=$R/jobs/$N
mkdir -p "$J"
cp -r "$G/tools" "$G/pcin" "$J/"
rm -rf "$G"
python3 - "$N" "$*" $IDS <<'PY'
import json, os, sys, time
n, rargs, ids = sys.argv[1], sys.argv[2].split(), sys.argv[3:]
R = os.path.expanduser("~/mnt/Documents/AgeOfTD")
J = "{ROOT}/jobs/%s" % n
HQ = J + "/tools/blender/hq"
env = {"AOTD_GPU": "OPTIX", "HEROTRIPO_WORK": J + "/pcin", "HEROTRIPO_OLD_DIR": J + "/pcin/old"}
stamp = time.strftime("%H%M%S")
for i, hid in enumerate(ids):
    o = "{OUT}/pc/%s/%s" % (n, hid)
    rig = dict(name="%s_%s_rig" % (n, hid), cwd=HQ, env=env, mem_gb=3, mkdirs=[o],
               cmd=["{PY}", "herotripo_rig.py", "--", "--hero", hid, "--low", J + "/pcin/%s/bake/low.blend" % hid, "--out", o],
               expect=[o + "/%s.glb" % hid])
    rev = dict(name="%s_%s_review" % (n, hid), cwd=HQ, env=env, mem_gb=3, after=[rig["name"]],
               cmd=["{PY}", "herotripo_review.py", "--", "--hero", hid, "--new", o + "/%s_hq.blend" % hid, "--out", o] + rargs,
               expect=[o + "/clips.png"] if not rargs else [])
    for k, spec in ((0, rig), (1, rev)):
        p = os.path.join(R, "queue", "%s_%02d%d_%s.json" % (stamp, i, k, spec["name"]))
        json.dump(spec, open(p + ".tmp", "w"), indent=1)
        os.replace(p + ".tmp", p)
        print("queued", os.path.basename(p))
PY
