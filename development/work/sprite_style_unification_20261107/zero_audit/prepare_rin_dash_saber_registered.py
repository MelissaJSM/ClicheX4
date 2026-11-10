"""질풍아8 새 원화·국소 등록의 고정 입력을 모은다."""
from pathlib import Path
import hashlib,json,struct,sys,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from scripts.prepare_rin_run import connected_groups
D=Path(__file__).parent/'rin_extension';O=D/'dash_saber_registered_v1';assert not O.exists();O.mkdir()
P=D/'prepared_ladder_dash01/PL01_U.ARC';SHA='c2ec4099740eb77cca2d37e4b0f997728e1748a35e47b45475289725ec1dd09b';arc=P.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(P)==SHA
sources={n:D/'dash_saber_followup01/registered_probe_v2'for n in(158,160,162,164)}
sources[168]=D/'dash_saber_followup02/anchor_probe'
sources.update({n:D/'dash_saber_followup02/local_legs01/registered_probe_v2'for n in(166,170,172)})
generated=[(D/'dash_saber_followup01/generated.png','5822662cbf913ecb8423c22aabc907c54320b01cda093630ad65df7c283c92e2'),(D/'dash_saber_followup02/generated.png','7c79a91f84ef0c0d54f2ece05bba359cf25eb4c94b2ef457be416c5054c337f4'),(D/'dash_saber_followup02/local_legs01/generated.png','294299cbf65a3f2946d80422ca522998f5fd53facffb492bbdca94e0eda01b66')]
for p,h in generated:assert sha(p)==h
rows=[];arrays={}
for n,path in sorted(sources.items()):
 key=f'b0_{n:03}';p=path/(key+'_indices.png');a=np.array(Image.open(p));assert a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15
 assert len(connected_groups(a>0))==1;old=render(arc,0,0,n)[0];assert np.nonzero(old)[0].max()==np.nonzero(a)[0].max()
 shutil.copyfile(p,O/p.name);arrays[n]=a
 rows.append({'key':key,'source_indices':str(p.relative_to(ROOT)),'source_sha256':sha(p),'registration':str((path/'registration.json').relative_to(ROOT)),'registration_sha256':sha(path/'registration.json'),'output_sha256':sha(O/p.name),'new_body_pixel_count':int(np.count_nonzero(a)),'floor':int(np.nonzero(a)[0].max()),'old_head_override':False})
for name,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(arc,9),row*32)
 for i,start in enumerate((158,166)):
  items=[]
  for n in range(start,start+8,2):items.extend([(f'b0_{n:03} old',rgba(render(arc,0,0,n)[0],pal)),(f'b0_{n:03} new',rgba(arrays[n],pal))])
  page(items,rgba(render(arc,0,0,147)[0],pal),O/f'{name}_comparison_{i:02}.png',cols=2,scale=5)
result={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'generated':[{'path':str(p.relative_to(ROOT)),'sha256':h}for p,h in generated],'records':rows,'scope':'질풍아158..172 짝수8 전신 세부 통일. 원 검기/타이밍/게임 원점 보존.166/170/172 새 종아리 원화로 길이 보완.','user_accepted':False,'runtime_verified':False,'root_review_pending':True}
(O/'registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'frames':len(rows),'registration_sha256':sha(O/'registration.json')}))
