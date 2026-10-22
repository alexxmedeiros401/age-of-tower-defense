#!/bin/sh
# Brings the build scripts (tools/, data/) up to date with the art branch.
R=$HOME/mnt/Documents/AgeOfTD
cd $R/repo && git fetch -q --depth 1 origin art/stone-age-v2 && git reset -q --hard FETCH_HEAD && git log --oneline -1
cp tools/pc/runner.py $R/runner.py
cp tools/pc/start_runner.bat "$R/Start AgeOfTD runner.bat"
