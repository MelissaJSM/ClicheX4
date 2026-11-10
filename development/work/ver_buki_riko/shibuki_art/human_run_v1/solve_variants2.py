from pathlib import Path
import sys,json,itertools
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
from scripts.discover_inputs import psx_arc
from src.psx_player import composition_frame,graphics_bank,decode_stream
from src.psx_paired_layout import pack_variant_pair
from src.psx_compress import encode_stream
d=Path(__file__).parent;p=d/'paired';pairs=json.loads((p/'pairs.json').read_text());layouts=json.loads((d/'joint_layout.json').read_text());plan=json.loads((ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json').read_text())
arc=(ROOT/'out/ver_buki_riko/shibuki_idle_20261026T044150188556Z/modified.arc').read_bytes();entries=psx_arc(arc)
def entry(t):
 e=next(e for e in entries if int(e['type'],16)==t);return arc[e['offset']:e['offset']+e['size']]
parts,gfx=entry(3),entry(2);bank=graphics_bank(gfx,0,allow_bank_aliases=True)
for n in [3,27,29]:
 a=np.array(Image.open(p/f'run_{n:03d}.png'));b=np.array(Image.open(p/f'shoot_{n:03d}.png'));pair=next(q for q in plan['paired_frames'] if q['frames'][0]==n)
 writable=set(pair['common_base_tiles']+pair['nonshoot_only_tiles']+pair['shoot_only_tiles']);nr=len(composition_frame(parts,0,n)['parts']);ns=len(composition_frame(parts,0,n+1)['parts'])
 f=bank['frames'][n];dec=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128);budget=dec.end-dec.start
 pools=[cover(a!=0,nr,3),cover(b!=0,ns,3)];best=None;bestsize=100000
 for c in range(min(nr-1,ns-1,len(writable)-2),max(0,nr+ns-len(writable)-3),-1):
  for pool in pools:
   if not pool['fits'] or len(pool['rects'])<c:continue
   for rects in itertools.combinations(pool['rects'],c):
    mask=np.zeros(a.shape,bool)
    for x,y in rects:mask[y:y+16,x:x+16]=True
    shared=mask&(a==b)&(a!=0);ra=(a!=0)&~shared;rb=(b!=0)&~shared
    la=cover(ra,min(nr-c,len(writable)-c-1),.7)
    if not la['fits']:continue
    lb=cover(rb,min(ns-c,len(writable)-c-len(la['rects'])),.7)
    if not lb['fits']:continue
    try:raw,*_=pack_variant_pair(dec.data,f['tile_count'],a,b,rects,la['rects'],lb['rects'],writable)
    except ValueError:continue
    size=len(encode_stream(raw))
    if size<bestsize:
     bestsize=size;best={'frame':n,'fits':True,'mode':'variant','rects':list(rects),'run_rects':la['rects'],'shot_rects':lb['rects'],'initial_encoded_bytes':size}
     print(json.dumps({'frame':n,'best':size,'budget':budget,'common':c,'unique':[len(la['rects']),len(lb['rects'])]}),flush=True)
    if size<=budget:break
   if bestsize<=budget:break
  if bestsize<=budget:break
 if best:
  for i,l in enumerate(layouts):
   if l['frame']==n:layouts[i]=best
  for r in pairs['frames']:
   if r['run']==n:r['common_rects']=best['rects']
  (d/'joint_layout.json').write_text(json.dumps(layouts,indent=2));(p/'pairs.json').write_text(json.dumps(pairs,indent=2))
 print(json.dumps(best or {'frame':n,'fits':False}),flush=True)
