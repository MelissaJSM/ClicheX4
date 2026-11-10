"""Preflight accepted Rin run poses while three corrected poses are pending."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_keys as base
from fit_rin_windows import fit_windows
arc=base.read_disc(ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin',('PL01_U.ARC',))[0]['PL01_U.ARC'];g,c=base.entry(arc,2),base.entry(arc,3);bank=base.graphics_bank(g,0);paths={}
for folder in [base.ART/'native',*(D/'rin_extension/run_inputs'/f'run{i:02d}/native'for i in(1,2,3))]:
 for p in folder.glob('*_indices.png'):paths[int(p.stem.split('_')[1])]=p
for n in(13,16):paths[n]=D/'rin_extension/run_registration_v1'/f'b0_{n:03d}_indices.png'
rows=[]
for n in [7,8,9,10,11,12,13,14,15,16,19]:
 a=np.array(Image.open(paths[n]));f=bank['frames'][n];raw=base.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 try:
  parts,edits=fit_windows(c,n,raw,f['tile_count'],a,base.packer.edit_visible_set);cp=base.composition_frame(parts,0,n);_,sz,bb,_=base.compose_indices(raw,f['tile_count'],cp);want=a[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]];nr=base.packer.edit_visible_set(raw,f['tile_count'],[(cp,want.tobytes(),sz)]);row={'ref':n,'passed':True,'source':str(paths[n].relative_to(ROOT)),'source_sha256':base.sha(paths[n].read_bytes()),'window_edits':edits,'raw_size':len(nr)}
 except ValueError as e:row={'ref':n,'passed':False,'reason':str(e)}
 rows.append(row);print(json.dumps(row),flush=True)
(D/'rin_extension/run_preflight.json').write_text(json.dumps({'frames':rows,'pending_regenerated_refs':[17,18,20],'game_changed':False},ensure_ascii=False,indent=2)+'\n','utf8')
