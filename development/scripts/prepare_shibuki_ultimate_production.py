"""Replace every selected Ultimate overlay; preserve pre-capsule Shibuki."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_paired_layout import pack_variant_pair
import scripts.prepare_shibuki_armor_remaining as remaining
import scripts.prepare_shibuki_armor_motion as motion

PILOT={0,115,116,117,118,119};PLACEHOLDERS={105,*range(175,183)}
original_fit=motion.fit

def fast_fit(mask,count):
 y,x=np.nonzero(mask)
 if not len(x):return []
 best=None
 for dy in range(16):
  for dx in range(16):
   cells=sorted(set(zip(((x-dx)//16).tolist(),((y-dy)//16).tolist())))
   rr=[[max(0,min(mask.shape[1]-16,tx*16+dx)),max(0,min(mask.shape[0]-16,ty*16+dy))] for tx,ty in cells]
   if len(rr)<=count and (best is None or len(rr)<len(best)):best=rr
 if best is not None:return best
 return original_fit(mask,count)

remaining.fit=motion.fit=fast_fit

def pack_shared(raw,count,images,pool,limits):
 unique=[];indices=[]
 for a in images:
  k=next((j for j,v in enumerate(unique) if np.array_equal(a,v)),None)
  if k is None:k=len(unique);unique.append(a)
  indices.append(k)
 if len(unique)==2:
  a,b=unique;la,lb=[min(limits[i] for i,k in enumerate(indices) if k==j) for j in range(2)]
  common=(a==b)&(a>0);ra=np.where(common,0,a).astype(np.uint8);rb=np.where(common,0,b).astype(np.uint8)
  for k in range(1,min(la,lb)):
   cr=fast_fit(common,k)
   if cr is None:continue
   ar=fast_fit(ra>0,la-len(cr));br=fast_fit(rb>0,lb-len(cr))
   if ar is None or br is None or len(cr)+len(ar)+len(br)>len(pool):continue
   try:
    new,aa,bb,_,_=pack_variant_pair(raw,count,a,b,cr,ar,br,pool)
    return new,[[(t,x,y,0) for t,x,y in (aa,bb)[j]] for j in indices]
   except ValueError:pass
 return pack_many(raw,count,images,pool,limits)

def records(c,bi,n):
 return b''.join(c[q['record_offset']:q['record_offset']+4] for q in composition_frame(c,bi,n)['parts'])

def repack_parts(c,bi,replacements):
 starts=bank_offsets(c);start=starts[bi];end=starts[bi+1] if bi+1<len(starts) else len(c)
 count=composition_frame(c,bi,0)['bank_frame_count'];rr=[replacements.get(n,records(c,bi,n)) for n in range(count)]
 packed=bytearray(rr[0]);positions={0:0}
 for n in sorted(range(1,count),key=lambda n:(-len(rr[n]),n)):
  v=rr[n];pos=next((i for i in range(0,len(packed)-len(v)+1,4) if packed[i:i+len(v)]==v),None)
  if pos is None:
   overlap=next((i for i in range(min(len(packed),len(v)),0,-4) if packed[-i:]==v[:i]),0)
   pos=len(packed)-overlap;packed+=v[overlap:]
  positions[n]=pos
 if count*4+len(packed)>end-start:raise ValueError(f'Parts bank {bi} exceeds capacity by {count*4+len(packed)-(end-start)}')
 out=bytearray(c);out[start+count*4:start+count*4+len(packed)]=packed
 for n in range(count):struct.pack_into('<I',out,start+n*4,((count+positions[n]//4)<<16)|len(rr[n])//4)
 for n in range(count):
  if records(out,bi,n)!=rr[n]:raise ValueError('Parts readback mismatch')
 return bytes(out),end-start-count*4-len(packed)

def main(art,out,audit=False):
 art=art.resolve();out=out.resolve()
 if not art.is_relative_to(D) or not out.is_relative_to(D) or out.exists():raise ValueError('Fresh isolated paths required')
 arc=(D/'base_fix02/PL02_U.ARC').read_bytes();meta=json.loads((art/'art.json').read_text())
 if sha256(arc)!=meta['source_arc_sha256'] or sha256(arc)!='2ea5ed73ec35549f571591008748c45dc31598d02128089a966073a5ff8650ef':raise ValueError('Wrong parent')
 g,c,pal=[entry(arc,k) for k in (2,3,9)];bank=graphics_bank(g,0,allow_bank_aliases=True)
 targets={n:np.array(Image.open(art/f'overlay_{n:03}.png')) for n in meta['frames']}
 if set(targets)!=set(range(237))-PILOT-PLACEHOLDERS:raise ValueError('Incomplete production scope')
 groups={};replacement={};parts={0:{},5:{}};reports=[];failures=[]
 for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
 for offset,refs in groups.items():
  if not set(refs)&set(targets):continue
  if set(refs)-set(targets):raise ValueError('Scope does not contain shared group')
  f=bank['frames'][refs[0]];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
  keep={q['tile'] for n in refs for bi in (0,6,7,8) for q in composition_frame(c,bi,n)['parts']}
  if set(refs)<=set(range(217,231)):
   # These states require armor. Their old X base is redundant under the new body.
   blank=composition_frame(c,6,refs[0])['parts'][0]['tile']
   if any(composition_frame(c,6,n)['parts'][0]['tile']!=blank for n in refs):raise ValueError('Blank alias differs')
   for n in refs:
    parts[0][n]=struct.pack('<BBbb',0,blank,-8,-8)*len(composition_frame(c,0,n)['parts'])
   keep={q['tile'] for n in refs for bi in (6,7,8) for q in composition_frame(c,bi,n)['parts']}
  pool=set(range(f['tile_count']))-keep
  try:
   images=[targets[n] for n in refs];limits=[len(composition_frame(c,5,n)['parts']) for n in refs]
   # Empty armor references retain their exact original geometry and tiles.
   if not any(np.any(a) for a in images):
    for n in refs:
     if np.any(canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,5,n)))):raise ValueError('Unexpected opaque original armor')
    reports.append({'refs':refs,'mode':'original_transparent'});continue
   nr,assignments=pack_shared(raw,f['tile_count'],images,pool,limits)
   for n,assignment,limit in zip(refs,assignments,limits):
    if not assignment or len(assignment)>limit:raise ValueError('Part budget exceeded')
    padded=assignment+[assignment[-1]]*(limit-len(assignment))
    parts[5][n]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80) for t,x,y,flag in padded)
    replacement[n]=nr
   reports.append({'refs':refs,'mode':'new_overlay','tile_capacity':len(pool),'parts':[len(a) for a in assignments],'encoded_bytes':len(encode_stream(nr))})
  except ValueError as e:
   failures.append({'refs':refs,'error':str(e)});print(json.dumps(failures[-1]),flush=True)
   if not audit:raise
 out.mkdir()
 if failures:
  (out/'audit.json').write_text(json.dumps({'failures':failures,'reports':reports},indent=2));return
 nc=c;slack={}
 for bi,updates in parts.items():
  if updates:nc,slack[bi]=repack_parts(nc,bi,updates)
 ng,repack=repack_graphics_bank(g,0,{n:encode_stream(v) for n,v in replacement.items()})
 nb=graphics_bank(ng,0,allow_bank_aliases=True);checked=base_exact=overlay_exact=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  f=nb['frames'][n];nr=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
  old=bank['frames'][n];raw=decode_stream(g,old['offset'],old['limit'],old['tile_count']*128).data
  for bi in (0,5,6,7,8):
   shape=targets[n].shape if n in targets else (160,160)
   size=(shape[1],shape[0])
   a=canvas_from_parts(nr,f['tile_count'],local_composition(composition_frame(nc,bi,n)),size=size)
   if bi==5 and n in targets:expected=targets[n];overlay_exact+=1
   elif bi==0 and 217<=n<=230:expected=np.zeros(shape,np.uint8)
   else:
    expected=canvas_from_parts(raw,old['tile_count'],local_composition(composition_frame(c,bi,n)),size=size)
    if bi==0:base_exact+=1
   if not np.array_equal(a,expected):raise ValueError(f'Final pixels differ: frame {n}, layer {bi}')
   checked+=1
 for bi in range(1,len(bank_offsets(g,allow_aliases=True))):
  if graphics_bank(ng,bi,allow_bank_aliases=True)!=graphics_bank(g,bi,allow_bank_aliases=True):raise ValueError('Other graphics metadata changed')
 if entry(arc,9)!=pal:raise ValueError('Palette changed')
 result=replace_entry(replace_entry(arc,2,ng),3,nc)
 if len(result)!=len(arc):raise ValueError('Archive size changed')
 (out/'PL02_U.ARC').write_bytes(result)
 recipe={'kind':'ultimate_production_overlay_fix','source_arc_sha256':sha256(arc),'modified_arc_sha256':sha256(result),'art':str(art.relative_to(ROOT)),'art_sha256':sha256((art/'art.json').read_bytes()),'edited_frames':sorted(targets),'base_frames_exact':base_exact,'overlays_exact':overlay_exact,'checked_layers':checked,'parts_slack':slack,'graphics_repack':repack,'groups':reports,'runtime_verified':False,'full_ultimate_complete':False,'timing_logic_preserved':True}
 (out/'recipe.json').write_text(json.dumps(recipe,indent=2));print(json.dumps({k:v for k,v in recipe.items() if k not in ('groups','graphics_repack','edited_frames')}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--audit',action='store_true');a=p.parse_args();main(a.art,a.output,a.audit)
