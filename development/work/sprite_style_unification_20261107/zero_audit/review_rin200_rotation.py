"""원표 회전·효과 참고와 마지막→처음 연결을 분리해 표시한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'spin200_review'
old=(D/'prepared_ice01/PL01_U.ARC').read_bytes();new=(D/'prepared_spin01/PL01_U.ARC').read_bytes()
assert hashlib.sha256(new).hexdigest()=='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a'
seq=list(range(161,176,2));box=(104,104,216,216);scale=3;size=336;records=[]
for form,row in [('normal',0),('black',13)]:
 words=list(struct.unpack_from('<64H',entry(new,9)));words[:16]=struct.unpack_from('<16H',entry(new,9),row*32)
 # 마지막→처음은 원게임 재생 분기라고 주장하지 않는 별도 미술 반복이다.
 for effects in (False,True):
  sheet=Image.new('RGB',(size*9,(size+25)*2),'#64717b');dr=ImageDraw.Draw(sheet)
  for col,n in enumerate(seq+[161]):
   for y,(arc,label)in enumerate([(old,'old'),(new,'new')]):
    a=render(arc,1,5,n)[0];eff=render(arc,1,5,n+1)[0]
    if effects:a=np.where(eff,eff,a)
    outside=a.copy();outside[104:216,104:216]=0;assert not outside.any()
    im=rgba(a,words).crop(box).resize((size,size),Image.Resampling.NEAREST);sheet.paste(im,(col*size,y*(size+25)+25),im);dr.text((col*size+4,y*(size+25)+4),f'{label} {n}'+(' repeat'if col==8 else ''),fill='white')
    cx=col*size+(160-104)*scale;cy=y*(size+25)+25+(160-104)*scale;dr.line((cx-2,cy,cx+2,cy),fill='#3d474c');dr.line((cx,cy-2,cx,cy+2),fill='#3d474c')
  name=f'rotation_{form}_'+('effects_reference'if effects else 'closed_art_cycle')+'.png';sheet.save(O/name);records.append({'path':name,'effect_reference':effects,'closed_cycle_is_art_review_only':True,'native_animation100_exits_175_to160':True})
  # GIF는 각 native2호출을 약33ms로 근사; 실제게임의 루프가 아닌 검토 반복.
  frames=[]
  for n in seq:
   frame=Image.new('RGB',(size*2,size+25),'#64717b');dr=ImageDraw.Draw(frame)
   for col,(arc,label)in enumerate([(old,'old'),(new,'new')]):
    a=render(arc,1,5,n)[0];eff=render(arc,1,5,n+1)[0]
    if effects:a=np.where(eff,eff,a)
    im=rgba(a,words).crop(box).resize((size,size),Image.Resampling.NEAREST);frame.paste(im,(col*size,25),im);dr.text((col*size+4,4),f'{label} {n}',fill='white')
   frames.append(frame)
  frames[0].save(O/name.replace('.png','.gif'),save_all=True,append_images=frames[1:],duration=33,loop=0)
(O/'rotation_review.json').write_text(json.dumps({'candidate_sha256':hashlib.sha256(new).hexdigest(),'rotation_pivot':[159.5,159.5],'sequence':seq,'source_native_animation':100,'actual_native_sequence':[132]+seq+[160,160],'actual_terminal_frame':160,'closed_cycle_native_claim':False,'effect_composition_runtime_claim':False,'sheets':records,'limitations':['原표100은132에서 시작해8방향 회전한 뒤160을 유지한다. 마지막175→161 반복은 모양 연속 확인용이며 원게임 분기가 아니다.','짝수 검기를 원점 동일·불투명 덮기로 합성한 정적 참고이다. 실제 무기객체 위치/CLUT/배합·물리는 미재현이다.']},ensure_ascii=False,indent=2)+'\n','utf8')
print(O)
