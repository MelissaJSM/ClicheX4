"""Unlabeled approved-scope reference inputs; no generated or modified artwork."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;R=D/'rin_extension'
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
P=R/'prepared_air_continuation2_v2/PL01_U.ARC';arc=P.read_bytes();s=hashlib.sha256(arc).hexdigest();assert s=='ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df'
OUT=R/'detail_priority01';assert not OUT.exists();OUT.mkdir()
pal=struct.unpack_from('<16H',entry(arc,9));crop=(100,112,220,192);cw,ch=120,80;scale=8
sheet=Image.new('RGBA',(cw*2,ch*2));records=[]
for i,(b,n)in enumerate([(0,61),(0,174),(1,5),(1,183)]):
 a=render(arc,b,b*5,n)[0];im=rgba(a,pal);part=im.crop(crop)
 assert np.count_nonzero(np.array(part.getchannel('A')))==np.count_nonzero(a)
 key=f'b{b}_{n:03d}';sheet.alpha_composite(part,(i%2*cw,i//2*ch));im.save(OUT/(key+'_native.png'));Image.fromarray(a).save(OUT/(key+'_indices.png'))
 records.append({'key':key,'bank':b,'ref':n,'cell':[i%2,i//2],'bounds':im.getbbox()})
sheet.resize((cw*2*scale,ch*2*scale),Image.Resampling.NEAREST).save(OUT/'input.png')
style=Image.new('RGBA',(cw*2,ch*2))
for i,n in enumerate([147,8,95,29]):style.alpha_composite(rgba(render(arc,0,0,n)[0],pal).crop(crop),(i%2*cw,i//2*ch))
style.resize((cw*2*scale,ch*2*scale),Image.Resampling.NEAREST).save(OUT/'style.png')
info={'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','archive_sha256':s,'actual_input_arc':str(P.relative_to(ROOT)),'character':'rin','crop':crop,'native_cell':[cw,ch],'columns':2,'rows':2,'scale':scale,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'generated':False,'generation_pose_rules':['61의 앞/뒷발과 양손을 보존하고 상세 옷 주름과 머릿결을 다시 그린다.','174는 후면이고 정면 눈/얼굴을 넣지 않는다. 사다리 손과 양발 높이를 보존한다.','bank1_5는 반대 방향 옆면 승리 자세다. 정면/왼쪽 머리를 복사하지 않는다.','bank1_183의 낮은 손·무릎·양발 지면 접점과 위로 휜 리본을 유지한다.']}
(OUT/'inputs.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n','utf8');print(str(OUT))
