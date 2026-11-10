"""원MIPS 시간표104/125의 첫4 몸체·검기를 같은 원점으로 대조한다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'dash_saber_followup01';O=A/'effect_probe_v2';assert not O.exists();O.mkdir()
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['archive_sha256']
proof=D/'ladder_dash01/contact_probe/report.json';timeline=json.loads(proof.read_text('utf8'));assert timeline['passed']and timeline['native_animation_calls']==160
pairs=list(dict.fromkeys((v['body'],v['effect'])for v in timeline['timelines']['dash']if v['body']in(158,160,162,164)));assert pairs==[(158,159),(160,161),(162,163),(164,165)]
roi={158:(125,159,136,170),160:(127,149,138,158),162:(132,149,145,162),164:(162,151,176,163)}
records=[]
fxpal=struct.unpack_from('<16H',entry(arc,9),9*32)
for name,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(arc,9),row*32);items=[]
 for n,e in pairs:
  old=render(arc,0,0,n)[0];new=np.array(Image.open(A/'registered_probe_v2'/f'b0_{n:03}_indices.png'));fx=render(arc,0,0,e)[0];ys,xs=np.where(fx>0)
  rec={'body':n,'effect':e,'form':name,'hand_roi':roi[n]}
  for label,body in [('old',old),('new',new)]:
   img=rgba(body,pal);img.alpha_composite(rgba(fx,fxpal));items.append((f'{n}+{e} {label}',img));x0,y0,x1,y1=roi[n];r=np.zeros_like(body,bool);r[y0:y1,x0:x1]=True;by,bx=np.where((body>0)&r)
   assert len(bx);rec[label+'_hand_effect_distance']=int(np.maximum(abs(by[:,None]-ys),abs(bx[:,None]-xs)).min());rec[label+'_roi_overlap']=int(np.count_nonzero((body>0)&(fx>0)&r))
  records.append(rec)
 page(items,rgba(render(arc,0,0,147)[0],pal),O/(name+'_comparison.png'),cols=2,scale=4)
(O/'report.json').write_text(json.dumps({'candidate_only':True,'source_arc_sha256':info['archive_sha256'],'native_timeline_proof':str(proof.relative_to(ROOT)),'native_timeline_proof_sha256':hashlib.sha256(proof.read_bytes()).hexdigest(),'pairs':pairs,'effect_palette_row':9,'records':records,'runtime_verified':False,'limitations':['원래 검기 자체가 손과 겹치지 않는 후속 구간이 있으므로 최소 거리만으로 접점 합격을 판정하지 않는다.','같은 원점 합성은 미술 참고이며 실제 객체 위치/좌우별 실기 검증을 대신하지 않는다.']},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
