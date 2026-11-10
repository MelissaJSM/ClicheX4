"""Exact source sharing and small native differences; not an art pass heuristic."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.verify_nana_ultimate_ui import read_assets
D=Path(__file__).parent/'rin_extension';O=D/'remaining141_review'
ledger=json.loads((D/'progress_ledger.json').read_text('utf8'));done=set(ledger['new_art_prepared_refs']);remaining=ledger['remaining_refs_in_original_audit']
parent=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin'
assets,_=read_assets(parent,['PL01_U.ARC']);original=assets['PL01_U.ARC'];sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(original)=='e6dbffce1b3f3fa4842c4092c6a4de09109db1bd5569864d4959cb7ec92849e2'
arc=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes();assert sha(arc)==ledger['current_sha256']
allkeys=sorted(set(done)|set(remaining));originals={};current={}
for key in allkeys:
 if not(key.startswith('b0_')or key.startswith('b1_')):continue
 b,n=int(key[1]),int(key[3:]);originals[key]=render(original,b,b*5,n)[0];current[key]=render(arc,b,b*5,n)[0]
def normalized(a):
 y,x=np.where(a>0)
 if not len(x):return '',[0,0]
 crop=a[y.min():y.max()+1,x.min():x.max()+1]
 return sha(str(crop.shape).encode()+crop.tobytes()),[int(x.min()),int(y.min())]
norm={k:normalized(v)for k,v in originals.items()};shares=[]
for k in remaining:
 if k not in originals:continue
 for n in done:
  if norm[k][0] and norm[k][0]==norm[n][0]:shares.append({'remaining':k,'authored_counterpart':n,'original_full_display_translation':[norm[k][1][0]-norm[n][1][0],norm[k][1][1]-norm[n][1][1]],'automatic_copy_allowed':False})
ground=[f'b0_{n:03}'for n in(3,4,83,85,87,89,91,93,105,107,130,133,134)]
pairs=[]
for i,k in enumerate(ground):
 for n in ground[i+1:]:
  diff=current[k]!=current[n];count=int(diff.sum());y,x=np.where(diff)
  pairs.append({'a':k,'b':n,'difference_pixels':count,'difference_bbox':None if not count else[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]})
oldbands={}
for y0 in (146,156,166,172):
 groups={}
 for k in ground:
  key=sha(current[k][y0:].tobytes());groups.setdefault(key,[]).append(k)
 oldbands[str(y0)]=[v for v in groups.values()if len(v)>1]
result={'source_arc_sha256':sha(arc),'original_arc_sha256':sha(original),'original_exact_or_rigid_to_already_authored':shares,'ground_pairwise_differences':sorted(pairs,key=lambda r:r['difference_pixels']),'ground_same_absolute_lower_bands':oldbands,'limits':['같은 하체/몸통 일부만으로 전신 공유를 승인하지 않는다.','같은 원본 전신도 현재 보존할 무기/손/이펙트 차이를 확인한 뒤 새 원화 확대를 결정한다.']}
(O/'sharing_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'matches':shares,'closest_ground':result['ground_pairwise_differences'][:15],'same_bands':oldbands}))
