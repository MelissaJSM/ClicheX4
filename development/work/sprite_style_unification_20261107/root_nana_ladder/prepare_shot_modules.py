"""Register the newly authored sleeves and the accepted compact pistol."""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((D/'first_inputs01/manifest.json').read_text('utf8'));a=Archive((ROOT/m['source_arc']).read_bytes());assert sha(a.data)==m['source_arc_sha256']
Y,X=np.indices((384,384));Y-=160;X-=160
ap=argparse.ArgumentParser();ap.add_argument('--v2',action='store_true');ap.add_argument('--v3',action='store_true');args=ap.parse_args();args.v2|=args.v3;out=D/('shot_modules03'if args.v3 else('shot_modules02'if args.v2 else'shot_modules01'));out.mkdir(exist_ok=False);rows=[];records=[]
for form,pal in(('base',0),('fourth',16)):
 for n in(150,155):
  body=np.array(Image.open(D/'common_legs02'/f'{form}_149_indices.png'));z=np.array(Image.open(D/'shot_registered01'/f'{form}_{n:03}_indices.png'))
  region=(X<=-2)&(Y>=-12)&(Y<=-2);arm=np.where(region&np.isin(z,[1,2,3,4,5,6,10,11,12,13]),z,0).astype(np.uint8)
  yy,xx=np.nonzero(arm);sx=int(xx.min()-160);sy=float(np.median(yy[xx==xx.min()])-160)
  old=a.layer(n)[0];oy,ox=np.nonzero(old);mx=int(ox.min()-160);my=float(np.median(oy[ox==ox.min()])-160);dx=mx-sx;dy=round(my-sy)
  shifted=np.zeros_like(arm);shifted[yy+dy,xx+dx]=arm[yy,xx]
  # The accepted 8-column barrel/grip front is a native asset, not painted.
  guard=(X>=mx)&(X<mx+8)&(Y>=int(my)-3)&(Y<=int(my)+5)
  shifted[guard]=old[guard]
  # Preserve the accepted new149 head, raised arm, hair, skirt and legs.
  remove=(X<=-4)&(Y>=-10)&(Y<=-1);rest=body.copy();rest[remove]=0
  shifted[(X>-2)|(Y>0)]=0
  if args.v2:
   head_guard=(X>=(-11 if args.v3 else -8))&(Y<=-11);shifted[head_guard]=0;rest[head_guard]=body[head_guard]
  merged=np.where(shifted,shifted,rest).astype(np.uint8)
  for kind,arr in(('arm',shifted),('body',merged),('removed_mask',remove.astype(np.uint8))):Image.fromarray(arr).save(out/f'{form}_{n:03}_{kind}.png')
  samebody=(~remove)&(shifted==0);assert np.array_equal(body[samebody],merged[samebody])
  records.append({'form':form,'ref':n,'source_sha256':sha(z.tobytes()),'body_sha256':sha(body.tobytes()),'old_muzzle':[mx,my],'source_muzzle':[sx,sy],'arm_translation':[dx,dy],'whole_body_rescale':False,'canonical_pistol_columns':8,'canonical_guard_exact':bool(np.array_equal(merged[guard],old[guard])),'components':int(label(merged>0,np.ones((3,3)))[1]),'native_indices_sha256':sha(merged.tobytes())})
  rows.append((f'{form} shot{n}',[('new rest149',a.rgba(body,pal)),('full generated source - not adopted',a.rgba(z,pal)),('registered arm only',a.rgba(shifted,pal)),('new149 plus new arm',a.rgba(merged,pal))]))
for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
(out/'manifest.json').write_text(json.dumps({'frames':records,'scope':'새 사격 원화의 전체몸은 크기/의상 차이로 미채택. 새149의 머리·몸·다리와 새팔만 결합한 검토 후보.','packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(records))
