"""새 전후16몸체와 원총구를 4키씩 분리한 사격 편집 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need
from make_costume_review import AFTER
SRC=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'
EXPECTED='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
def merged(a,n,mask):
 v=a.layer(n)[0].copy()
 if mask:
  for pb in(8,5,7,6):
   q=a.layer(n,pb)[0];v[q>0]=q[q>0]
 return v
def main():
 need(digest(SRC)==EXPECTED,'Frozen parent');a=Archive(SRC.read_bytes());out=D/'firing_inputs_v1';out.mkdir(exist_ok=False);Y,X=np.indices((384,384));paths={};records=[]
 for page,folder in AFTER.items():
  q=json.loads((D/folder/'registration.json').read_text('utf8'))
  for r in q['frames']:paths[r['ref']]={'before':ROOT/r['before_path'],'after':D/folder/f"after_{r['ref']:03}.png",'case':D/folder/f"case_{r['ref']:03}.png"}
 cons=json.loads((D/'fire_constraints_v1/manifest.json').read_text('utf8'));pages={c:list(range(i*8+2,i*8+9,2))for i,c in enumerate('abcd')}
 for page,refs in pages.items():
  boards={k:Image.new('RGBA',(1536,1536))for k in('before_targets','after_targets','original_before_geometry','original_after_geometry','weapons_only_before','weapons_only_after')}
  for i,n in enumerate(refs):
   body=n-1;q=next(x for x in cons['frames']if x['ref']==n);x0,y0,x1,y1=q['window_world'];win=(X>=160+x0)&(X<160+x1)&(Y>=160+y0)&(Y<160+y1);heldp=paths[body]['case'];held=np.array(Image.open(heldp));sources={}
   need((held>0).sum()==20,'Canonical held gun20')
   for form,mask in(('before',15),('after',0)):
    p=paths[body][form];v=np.array(Image.open(p));need(np.array_equal(v[held>0],held[held>0]),'Current canonical held gun');v[held>0]=0
    old=merged(a,n,mask);weapon=np.where(win,old,0).astype(np.uint8);need(weapon.max()<16,'No effect inside case');v[weapon>0]=weapon[weapon>0]
    Image.fromarray(v).save(out/f'{form}_input_{n:03}.png');Image.fromarray(weapon).save(out/f'{form}_case_{n:03}.png')
    for k,im in((f'{form}_targets',a.rgba(v,16 if mask else 0)),(f'original_{form}_geometry',a.composite(n,mask)[0]),(f'weapons_only_{form}',a.rgba(weapon,16 if mask else 0))):
     al=np.array(im)[:,:,3].copy();al[112:208,112:208]=0;need(not al.any(),'No crop loss');boards[k].alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
    sources[form]={'body_path':p.relative_to(ROOT).as_posix(),'body_sha256':digest(p),'input_index_sha256':sha(v.tobytes()),'case_index_sha256':sha(weapon.tobytes())}
   records.append({'page':page,'ref':n,'body_ref':body,'window_world':q['window_world'],'muzzle_world':q['muzzle_world'],'existing_mask_case_variants':q['existing_color_variants'],'held_gun_path':heldp.relative_to(ROOT).as_posix(),'held_gun_sha256':digest(heldp),'sources':sources,'same_near_hand_to_be_redrawn':True})
  for key,im in boards.items():im.save(out/f'{page}_{key}.png')
 for form,mask in(('before',15),('after',0)):
  im=Image.new('RGBA',(1536,1536))
  for i,n in enumerate((0,85,34,68)):im.alpha_composite(a.composite(n,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
  im.save(out/f'{form}_accepted_style.png')
 write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'frames':records,'pages':pages,'window_world':[-48,-48,48,48],'cell':[768,768],'integer_scale':8,'images':{p.name:digest(p)for p in out.glob('*.png')},'native_packed':False,'runtime_verified':False,'source_policy':'새 몸체에 기존총구 8열을 고정하고 사격팔을 새로 제작할 입력. 접힌 앞팔은 같은 팔이므로 원화 편집에서 제거·교체. 이전 단색 소매와 머리는 채택하지 않음.'})
 print(json.dumps({'directory':str(out),'frames':len(records),'variants':{q['ref']:q['existing_mask_case_variants']for q in records}}))
if __name__=='__main__':main()
