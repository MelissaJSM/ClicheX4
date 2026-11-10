"""표시 도트 불변: 16px 타일 창의 격자 위치만 탐색한다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'work/tools'))
from native_pose_pack import need,sha,write,crop
from scripts.export_x_consistency import Archive
import scripts.prepare_shibuki_armor_remaining as rem
from scripts.prepare_shibuki_ultimate_production import fast_fit
from pack_shibuki_hurt import repack_fixed_global
from optimize_hurt_tile_storage import optimize
from psx_compress_cost import encoded_cost
from src.psx_compress import encode_stream
PBS=(0,5,6,7,8)
def opts(im):
 yy,xx=np.nonzero(im);choices={}
 for dy in range(16):
  for dx in range(16):
   cells=sorted(set(zip(((xx-dx)//16).tolist(),((yy-dy)//16).tolist())));r=tuple((max(0,min(im.shape[1]-16,tx*16+dx)),max(0,min(im.shape[0]-16,ty*16+dy)))for tx,ty in cells);choices[r]=None
 minimum=min(map(len,choices));return sorted([r for r in choices if len(r)==minimum],key=lambda r:(len(r),r))
def main():
 o=H/'standing_special_storage03';need(not o.exists(),'Fresh grid probe');o.mkdir();a=Archive((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes());s=H/'standing_special_layers01';keys=[(n,b)for n in(95,97)for b in PBS];images=[crop(np.array(Image.open(s/f'{n:03}_bank{b}_indices.png')))for n,b in keys];options=[opts(im)for im in images];current=[tuple(map(tuple,fast_fit(im>0,24)))for im in images];maskkeys=[sha((im>0).tobytes())for im in images];cache={};trials=0
 def evaluate(choices):
  nonlocal trials
  mapping=dict(zip(maskkeys,choices));rem.fit=lambda mask,count:mapping[sha(mask.tobytes())];trials+=1
  try:r,rr=rem.pack_many_patterns(bytes(4096),32,images,set(range(1,32)),[24]*len(images))
  except ValueError:return 100000,None,None
  key=sha(r)
  if key not in cache:cache[key]=encoded_cost(r)
  return cache[key],r,rr
 best,raw,parts=evaluate(current);history=[{'initial':best,'options':list(map(len,options))}];print(json.dumps(history[-1]),flush=True)
 for round in range(3):
  initial=best
  for i,choices in enumerate(options):
   winner=current[i]
   for c in choices:
    test=current.copy();test[i]=c;value,nr,rr=evaluate(test)
    if value<best:best,raw,parts,winner=value,nr,rr,c
   current[i]=winner;history.append({'round':round,'layer':list(keys[i]),'best':best,'trials':trials});write(o/'progress.json',history);print(json.dumps(history[-1]),flush=True)
  if best==initial:break
 need(raw is not None,'No grid');need(len(encode_stream(raw))==best,'Cost mismatch');nr,mapping,opt=optimize(raw,{0,16},steps=16);parts=[[(mapping[t],x,y,fl)for t,x,y,fl in ps]for ps in parts]
 try:_,gr=repack_fixed_global(a,{95:nr,96:nr,97:nr},{95:32,96:32,97:32});trial={'passed':True,'graphics':gr}
 except ValueError as e:trial={'passed':False,'error':str(e)}
 (o/'joint.raw').write_bytes(nr);write(o/'report.json',{'keys':keys,'parts':parts,'grid_choices':current,'options':list(map(len,options)),'grid_best':best,'optimization':opt,'fixed_bank_trial':trial,'raw_sha256':sha(nr),'trials':trials,'unique_costs':len(cache),'art_unchanged':True,'arc_written':False});print(json.dumps({'grid_best':best,'final':opt['after'],'trial':trial}),flush=True)
if __name__=='__main__':main()
