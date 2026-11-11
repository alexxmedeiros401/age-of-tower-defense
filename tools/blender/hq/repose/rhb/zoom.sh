# zoom.sh GLB NAME BONE:t "spec" [FSIZE] -> /home/claude/work/repose/rhB_look/NAME.jpg
mkdir -p "/home/claude/work/repose/rhB_look/z_$2"; rm -f "/home/claude/work/repose/rhB_look/z_$2"/*.png
cd /home/claude/wt/rhB/tools/blender/hq/repose
FOCUS=$3 FSIZE=${5:-0.6} RX=260 RY=260 python3 shots.py $1 "/home/claude/work/repose/rhB_look/z_$2/s" "$4" 315,200,90 20 >/dev/null 2>&1
python3 - "$2" <<'PY'
import glob,sys
from PIL import Image, ImageDraw
n_=sys.argv[1]
fs=sorted(glob.glob(f'/home/claude/work/repose/rhB_look/z_{n_}/s_*.png'))
w,h=260,260; n=6
im=Image.new('RGB',(w*n,h*((len(fs)+n-1)//n)),'white'); d=ImageDraw.Draw(im)
for i,f in enumerate(fs): im.paste(Image.open(f).convert('RGB'),((i%n)*w,(i//n)*h)); d.text(((i%n)*w+3,(i//n)*h+3),f.split('/')[-1][2:-4],fill='black')
im.save(f'/home/claude/work/repose/rhB_look/{n_}.jpg',quality=85)
PY
