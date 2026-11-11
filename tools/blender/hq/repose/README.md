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
| triage.py | detection over every clip (heroes, towers): `python3 triage.py GLB OUT.json [clips|all] [step]`. The body is voxelized at rest (1 cm) and labelled by bone; posed arm/hand/weapon points are taken back to rest through head/chest/spine/root and looked up: `pen_<side>_head/torso` (m, beyond the rest overlap), `near_<side>_head`, and per frame psi / forearm twist / elbow / wrist |
| landmarks.py | authoring aid: shoulders, head/hair volume slices, torso, and each clip's shipped wrist/elbow positions in chest-relative rest coords (`EXTRA=bone`, `AXIS="hand.R:x,y,z"` print a prop's position / axis) |
| hero_arm.py | generic re-author (heroes): `python3 hero_arm.py IN OUT CFG.py [NUMBERS.json]`. CFG.CLIPS: per clip and side, wrist/pole keys (chest-relative rest coords, Catmull-Rom) or a function; hand mode `keep` / `straight` (+ `twist_<side>` keys) / `world` (the hand keeps its shipped orientation: only where the fist is changes) / aim keys `[(f, dir, up)]` with CFG.AXIS_<side>; `{'offset': vec or f->vec}` in place of keys (the shipped wrist path moved by a chest-relative offset; the shipped arm is used where the offset is 0, eased by its size), `blend`, `blend_<side>` (ease from/to the shipped arm at the ends), `world_rot` (an extra turn of a 'world' hand about a chest axis, e.g. a weapon turned off the head), `aim_fix_<side>` (swing a held axis onto a bone point, e.g. an arrow onto the bow), `follow_tail` (bones whose tails met the old hand, e.g. bowstrings, re-aimed and stretched), `keep_roll` (keep the shipped upper-arm roll and forearm twist: forearm-mounted blades), CFG.HOLD_PROPS (which parentless props follow the hands), `keep_world` (child props keep their world turn, e.g. a sling), `hand_smooth` (sigma, for shipped fists that spin), `psi_max`, `wrist_max`, `tw_max`, `loop`. Analytic two-bone IK; upper-arm roll only to line up the elbow hinge, within +-30, smoothed and <= 6 deg/frame; twist smoothed <= 10 deg/frame; `_half` / `forearm_twist` bones get their herotripo shares; parentless props held by a re-authored hand keep their grip |
| frames.py / video.py | every frame of chosen clips (workbench, az list, `ZOOM`) and the side-by-side before/after mp4 |

Hero configs: `cfg/<id>_arms.py` (rhB pass; deliverables in /home/claude/work/repose/<id>/).

Club Warrior was built as `author.py` (left arm, cfg/club_warrior_ik.py) then `clubarm.py` (right arm, cfg/club_warrior_arm.py).

Lessons (each was a rejected take):
- Patching the old motion (rotating the arm out where it clips) looks wrong. Re-author the whole move from the ready pose.
- Keep hands and weapons outside the head/hair silhouette: overhead moves go out to the side, beside the head.
- Never aim a weapon with the wrist alone (wrist > ~65 deg, twist flips): it reads as janky.
- Never let the upper arm roll a lot (> ~30 deg): the skin twists (watch an armband or bracer go diagonal).
- Forearm twist must be continuous frame to frame (no +60 -> -60 flips).
- Check per frame: upper-arm roll, forearm twist, wrist angle, elbow angle, and their frame-to-frame deltas.
- A weapon fist on these Tripo hands often grips at 100-180 deg from the hand bone's rest frame: re-aiming the weapon from
  keys (or a straight wrist) lays blades across faces or needs a 100+ deg wrist. Keep the shipped weapon orientation
  (`world`) and move the fist (heroes: Kira, Tarek).
- The 315 camera puts anything at the unit's front-right at head height over its face: raised right hands go out (x >= 0.45)
  and level with or behind the head (y >= 0), not forward.
- Review as video (front az 315 and back az 200, elev 35) and close-ups; the user judges the motion, not stills.

Tower pass notes (rtA):
- Weapons sit in the fist across the palm (perpendicular to the forearm): with a straight wrist a held staff/axe/mallet
  stands up when the forearm is level, points back when it is upright, forward when the arm hangs. Design the hand
  path so the arm carries the weapon, and use `aim` < 1 where the weapon direction only matters a little.
- Arms are short on the Tripo bodies (~0.6 m reach): two-handed grips only meet close in front of the chest; check
  the elbow angle in the report (12 deg = the target was out of reach and was clamped).
- Several stances are side-on (chest yawed, head turned to the target along chest +X): author in chest space, use
  headpose numbers to find where the face is.

Hero tools (from the heroes pass) ship as triage_heroes.py and shots_heroes.py; hero_arm.py imports may expect the names triage/shots, so check before reusing.
