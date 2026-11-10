"""사다리14참조의 반전·사격 공유 그림을 원래 스트림에 삽입한다."""
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
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from src.psx_paired_layout import pack_variant_pair

GROUPS={143:[143],144:[144,145],146:[146,147],149:[148,149,150],151:[151,152],153:[153],154:[154],155:[155],183:[183]}
MIRRORS={144:(145,-16),146:(147,-15),149:(148,-15),151:(152,-15)}
FRAMES={f for values in GROUPS.values() for f in values}

def mirror_canvas(target,delta):
 out=np.zeros_like(target);yy,xx=np.nonzero(target);nx=111+delta-xx
 if len(nx) and (nx.min()<0 or nx.max()>=96):raise ValueError('Mirror outside canvas')
 out[yy,nx]=target[yy,xx];return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--art',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');args=p.parse_args();d=args.art.resolve();parent=args.parent.resolve();project=args.project;character='nana' if project=='ver_rin_nana' else 'shibuki'
 if not d.is_relative_to(ROOT/'work'/project/(character+'_art')) or not parent.is_relative_to(ROOT/'out'/project):raise ValueError('Isolated inputs required')
 inspect_references(ROOT,load_project(ROOT,project));pm=json.loads((parent/'manifest.json').read_text(encoding='utf-8'));arc=(parent/'modified.arc').read_bytes()
 if pm['task']!='x_'+character or sha256(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent ARC mismatch')
 cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());art=json.loads((d/'art.json').read_text());packing=json.loads((d/'packing.json').read_text());inv=json.loads((ROOT/art['source_inventory']).read_text())
 if {r['frame'] for r in art['frames']}!=set(GROUPS)|{150} or {r['frame'] for r in packing}!=set(GROUPS) or len(packing)!=9 or not all(r['fits'] for r in packing):raise ValueError('Incomplete ladder art')
 entries=psx_arc(arc)
 def entry(t):
  e=next(e for e in entries if int(e['type'],16)==t);return e,arc[e['offset']:e['offset']+e['size']]
 gm,gfx=entry(2);cm,parts=entry(3);_,pal=entry(9)
 if list(struct.unpack('<16H',pal[:32]))!=art['palette_words']:raise ValueError('Palette mismatch')
 bank=graphics_bank(gfx,0,allow_bank_aliases=True);ng=gfx;np_=bytearray(parts);allowed_records=set();reports=[];hashes={}
 def raster(n):
  r=next(q for q in art['frames'] if q['frame']==n);path=(d/r['image']).resolve()
  if not path.is_relative_to(d):raise ValueError('Raster escaped art directory')
  im=Image.open(path);a=np.array(im)
  if im.mode!='P' or im.size!=(96,80) or a.max()>15:raise ValueError('Invalid indexed image')
  hashes[r['image']]=sha256(path.read_bytes());return a
 for r in packing:
  n=r['frame'];desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
  if inv['stream_sharing'][str(desc['offset'])]!=[[0,k] for k in GROUPS[n]]:raise ValueError('Unexpected stream sharing')
  writable={q['tile'] for k in GROUPS[n] for q in composition_frame(parts,0,k)['parts']};armor={q['tile'] for b in range(5,9) for k in GROUPS[n] for q in composition_frame(parts,b,k)['parts']}
  if writable&armor or writable!=set(r['writable']):raise ValueError('Writable/armor conflict')
  a=raster(n);b=raster(150) if n==149 else a
  raw,rp,sp,blank,_=pack_variant_pair(dec.data,desc['tile_count'],a,b,r['rects'],r.get('run_rects',[]),r.get('shot_rects',[]),writable)
  if sha256(raw)!=r['raw_sha256']:raise ValueError('Packing source changed')
  mapping={int(k):v for k,v in r['mapping'].items()};flips={int(k):v for k,v in r['flips'].items()};shifts={int(k):v for k,v in r['shifts'].items()}
  if set(mapping)!=writable or set(mapping.values())!=writable or not set(flips)<=writable or not set(shifts)<=writable:raise ValueError('Storage permutation escaped body tiles')
  raw=remap_tiles(raw,desc['tile_count'],mapping,flips,shifts)
  def remap(rows):return [(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,x,y in rows]
  assignments={n:remap(rp)};targets={n:a}
  if n==149:assignments[150]=remap(sp);targets[150]=b
  if n in MIRRORS:
   alias,delta=MIRRORS[n];original=composition_frame(parts,0,n)['parts'];other=composition_frame(parts,0,alias)['parts']
   if [(q['tile'],q['flags']^64,-q['x']+delta,q['y']) for q in original]!=[(q['tile'],q['flags'],q['x'],q['y']) for q in other]:raise ValueError('Mirror relationship changed')
   assignments[alias]=[(t,96+delta-x,y,flag^64) for t,x,y,flag in assignments[n]];targets[alias]=mirror_canvas(a,delta)
  raw=fill_redundant_pixels(raw,desc['tile_count'],assignments,targets,r.get('overlap_fill',[]),writable)
  if r.get('post_mapping'):
   post={int(k):v for k,v in r['post_mapping'].items()};pf={int(k):v for k,v in r.get('post_flips',{}).items()}
   if set(post)!=writable or set(post.values())!=writable:raise ValueError('Post mapping escaped body tiles')
   raw=remap_tiles(raw,desc['tile_count'],post,pf)
   assignments={k:[(post[t],x,y,flag^pf.get(t,0)) for t,x,y,flag in rows] for k,rows in assignments.items()}
   if blank is not None:mapping[blank]=post[mapping[blank]]
  atlas,_,_=indexed_atlas(raw,desc['tile_count'])
  for k,rows in assignments.items():
   comp=composition_frame(parts,0,k)
   if len(rows)>len(comp['parts']):raise ValueError('Too many parts')
   for j,q in enumerate(comp['parts']):
    if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported flags')
    if j<len(rows):t,x,y,flag=rows[j]
    else:
     if blank is None:raise ValueError('No blank spare part')
     t,x,y,flag=mapping[blank],48,40,0
    tx,ty=t%16*16,t//16*16;tile=[atlas[(ty+i)*256+tx:(ty+i)*256+tx+16] for i in range(16)]
    if any(any(v) for v in tile):
     if t%16==0 and (flag&64 or any(v[0] for v in tile)):raise ValueError('GPU U boundary')
     if flag&128 and t//16%16==0 and any(tile[0]):raise ValueError('GPU V boundary')
    struct.pack_into('<BBbb',np_,q['record_offset'],flag,t,x-48,y-40);allowed_records.update(range(q['record_offset'],q['record_offset']+4))
   if not np.array_equal(world_canvas(raw,desc['tile_count'],composition_frame(np_,0,k)),targets[k]):raise ValueError('Raster readback mismatch')
  old,_,_=indexed_atlas(dec.data,desc['tile_count'])
  for t in range(desc['tile_count']):
   if t in writable:continue
   x,y=t%16*16,t//16*16
   if any(old[(y+j)*256+x:(y+j)*256+x+16]!=atlas[(y+j)*256+x:(y+j)*256+x+16] for j in range(16)):raise ValueError('Unselected tile changed')
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
 out=new_run(ROOT,project,character+'_ladder');(out/'modified.arc').write_bytes(patched)
 recipe={'task':'x_shibuki','scope':'base_ladder_14','parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(patched),'arc_size':len(patched),'source_art':str(d.relative_to(ROOT)),'art_manifest_sha256':sha256((d/'art.json').read_bytes()),'packing_manifest_sha256':sha256((d/'packing.json').read_bytes()),'art_hashes':hashes,'compression':reports,'changed_composition_bytes':changed_parts,'changed_bitmap_references':changed,'checked_bitmap_references':refs,'checked_other_compositions':checked,'armor_tiles_preserved':True,'idle_frames_preserved':True,'run_frames_preserved':True,'air_frames_preserved':True,'dash_frames_preserved':True,'wall_frames_preserved':True,'hurt_frames_preserved':True,'idle_palette_preserved':True,'timing_changed':False,'resources_relocated':False,'runtime_verified':False,'shooting_body_uses_same_run_pose':False,'shooting_arm_art_pending':False}
 recipe['task']='x_'+character
 if character=='nana':
  from scripts.prepare_nana_idle_shot import PILOT
  from scripts.project import digest
  from scripts.extract_zero import save_image
  import shutil
  if digest(PILOT/'nana_000_indexed.png')!=art['master_sha256'] or digest(PILOT/'palette.bin')!=art['palette_sha256']:raise ValueError('Approved Nana style changed')
  frame_hashes={}
  for n in sorted(FRAMES):
   f=bank['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;canvas=world_canvas(raw,f['tile_count'],composition_frame(np_,0,n));path=out/f'frame_{n:03d}.png';save_image(canvas.tobytes(),(96,80),art['palette_words'],path);frame_hashes[str(n)]=digest(path)
  shutil.copyfile(d/'family_3x.png',out/'family_3x.png')
  recipe.update(master_sha256=art['master_sha256'],palette_sha256=art['palette_sha256'],frame_sha256=frame_hashes,standing_frames_preserved=True,other_compositions_preserved=True,other_decoded_bitmaps_preserved=True)
 write_json(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'arc_sha256':sha256(patched),'compression':reports}))
if __name__=='__main__':main()
