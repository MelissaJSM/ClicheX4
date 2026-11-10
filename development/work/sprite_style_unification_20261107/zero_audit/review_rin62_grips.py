from pathlib import Path
import sys,struct,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'third_saber_grip_review';O.mkdir(exist_ok=True)
old=(D/'prepared_burst_pair_final_v1/PL01_U.ARC').read_bytes();new=(D/'prepared_third_saber_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(old,9))
box=(124,148,164,174);scale=12;cell=(530,360)
out=Image.new('RGB',(cell[0]*2,cell[1]*5),(82,90,103));dr=ImageDraw.Draw(out)
for i,n in enumerate((109,111,113,115,121)):
 for j,arc in enumerate((old,new)):
  a=render(arc,0,0,n)[0];im=rgba(a,pal).crop(box).resize((480,312),Image.Resampling.NEAREST);x=j*cell[0]+35;y=i*cell[1]+28;out.paste(im,(x,y),im);dr.text((x,y-20),f'{n} '+('before'if j==0 else'new'),fill='white')
  for xx in range(box[0],box[2],2):dr.text((x+(xx-box[0])*scale,y-12),str(xx),fill='white')
  for yy in range(box[1],box[3],2):dr.text((x-27,y+(yy-box[1])*scale),str(yy),fill='white')
  for xx in range(box[0],box[2]+1):dr.line((x+(xx-box[0])*scale,y,x+(xx-box[0])*scale,y+312),fill=(45,52,65))
  for yy in range(box[1],box[3]+1):dr.line((x,y+(yy-box[1])*scale,x+480,y+(yy-box[1])*scale),fill=(45,52,65))
out.save(O/'hand_grid.png')
rois={109:(148,157,156,164),111:(128,163,135,170),113:(134,158,141,165),115:(133,160,141,166),121:(136,161,142,167)}
rows=[]
for n,roi in rois.items():
 samples=[]
 for arc in(old,new):
  a=render(arc,0,0,n)[0];x0,y0,x1,y1=roi;m=np.isin(a[y0:y1,x0:x1],(10,11));y,x=np.nonzero(m);assert len(x)
  samples.append({'pale_sample_count':len(x),'bbox':[int(x.min()+x0),int(y.min()+y0),int(x.max()+x0+1),int(y.max()+y0+1)],'centroid':[float(x.mean()+x0),float(y.mean()+y0)]})
 rows.append({'ref':n,'review_roi':list(roi),'before':samples[0],'after':samples[1],'pale_centroid_delta':[round(samples[1]['centroid'][k]-samples[0]['centroid'][k],3)for k in(0,1)]})
report={'source_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(new).hexdigest(),'review_image':'hand_grid.png','origin':[160,160],'world_translation':[0,0],'rows':rows,'method':'실제 확대 그림에서 고른 앞쪽 장갑 부분 ROI의 밝은 색인10·11만 비교한다. 새로운 명암 묘사 때문에 중심은 손 전체나 게임 접점 좌표와 같지 않다.','engine_hand_anchor_changed':False,'engine_anchor_scope':'게임 코드·시간표·게임 객체 원점은 변경하지 않았다. 새 손의 모든 윤곽 좌표가 원래와 같다는 뜻이 아니다.','effect_support_refs':[110,112,114,116,118,120,122,124,126,128,129],'effect_display_preservation_proof':'../final62_readback_audit.json','visual_observation':'팔·손이 따로 떨어지는 부분은 보이지 않는다. 밝은 장갑 묘사는 일부 약1픽셀 위아래로 바뀌며 121 손등의 어두운 면이 커졌다. 빠른 검기와 실제 맞물림은 실기 검증 전이다.','runtime_verified':False}
(O/'anchors.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(rows))
