"""읽기 전용 입력으로 메모리에서 재배치안을 검증한다. 게임/ARC 출력은 쓰지 않는다."""
import json,sys,struct,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles
from src.psx_sprite_batch import canvas_from_parts,pack_original_layout
from src.psx_compress import encode_stream

d=Path(__file__).parent;a=d/'production09';art=json.loads((a/'art.json').read_text());parent=ROOT/art['parent'];arc=(parent/'modified.arc').read_bytes();manifest=json.loads((parent/'manifest.json').read_text())
assert hashlib.sha256(arc).hexdigest()==manifest['modified_archive_sha256']
es=psx_arc(arc);g,c=[arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t]
bank=graphics_bank(g,0,allow_bank_aliases=True);nc=bytearray(c);raw_targets={};encoded={};rows=[];selected=set(art['remaining_frames'])
assert selected==set(range(133,140))|set(range(204,208))
for q in art['groups']:
 n=q['frame'];assert q['aliases']==[n];f=bank['frames'][n];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128);r=json.loads((a/f'packing_{n:03}.json').read_text());v=np.array(Image.open(a/f'frame_{n:03}.png'));cp=composition_frame(c,0,n);w=set(q['writable'])
 assert not r.get('post_mapping') and not r.get('overlap_fill')
 if q['kind']=='original_grid':raw=pack_original_layout(old.data,f['tile_count'],v,cp,w)
 else:
  raw,parts,*_=pack_variant_pair(old.data,f['tile_count'],v,v,r['rects'],r['run_rects'],r['shot_rects'],w)
  assert hashlib.sha256(raw).hexdigest()==r['raw_sha256']
  mp={int(k):value for k,value in r['mapping'].items()};fl={int(k):value for k,value in r['flips'].items()};sh={int(k):value for k,value in r['shifts'].items()}
  raw=remap_tiles(raw,f['tile_count'],mp,fl,sh);records=[(mp[t],x-sh.get(t,[0,0])[0],y-sh.get(t,[0,0])[1],fl.get(t,0)) for t,x,y in parts]
  slots=q['part_slots'][str(n)];assert len(records)<=len(slots)
  for i,slot in enumerate(slots):
   p=cp['parts'][slot];t,x,y,flag=records[min(i,len(records)-1)];struct.pack_into('<BBbb',nc,p['record_offset'],(p['flags']&63)|flag,t,x-80,y-80)
 body=composition_frame(nc,0,n);body={**body,'parts':[p for p in body['parts'] if p['index'] in q['part_slots'][str(n)]]}
 assert np.array_equal(canvas_from_parts(raw,f['tile_count'],body),v),n
 before,_,_=indexed_atlas(old.data,f['tile_count']);after,_,_=indexed_atlas(raw,f['tile_count']);before=np.frombuffer(before,np.uint8).reshape(-1,256);after=np.frombuffer(after,np.uint8).reshape(-1,256)
 armor={p['tile'] for bi in range(5,9) for p in composition_frame(c,bi,n)['parts']};assert not w&armor
 for t in range(f['tile_count']):
  if t not in w:assert np.array_equal(before[t//16*16:t//16*16+16,t%16*16:t%16*16+16],after[t//16*16:t//16*16+16,t%16*16:t%16*16+16]),(n,t)
 for p in body['parts']:
  t=p['tile'];tile=after[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
  if not tile.any():continue
  assert not (t%16==0 and (p['flip_x'] or tile[:,0].any())),('U boundary',n)
  assert not (p['flip_y'] and t//16%16==0 and tile[0].any()),('V boundary',n)
 code=encode_stream(raw);assert len(code)==r['encoded_bytes'];assert decode_stream(code,0,len(code),len(raw)).data==raw
 raw_targets[n]=raw;encoded[f['offset']]=code;rows.append({'frame':n,'old_bytes':old.end-f['offset'],'new_bytes':len(code),'difference':len(code)-(old.end-f['offset'])})

unique={f['offset']:f for f in bank['frames']};table_size=len(bank['frames'])*4;cursor=bank['base']+table_size;ng=bytearray(g);locations={};changed_locations=0
for start,f in sorted(unique.items()):
 old=decode_stream(g,start,f['limit'],f['tile_count']*128);code=encoded.get(start,g[start:old.end]);locations[start]=cursor;assert cursor+len(code)<=bank['end'];ng[cursor:cursor+len(code)]=code;cursor+=len(code);changed_locations+=locations[start]!=start
for f in bank['frames']:
 struct.pack_into('<I',ng,bank['base']+f['index']*4,(f['tile_count']<<20)|(locations[f['offset']]-bank['base']))
assert len(ng)==len(g) and ng[:bank['base']]==g[:bank['base']] and ng[bank['end']:]==g[bank['end']:]
assert locations[bank['frames'][0]['offset']]==bank['base']+table_size
checked=0;changed=[]
for bi in range(len(bank_offsets(g,allow_aliases=True))):
 oldbank=graphics_bank(g,bi,allow_bank_aliases=True);newbank=graphics_bank(ng,bi,allow_bank_aliases=True)
 assert oldbank['base']==newbank['base'] and oldbank['end']==newbank['end']
 for oldf,newf in zip(oldbank['frames'],newbank['frames']):
  n=oldf['index'];assert oldf['tile_count']==newf['tile_count'];v0=decode_stream(g,oldf['offset'],oldf['limit'],oldf['tile_count']*128).data;v1=decode_stream(ng,newf['offset'],newf['limit'],newf['tile_count']*128).data
  expected=raw_targets[n] if bi==0 and n in raw_targets else v0;assert v1==expected,(bi,n)
  if v0!=v1:changed.append([bi,n])
  checked+=1
count=0
for bi,base in enumerate(bank_offsets(c)):
 for n in range(struct.unpack_from('<I',c,base)[0]>>16):
  if bi==0 and n in selected:continue
  assert composition_frame(c,bi,n)==composition_frame(nc,bi,n);count+=1
assert changed==[[0,n] for n in sorted(selected)]
report={'mode':'read_only_inputs_in_memory_simulation_no_game_output','parent_build':art['parent'],'parent_bin_sha256':manifest['modified_bin']['sha256'],'source_art':str(a.relative_to(ROOT)),'target_frames':sorted(selected),'streams':rows,'extra_compressed_bytes':sum(r['difference'] for r in rows),'bank0_original_slack':3866,'bank0_remaining_slack':bank['end']-cursor,'bank0_size':bank['end']-bank['base'],'bank0_unique_streams':len(unique),'streams_with_new_locations':changed_locations,'checked_graphics_references':checked,'checked_other_compositions':count,'decoded_changed_references':changed,'target_rasters_exact':True,'armor_tiles_preserved':True,'separate_effect_tiles_preserved':True,'palette_and_timing_untouched':True,'bank_boundaries_and_archive_length_unchanged':True,'unselected_bitmaps_exact':True,'new_gpu_boundaries':False,'runtime_verified':False,'approval_required_before_game_build':True,'game_file_written':False}
(d/'repack_dry_run.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))

# Art previews are allowed while the game-data write awaits approval.
from scripts.extract_zero import save_image
preview=d/'pending_preview';preview.mkdir(exist_ok=True);inv=json.loads((ROOT/art['source_inventory']).read_text());newbank=graphics_bank(ng,0,allow_bank_aliases=True);pictures={}
for aid in [2,39,95]:
 steps=[{'frame':0,'duration_ticks':29}]+inv['animations'][aid]['steps']+[{'frame':0,'duration_ticks':29}];pics=[];dur=[]
 for step in steps:
  n=step['frame']
  if n not in pictures:
   f=newbank['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;v=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,0,n))%16
   pictures[n]=save_image(v.tobytes(),(160,160),art['palette_words'],preview/f'frame_{n:03}.png').convert('RGBA')
  bg=Image.new('RGB',(160,160),'#253546');bg.paste(pictures[n],(0,0),pictures[n]);pics.append(bg.resize((480,480),Image.Resampling.NEAREST));dur.append(max(20,round((step['duration_ticks']+1)*1000/60)))
 pics[0].save(preview/f'animation_{aid:03}.gif',save_all=True,append_images=pics[1:],duration=dur,loop=0,disposal=2)
(preview/'NOTICE.txt').write_text('메모리 재배치안의 정적 미리보기. 실제 게임 실행 증거가 아니며 BIN/ARC 파일은 작성하지 않았다.\n',encoding='utf-8')
