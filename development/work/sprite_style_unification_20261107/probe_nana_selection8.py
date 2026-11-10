"""Measure Nana's old UI1..8 origins against the same pre-rework game body."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.build_sprite_style_album import selection_image
sha=lambda b:hashlib.sha256(b).hexdigest()
p=json.loads((W/'staging_rn_v36.json').read_text('utf8'));src=ROOT/p['source_bin'];assert sha(src.read_bytes())==p['source_sha256'];assets=read_disc(src,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0];a=Archive(assets['PL00_U.ARC']);rows=[]
for ref in range(1,9):
 body=ref+84;pic=np.array(a.composite(body)[0]);yy,xx=np.where(pic[:,:,3]>0);want=np.array(selection_image(assets,{'bank':2,'ref':ref}));matches=[];best=None
 for flip in (False,True):
  for dx in range(-3,4):
   for dy in range(-3,4):
    z=np.zeros_like(pic);tx=(319-xx if flip else xx)+dx;ty=yy+dy
    if np.any((tx<0)|(tx>=384)|(ty<0)|(ty>=384)):continue
    z[ty,tx]=pic[yy,xx];difference=int(np.count_nonzero(np.any(z!=want,axis=2)))
    q={'flip_x':flip,'dx':dx,'dy':dy,'different_pixels':difference}
    if best is None or difference<best['different_pixels']:best=q
    if difference==0:matches.append(q)
 rows.append({'ui_ref':ref,'game_ref':body,'exact_matches':matches,'nearest':best})
r={'source_bin':p['source_bin'],'source_sha256':p['source_sha256'],'asset_hashes':{name:sha(data)for name,data in assets.items()},'rows':rows,'all_eight_exact':all(len(q['exact_matches'])==1 for q in rows),'files_or_memory_modified':False}
out=W/'nana_selection8_origins.json';assert not out.exists();out.write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'all_eight_exact':r['all_eight_exact'],'rows':rows}))
