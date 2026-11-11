# repose: re-animating arms for the Tripo bodies

The Tripo rebuilds kept the old skeletons and clips, but the new bodies have bigger heads, beards, bellies and
shorter arms, so the old arm motion drives arms and weapons through heads and bodies. These tools re-author the arm
motion of a clip on a shipped GLB (body, legs, head keep their keys) and export it with the rig's export settings.

| file | what |
|---|---|
| shots.py | `python3 shots.py GLB OUTPREFIX "Clip:f,f,..;Clip2:..." AZ[,AZ] [ELEV]` workbench renders (RX/RY env for size) |
| sheet.py | `python3 sheet.py OUT.jpg AZ PREFIX [PREFIX ...]` one row per prefix |
| armclear.py | triage: per frame, how deep arm/hand/weapon vertices sit inside the head/neck or torso (prints `pen`). Its auto-correction output is NOT shippable (it was rejected); use it only to find bad clips/frames |
| author_rs.py | Rock Slinger: IK hand paths (Catmull-Rom through keyed wrist targets and elbow poles, chest-relative) for both arms, straight wrists, sling trails the hand (lag) |
| author.py | the same, generic: `python3 author.py IN OUT CFG.py`; CFG gives ATTACK/LOOP clip names, ATK_R/ATK_L key lists `(frame, wrist, pole)`, loop_r/loop_l(f), optional SLING, optional CLUB_AXIS + club_dir(clip, f) |
| clubarm.py | weapon arm: `python3 clubarm.py IN OUT CFG.py`, CFG.CLIPS = {clip: [(frame, wrist, weapon_dir)]}, CLUB_AXIS (weapon axis, rest armature space). Solves forearm direction, upper-arm roll (psi, kept small) and forearm twist (continuous) so the weapon points along weapon_dir with a modest wrist |

| armsolve.py | generic two-arm re-author (towers, rtA): `python3 armsolve.py IN OUT cfg/<id>.py [report.json]`. Wrist paths (+ optional weapon dir/up, elbow pole, aim) keyed chest-relative per clip/side; per frame the elbow goes where the upper arm needs the least roll, the forearm twist gives the smallest wrist, both smoothed in time; WINDOW (re-author only some frames), GRAB (two-handed: one wrist rides the other hand's weapon), PRE/POST hooks. Prints/reports psi, twist, wrist, elbow and their frame deltas |
| triage.py | detection: per clip/frame, forearm/hand/weapon depth inside head/neck and torso (bind-pose overlaps left out), joint numbers, chest-relative wrist/elbow/hand frame. `python3 triage.py GLB OUT.json` |
| follow.py | cfg helper: keep the shipped hand paths/orientations but move them (an offset per frame) and rebuild the arms; `attach()` keeps a prop on its own bone (halberd, linstock) with the hand |
| bowstring.py | cfg helper (bows): string tails follow the nock, the arrow re-aims at its rest on the bow, where the shipped clip had them |
| beforeafter.py / unitnums.py | deliverables: shipped-vs-new video (315 then 200, clips twice), notes numbers tables |

Club Warrior was built as `author.py` (left arm, cfg/club_warrior_ik.py) then `clubarm.py` (right arm, cfg/club_warrior_arm.py).

Lessons (each was a rejected take):
- Patching the old motion (rotating the arm out where it clips) looks wrong. Re-author the whole move from the ready pose.
- Keep hands and weapons outside the head/hair silhouette: overhead moves go out to the side, beside the head.
- Never aim a weapon with the wrist alone (wrist > ~65 deg, twist flips): it reads as janky.
- Never let the upper arm roll a lot (> ~30 deg): the skin twists (watch an armband or bracer go diagonal).
- Forearm twist must be continuous frame to frame (no +60 -> -60 flips).
- Check per frame: upper-arm roll, forearm twist, wrist angle, elbow angle, and their frame-to-frame deltas.
- Review as video (front az 315 and back az 200, elev 35) and close-ups; the user judges the motion, not stills.

Tower pass notes (rtA):
- Weapons sit in the fist across the palm (perpendicular to the forearm): with a straight wrist a held staff/axe/mallet
  stands up when the forearm is level, points back when it is upright, forward when the arm hangs. Design the hand
  path so the arm carries the weapon, and use `aim` < 1 where the weapon direction only matters a little.
- Arms are short on the Tripo bodies (~0.6 m reach): two-handed grips only meet close in front of the chest; check
  the elbow angle in the report (12 deg = the target was out of reach and was clamped).
- Several stances are side-on (chest yawed, head turned to the target along chest +X): author in chest space, use
  headpose numbers to find where the face is.
