"""Clothes candidate with exact accepted head and original neck seam protection."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;A=D/'riko_cloth_inputs';OUT=A/'registered_candidate_v1';OUT.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
arc=(D/'riko_restore/prepared_rear_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));meta=json.loads((A/'inputs.json').read_text('utf8'));probe=json.loads((A/'registration_probe/inspection.json').read_text('utf8'));offsets={r['ref']:r['new_head_translation_vs_original']for r in probe['frames']};targets={};records=[]
for r in meta['frames']:
 n=r['ref'];old=render(arc,0,0,n)[0];source=np.array(Image.open(A/'native'/f'b0_{n:03d}_indices.png'));mask=np.array(Image.open(A/r['preserve_head_mask']))>0;dx,dy=offsets[n];generated_head=np.roll(np.roll(mask,dy,axis=0),dx,axis=1);hx,hy=r['head_origin_world'];box=np.zeros_like(mask);box[160+hy+dy:160+hy+dy+19,160+hx+dx:160+hx+dx+23]=True;generated_head|=box&np.isin(source,[4,8,14]);out=source.copy();out[generated_head]=0;out[mask]=old[mask]
 seam=np.zeros_like(mask);seam[160+hy+17:160+hy+19+dy+2,160+hx-2:160+hx+25]=True;restore=seam&(out==0)&(old>0)&~mask;out[restore]=old[restore]
 assert np.array_equal(out[mask],old[mask]);targets[n]=out;Image.fromarray(out).save(OUT/f'b0_{n:03d}_indices.png');records.append({'ref':n,'generated_native_sha256':hashlib.sha256((A/'native'/f'b0_{n:03d}_indices.png').read_bytes()).hexdigest(),'generated_head_offset':[dx,dy],'head_preserved_pixels':int(mask.sum()),'neck_existing_pixels_restored':int(restore.sum()),'head_exact':True,'new_sha256':hashlib.sha256((OUT/f'b0_{n:03d}_indices.png').read_bytes()).hexdigest()})
for name,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);board=Image.new('RGB',(1200,428*4),'#64717b');draw=ImageDraw.Draw(board)
 for i,n in enumerate(targets):
  for j,(label,p)in enumerate([('original',render(arc,0,0,n)[0]),('authored',np.array(Image.open(A/'native'/f'b0_{n:03d}_indices.png'))),('protected head / neck',targets[n])]):
   im=rgba(p,words).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST);board.paste(im,(j*400,i*428+28),im);draw.text((j*400+4,i*428+4),f'{n} {label}',fill='white')
 board.save(OUT/f'{name}_comparison.png')
 for p in range(2):board.crop((0,p*856,1200,(p+1)*856)).save(OUT/f'{name}_comparison_{p}.png')
(OUT/'registration.json').write_text(json.dumps({'source_arc_sha256':hashlib.sha256(arc).hexdigest(),'generated_sha256':hashlib.sha256((A/'generated.png').read_bytes()).hexdigest(),'frames':records,'packed':False,'runtime_verified':False,'game_changed':False,'review_only':True},ensure_ascii=False,indent=2)+'\n','utf8')
