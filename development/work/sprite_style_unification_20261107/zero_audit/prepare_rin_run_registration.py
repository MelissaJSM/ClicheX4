"""Review whole-pose horizontal registration; never warp individual limbs."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rin_extension/run_registration_v1';OUT.mkdir(exist_ok=True)
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
parent=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';arc=read_disc(parent,('PL01_U.ARC',))[0]['PL01_U.ARC'];records=[];targets={}
for n,dx in [(13,3),(16,4)]:
 source=D/'rin_extension/run_inputs/run02/native'/f'b0_{n:03d}_indices.png';a=np.array(Image.open(source));target=np.roll(a,dx,axis=1);assert np.count_nonzero(target)==np.count_nonzero(a);Image.fromarray(target).save(OUT/f'b0_{n:03d}_indices.png');targets[n]=(a,target);records.append({'ref':n,'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'translation':[dx,0],'per_limb_edit':False,'native_image':f'b0_{n:03d}_indices.png','registered_sha256':hashlib.sha256((OUT/f'b0_{n:03d}_indices.png').read_bytes()).hexdigest()})
for name,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(arc,9),row*32);board=Image.new('RGB',(1152,408*2),'#64717b');draw=ImageDraw.Draw(board)
 for y,n in enumerate((13,16)):
  for x,(label,a)in enumerate([('current game',render(arc,0,0,n)[0]),('new initial',targets[n][0]),('new aligned',targets[n][1])]):
   p=rgba(a,pal).crop((128,128,192,192)).resize((384,384),Image.Resampling.NEAREST);board.paste(p,(x*384,y*408+24),p);draw.text((x*384+4,y*408+4),f'{n} {label}',fill='white')
 board.save(OUT/(name+'_comparison.png'))
(OUT/'registration.json').write_text(json.dumps({'frames':records,'reason':'얼굴·허벅지·발이 같은 방향으로 이동한 원화 셀의 위치만 교정했다. 다리 포즈나 크기를 바꾸지 않는다.','game_changed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
