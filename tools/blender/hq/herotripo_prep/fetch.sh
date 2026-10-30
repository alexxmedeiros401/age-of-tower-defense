#!/bin/bash
# Fetch a runner result: bash fetch.sh NAME DEST   (NAME as TAG_ID_RUN; unzips into DEST). Exit 2 if not there yet.
set -e
NAME=$1; DEST=$2
R=alexxmedeiros401/age-of-tower-defense
RID=$(gh api "repos/$R/releases?per_page=100" --jq '[.[] | select(.tag_name=="art-builds")] | sort_by(.created_at) | .[0].id')
AID=""
for p in $(seq 1 30); do
  L=$(gh api "repos/$R/releases/$RID/assets?per_page=100&page=$p" --jq ".[] | select(.name==\"$NAME.zip\") | .id")
  [ -n "$L" ] && { AID=$L; break; }
  [ "$(gh api "repos/$R/releases/$RID/assets?per_page=100&page=$p" --jq 'length')" = "0" ] && break
done
[ -n "$AID" ] || { echo "no $NAME.zip yet"; exit 2; }
mkdir -p "$DEST"
gh api -H "Accept: application/octet-stream" "repos/$R/releases/assets/$AID" > "$DEST/$NAME.zip"
(cd "$DEST" && unzip -qo "$NAME.zip" && rm "$NAME.zip")
echo "fetched $NAME -> $DEST"; ls "$DEST"
