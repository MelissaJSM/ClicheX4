"""Current52 representative remaining-art boards, without modifying art/resources."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rin_extension';O=D/'remaining_after52_review';O.mkdir(exist_ok=True)
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
arc=(D/'prepared_burst_pair_final_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
groups=[
 ('movement_remaining',[(0,3),(0,34),(0,36),(0,38),(0,41),(0,45)]),
 ('ground_attacks',[(0,63),(0,73),(0,85),(0,111),(0,125),(0,133)]),
 ('wall_air_attacks',[(1,50),(1,54),(1,61),(0,213),(0,229),(0,230)]),
 ('special_angles',[(1,132),(1,150),(1,165),(1,171),(0,156),(0,166)]),
 ('hurt_and_ceremony',[(0,136),(0,143),(0,149),(1,1),(1,3),(1,6)]),
 ('vehicle_angles',[(1,17),(1,20),(1,34),(1,66),(1,75),(1,85)]),
 ('rear_arrival_burst',[(0,178),(0,186),(0,195),(0,250),(0,252),(1,177)]),
]
idle=render(arc,0,0,147)[0];arrays={k:render(arc,k[0],k[0]*5,k[1])[0]for _,keys in groups for k in keys};arrays[0,147]=idle
pal=list(struct.unpack_from('<64H',entry(arc,9)));hist=(ROOT/'out/sprite_consistency_20261105/rin/normal/preview_palettes.bin').read_bytes();historical=struct.unpack('<64H',hist);assert pal[:16]==list(historical[:16]);pal[32:48]=historical[32:48]
boxes=[rgba(a,pal).getbbox()for a in arrays.values()];boxes=[b for b in boxes if b];crop=(min(b[0]for b in boxes)-4,min(b[1]for b in boxes)-4,max(b[2]for b in boxes)+4,max(b[3]for b in boxes)+4);cw,ch=crop[2]-crop[0],crop[3]-crop[1];scale=5
manifest=[]
for page,(name,keys)in enumerate(groups):
 for variant,row in[('normal',0),('black',13)]:
  words=pal.copy();words[:16]=struct.unpack_from('<16H',entry(arc,9),row*32);cellw=2*cw*scale+22;cellh=ch*scale+35;sheet=Image.new('RGB',(cellw*2,cellh*3),'#313c49');draw=ImageDraw.Draw(sheet)
  for j,(b,n)in enumerate(keys):
   col,rr=j%2,j//2;x,y=col*cellw,rr*cellh;label=f'b{b}_{n:03} {name}';draw.text((x+6,y+7),label,fill='white')
   for k,a in enumerate((idle,arrays[b,n])):
    im=rgba(a,words);bb=im.getbbox();assert not bb or(crop[0]<=bb[0]and crop[1]<=bb[1]and crop[2]>=bb[2]and crop[3]>=bb[3]);im=im.crop(crop).resize((cw*scale,ch*scale),Image.Resampling.NEAREST);xy=(x+k*(cw*scale+8),y+25);sheet.paste(im,xy,im)
  file=O/f'{variant}_{page:02}_{name}.png';sheet.save(file)
  manifest.append({'path':str(file.relative_to(ROOT)),'variant':variant,'refs':[[b,n]for b,n in keys],'fixed_crop':crop,'scale':scale,'all_native_alpha_included':True})
report={'source_arc_sha256':sha(arc),'new_art_generated':False,'sheets':manifest,'representatives':len(arrays)-1,'palette_scope':'몸체0/블랙13은 현재ARC. 비제로CLUT 효과 중2는 기존갤러리 역사캡처 프리뷰이며 현재실기색증거 아님.','purpose':'이전 장부에서 아직 새 원화 등록하지 않은 큰 동작의 실제 윤곽·체형·내부 묘사를 대기와 대조하는 별도 자료. 생성만으로 열람을 주장하지 않음.'}
(O/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'crop':crop,'representatives':len(arrays)-1,'sheets':len(manifest)}))
