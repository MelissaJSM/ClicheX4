"""Arrange diagnostic ARC partial forms at a fixed origin, without editing art."""
from pathlib import Path
import sys,json,hashlib,argparse
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
source=W/'nana_audit/hurt_repaint/packed_hurt_diagnostic_v1/PL00_U.ARC'
data=source.read_bytes();assert sha(data)=='f82332cada27d4b39ea73f12d449e284057e36c4c337b8d1b0ae8e32d0483879'
parser=argparse.ArgumentParser();parser.add_argument('--version',default='01');a=parser.parse_args()
assert a.version in ('01','02')
arc=Archive(data);D=W/('nana_hurt_partial_review'+a.version);D.mkdir(exist_ok=False)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
manifest={'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(data),'origin':[160,160],
 'scope':'기본/포스 새피격4키포즈×16마스크×팔2유형, 동일RGBA만 중복제거해 표시. 오라 후속 교정 전 진단.',
 'art_or_game_modified':False,'all128_actually_viewed':False,'frames':[],'pages':[]}
for ref in (106,110,233,234):
 images={};arm_alias={}
 for mask in range(16):
  hashes=[]
  for arm in (1,2):
   im,_=arc.composite(ref,mask,arm);images[mask,arm]=im;digest=sha(im.tobytes());hashes.append(digest)
   manifest['frames'].append({'ref':ref,'mask':mask,'arm':arm,'rgba_sha256':digest,'bbox':im.getbbox()})
  arm_alias[mask]=hashes[0]==hashes[1]
 assert all(arm_alias.values()),'Arm variants differ: render separately instead of skipping'
 # Four rows by four columns: same origin and same crop in every cell.
 box=(130,120,194,188);scale=4;cw=(box[2]-box[0])*scale+8;ch=(box[3]-box[1])*scale+25
 board=Image.new('RGB',(cw*4,ch*4),'#83939c');draw=ImageDraw.Draw(board)
 for mask in range(16):
  x,y=(mask%4)*cw,(mask//4)*ch;draw.text((x+4,y+4),f'Nana {ref} / mask {mask:02} / arm1=arm2',font=font,fill='white')
  src=images[mask,2].crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST)
  board.paste(src,(x+4,y+24),src)
 p=D/f'partial_{ref}.png';board.save(p);manifest['pages'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'ref':ref,'displayed_masks':list(range(16)),'equivalent_arm_types':[1,2]})
(D/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'images':len(manifest['frames']),'pages':len(manifest['pages']),'manifest_sha256':sha((D/'manifest.json').read_bytes())}))
