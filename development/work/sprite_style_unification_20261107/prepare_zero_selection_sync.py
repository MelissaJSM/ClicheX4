"""Pack current Zero body art into its existing character-select allocation."""
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry,SELECTION_MAPPING,actual_frame
from scripts.prepare_rin_ui_small import register,protected_repack,world
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_album import selection_image,zero_image,zero_palettes
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
W=Path(__file__).resolve().parent
def sha(x):return hashlib.sha256(x).hexdigest()
p=argparse.ArgumentParser();p.add_argument('character',choices=['riko','rin']);a=p.parse_args()
mode='br' if a.character=='riko' else 'rn'
plan=json.loads((W/f'staging_{mode}_v12.json').read_text('utf8'))
audit=json.loads((W/'selection_sync_audit01'/a.character/'report.json').read_text('utf8'))
src=ROOT/plan['source_bin'];assert sha(src.read_bytes())==plan['source_sha256']
assets=read_disc(src,('PL01_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
for n in list(assets):
 if n in plan['resources']:
  row=plan['resources'][n];assets[n]=(ROOT/row['path']).read_bytes();assert sha(assets[n])==row['after']
if a.character=='rin':assets['PL01_U.ARC']=(W/'zero_audit/rin_extension/prepared_bank1_recovery128/PL01_U.ARC').read_bytes()
assert {n:sha(b)for n,b in assets.items()}==audit['asset_hashes']
arc=assets['PL01_U.ARC'];old=assets['ST0E_U1.ARC'];tex=entry(old,0x10102);parts=entry(old,10)
out=W/'selection_sync01'/a.character;assert not out.exists() or not any(out.iterdir());out.mkdir(parents=True,exist_ok=True)
# The sprite itself remains in the exact gameplay coordinate system. Only
# transparent covering windows may be fitted inside existing part counts.
positioned,targets,layouts=register(parts,0,SELECTION_MAPPING,tex[:40960],arc)
if a.character=='riko':
 from pack_selection_mirrors import repack
 texture,nparts,packing=repack(tex[:40960],parts,positioned,0,targets,{38:0})
else:
 texture,nparts,packing=protected_repack(tex[:40960],parts,positioned,0,targets,{38:0})
new=replace_entry(replace_entry(old,0x10102,texture+tex[40960:]),10,nparts)
assert len(new)==len(old)
assert entry(new,0x10102)[40960:]==tex[40960:]
assert replace_entry(replace_entry(old,0x10102,entry(new,0x10102)),10,nparts)==new
allowed=set();copied=0;others=0
for bank,lo,hi in ((0,0,40960),(1,40960,90112),(2,90112,len(tex))):
 for n in range(composition_frame(parts,bank,0)['bank_frame_count']):
  before=composition_frame(parts,bank,n);after=composition_frame(nparts,bank,n)
  assert len(before['parts'])==len(after['parts'])
  if bank==0 and n in SELECTION_MAPPING:
   expected=world(actual_frame({'built_arc':arc},*SELECTION_MAPPING[n]))
   assert world(compose_static(texture,local_composition(after)))==expected
   for x,y in zip(before['parts'],after['parts']):
    assert all(x[k]==y[k]for k in ('unknown_flags','record_offset'))
    if a.character!='riko':assert all(x[k]==y[k]for k in ('flip_x','flip_y'))
    assert y['clut']==(0 if n==38 else x['clut'])
    allowed.update(range(x['record_offset'],x['record_offset']+4))
   copied+=1
  else:
   assert before==after
   assert compose_static(tex[lo:hi],local_composition(before))==compose_static(entry(new,0x10102)[lo:hi],local_composition(after))
   others+=1
assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(parts,nparts)))
pal=zero_palettes(arc);newassets={**assets,'ST0E_U1.ARC':new}
for n,(bank,ref) in SELECTION_MAPPING.items():
 ui=selection_image(newassets,{'bank':0,'ref':n})
 body=zero_image(arc,a.character,{'id':f'{a.character}:normal:b{bank}_{ref:03d}','bank':bank,'ref':ref,'form':'normal'},pal)
 assert np.array_equal(np.array(ui),np.array(body)),f'RGBA mismatch:{n}'
assert entry(assets['COL0E_U1.ARC'],5)[:32]==entry(arc,9)[:32]
(out/'ST0E_U1.ARC').write_bytes(new)
report={'character':a.character,'source_bin':plan['source_bin'],'source_sha256':plan['source_sha256'],'source_selection_sha256':sha(old),'candidate_sha256':sha(new),'body_sha256':sha(arc),'mapping':{str(k):list(v) for k,v in SELECTION_MAPPING.items()},'selection_targets':copied,'other_selection_frames_exact':others,'pixel_coordinates_and_rgba_exact':True,'portrait_and_x_texture_exact':True,'palette_unchanged':True,'part_counts_unchanged':True,'part_flips_unchanged':a.character!='riko','layouts':layouts,'packing':packing,'runtime_verified':False,'root_art_review_pending':True,'active_pointer_changed':False}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'character':a.character,'sha256':sha(new),'targets':copied,'other_frames':others,'packing':packing}))
