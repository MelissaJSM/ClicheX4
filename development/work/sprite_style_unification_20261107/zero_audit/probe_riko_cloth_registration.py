"""Inspect generated clothes placement before committing semantic region edits."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;A=D/'riko_cloth_inputs';OUT=A/'registration_probe';OUT.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
arc=(D/'riko_restore/prepared_rear_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35];green=np.isin(front,[4,8,14]);meta=json.loads((A/'inputs.json').read_text('utf8'));rows=[];targets={}
for r in meta['frames']:
 n=r['ref'];old=render(arc,0,0,n)[0];source=np.array(Image.open(A/'native'/f'b0_{n:03d}_indices.png'));hx,hy=r['head_origin_world'];options=[]
 for dy in range(-4,5):
  for dx in range(-4,5):
   patch=source[160+hy+dy:160+hy+dy+19,160+hx+dx:160+hx+dx+23];diff=int(np.count_nonzero(patch[green]!=front[green]));extra=int(np.count_nonzero(np.isin(patch,[4,8,14])&~green));options.append((diff+extra,abs(dx)+abs(dy),dx,dy,diff,extra))
 score,_,dx,dy,diff,extra=min(options);out=source.copy();out[160+hy+dy:160+hy+dy+19,160+hx+dx:160+hx+dx+23]=0;mask=np.array(Image.open(A/r['preserve_head_mask']))>0;out[mask]=old[mask];targets[n]=out;rows.append({'ref':n,'new_head_translation_vs_original':[dx,dy],'matched_green_mismatch':diff,'extra_green':extra,'probe_scope':'Generated head rectangle cleared; original head semantic opaque mask restored. Body remains authored. Not a final clothing mask.','old_skin_colors':{int(k):int(v)for k,v in zip(*np.unique(old[np.isin(old,[2,6,11])],return_counts=True))}});Image.fromarray(out).save(OUT/f'b0_{n:03d}_indices.png')
for name,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);board=Image.new('RGB',(1200,428*4),'#64717b');draw=ImageDraw.Draw(board)
 for i,n in enumerate(targets):
  source=np.array(Image.open(A/'native'/f'b0_{n:03d}_indices.png'))
  for j,(label,p)in enumerate([('original',render(arc,0,0,n)[0]),('authored',source),('head protected probe',targets[n])]):
   im=rgba(p,words).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST);board.paste(im,(j*400,i*428+28),im);draw.text((j*400+4,i*428+4),f'{n} {label}',fill='white')
 board.save(OUT/f'{name}_comparison.png')
(OUT/'inspection.json').write_text(json.dumps({'generated_sha256':hashlib.sha256((A/'generated.png').read_bytes()).hexdigest(),'frames':rows,'packed':False,'game_changed':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
