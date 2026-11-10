"""새 전신을 보존하고 생성한 팔 영역만 등록한다. 원래 배럴은 좌표 그대로."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_rin_run import quantize
from native_pose_pack import SOURCE,SOURCE_SHA
from register_run_costumes import LANDMARKS
from src.psx_disc import file_hash
LANDMARKS.update({11:(151,155,169),13:(151,155,169),17:(152,157,170)})
def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 a=Archive(read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC']);refs=list(range(3,32,2));records=json.loads((H/'shot_inputs01/inputs.json').read_text('utf8'))['frames']
 out=H/'shot_registered05';out.mkdir(exist_ok=False);report=[];final={};registered_offsets={}
 for kind,start in [('before',16),('after',0)]:
  folder=out/kind;folder.mkdir();rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start+1:start+16]],np.int32)
  for pg in range(1,5):
   src=H/f'shot_inputs01/{kind}/generated_{pg:02}.png';im=Image.open(src).convert('RGBA');assert im.size==(1536,1024)
   for j,n in enumerate(refs[(pg-1)*4:pg*4]):
    new=np.zeros((384,384),np.uint8);new[128:192,112:208]=quantize(im.crop((j%2*768,j//2*512,j%2*768+768,j//2*512+512)),rgb,.125)
    body=np.array(Image.open(H/f'run_registered02/{kind}/{n:03}_indices.png'));r=next(r for r in records if r['run_ref']==n);mx,my=[q+160 for q in r['muzzle_world']];cx,neck,hip=LANDMARKS[n]
    # Generated head drift is measured only to register the small new arm.
    best=[]
    for dy in range(-2,3):
     for dx in range(-2,3):
      b=np.roll(np.roll(new,dx,1),dy,0);s=(slice(130,neck),slice(140,173));m=body[s]>0;score=int(np.count_nonzero((b[s]==body[s])&m))-int(np.count_nonzero((b[s]>0)^(body[s]>0)))
      best.append((score,-abs(dx)-abs(dy),dx,dy))
    _,_,dx,dy=max(best)
    if kind=='before':registered_offsets[n]=(dx,dy)
    else:
     # The edit output shifted these arms despite keeping the source layout.
     # Integer registration, checked against the jacket arm alpha, no resize.
     dx,dy={5:(2,0),9:(4,0),29:(4,0)}.get(n,registered_offsets[n])
    new=np.roll(np.roll(new,dx,1),dy,0)
    polygon=[(mx+2,my+2),(cx-5,my+2),(cx-2,neck),(cx+3,neck+1),(cx+3,neck+10),(mx+7,neck+10),(mx-1,my+6)]
    m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(polygon,fill=1);edit=np.array(m,dtype=bool)
    # Head/neck upper surface remains the detailed approved new run art.
    edit[:neck+1,cx-4:]=False
    target=body.copy();target[edit]=new[edit];trim=[]
    if kind=='after':
     outside=edit&(target>0)&(final['before',n+1]==0);yy,xx=np.nonzero(outside);trim=list(map(list,zip(xx.tolist(),yy.tolist())));target[outside]=0
    barrel=np.array(Image.open(H/f'shot_inputs01/{kind}/{n+1:03}_barrel_indices.png'));barrel_protection=barrel>0
    if kind=='after':
     # Current base gun colours differ from the current jacket gun colours.
     # Preserve each form's own accepted barrel, rather than copying coat RGB.
     native=np.array(a.composite(n+1,0)[0]);m=barrel>0
     ix=((native[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-rgb[None,None,:,:])**2).sum(3).argmin(2).astype(np.uint8)+1
     barrel=np.where(m&(native[:,:,3]>0),ix,0).astype(np.uint8)
     assert np.array_equal(np.array(a.rgba(barrel,0))[m],native[m])
    target[barrel_protection]=barrel[barrel_protection]
    Image.fromarray(barrel).save(folder/f'{n+1:03}_barrel_indices.png')
    assert np.array_equal(target[~edit&~barrel_protection],body[~edit&~barrel_protection])
    for suffix,v in [('indices',target),('raw_generated',new),('edit_mask',edit.astype(np.uint8)*255)]:Image.fromarray(v).save(folder/f'{n+1:03}_{suffix}.png')
    a.rgba(target,start).save(folder/f'{n+1:03}.png');a.rgba(new,start).save(folder/f'{n+1:03}_generated.png')
    final[kind,n+1]=target
    report.append({'ref':n+1,'form':kind,'generated_path':src.relative_to(ROOT).as_posix(),'generated_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'generated_arm_translation':[dx,dy],'edit_polygon':polygon,'head_protection':[cx-4,neck+1],'barrel_pixels_exact':int(np.count_nonzero(barrel)),'after_boundary_trim_xy':trim,'changed_pixel_count':int(np.count_nonzero(target!=body)),'non_arm_new_body_exact':True,'old_body_copied':False})
  items=[]
  for n in refs:items +=[(f'{n} new run',Image.open(H/f'run_registered02/{kind}/{n:03}.png')),(f'{n+1} new shot',Image.open(folder/f'{n+1:03}.png'))]
  for k in range(0,len(items),8):page(items[k:k+8],a.composite(0,15 if kind=='before'else 0)[0],folder/f'comparison_{k//8:02}.png',cols=2,scale=4)
 conflicts={}
 for n in refs:
  b=final['before',n+1];v=final['after',n+1];yy,xx=np.nonzero((v>0)&(b==0));conflicts[n+1]=list(map(list,zip(xx.tolist(),yy.tolist())))
 (out/'registration.json').write_text(json.dumps({'source_sha256':SOURCE_SHA,'frames':report,'after_outside_before':conflicts,'not_final_until_review':True},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({n:len(v)for n,v in conflicts.items()}))
if __name__=='__main__':main()
