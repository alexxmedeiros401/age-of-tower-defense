# PC build runner

Runs the art pipeline's Blender jobs on a Windows PC (Alexx's: Ryzen 7 5700, RTX 4060 Ti) instead of the 2-core cloud
machine. Everything lives in one folder, `Documents\AgeOfTD`:

- `Start AgeOfTD runner.bat` (from `start_runner.bat`): the first time it downloads a standalone Python 3.13 and
  pip-installs `bpy==5.2.2`, numpy, scipy, scikit-image and pillow into it; then it runs `runner.py`.
- `runner.py`: takes job files from `queue\` (sorted by name), runs them at below-normal priority, at most `max_jobs` at
  once and only while `reserve_gb` of RAM stays free for the PC's owner (`runner_conf.json` overrides both), keeps the
  PC awake while jobs run, and records each job in `done\` or `failed\` with its log in `logs\`. `status.json` shows
  what is running; `sysinfo.json` the CPU, RAM and GPU. A file named `STOP` lets the running jobs finish and starts no
  more; closing the window stops everything (unfinished jobs go back in the queue).
- `repo\`: a sparse checkout of this repository (`tools/`, `data/`), kept up to date with `sync.sh` from the linked
  Linux sandbox (which sees `Documents` mounted under `~/mnt`).
- `out\`: everything the jobs build; the cloud session copies the finished files back.

A job file: `{"name", "cmd": ["{PY}", "script.py", ...], "cwd", "env", "mkdirs", "after": [job names], "mem_gb",
"expect": [files that must exist afterwards]}`; `{PY}`, `{ROOT}`, `{REPO}` and `{OUT}` are replaced with the folder's
paths. `AOTD_GPU=CUDA` in a job's env makes Cycles bake and render on the GPU (`tools/blender/hq/cycles_dev.py`).
`addjobs.py` queues a unit's three build steps, `addprev.py` a quick preview (coarse sculpt, quick rig, clip frames).
