#!/bin/bash
# ship.sh VERSION CODE MESSAGE   e.g.  bash tools/wip/ship.sh 0.9.114-art 123 "the Stone Age rigging pass"
# Bumps project.godot and export_presets.cfg, commits "vVERSION: MESSAGE", pushes the current branch and starts the
# Build workflow (APK + Windows) on it. The dev log itself lives in the claude.ai project ("claude/Dev Log.md").
set -e
V=$1; C=$2; M=$3
cd "$(dirname "$0")/../.."
sed -i "s/^config\/version=\".*\"/config\/version=\"$V\"/" project.godot
sed -i "s/^version\/code=.*/version\/code=$C/; s/^version\/name=\".*\"/version\/name=\"$V\"/" export_presets.cfg
grep -q "config/version=\"$V\"" project.godot && grep -q "version/code=$C" export_presets.cfg
git add project.godot export_presets.cfg
git commit -q -m "v$V: $M

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_013nZ2Ds3fGKMnyjcHQazzE2"
B=$(git rev-parse --abbrev-ref HEAD)
git push -q origin "$B"
gh workflow run build.yml --ref "$B" -R alexxmedeiros401/age-of-tower-defense
sleep 5
gh run list -R alexxmedeiros401/age-of-tower-defense --workflow build.yml --branch "$B" -L 1 --json url -q '.[0].url'
echo "SHIPPED $V"
