"""총구를 고정한 채 대시 사격 아래팔의 등록 좌표를 보정한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from common import board,write,sha
from pack import pack
from warp_parts import warp
S=H/'ver_buki_riko';OLD=ROOT/'work/sprite_style_unification_20261107/shibuki_audit'
PBS=(0,5,6,7,8)
def main():
 out=S/'wrist_registration';out.mkdir(exist_ok=True);rows=[]
 for file,guarddir,forms in [('PL00_U.ARC','dash_barrel_guard02',[('base',0),('fourth',15)]),('PL02_U.ARC','ultimate_dash_barrel_guard01',[('ultimate_before',15),('ultimate_after',0)])]:
  arc=Archive((S/file).read_bytes());rr=json.loads((OLD/guarddir/'report.json').read_text('utf8'))['rows'];targets={}
  for n in range(68,85,2):
   q=72 if n==74 else n;row=next(r for r in rr if r['shot_ref']==q);mx,my=row['muzzle_world'];guard=np.array(Image.open(OLD/guarddir/f'{q:03}_mask.png'))>0
   # Ref82 already has a short folded wrist at the rear of the barrel.
   lift=0 if n==82 else 3
   yy,xx=np.indices((384,384));wx=xx-160;wy=yy-160
   left=mx+9;right=mx+20
   region=(wx>=left)&(wx<right)&(wy>=my+2)&(wy<=my+13)&~guard
   shift=np.rint(lift*np.clip((right-1-wx)/7,0,1)).astype(int)
   for b in PBS:
    v=arc.layer(n,b)[0];dest=v.copy();sy,sx=np.nonzero(region&(v>0));dest[region]=0
    dy=sy-shift[sy,sx];dest[dy,sx]=v[sy,sx]
    # Preserve every native barrel texel and transparent aperture in every layer.
    dest[guard]=v[guard]
    assert np.array_equal(dest[guard],v[guard]);targets[n,b]=dest
    Image.fromarray(dest).save(out/f'{file[:4]}_layer{b}_{n:03}.png')
   rows.append({'file':file,'ref':n,'muzzle_world':[mx,my],'wrist_lift_pixels':lift,'barrel_exact':True,'changed_pixels':sum(int(np.count_nonzero(targets[n,b]!=arc.layer(n,b)[0])) for b in PBS)})
  def transform(v,n,b):
   q=72 if n==74 else n;row=next(r for r in rr if r['shot_ref']==q);mx,my=row['muzzle_world'];guard=np.array(Image.open(OLD/guarddir/f'{q:03}_mask.png'))>0
   lift=0 if n==82 else 3;yy,xx=np.indices(v.shape);wx=xx-160;wy=yy-160;right=mx+20
   region=(wx>=mx+9)&(wx<right)&(wy>=my+2)&(wy<=my+13)&~guard
   if n==74:
    original=arc.layer(74,b)[0];body=arc.layer(72,b)[0];region&=~((original>0)&(body==0))
   shift=np.rint(lift*np.clip((right-1-wx)/7,0,1)).astype(int);dest=v.copy();sy,sx=np.nonzero(region&(v>0));dest[region]=0;dest[sy-shift[sy,sx],sx]=v[sy,sx];dest[guard]=v[guard];return dest
  data,proof=warp(arc.data,list(range(68,85,2)),PBS,transform);(S/(file[:4]+'_fixed.ARC')).write_bytes(data);write(out/(file[:4]+'_pack.json'),proof);new=Archive(data)
  for form,mask in forms:
   pics=[]
   for n in (68,70,72,76,78,80,82,84):pics.extend([(f'{form} {n} before',arc.composite(n,mask)[0]),(f'{form} {n} aligned',new.composite(n,mask)[0])])
   board(pics,out/(form+'.png'),cols=4)
 write(out/'registration.json',rows);print(rows)
if __name__=='__main__':main()
