"""Test full native window reassignment when local moves cannot fit new art."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_keys as base
from scripts.prepare_shibuki_ultimate_production import fast_fit
from scripts.solve_sprite_cover import cover
from scripts.prepare_shibuki_armor_motion import identical
import scripts.prepare_shibuki_armor_motion as motion
def patient_fit(mask,count):
 result=fast_fit(mask,count)
 if result is not None:return result
 solved=cover(mask,count,15)
 print(json.dumps({'cover_status':solved['status'],'fits':solved['fits'],'limit':count}),flush=True)
 return solved['rects']if solved['fits']else None
motion.fit=patient_fit
arc=base.read_disc(ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin',('PL01_U.ARC',))[0]['PL01_U.ARC'];g,c=base.entry(arc,2),base.entry(arc,3);bank=base.graphics_bank(g,0);rows=[]
for n in(9,10,15,16):
 source=D/'rin_extension/run_inputs'/('run01'if n<12 else'run02')/'native'/f'b0_{n:03d}_indices.png'
 if n==16:source=D/'rin_extension/run_registration_v1/b0_016_indices.png'
 target=np.array(Image.open(source));f=bank['frames'][n];raw=base.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cp=base.composition_frame(c,0,n)
 try:
  new,records=identical(raw,f['tile_count'],target,set(range(f['tile_count'])),len(cp['parts']));nc=bytearray(c);assert all(p['flags']==0 for p in cp['parts'])
  for i,p in enumerate(cp['parts']):
   t,x,y=records[min(i,len(records)-1)];off=p['record_offset'];nc[off:off+4]=bytes([0,t,(x-160)&255,(y-160)&255])
  ng,_=base.packer.repack_raw(g,0,{n:new});out=base.replace_entry(base.replace_entry(arc,2,ng),3,bytes(nc));assert np.array_equal(base.render(out,0,0,n)[0],target);rows.append({'ref':n,'passed':True,'tile_count_preserved':f['tile_count'],'part_count_preserved':len(cp['parts']),'used_parts':len(records),'raw_sha256':base.sha(new)})
 except(ValueError,AssertionError)as exc:rows.append({'ref':n,'passed':False,'reason':str(exc)})
(D/'rin_extension/rewindow_probe.json').write_text(json.dumps({'frames':rows,'game_changed':False,'arc_saved':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
