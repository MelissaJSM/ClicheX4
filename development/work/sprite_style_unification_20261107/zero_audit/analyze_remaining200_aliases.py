"""既수용 새 원화와 남은 자세의 정확한 원래 표시 공유만 조사한다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render
D=Path(__file__).parent/'rin_extension';O=D/'remaining200_review';sha=lambda b:hashlib.sha256(b).hexdigest()
plan=json.loads((D/'rin200_components.json').read_text('utf8'));old=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(old)==plan['resources']['PL01_U.ARC']['before']
new=(D/'prepared_spin01/PL01_U.ARC').read_bytes();assert sha(new)==plan['resources']['PL01_U.ARC']['after']
ledger=json.loads((D/'progress_ledger.json').read_text('utf8'));proposal=json.loads((D/'prepared_spin01/proposal.json').read_text('utf8'));done=set(ledger['new_art_prepared_refs'])|set(proposal['new_art_refs']);manifest=json.loads((O/'manifest.json').read_text('utf8'))
def image(k):return render(old,int(k[1]),int(k[1])*5,int(k[3:]))[0]
def cropped(a):
 b=Image.fromarray(a).getbbox();return (sha(a[b[1]:b[3],b[0]:b[2]].tobytes()),[b[2]-b[0],b[3]-b[1]],list(b))if b else(None,None,None)
groups={}
for key in sorted(done):
 if not key.startswith(('b0_','b1_')):continue
 a=image(key);h,wh,b=cropped(a)
 if h:groups.setdefault((h,*wh),[]).append((key,b))
rows=[]
for g in manifest['groups']:
 for key in g['remaining_body_or_head_refs']:
  if not key.startswith(('b0_','b1_')):continue
  a=image(key);h,wh,b=cropped(a)
  if h:
   for match,mb in groups.get((h,*wh),[]):
    dx,dy=b[0]-mb[0],b[1]-mb[1];z=np.roll(image(match),(dy,dx),(0,1));assert np.array_equal(a,z)
    rows.append({'remaining_ref':key,'accepted_master':match,'translation':[dx,dy],'original_complete_indexed_canvas_exact':True,'same_new_source_after_translation_guaranteed':False})
(O/'exact_baseline_aliases.json').write_text(json.dumps({'source_sha256':sha(old),'candidate_sha256':sha(new),'matches':rows,'scope':'원래 전체 색인/알파가 정확 같은 평행이동만 기록한다. 서로 다른 자세·팔·의상에 대기 머리를 덮는 근거가 아니다. 아직 대상의 새 원화 확장이나 ARC 변경은 하지 않았다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(rows))
