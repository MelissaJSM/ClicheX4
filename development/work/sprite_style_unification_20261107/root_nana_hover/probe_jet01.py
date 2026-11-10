"""Check fixed-origin jet contacts; only reuse decoded effects after semantic comparison."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
from scripts.export_x_consistency import entry,composition_frame
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';ult=W/'nana_audit/ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC'
aa=parent.read_bytes();bb=ult.read_bytes();assert entry(aa,0x10206)==entry(bb,0x10206)
def semantics(data,n):
 return [{k:v for k,v in part.items() if k!='record_offset'}for part in composition_frame(entry(data,3),12,n)['parts']]
assert all(semantics(aa,n)==semantics(bb,n) for n in range(15))
audit=W/'zero_audit/nana_ultimate_hover_relations01/conclusions.json';m=json.loads(audit.read_text('utf8'));a=Archive(aa)
out=D/'jet_probe01';out.mkdir(exist_ok=False);pal=np.zeros((16,4),np.uint8)
for i in range(1,16):pal[i]=[65+i*10,85+i*8,115+i*6,255]
records=[]
for n in (221,223):
 for form,mask,start in [('base_legs',8,0),('fourth',15,16)]:
  src=D/f'registered01/{form}_{n:03}_indices.png';z=np.array(Image.open(src));old=a.composite(n,mask)[0];new=a.rgba(z,start);rows=[(f'{form} {n} current',[]),(f'{form} {n} new fixed cell',[])]
  frames=[]
  for q in m['effect_frames']:
   if n not in q['player_refs']:continue
   jet=np.load(ROOT/q['source_dump']);assert hashlib.sha256(jet.tobytes()).hexdigest()==q['indexed_sha256'];im=Image.fromarray(pal[jet])
   for row,body in zip(rows,[old,new]):
    merge=im.copy();merge.alpha_composite(body);row[1].append((f'original FX {q["effect_frame"]}',merge))
   frames.append({'frame':q['effect_frame'],'effect_sha256':q['indexed_sha256'],'new_body_overlap':int(((jet>0)&(z>0)).sum()),'effect_transform':[0,0]})
  helper.grid(rows,out/f'{form}_{n:03}.png',6);records.append({'ref':n,'form':form,'source_sha256':sha(src),'phases':frames})
(out/'manifest.json').write_text(json.dumps({'base_sha256':sha(parent),'ultimate_sha256':sha(ult),'static_texture_byte_equal':True,'all15_effect_part_semantics_equal':True,'record_offsets_not_compared':True,'source_audit_sha256':sha(audit),'frames':records,'scope':'중립색 원추진 정적합성. 실제CLUT/블렌딩/실기 아님. 몸체/효과 원점이 같다는 원코드근거 재사용; 기본별도 독립감사 진행.','runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print('4 figures x 3 original jet phases; no body or effect changes')
