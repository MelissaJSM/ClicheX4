"""X 체력 부족 대기120..125를 교체하며 입 오버레이와 아머를 분리한다."""
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

FRAMES=set(range(120,126))
GROUPS={120:[120,121],122:[122,123],124:[124,125]}
PRIMARY=set(GROUPS)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--art',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');args=p.parse_args();project=args.project;character='nana' if project=='ver_rin_nana' else 'shibuki'
 d=args.art.resolve();parent=args.parent.resolve()
 if not d.is_relative_to(ROOT/'work'/project/(character+'_art')) or not parent.is_relative_to(ROOT/'out'/project):raise ValueError('Isolated inputs required')
 inspect_references(ROOT,load_project(ROOT,project))
 pm=json.loads((parent/'manifest.json').read_text(encoding='utf-8'));arc=(parent/'modified.arc').read_bytes()
 if pm['task']!='x_'+character or sha256(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent ARC mismatch')
 cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());art=json.loads((d/'art.json').read_text());packing=json.loads((d/'packing.json').read_text())
 if {r['frame'] for r in art['frames']}!=FRAMES or {r['frame'] for r in packing}!=PRIMARY or len(packing)!=3 or not all(r['fits'] for r in packing):raise ValueError('Incomplete low HP art')
 inv=json.loads((ROOT/art['source_inventory']).read_text());entries=psx_arc(arc)
 def entry(t):
  e=next(e for e in entries if int(e['type'],16)==t);return e,arc[e['offset']:e['offset']+e['size']]
 gm,gfx=entry(2);cm,parts=entry(3);_,palette=entry(9)
 if list(struct.unpack('<16H',palette[:32]))!=art['palette_words']:raise ValueError('Palette mismatch')
 bank=graphics_bank(gfx,0,allow_bank_aliases=True);ng=gfx;np_=bytearray(parts);allowed_records=set();reports=[];art_hashes={}
 for r in packing:
  n=r['frame'];desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);comp=composition_frame(parts,0,n)
  if inv['stream_sharing'][str(desc['offset'])]!=[[0,k] for k in GROUPS[n]]:raise ValueError('Unexpected stream sharing')
  writable={q['tile'] for q in comp['parts']}
  armor={q['tile'] for b in range(5,9) for alias in GROUPS[n] for q in composition_frame(parts,b,alias)['parts']}
  if writable&armor or writable!=set(r['writable']):raise ValueError('Writable/armor conflict')
  ar=next(q for q in art['frames'] if q['frame']==n);path=(d/ar['image']).resolve()
  if not path.is_relative_to(d):raise ValueError('Raster escaped art directory')
  im=Image.open(path);target=np.array(im);art_hashes[ar['image']]=sha256(path.read_bytes())
  if im.mode!='P' or im.size!=(96,80) or target.max()>15:raise ValueError('Invalid indexed image')
  raw=pack_rectangles(dec.data,desc['tile_count'],im.tobytes(),im.size,r['rects'],r['tiles'],writable)
  if sha256(raw)!=r['raw_sha256']:raise ValueError('Packing source changed')
  mapping={int(k):v for k,v in r['mapping'].items()};flips={int(k):v for k,v in r['flips'].items()};shifts={int(k):v for k,v in r['shifts'].items()}
  if set(mapping)!=writable or set(mapping.values())!=writable or not set(flips)<=writable or not set(shifts)<=writable:raise ValueError('Tile permutation escaped base set')
  raw=remap_tiles(raw,desc['tile_count'],mapping,flips,shifts)
  records=[(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,(x,y) in zip(r['tiles'],r['rects'])]
  spare=sorted(writable-set(r['tiles']))
  if len(records)>len(comp['parts']) or (len(records)<len(comp['parts']) and not spare):raise ValueError('No room/blank part')
  for i,q in enumerate(comp['parts']):
   expected_clut=0
   if q['page'] or q['clut']!=expected_clut or q['unknown_flags']:raise ValueError('Unsupported part flags')
   t,x,y,flags=records[i] if i<len(records) else (mapping[spare[0]],48,40,0)
   struct.pack_into('<BBbb',np_,q['record_offset'],(q['flags']&0x3f)|flags,t,x-48,y-40);allowed_records.update(range(q['record_offset'],q['record_offset']+4))
  if not np.array_equal(world_canvas(raw,desc['tile_count'],composition_frame(np_,0,n),allowed_cluts={0,2})%16,target):raise ValueError('Raster readback mismatch')
  final_atlas,_,_=indexed_atlas(raw,desc['tile_count'])
  for tile,x,y,flag in records:
   tx,ty=tile%16*16,tile//16*16
   if tile%16==0 and (flag&64 or any(final_atlas[(ty+j)*256+tx] for j in range(16))):raise ValueError('GPU U boundary')
   if flag&128 and tile//16%16==0 and any(final_atlas[ty*256+tx:ty*256+tx+16]):raise ValueError('GPU V boundary')
  alias=n+1;ac=composition_frame(parts,0,alias);primary_signature=lambda q:(q['flags'],q['tile'],q['x'],q['y']);old_body=comp['parts'];body=[q for q in ac['parts'] if q['tile']!=7];mouth=[q for q in ac['parts'] if q['tile']==7]
  if list(map(primary_signature,old_body))!=list(map(primary_signature,body)) or len(mouth)!=1 or 7 in armor:raise ValueError('Mouth overlay structure changed')
  for old,new in zip(body,composition_frame(np_,0,n)['parts']):
   off=old['record_offset'];np_[off:off+4]=np_[new['record_offset']:new['record_offset']+4];allowed_records.update(range(off,off+4))
  ar=next(q for q in art['frames'] if q['frame']==alias);ap=(d/ar['image']).resolve()
  if not ap.is_relative_to(d):raise ValueError('Alias image escaped art directory')
  im=Image.open(ap);opened=np.array(im)
  if im.mode!='P' or im.size!=(96,80) or opened.max()>15:raise ValueError('Invalid mouth image')
  art_hashes[ar['image']]=sha256(ap.read_bytes());yy,xx=np.nonzero(opened!=target)
  if not len(xx) or np.any(opened[yy,xx]==0) or np.any(target[yy,xx]==0):raise ValueError('Mouth overlay changed silhouette')
  left,top=int(xx.min())-2,int(yy.min())-2
  if xx.max()-left>=16 or yy.max()-top>=16:raise ValueError('Mouth patch exceeds tile')
  overlay=np.zeros_like(target);overlay[yy,xx]=opened[yy,xx];raw=pack_rectangles(raw,desc['tile_count'],overlay.tobytes(),(96,80),[[left,top]],[7],{7});q=mouth[0]
  if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported mouth flags')
  struct.pack_into('<BBbb',np_,q['record_offset'],0,7,left-48,top-40);allowed_records.update(range(q['record_offset'],q['record_offset']+4))
  if not np.array_equal(world_canvas(raw,desc['tile_count'],composition_frame(np_,0,alias)),opened):raise ValueError('Mouth readback mismatch')
  if not np.array_equal(world_canvas(raw,desc['tile_count'],composition_frame(np_,0,n)),target):raise ValueError('Mouth changed base body')
  writable=writable|{7}
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
 out=new_run(ROOT,project,character+'_low_hp');(out/'modified.arc').write_bytes(patched)
 recipe={'task':'x_shibuki','scope':'base_low_hp_6','parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(patched),'arc_size':len(patched),'source_art':str(d.relative_to(ROOT)),'art_manifest_sha256':sha256((d/'art.json').read_bytes()),'packing_manifest_sha256':sha256((d/'packing.json').read_bytes()),'art_hashes':art_hashes,'compression':reports,'changed_composition_bytes':changed_parts,'changed_bitmap_references':changed,'checked_bitmap_references':refs,'checked_other_compositions':checked,'armor_tiles_preserved':True,'idle_frames_preserved':True,'run_frames_preserved':True,'air_frames_preserved':True,'dash_frames_preserved':True,'wall_frames_preserved':True,'hurt_frames_preserved':True,'ladder_frames_preserved':True,'mouth_overlay_verified':True,'idle_palette_preserved':True,'timing_changed':False,'resources_relocated':False,'runtime_verified':False,'shooting_body_uses_same_run_pose':False,'shooting_arm_art_pending':False}
 recipe['task']='x_'+character
 if character=='nana':
  from scripts.prepare_nana_idle_shot import PILOT
  from scripts.project import digest
  from scripts.extract_zero import save_image
  import shutil
  if digest(PILOT/'nana_000_indexed.png')!=art['master_sha256'] or digest(PILOT/'palette.bin')!=art['palette_sha256']:raise ValueError('Approved Nana style changed')
  frame_hashes={};canvases={}
  for n in sorted(FRAMES):
   f=bank['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;canvas=world_canvas(raw,f['tile_count'],composition_frame(np_,0,n));canvases[n]=canvas;path=out/f'frame_{n:03d}.png';save_image(canvas.tobytes(),(96,80),art['palette_words'],path);frame_hashes[str(n)]=digest(path)
  if any(not np.array_equal(v[58:],canvases[120][58:])for v in canvases.values()):raise ValueError('Feet drift between low HP frames')
  for name in ('body_review.png','breathing_preview.gif'):shutil.copyfile(d/name,out/name)
  recipe.update(master_sha256=art['master_sha256'],palette_sha256=art['palette_sha256'],frame_sha256=frame_hashes,standing_frames_preserved=True,other_compositions_preserved=True,other_decoded_bitmaps_preserved=True,ground_contact_preserved=True)
 write_json(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'arc_sha256':sha256(patched),'compression':reports}))

if __name__=='__main__':main()
