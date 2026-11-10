"""Restore authored Riko midtone texels, without new art or game BIN writes."""
from pathlib import Path
from collections import defaultdict
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import edit_frame_set
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from scripts.ultimate_costume_swap import replace_entry
SOURCE=ROOT/'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
EXPECTED='21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'
ART=ROOT/'work/ver_buki_riko/art_pilot/ground_slash_v2'
TARGET={111:0,113:1,115:1,117:1,119:1,121:2,123:2,125:3,127:3}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8')
def need(value,message):
 if not value:raise ValueError(message)
def poly(points):
 im=Image.new('1',(192,192));ImageDraw.Draw(im).polygon([(x+96,y+96)for x,y in points],fill=1);return np.array(im)
def sources():
 data=np.load(ART/'lunge_worlds.npz');poses={int(n):data[n].copy()for n in data.files}
 mask=poly([(-5,-2),(10,-2),(10,7),(-5,7)])
 for n,w in poses.items():
  layer=np.where(mask,w,0).astype(np.uint8);body=np.where(mask,0,w).astype(np.uint8);layer=np.roll(layer,-6,axis=1);layer[body!=0]=body[body!=0];poses[n]=layer
 yy,xx=np.indices((192,192));wx,wy=xx-96,yy-96;common=((wy>=-5)&(wx < -12))|((wy>=0)&(wx < -6))|(wy>=8)
 for n,w in poses.items():w[common]=poses[1][common]
 return poses
def preview(arc,targets,path):
 pal=entry(arc,9);normal=struct.unpack_from('<64H',pal);black=list(normal);black[:16]=struct.unpack_from('<16H',pal,13*32)
 refs=[147]+list(TARGET);box=(118,114,197,190);scale=5;cw=(box[2]-box[0])*scale;ch=(box[3]-box[1])*scale+28
 board=Image.new('RGB',(cw*4,ch*len(refs)), '#68747c');d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
 for row,n in enumerate(refs):
  before=render(arc,0,0,n)[0];after=targets.get(n,before)
  for col,(a,p,label)in enumerate(((before,normal,'normal before'),(after,normal,'normal proposed'),(before,black,'black before'),(after,black,'black proposed'))):
   im=rgba(a,p).crop(box).resize((cw,ch-28),Image.Resampling.NEAREST);board.paste(im,(col*cw,row*ch+28),im);d.text((col*cw+4,row*ch+5),f'{n} {label}',font=font,fill='white')
 board.save(path)
def main():
 digest=hashlib.sha256()
 with SOURCE.open('rb')as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
 need(digest.hexdigest()==EXPECTED,'Parent hash mismatch')
 assets,_=read_disc(SOURCE,('PL01_U.ARC',));arc=assets['PL01_U.ARC'];poses=sources();targets={};proof=[]
 records={r['frame']:r for r in json.loads((ART/'lunge_registration.json').read_text('utf8'))}
 for n,key in TARGET.items():
  authored=np.zeros((384,384),np.uint8);authored[64:256,64:256]=poses[key]
  if n==113:authored=np.roll(authored,-1,axis=1)
  flat=authored.copy();flat[flat==12]=15;before=render(arc,0,0,n)[0]
  options=[]
  for dy in range(-8,9):
   for dx in range(-8,9):
    q=np.roll(np.roll(flat,dx,axis=1),dy,axis=0);options.append((int(np.count_nonzero(q!=before)),abs(dx)+abs(dy),dx,dy))
  mismatch,_,dx,dy=min(options);authored=np.roll(np.roll(authored,dx,axis=1),dy,axis=0)
  hx,hy=records[key]['head_world'];hx+=dx+(-1 if n==113 else 0);hy+=dy
  oldmask=authored==12;oldmask[160+hy:160+hy+19,160+hx:160+hx+23]=False
  mask=oldmask&(before==15);target=before.copy();target[mask]=12
  proof.append({'frame':n,'authored_pose':key,'registration_delta':[dx,dy],'flattened_source_current_mismatch':mismatch,'authored_midtones_outside_head':int(oldmask.sum()),'restored_pixels':int(mask.sum()),'skipped_not_current_white':int((oldmask&~mask).sum()),'world_pixels':[[int(x-160),int(y-160)]for y,x in np.argwhere(mask)],'head_box_preserved':[hx,hy,hx+23,hy+19]})
  need(mask.any(),f'No restoration for {n}');need(np.array_equal(before>0,target>0),'Alpha changed');targets[n]=target
 preview(arc,targets,OUT/'comparison.png');np.savez_compressed(OUT/'targets.npz',**{str(n):a for n,a in targets.items()});(OUT/'baseline_PL01_U.ARC').write_bytes(arc)
 dump(OUT/'inspection.json',{'source':str(SOURCE.relative_to(ROOT)),'sha256':EXPECTED,'arc_sha256':sha(arc),'original_lunge_sha256':sha((ART/'generated_lunge_v3.png').read_bytes()),'indices_source_sha256':sha((ART/'lunge_worlds.npz').read_bytes()),'restore_rule':'Only authored12 that is currently15; authored head region protected. Current all other pixels and geometry untouched.','proof':proof,'game_modified':False})
 print(json.dumps({'refs':len(proof),'changed_pixels':sum(r['restored_pixels']for r in proof),'alignment':[{k:r[k]for k in ('frame','registration_delta','flattened_source_current_mismatch','restored_pixels','skipped_not_current_white')}for r in proof]}))
if __name__=='__main__':main()
