"""정지 버스터 85/86/87/92만 같은 크기 ARC에 재삽입한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,inspect_references,load_project
from scripts.discover_inputs import psx_arc,sha256
from scripts.prepare_shibuki_run import world_canvas
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas,bank_offsets
from src.psx_compress import replace_stream
from src.psx_tile_layout import pack_rectangles,remap_tiles

FRAMES={85,86,87,92}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--art',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);args=p.parse_args()
 d=args.art.resolve();parent=args.parent.resolve()
 if not d.is_relative_to(ROOT/'work/ver_buki_riko/shibuki_art') or not parent.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated inputs required')
 inspect_references(ROOT,load_project(ROOT,'ver_buki_riko'))
 pm=json.loads((parent/'manifest.json').read_text(encoding='utf-8'));arc=(parent/'modified.arc').read_bytes()
 if pm['task']!='x_shibuki' or sha256(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent ARC mismatch')
 cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());art=json.loads((d/'art.json').read_text());packing=json.loads((d/'packing.json').read_text())
 if {r['frame'] for r in art['frames']}!=FRAMES or {r['frame'] for r in packing}!=FRAMES or len(packing)!=4 or not all(r['fits'] for r in packing):raise ValueError('Incomplete standing art')
 inv=json.loads((ROOT/art['source_inventory']).read_text());entries=psx_arc(arc)
 def entry(t):
  e=next(e for e in entries if int(e['type'],16)==t);return e,arc[e['offset']:e['offset']+e['size']]
 gm,gfx=entry(2);cm,parts=entry(3);_,palette=entry(9)
 if list(struct.unpack('<16H',palette[:32]))!=art['palette_words']:raise ValueError('Palette mismatch')
 bank=graphics_bank(gfx,0,allow_bank_aliases=True);ng=gfx;np_=bytearray(parts);allowed_records=set();reports=[];art_hashes={}
 for r in packing:
  n=r['frame'];desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);comp=composition_frame(parts,0,n)
  if inv['stream_sharing'][str(desc['offset'])]!=[[0,n]]:raise ValueError('Unexpected stream sharing')
  writable={q['tile'] for q in comp['parts']}
  armor={q['tile'] for b in range(5,9) for q in composition_frame(parts,b,n)['parts']}
  if writable&armor or writable!=set(r['writable']):raise ValueError('Writable/armor conflict')
  ar=next(q for q in art['frames'] if q['frame']==n);path=(d/ar['image']).resolve()
  if not path.is_relative_to(d):raise ValueError('Raster escaped art directory')
  im=Image.open(path);target=np.array(im);art_hashes[ar['image']]=sha256(path.read_bytes())
  if im.mode!='P' or im.size!=(96,80) or target.max()>15:raise ValueError('Invalid indexed image')
  raw=pack_rectangles(dec.data,desc['tile_count'],im.tobytes(),im.size,r['rects'],r['tiles'],writable)
  if sha256(raw)!=r['raw_sha256']:raise ValueError('Packing source changed')
  mapping={int(k):v for k,v in r['mapping'].items()};flips={int(k):v for k,v in r['flips'].items()};shifts={int(k):v for k,v in r['shifts'].items()}
  if set(mapping)!=writable:raise ValueError('Tile permutation escaped base set')
  raw=remap_tiles(raw,desc['tile_count'],mapping,flips,shifts)
  records=[(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,(x,y) in zip(r['tiles'],r['rects'])]
  spare=sorted(writable-set(r['tiles']))
  if len(records)>len(comp['parts']) or (len(records)<len(comp['parts']) and not spare):raise ValueError('No room/blank part')
  for i,q in enumerate(comp['parts']):
   if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported part flags')
   t,x,y,flags=records[i] if i<len(records) else (mapping[spare[0]],48,40,0)
   struct.pack_into('<BBbb',np_,q['record_offset'],flags,t,x-48,y-40);allowed_records.update(range(q['record_offset'],q['record_offset']+4))
  if not np.array_equal(world_canvas(raw,desc['tile_count'],composition_frame(np_,0,n)),target):raise ValueError('Raster readback mismatch')
  old,_,_=indexed_atlas(dec.data,desc['tile_count']);new,_,_=indexed_atlas(raw,desc['tile_count'])
  for t in range(desc['tile_count']):
   if t in writable:continue
   x,y=t%16*16,t//16*16
   if any(old[(y+j)*256+x:(y+j)*256+x+16]!=new[(y+j)*256+x:(y+j)*256+x+16] for j in range(16)):raise ValueError('Unselected tile changed')
  ng,report=replace_stream(ng,desc,raw);report.update(frame=n,armor_tiles=sorted(armor),raster_exact=True);reports.append(report)
 changed_parts=[i for i,(a,b) in enumerate(zip(parts,np_)) if a!=b]
 if not set(changed_parts)<=allowed_records:raise ValueError('Part mutation escaped records')
 checked=0
 for bi,base in enumerate(bank_offsets(parts)):
  count=struct.unpack_from('<I',parts,base)[0]>>16
  for n in range(count):
   if bi==0 and n in FRAMES:continue
   if composition_frame(parts,bi,n)!=composition_frame(np_,bi,n):raise ValueError('Other composition changed')
   checked+=1
 changed=[];refs=0
 for bi in range(len(inv['graphics_banks'])):
  for f in graphics_bank(gfx,bi,allow_bank_aliases=True)['frames']:
   refs+=1;a=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;b=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
   if a!=b:
    if bi!=0 or f['index'] not in FRAMES:raise ValueError('Other bitmap changed')
    changed.append([bi,f['index']])
 if {n for bi,n in changed}!=FRAMES:raise ValueError('Missing edited frame')
 patched=bytearray(arc);patched[gm['offset']:gm['offset']+gm['size']]=ng;patched[cm['offset']:cm['offset']+cm['size']]=np_
 allowed=[(gm['offset']+r['start'],gm['offset']+r['start']+r['encoded_bytes']) for r in reports]+[(cm['offset']+i,cm['offset']+i+1) for i in changed_parts]
 if len(patched)!=len(arc) or any(a!=b and not any(lo<=i<hi for lo,hi in allowed) for i,(a,b) in enumerate(zip(arc,patched))):raise ValueError('Unexpected archive mutation')
 out=new_run(ROOT,'ver_buki_riko','shibuki_standing');(out/'modified.arc').write_bytes(patched)
 recipe={'task':'x_shibuki','scope':'base_standing_buster_4','parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(patched),'arc_size':len(patched),'source_art':str(d.relative_to(ROOT)),'art_manifest_sha256':sha256((d/'art.json').read_bytes()),'packing_manifest_sha256':sha256((d/'packing.json').read_bytes()),'art_hashes':art_hashes,'compression':reports,'changed_composition_bytes':changed_parts,'changed_bitmap_references':changed,'checked_bitmap_references':refs,'checked_other_compositions':checked,'armor_tiles_preserved':True,'idle_frames_preserved':True,'run_frames_preserved':True,'idle_palette_preserved':True,'timing_changed':False,'resources_relocated':False,'runtime_verified':False,'shooting_body_uses_same_run_pose':False,'shooting_arm_art_pending':False}
 write_json(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'arc_sha256':sha256(patched),'compression':reports}))

if __name__=='__main__':main()
