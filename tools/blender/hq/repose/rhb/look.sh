# look.sh GLB NAME "spec" [zoom]  -> sheets /home/claude/work/repose/rhB_look/NAME_315.jpg and _200.jpg
D=/home/claude/work/repose/rhB_look; mkdir -p $D/$2; rm -f $D/$2/*.png
cd /home/claude/wt/rhB/tools/blender/hq/repose
ZOOM=${4:-1.6} RX=${RX:-300} RY=${RY:-330} python3 shots.py $1 $D/$2/s "$3" 315,200 35 >/dev/null 2>&1
python3 - "$D/$2" "$D/$2" <<'PY'
import sys,glob
from PIL import Image, ImageDraw
d=sys.argv[1]
for az in ('315','200'):
    fs=sorted(glob.glob(f'{d}/s_*_az{az}.png'))
    w,h=Image.open(fs[0]).size; n=min(len(fs),8); rows=(len(fs)+n-1)//n
    s=Image.new('RGB',(w*n,h*rows),'white'); dr=ImageDraw.Draw(s)
    for i,f in enumerate(fs):
        s.paste(Image.open(f).convert('RGB'),((i%n)*w,(i//n)*h)); dr.text(((i%n)*w+4,(i//n)*h+4),f.split('/')[-1][2:-4],fill='black')
    s.save(f'{d}_{az}.jpg',quality=85)
PY
