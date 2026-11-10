"""현재 Ultimate 사격 위치와 새 대시 몸체의 원화 입력을 읽기 조립한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
from prepare_inputs import SRC,EXPECTED,merged
from collect_before_bodies import SOURCES
AFTER={**{n:'after_a_costume_probe_v4' for n in(67,71,79,93)},**{n:'after_b_costume_probe_v3' for n in(69,75,77,81)},**{n:'after_c_costume_probe_v4' for n in(83,94)}}
WINDOW=(112,112,208,208)
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());Y,X=np.indices((384,384));out=D/'firing_inputs_v1';out.mkdir(exist_ok=False);recs=[]
 cons=json.loads((D/'fire_constraints_v2/manifest.json').read_text('utf8'))
 for page,refs in [('a',(68,70,72,76)),('b',(78,80,82,84))]:
  boards={k:Image.new('RGBA',(1536,1536))for k in('before_targets','after_targets','original_before_geometry','original_after_geometry','weapons_only_before','weapons_only_after')};rows=[]
  for i,n in enumerate(refs):
   body=n-1;q=next(r for r in cons['frames']if r['ref']==n);x0,y0,x1,y1=q['window_world'];win=(X>=160+x0)&(X<160+x1)&(Y>=160+y0)&(Y<160+y1)
   heldp=D/('first_cases_probe_v2'if body in(67,71,79,93)else'more_cases_probe_v2')/f'case_{body:03}.png';held=np.array(Image.open(heldp));sources={}
   for form,mask in(('before',15),('after',0)):
    p=D/(SOURCES[body]if form=='before'else AFTER[body])/f'{form}_{body:03}.png';v=np.array(Image.open(p));v[held>0]=0;source=merged(a,n,mask);weapon=np.where(win,source,0).astype(np.uint8);need(weapon.max()<16,'Weapon CLUT');v[weapon>0]=weapon[weapon>0]
    Image.fromarray(weapon).save(out/f'{form}_case_{n:03}.png');Image.fromarray(v).save(out/f'{form}_input_{n:03}.png')
    rgba=a.rgba(v,16 if mask else 0);orig=a.composite(n,mask)[0];wim=a.rgba(weapon,16 if mask else 0)
    for k,im in((f'{form}_targets',rgba),(f'original_{form}_geometry',orig),(f'weapons_only_{form}',wim)):
     outside=np.array(im)[:,:,3].copy();outside[112:208,112:208]=0;need(not outside.any(),'Clipped input');boards[k].alpha_composite(im.crop(WINDOW).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
    sources[form]={'body_path':p.relative_to(ROOT).as_posix(),'body_sha256':digest(p),'input_index_sha256':sha(v.tobytes()),'case_index_sha256':sha(weapon.tobytes())}
   rows.append({'ref':n,'body_ref':body,'muzzle_world':q['muzzle_world'],'window_world':q['window_world'],'sources':sources,'held_gun_path':heldp.relative_to(ROOT).as_posix(),'held_gun_sha256':digest(heldp),'same_near_hand_to_be_redrawn':True,'existing_mask_case_variants':q['existing_color_variants']})
  for key,im in boards.items():im.save(out/f'{page}_{key}.png')
  recs.extend(rows)
 for form,mask in(('before',15),('after',0)):
  board=Image.new('RGBA',(1536,1536))
  for i,n in enumerate((0,85,34,58)):board.alpha_composite(a.composite(n,mask)[0].crop(WINDOW).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
  board.save(out/f'{form}_accepted_style.png')
 write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'frames':recs,'window_world':[-48,-48,48,48],'cell':[768,768],'integer_scale':8,'pages':{'a':[68,70,72,76],'b':[78,80,82,84]},'case72_existing_variant':'mask bit1: (-35,4) 검정 1점; mask0에서는 투명. 양 폼 실제 원조립을 개별 추출.','omitted74':'스파크와 원권총1점 변형을 별도 처리할 공유 동작. 단순72복사 금지.','images':{p.name:digest(p)for p in out.glob('*.png')},'native_packed':False,'runtime_verified':False})
 print(out)
if __name__=='__main__':main()
