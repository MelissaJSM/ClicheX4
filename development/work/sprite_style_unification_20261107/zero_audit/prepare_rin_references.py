"""Collect unchanged current Rin poses for a later authored art pilot."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;OUT=D/'rin_reference';OUT.mkdir(exist_ok=True)
source=json.loads((D/'sources.json').read_text('utf8'))['rin']
refs={'b0_147':'대기 기준: 머릿결·눈·턱·목과 카라·몸통 명암',
      'b0_008':'달리기: 얼굴과 흰 장갑의 덩어리화, 목·카라 분리',
      'b0_014':'달리기 반대 다리: 머리·팔·몸통의 같은 디테일 기준',
      'b0_049':'대시: 목·얼굴·커프스 구분과 단순한 의상 내부',
      'b0_095':'지상 검: 둥근 얼굴·장갑, 몸통의 넓은 단색 면',
      'b0_229':'공중 검: 턱·목·팔과 커프스 연결, 얇은 내부 명암',
      'b1_183':'웅크림 특수: 머리결·카라·몸통의 세부 단순화'}
manifest={'source_bin':source['source'],'source_sha256':source['sha256'],'PL01_sha256':source['PL01_sha256'],'native_size':[384,384],'origin':[160,160],'idle':'b0_147','authored_new_art':False,'game_changed':False,'frames':{}}
for form in ('normal','black'):
 folder=OUT/form;folder.mkdir(exist_ok=True);pics={}
 for key,reason in refs.items():
  path=ROOT/source['native_paths'][form+':'+key];data=path.read_bytes();target=folder/(key+'.png');target.write_bytes(data);pics[key]=Image.open(target).convert('RGBA')
  manifest['frames'][form+':'+key]={'source_png':str(path.relative_to(ROOT)),'file':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'review':reason}
 boxes=[p.getbbox()for p in pics.values()];box=(min(b[0]for b in boxes)-4,min(b[1]for b in boxes)-4,max(b[2]for b in boxes)+4,max(b[3]for b in boxes)+4);scale=6;cw=(box[2]-box[0])*scale;ch=(box[3]-box[1])*scale+30
 board=Image.new('RGB',(cw*3,ch*3),'#65727a');d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
 for i,(key,p)in enumerate(pics.items()):
  x,y=i%3*cw,i//3*ch;q=p.crop(box).resize((cw,ch-30),Image.Resampling.NEAREST);board.paste(q,(x,y+30),q);d.text((x+5,y+5),f'{form} {key}'+(' idle'if key=='b0_147'else''),font=font,fill='white')
 board.save(OUT/(form+'_six_poses.png'))
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'current_poses':6,'idle':1,'forms':2,'new_art':False}))
