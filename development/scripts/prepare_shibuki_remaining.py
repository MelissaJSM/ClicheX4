"""남은 기본 X 105참조를 원래 공간에 일괄 재삽입하고 모든 다른 참조를 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,inspect_references,load_project
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from src.psx_sprite_batch import canvas_from_parts,recolor_tiles,pack_original_layout,inherited_recolored_part
from src.psx_compress import replace_stream,encode_stream
from src.psx_bank_repack import repack_graphics_bank
from scripts.prepare_shibuki_remaining_plan import APPLIED,STUBS
FRAMES=set(range(237))-APPLIED-STUBS
STYLE_SCOPES={'base_special_style_7':{88,89,90,91,97,98,99},'base_arrival_victory_style_11':set(range(133,140))|set(range(204,208))}
STYLE_SCOPES['base_nana_arrival_17']=set(range(126,143))
STYLE_SCOPES['base_nana_victory_return_10']=set(range(156,162))|set(range(204,208))
STYLE_SCOPES['base_nana_special_7']={88,89,90,91,97,98,99}
STYLE_SCOPES['base_nana_special_remaining_9']={95,96,100,101,102,103,104,231,232}
STYLE_SCOPES['base_nana_air_clone_17']={93,94,*range(208,213),*range(221,231)}
STYLE_SCOPES['base_nana_vehicle_hurt_37']={*range(162,175),*range(184,204),*range(233,237)}
NANA_PARENTS={
 'base_nana_arrival_17':('6c792794979e4f4ceb15e1d6863efec0cae42b2b857a65c38cfb7fc2406d9556','04eb92e3a509ebf34d87ca58145ce48041da18d30d09525c605d10d6d25ff521'),
 'base_nana_victory_return_10':('fced8569fa4492f17d13db8b173bd706fd3f7208d8d141f804e0996e3a765547','30e4ee72fc00b3917b754687bb7e1c94d865bc7d583cbe5d70a5c0bc01b35879'),
 'base_nana_special_7':('6862abbe69cfca5800725d5346c6119123cf8c39705400e58478fa4960ee9d70','a225875d841e211d490b147779431af999315079fb30a8b4e9e6ed47f9b62c20'),
 'base_nana_special_remaining_9':('03ed2ae651fcf4ab54f97128b52fdd959dfb78994ba15d6e7e5d4c97824054f9','796238e5366d63d22228fb9995be563d8bebd3437855ae0bb65e5e1dbc2c09cb'),
 'base_nana_air_clone_17':('c29abbd84c29e5ab2a20b1b4869a167352c3e53cc02d01c9f0bd23dd2c60aa17','1521ce5112d92445c369867e7e62560868be2de32b275d80d00e8d6ff3360eb0'),
 'base_nana_vehicle_hurt_37':('423522ffc88e33fa1ab5c8f98e1eaa510bb8507babe7b0d8deb1f298b027b11b','4f82fba9883df2f209699620fa007f3f071c2072d150d717ab2c8e604f11edb2')}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--art',type=Path,required=True);parser.add_argument('--parent',type=Path,required=True);parser.add_argument('--scope',choices=['base_remaining_105',*STYLE_SCOPES],default='base_remaining_105');parser.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');parser.add_argument('--repack-bank',action='store_true',help='2026-10-27 approved arrival/victory bank0 compaction');args=parser.parse_args();d=args.art.resolve();parent=args.parent.resolve();project=args.project;character='nana'if project=='ver_rin_nana'else'shibuki'
 if (character=='nana')!=(args.scope in NANA_PARENTS):raise ValueError('Scope belongs to another character')
 if args.repack_bank and args.scope!='base_arrival_victory_style_11':raise ValueError('Bank repack is approved only for arrival/victory revision')
 frames=FRAMES if args.scope=='base_remaining_105' else STYLE_SCOPES[args.scope]
 if not d.is_relative_to(ROOT/'work'/project/(character+'_art')) or not parent.is_relative_to(ROOT/'out'/project):raise ValueError('Isolated inputs required')
 inspect_references(ROOT,load_project(ROOT,project));cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());pm=json.loads((parent/'manifest.json').read_text(encoding='utf-8'));arc=(parent/'modified.arc').read_bytes();art=json.loads((d/'art.json').read_text());inv=json.loads((ROOT/art['source_inventory']).read_text())
 if pm['task']!='x_'+character or sha256(arc)!=pm['modified_archive_sha256'] or inv['archive']['sha256']!=cfg['archive']['sha256']:raise ValueError('Unsupported parent/inventory')
 if character=='nana':
  from scripts.prepare_nana_idle_shot import PILOT
  from scripts.project import digest
  if art['task']!='x_nana' or art['scope']!=args.scope or (ROOT/art['parent']).resolve()!=parent:raise ValueError('Nana art identity mismatch')
  if (sha256(arc),pm['modified_bin']['sha256'])!=NANA_PARENTS[args.scope]:raise ValueError('Nana parent mismatch')
  if digest(PILOT/'nana_000_indexed.png')!=art['master_sha256'] or digest(PILOT/'palette.bin')!=art['palette_sha256']:raise ValueError('Approved Nana style changed')
 if args.repack_bank and (sha256(arc)!='5e79aec3d936db4975a8dc7953925b0e2bb8ef971db6dacc6db862c0d2e40e47' or pm['modified_bin']['sha256']!='9e03e1063c34a09672154f9a633954ce6397e6cb0a9c27ba72e9eca6060b5f2d' or (ROOT/art['parent']).resolve()!=parent):raise ValueError('Repack parent differs from approved build')
 if set(art['remaining_frames'])!=frames or {n for q in art['groups'] for n in q['aliases']}!=frames or len([n for q in art['groups'] for n in q['aliases']])!=len(frames):raise ValueError('Incomplete or overlapping groups')
 if args.scope=='base_special_style_7' and any(q['kind']!='body' or q['effect_tiles'] for q in art['groups']):raise ValueError('Style revision must preserve separate effects')
 if args.scope in ('base_nana_special_7','base_nana_special_remaining_9') and (art['effect_index_mapping']!=list(range(16)) or any(q['kind']!='body' or q['effect_tiles'] for q in art['groups'])):raise ValueError('Nana specials must preserve all attack effects')
 if args.scope=='base_nana_air_clone_17':
  effect_map=list(range(16))
  for old,new in ((5,13),(8,9),(12,7),(13,8)):effect_map[old]=new
  kinds={**{n:'body'for n in (93,94,208,209,210)},211:'effect',212:'effect',**{n:'pair'for n in (221,223,225,227,229)}}
  if art['effect_index_mapping']!=effect_map or {q['frame']:q['kind']for q in art['groups']}!=kinds or any(q['effect_tiles']for q in art['groups']):raise ValueError('Only clone disappearance colors may change')
 if args.scope=='base_nana_vehicle_hurt_37':
  kinds={**{n:'body'for n in(162,166,170,174,233,234,235,236)},**{n:'head'for n in(184,193,195,196,199)}}
  if art['effect_index_mapping']!=list(range(16))or {q['frame']:q['kind']for q in art['groups']}!=kinds or any(q['effect_tiles']for q in art['groups']):raise ValueError('Vehicle/hurt scope cannot recolor attack effects')
  q=next(q for q in art['groups']if q['frame']==196)
  if q['writable']!=[1]or q['part_slots']['198']!=[]:raise ValueError('Blank reference198 must be preserved')
 if args.scope=='base_arrival_victory_style_11' and (art['effect_index_mapping']!=list(range(16)) or any(q['kind'] not in ('body','original_grid') for q in art['groups'])):raise ValueError('Arrival/victory revision must preserve separate effect colors')
 if art['canvas_size']!=[160,160] or art['origin']!=[80,80]:raise ValueError('Unsupported scene coordinates')
 entries=psx_arc(arc)
 def entry(t):
  e=next(e for e in entries if int(e['type'],16)==t);return e,arc[e['offset']:e['offset']+e['size']]
 gm,gfx=entry(2);cm,parts=entry(3);_,palette=entry(9)
 if list(struct.unpack('<16H',palette[:32]))!=art['palette_words']:raise ValueError('Palette mismatch')
 bank=graphics_bank(gfx,0,allow_bank_aliases=True);ng=gfx;np_=bytearray(parts);allowed_records=set();reports=[];art_hashes={};desired={};whole_before={}
 replacements={};repack_report=None
 def raster(n):
  record=next(r for r in art['frames'] if r['frame']==n);path=(d/record['image']).resolve()
  if not path.is_relative_to(d):raise ValueError('Art escaped directory')
  im=Image.open(path);v=np.array(im);art_hashes[record['image']]=sha256(path.read_bytes())
  if im.mode!='P' or im.size!=(160,160) or v.max()>15:raise ValueError('Invalid indexed raster')
  return v
 for q in art['groups']:
  n=q['frame'];r=json.loads((d/f'packing_{n:03d}.json').read_text());art_hashes[f'packing_{n:03d}.json']=sha256((d/f'packing_{n:03d}.json').read_bytes())
  if r['frame']!=n or r['kind']!=q['kind'] or (not r['fits'] and not args.repack_bank):raise ValueError('Unfinished packing')
  desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);aliases=q['aliases'];w=set(q['writable']);fx=set(q['effect_tiles']);comps={k:composition_frame(parts,0,k) for k in aliases};base={p['tile'] for cp in comps.values() for p in cp['parts']};armor={p['tile'] for b in range(5,9) for k in aliases for p in composition_frame(parts,b,k)['parts']}
  if inv['stream_sharing'][str(desc['offset'])]!=[[0,k] for k in sorted(aliases)]:raise ValueError('Unexpected aliases')
  original_base={p['tile'] for k in aliases for p in inv['base_frames'][k]['composition']['parts']}
  spare=set(q.get('unreferenced_tiles',[]))
  if spare:
   if args.scope not in ('base_special_style_7','base_nana_special_7') or n!=97 or spare!={12,13}:raise ValueError('Unsupported spare tiles')
   for bi,off in enumerate(bank_offsets(parts)):
    count=struct.unpack_from('<I',parts,off)[0]>>16
    for k in aliases:
     if k<count and spare&{p['tile'] for p in composition_frame(parts,bi,k)['parts']}:raise ValueError('Spare tile is referenced')
  if not w<=base|original_base|spare or not fx<=base or (w|fx)&armor or w&fx:raise ValueError('Writable/armor/effect conflict')
  if r['budget']!=dec.end-desc['offset'] or q['budget']!=r['budget'] or q['tile_count']!=desc['tile_count']:raise ValueError('Stale stream budget')
  for k in aliases:
   slots=[p['index'] for p in comps[k]['parts'] if p['tile'] in w]
   if slots!=q['part_slots'][str(k)]:raise ValueError('Part slots changed')
  raw=dec.data
  if q['kind']=='effect':
   if fx or w!=base:raise ValueError('Incomplete effect selection')
   raw=recolor_tiles(raw,desc['tile_count'],w,art['effect_index_mapping'])
   if sha256(raw)!=r['raw_sha256']:raise ValueError('Effect packing source changed')
  elif q['kind']=='original_grid':
   if len(aliases)!=1 or fx:raise ValueError('Unsupported shared fixed layout')
   target=raster(n);raw=pack_original_layout(raw,desc['tile_count'],target,comps[n],w)
   if sha256(raw)!=r['raw_sha256']:raise ValueError('Fixed grid source changed')
   desired[n]=target
  else:
   if fx:raw=recolor_tiles(raw,desc['tile_count'],fx,art['effect_index_mapping'])
   target=raster(n);other=raster(n+1) if q['kind']=='pair' else target
   packed,rp,sp,blank,_=pack_variant_pair(raw,desc['tile_count'],target,other,r['rects'],r['run_rects'],r['shot_rects'],w)
   if sha256(packed)!=r['raw_sha256']:raise ValueError('Packing source changed')
   mapping={int(k):v for k,v in r['mapping'].items()};flips={int(k):v for k,v in r['flips'].items()};shifts={int(k):v for k,v in r['shifts'].items()}
   if set(mapping)!=w or set(mapping.values())!=w or not set(flips)<=w or not set(shifts)<=w:raise ValueError('Permutation escaped base tiles')
   raw=remap_tiles(packed,desc['tile_count'],mapping,flips,shifts)
   def remap(records):return [(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,x,y in records]
   for k in aliases:
    slots=q['part_slots'][str(k)]
    if not slots:continue
    records=remap(sp if q['kind']=='pair' and k==n+1 else rp);dx,dy=q['translations'][str(k)];records=[(t,x+dx,y+dy,flag) for t,x,y,flag in records]
    if not records or len(records)>len(slots):raise ValueError('Parts exceeded')
    for i,slot in enumerate(slots):
     p=comps[k]['parts'][slot];t,x,y,flag=records[min(i,len(records)-1)]
     if p['page'] or p['clut'] or p['unknown_flags'] or not -128<=x-80<=127 or not -128<=y-80<=127:raise ValueError('Unsupported composition')
     struct.pack_into('<BBbb',np_,p['record_offset'],(p['flags']&0x3f)|flag,t,x-80,y-80);allowed_records.update(range(p['record_offset'],p['record_offset']+4))
    cp=composition_frame(np_,0,k);cp={**cp,'parts':[p for p in cp['parts'] if p['index'] in slots]};want=raster(k)
    if not np.array_equal(canvas_from_parts(raw,desc['tile_count'],cp),want):raise ValueError(f'Body raster readback mismatch {k}')
    desired[k]=want
  if q['kind']!='effect':
   targets={k:desired[k] for k in aliases if k in desired}
   selected={k:[p for p in composition_frame(np_,0,k)['parts'] if p['index'] in q['part_slots'][str(k)]] for k in targets}
   assignments={k:[(p['tile'],p['x']+80,p['y']+80,p['flags']&192) for p in ps] for k,ps in selected.items()}
   raw=fill_redundant_pixels(raw,desc['tile_count'],assignments,targets,r.get('overlap_fill',[]),w)
   if r.get('post_mapping'):
    post={int(k):v for k,v in r['post_mapping'].items()};pf={int(k):v for k,v in r.get('post_flips',{}).items()};psh={int(k):v for k,v in r.get('post_shifts',{}).items()}
    if set(post)!=w or set(post.values())!=w or not set(pf)<=w or not set(psh)<=w:raise ValueError('Post permutation escaped base tiles')
    raw=remap_tiles(raw,desc['tile_count'],post,pf,psh)
    for k,ps in selected.items():
     for p in ps:
      t=p['tile'];dx,dy=psh.get(t,[0,0]);x=p['x']+dx if p['flip_x'] else p['x']-dx;y=p['y']+dy if p['flip_y'] else p['y']-dy
      if not -128<=x<=127 or not -128<=y<=127:raise ValueError('Post coordinates overflow')
      struct.pack_into('<BBbb',np_,p['record_offset'],p['flags']^pf.get(t,0),post[t],x,y);allowed_records.update(range(p['record_offset'],p['record_offset']+4))
   atlas,_,_=indexed_atlas(raw,desc['tile_count'])
   for k,want in targets.items():
    cp=composition_frame(np_,0,k);cp={**cp,'parts':[p for p in cp['parts'] if p['index'] in q['part_slots'][str(k)]]}
    for p in cp['parts']:
     t=p['tile'];rows=[atlas[(t//16*16+y)*256+t%16*16:(t//16*16+y)*256+t%16*16+16] for y in range(16)]
     if not any(any(row) for row in rows):continue
     unsafe=(t%16==0 and (p['flip_x'] or any(row[0] for row in rows))) or (p['flip_y'] and t//16%16==0 and any(rows[0]))
     if unsafe:
      old_atlas,_,_=indexed_atlas(dec.data,desc['tile_count']);old_rows=[old_atlas[(t//16*16+y)*256+t%16*16:(t//16*16+y)*256+t%16*16+16] for y in range(16)]
      inherited=q['kind']=='original_grid' and inherited_recolored_part(b''.join(old_rows),b''.join(rows),comps[k]['parts'][p['index']],p)
      if not inherited:raise ValueError(f'New GPU boundary {k}')
    if not np.array_equal(canvas_from_parts(raw,desc['tile_count'],cp),want):raise ValueError(f'Final raster readback mismatch {k}')
  old,_,_=indexed_atlas(dec.data,desc['tile_count']);new,_,_=indexed_atlas(raw,desc['tile_count'])
  for t in range(desc['tile_count']):
   if t in w|fx:continue
   x,y=t%16*16,t//16*16
   if any(old[(y+j)*256+x:(y+j)*256+x+16]!=new[(y+j)*256+x:(y+j)*256+x+16] for j in range(16)):raise ValueError('Unselected/armor tile changed')
  if args.repack_bank:
   code=encode_stream(raw)
   for k in aliases:replacements[k]=code
   report={'start':desc['offset'],'encoded_bytes':len(code),'old_encoded_bytes':dec.end-desc['offset'],'bank_repack':True}
  else:ng,report=replace_stream(ng,desc,raw)
  if report['encoded_bytes']!=r['encoded_bytes']:raise ValueError('Compression prediction differs')
  report.update(frame=n,aliases=aliases,kind=q['kind'],writable=sorted(w),effect_color_tiles=sorted(fx),armor_tiles=sorted(armor),raster_exact=q['kind']!='effect');reports.append(report)
 if args.repack_bank:ng,repack_report=repack_graphics_bank(gfx,0,replacements)
 changed_parts=[i for i,(x,y) in enumerate(zip(parts,np_)) if x!=y]
 if not set(changed_parts)<=allowed_records:raise ValueError('Unexpected part write')
 checked=0
 for bi,base in enumerate(bank_offsets(parts)):
  count=struct.unpack_from('<I',parts,base)[0]>>16
  for n in range(count):
   if bi==0 and n in frames:continue
   if composition_frame(parts,bi,n)!=composition_frame(np_,bi,n):raise ValueError('Other composition changed')
   checked+=1
 refs=0;changed=[]
 for bi in range(len(inv['graphics_banks'])):
  rebuilt=graphics_bank(ng,bi,allow_bank_aliases=True)
  for f in graphics_bank(gfx,bi,allow_bank_aliases=True)['frames']:
   nf=rebuilt['frames'][f['index']]
   if nf['tile_count']!=f['tile_count']:raise ValueError('Tile count changed')
   refs+=1;x=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;y=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
   if x!=y:
    if bi!=0 or f['index'] not in frames:raise ValueError('Other bitmap changed')
    changed.append([bi,f['index']])
 if {n for bi,n in changed}!=frames:raise ValueError('Missing edited stream reference')
 patched=bytearray(arc);patched[gm['offset']:gm['offset']+gm['size']]=ng;patched[cm['offset']:cm['offset']+cm['size']]=np_
 allowed=[(gm['offset']+r['start'],gm['offset']+r['start']+r['encoded_bytes']) for r in reports]+[(cm['offset']+i,cm['offset']+i+1) for i in changed_parts]
 palette_rows={}
 if args.scope=='base_nana_special_7':
  from scripts.prepare_shibuki_weapon_palette import edited_palette
  pm_meta,_=entry(9);newpal,palette_rows=edited_palette(palette)
  patched[pm_meta['offset']:pm_meta['offset']+pm_meta['size']]=newpal
  allowed.extend((pm_meta['offset']+int(row)*32,pm_meta['offset']+(int(row)+1)*32)for row in palette_rows)
 if args.repack_bank:allowed=[(gm['offset']+bank['base'],gm['offset']+bank['end'])]+[(cm['offset']+i,cm['offset']+i+1) for i in changed_parts]
 if len(patched)!=len(arc) or any(x!=y and not any(lo<=i<hi for lo,hi in allowed) for i,(x,y) in enumerate(zip(arc,patched))):raise ValueError('Unexpected ARC write')
 group={'base_remaining_105':'shibuki_remaining','base_special_style_7':'shibuki_special_style','base_arrival_victory_style_11':'shibuki_arrival_victory_style','base_nana_arrival_17':'nana_arrival','base_nana_victory_return_10':'nana_victory','base_nana_special_7':'nana_special','base_nana_special_remaining_9':'nana_special_remaining','base_nana_air_clone_17':'nana_air_clone','base_nana_vehicle_hurt_37':'nana_vehicle_hurt'}[args.scope]
 out=new_run(ROOT,project,group);(out/'modified.arc').write_bytes(patched)
 recipe={'task':'x_shibuki','scope':'base_remaining_105','parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(patched),'arc_size':len(patched),'source_art':str(d.relative_to(ROOT)),'art_manifest_sha256':sha256((d/'art.json').read_bytes()),'art_hashes':art_hashes,'compression':reports,'changed_composition_bytes':changed_parts,'changed_bitmap_references':changed,'checked_bitmap_references':refs,'checked_other_compositions':checked,'armor_tiles_preserved':True,'accepted123_frames_preserved':True,'remaining105_references_applied':True,'body_targets_exact':sorted(desired),'blank_reference198_preserved':True,'placeholder9_references_preserved':sorted(STUBS),'idle_frames_preserved':True,'run_frames_preserved':True,'palette_preserved':True,'timing_changed':False,'resources_relocated':False,'runtime_verified':False,'runtime_deferred_by_user':False,'shooting_body_uses_same_run_pose':True,'shooting_arm_art_pending':False}
 recipe.update(scope=args.scope,remaining105_references_applied=args.scope=='base_remaining_105',special_style7_references_applied=args.scope=='base_special_style_7',edited_frame_references=sorted(frames))
 if character=='nana':
  from scripts.extract_zero import save_image
  import shutil
  frame_hashes={};canvases={}
  for n in sorted(frames|{0,142}):
   f=bank['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;canvas=canvas_from_parts(raw,f['tile_count'],composition_frame(np_,0,n));canvases[n]=canvas
   if n in frames:
    path=out/f'frame_{n:03d}.png';save_image(canvas.tobytes(),(160,160),art['palette_words'],path);frame_hashes[str(n)]=digest(path)
  if not np.array_equal(canvases[142],canvases[0]):raise ValueError('Arrival endpoint differs from accepted idle')
  shutil.copyfile(d/'body_review.png',out/'body_review.png')
  recipe.update(task='x_nana',master_sha256=art['master_sha256'],palette_sha256=art['palette_sha256'],frame_sha256=frame_hashes,idle_palette_preserved=True,standing_frames_preserved=True,air_frames_preserved=True,dash_frames_preserved=True,wall_frames_preserved=True,hurt_frames_preserved=True,ladder_frames_preserved=True,low_hp_frames_preserved=True,other_compositions_preserved=True,other_decoded_bitmaps_preserved=True,arrival_endpoint_equals_idle=True,effect_shapes_preserved_for_pure_effects=True,effect_palette_mapping=art['effect_index_mapping'],shooting_body_uses_same_run_pose=False)
  if args.scope=='base_nana_victory_return_10':recipe.update(arrival_frames_preserved=True,accepted140_frames_preserved=True,special98_frames_preserved=True)
  if args.scope=='base_nana_special_7':recipe.update(arrival_frames_preserved=True,victory_return_frames_preserved=True,accepted150_frames_preserved=True,separate_effect_tiles_preserved=True,effect_and_armor_palette_rows_preserved=True,body_palette_rows=palette_rows,palette_preserved=False,unreferenced_tiles_reused={'97':[12,13]},all_composition_banks_checked_for_spares=True)
  if args.scope=='base_nana_special_remaining_9':recipe.update(arrival_frames_preserved=True,victory_return_frames_preserved=True,accepted157_frames_preserved=True,charge_cyclone_frames_preserved=True,separate_effect_tiles_preserved=True,effect_and_armor_palette_rows_preserved=True)
  if args.scope=='base_nana_air_clone_17':recipe.update(arrival_frames_preserved=True,victory_return_frames_preserved=True,accepted166_frames_preserved=True,charge_cyclone_frames_preserved=True,frost_fire_frames_preserved=True,separate_attack_effects_preserved=True,clone_disappearance_changed=True,armor_costumes_unchanged=True,nova_strike_preserved=True,reused_accepted_frames=art['reused_accepted_frames'])
  if args.scope=='base_nana_vehicle_hurt_37':
   if np.any(canvases[198])or composition_frame(parts,0,198)!=composition_frame(np_,0,198):raise ValueError('Blank198 display changed')
   recipe.update(arrival_frames_preserved=True,victory_return_frames_preserved=True,existing183_frames_preserved=True,charge_cyclone_frames_preserved=True,frost_fire_frames_preserved=True,extra_air_clone_frames_preserved=True,separate_attack_effects_preserved=True,armor_costumes_unchanged=True,nova_strike_preserved=True,blank198_display_preserved=True)
 if args.scope=='base_special_style_7':recipe.update(unreferenced_tiles_reused={'97':[12,13]},all_composition_banks_checked_for_spares=True,base_remaining_art_inherited=True,unedited_X_actions_recolored=False,shooting_body_uses_same_run_pose=False)
 if args.scope=='base_arrival_victory_style_11':recipe.update(arrival_victory11_references_applied=True,base_remaining_art_inherited=True,unedited_X_actions_recolored=False,shooting_body_uses_same_run_pose=False,separate_effect_tiles_preserved=True)
 if args.repack_bank:recipe.update(resources_relocated=True,resources_relocated_within_bank=True,repack=repack_report,archive_size_and_lba_preserved=True,approval={'date':'2026-10-27','user_quote':'진행 부탁할게','scope':'arrival/victory11, bank0 internal compaction, unchanged ARC size/LBA/EXE/logic'})
 write_json(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'arc_sha256':sha256(patched),'streams':len(reports),'new_refs':len(changed),'body_targets_exact':len(desired)}))
if __name__=='__main__':main()
