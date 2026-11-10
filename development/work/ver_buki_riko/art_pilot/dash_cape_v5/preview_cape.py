import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "dash_v1"))
from fit_dash import *
D=Path(__file__).resolve().parent
import shutil
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T000131718284Z'
inv=json.loads((ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json').read_text('utf8'))
def picture(n):
 p=B/f'{"idle" if n==147 else "frame"}_{n:03}.png';im=Image.open(p).convert('RGBA');b=inv['frames'][f'bank0_{n:03}']['bounds'];canvas=Image.new('RGBA',(96,80));canvas.alpha_composite(im,(48+b[0],40+b[1]));return canvas
# Original per-step ticks, with an explicitly chosen loop repetition for a synthetic preview.
seq=[(147,30),(3,1),(4,1),(44,2),(45,1),(45,1),*([(46,2),(47,2),(48,2)]*6),(49,3),(50,2),(51,7),(52,5),(147,30)]
for scale in (1,4):
 images=[]
 for n,t in seq:
  c=Image.new('RGB',(192*scale,80*scale),(40,43,55));p=picture(n).resize((96*scale,80*scale),Image.Resampling.NEAREST);c.paste(p,(0,0),p);p=p.transpose(Image.Transpose.FLIP_LEFT_RIGHT);c.paste(p,(96*scale,0),p);images.append(c)
 ticks=0;dur=[]
 for n,t in seq:
  start=round(ticks*100/60);ticks+=t;dur.append(max(10,(round(ticks*100/60)-start)*10))
 images[0].save(B/f'dash_preview_{scale}x.gif',save_all=True,append_images=images[1:],duration=dur,loop=0,disposal=2)
for name in ('cape_before_after.png','design_checks.json','imagegen_calls.local.json'):shutil.copyfile(D/name,B/name)
(B/'preview_metadata.json').write_text(json.dumps({'kind':'Synthetic aligned art preview; not game capture','native_tick_duration':'1/60 second assumed for visualization','sequence':seq,'loop_repetitions_chosen_for_preview':6,'runtime_dash_length_not_proven_by_preview':True},indent=2),encoding='utf8')
