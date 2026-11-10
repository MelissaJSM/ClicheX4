"""독립 추출한 원추진15위상을 동일 원점으로 새 다리와 합성한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def main():
 audit=N.parent/'zero_audit/nana_ultimate_hover_relations01';m=json.loads((audit/'conclusions.json').read_text('utf8'));a=Archive((N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC').read_bytes());out=D/'jet_contacts_probe_v1';out.mkdir(exist_ok=False);proof=[];pal=np.zeros((16,4),np.uint8)
 for i in range(1,16):pal[i]=[65+i*10,85+i*8,115+i*6,255]
 for n in(221,223,225,227,229):
  p=D/f'canonical_cases_probe_v3/body_{n:03}_indices.png';new=np.array(Image.open(p));old=a.composite(n,15)[0];rows=[(f'{n} old actual occupancy',[]),(f'{n} new candidate occupancy',[])];fxproof=[]
  for q in m['effect_frames']:
   if n not in q['player_refs']:continue
   f=q['effect_frame'];jet=np.load(ROOT/q['source_dump']);need(sha(jet.tobytes())==q['indexed_sha256'],'독립원효과hash');im=Image.fromarray(pal[jet]);oldmerge=im.copy();oldmerge.alpha_composite(old);newmerge=im.copy();newmerge.alpha_composite(a.rgba(new));rows[0][1].append((f'original FX{f}',oldmerge));rows[1][1].append((f'original FX{f}',newmerge));fxproof.append({'frame':f,'source_sha256':digest(ROOT/q['source_dump']),'indexed_sha256':q['indexed_sha256'],'opaque_effect':int((jet>0).sum()),'overlap_new_body':int(((jet>0)&(new>0)).sum()),'transform':[0,0],'part_records':q['parts']})
  helper.grid(rows,out/f'comparison_{n}.png',6);proof.append({'ref':n,'new_source':p.relative_to(ROOT).as_posix(),'new_sha256':digest(p),'original_effects':fxproof})
 write(out/'manifest.json',{'independent_source_report':(audit/'conclusions.json').relative_to(ROOT).as_posix(),'independent_source_sha256':digest(audit/'conclusions.json'),'frames':proof,'scope':'원파트·전체texel은 독립읽기와exact. 불꽃색은 구분용 중립색이며 실제0x7802 CLUT/블렌딩 재현이 아니다. 동일원점의 정적접점비교, 게임실기 미실행.','runtime_verified':False})
 print('5 keys x3 original phases compared')
if __name__=='__main__':main()
