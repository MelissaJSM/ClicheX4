"""질풍아 원몸체104/검기125의 MIPS 순서로 새 몸체 접점을 대조한다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'dash_saber222_review';O.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_ladder_dash01/PL01_U.ARC').read_bytes();new=(D/'prepared_dash_saber01/PL01_U.ARC').read_bytes()
assert sha(old)=='c2ec4099740eb77cca2d37e4b0f997728e1748a35e47b45475289725ec1dd09b'and sha(new)=='94b24181ee1d6ce463f1647e89f58fcf29c57e8eb8cc6ede457cc46e22fc36da'
tp=D/'ladder_dash01/contact_probe/report.json';proof=json.loads(tp.read_text('utf8'));assert proof['passed']and proof['native_animation_calls']==160
pairs=list(dict.fromkeys((v['body'],v['effect'])for v in proof['timelines']['dash']));assert pairs[:9]==[(156,157)]+[(n,n+1)for n in range(158,174,2)]
fxpal=struct.unpack_from('<16H',entry(new,9),9*32);files=[]
for form,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for start in range(0,len(pairs),4):
  items=[]
  for n,e in pairs[start:start+4]:
   fx=render(new,0,0,e)[0];assert np.array_equal(fx,render(old,0,0,e)[0])
   for label,arc in [('old',old),('new',new)]:
    pic=rgba(render(arc,0,0,n)[0],pal);pic.alpha_composite(rgba(fx,fxpal));items.append((f'{n}+{e} {label}',pic))
  p=O/f'effects_{form}_{start//4:02}.png';page(items,rgba(render(new,0,0,147)[0],pal),p,cols=2,scale=4);files.append(p.name)
 # Readable three-part source-order strips, same absolute origin in each cell.
 seq=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json').read_text('utf8'))['animations'];seq=next(s for s in seq if s['id']==104)
 refs=list(dict.fromkeys(s['frame']for s in seq['steps']))
 for ix in range(0,len(refs),5):
  subset=refs[ix:ix+5];cell=(96*4,96*4+24);sheet=Image.new('RGB',(cell[0]*len(subset),cell[1]*2),'#64717b');draw=ImageDraw.Draw(sheet)
  for j,n in enumerate(subset):
   for iy,(label,arc)in enumerate([('old',old),('new',new)]):
    pic=rgba(render(arc,0,0,n)[0],pal).crop((112,104,208,200)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(j*384,iy*cell[1]+24),pic);draw.text((j*384+4,iy*cell[1]+4),f'{label} b0_{n:03}',fill='white')
  p=O/f'body_sequence_{form}_{ix//5:02}.png';sheet.save(p);files.append(p.name)
report={'passed':True,'candidate_sha256':sha(new),'source_arc_sha256':sha(old),'native_timeline_proof':str(tp.relative_to(ROOT)),'native_timeline_proof_sha256':sha(tp.read_bytes()),'pairs':pairs,'effect_palette_row':9,'effect_pixels_exact':True,'sheets':files,'runtime_verified':False,'user_accepted':False,'limitations':['원MIPS 몸/검기 시간표 순서에 따른 같은 원점 합성이다. 실제 객체 이동·가림·카메라·물리는 재현하지 않는다.','마지막173의 잔존은 외부 이벤트 삭제를 시뮬레이션하지 않은 표 진행 결과이며 실제 종료 지연으로 해석하지 않는다.']}
(O/'effect_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sheets':len(files),'pairs':len(pairs)}))
