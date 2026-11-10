"""Independent output reader: no Shibuki production/packing/verification imports."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent;H=D.parent/'shibuki_audit';P=H/'air_pack_probe01';T=H/'air_targets_probe02'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
oldpath=H/'prepared_arrival_victory01/PL00_U.ARC';newpath=P/'candidate_PL00_U.ARC';old=oldpath.read_bytes();new=newpath.read_bytes()
assert sha(old)=='78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e'
assert sha(new)=='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be'
lock=json.loads((T/'LOCK.json').read_text('utf8'));manifest=json.loads((T/'targets.json').read_text('utf8'))
assert sha((T/'targets.json').read_bytes())==lock['target_manifest_sha256'] and lock['source_parent_sha256']==manifest['parent_sha256']==sha(old)
for name,h in lock['files'].items():assert sha((T/name).read_bytes())==h
a,b=Archive(old),Archive(new);PBS=(0,5,6,7,8);refs=set(range(33,55));reserved={105,*range(175,183)};count=collections.Counter();targets={};gpu=[];tile_changes=[]
assert replace_entry(replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(aa,bb)in enumerate(zip(a.banks,b.banks)):
 assert len(aa['frames'])==len(bb['frames'])
 for f,q in zip(aa['frames'],bb['frames']):
  n=f['index'];assert n==q['index'];x=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);y=decode_stream(b.g,q['offset'],q['limit'],q['tile_count']*128);assert x.serialize()==a.g[x.start:x.end]and y.serialize()==b.g[y.start:y.end];count['raw_checked']+=1
  if gb==0 and n in refs:
   assert q['tile_count']==32
   if f['tile_count']!=q['tile_count']:tile_changes.append({'ref':n,'before':f['tile_count'],'after':q['tile_count']})
  else:assert x.data==y.data and f['tile_count']==q['tile_count'];count['non_target_raw_exact']+=1
for n in range(33,55,2):assert b.banks[0]['frames'][n]['offset']==b.banks[0]['frames'][n+1]['offset'];count['original_pair_shared_streams']+=1
for n in range(237):
 if n in reserved:continue
 for pb in PBS:
  v=b.layer(n,pb)[0];count['layers_checked']+=1
  if n in refs:
   want=np.array(Image.open(T/f'{n:03}_bank{pb}_indices.png'));assert want.dtype==np.uint8 and want.shape==(384,384)and want.max()<16;assert np.array_equal(v,want);targets[n,pb]=want;count['target_layers_exact']+=1
  else:assert np.array_equal(v,a.layer(n,pb)[0]);count['non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  x,y=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n);sem=lambda q:[(p['flags'],p['tile'],p['x'],p['y'])for p in q['parts']]
  if pb in PBS and n in refs:
   f=b.banks[0]['frames'][n];raw=decode_stream(b.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
   for p in y['parts']:
    t=p['tile'];assert t<32;tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    assert t%16!=0 or not tile[:,0].any();assert not p['flip_y']or not tile[0].any();count['gpu_parts_checked']+=1
  else:assert sem(x)==sem(y);count['non_target_compositions_exact']+=1
def color(v,words):
 table=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i%16==0 else 255]for i,w in enumerate(words)],np.uint8);return table[v]
def combine(layers,mask,arm):
 z=color(layers[0],b.words)
 for bit,pb in[(8,8),(1,5),(4,7),(2,6)]:
  if mask&bit:
   q=color(layers[pb],b.words[(32 if pb==7 and arm==2 else 16):]);m=q[:,:,3]>0;z[m]=q[m]
 return z
# Recreate canonical original muzzle/casing from actual parent34, excluding old clothing.
master=a.layer(34)[0];yy,xx=np.indices(master.shape);ry,rx=np.where(master==4);mx=int(rx.min());my=int(ry[rx==mx].min());region=(xx>=mx-1)&(xx<=mx+9)&(yy>=my-2)&(yy<=my+4)
pix=region&(np.isin(master,[2,5,8,14,15])|((master==4)&(xx==mx)));gun=np.where(pix,master,0);guard=np.zeros_like(pix)
for y in np.flatnonzero(pix.any(1)):cols=np.flatnonzero(pix[y]);guard[y,mx-1:cols.max()+1]=True
guards={};casing_diffs=[];guardmeta=json.loads((H/'air_barrel_guard02/guard.json').read_text('utf8'));assert guardmeta['source_arc_sha256']==sha(old)
for n in range(34,55,2):
 oldlayer=a.layer(n)[0];ry,rx=np.where(oldlayer==4);x=int(rx.min());y=int(ry[rx==x].min());dx,dy=x-mx,y-my;g=np.roll(gun,(dy,dx),(0,1));m=np.roll(guard,(dy,dx),(0,1));assert np.array_equal(g,np.array(Image.open(H/f'air_barrel_guard02/{n:03}_indices.png')));assert np.array_equal(m,np.array(Image.open(H/f'air_barrel_guard02/{n:03}_mask.png'))>0)
 row=next(q for q in guardmeta['rows']if q['shot_ref']==n);d=m&(oldlayer!=g);diff=[[int(x)-160,int(y)-160,int(oldlayer[y,x]),int(g[y,x])]for y,x in zip(*np.where(d))];assert diff==row['existing_source_casing_diff_pixels'];casing_diffs.append({'ref':n,'source34_casing_vs_current_clothing_pixels':len(diff)});guards[n]=(g,m)
for n in sorted(refs):
 layers={pb:targets[n,pb]for pb in PBS}
 for mask in range(16):
  for arm in(1,2):
   actual=np.array(b.composite(n,mask,arm)[0]);expected=combine(layers,mask,arm);assert np.array_equal(actual,expected);count['partial_RGBA_conditions']+=1
   if n in guards:
    g,m=guards[n];assert np.array_equal(actual[m],color(g,b.words)[m]);count['canonical_original_casing_RGBA_conditions']+=1
 for name,mask in [('base',0),('fourth',15)]:assert np.array_equal(np.array(Image.open(P/'readback'/f'{name}_{n:03}.png')),np.array(b.composite(n,mask)[0]));count['actual_readback_PNGs_exact']+=1
assert count['raw_checked']==508 and count['non_target_raw_exact']==486 and count['target_layers_exact']==110 and count['non_target_layers_exact']==1030
assert count['partial_RGBA_conditions']==704 and count['canonical_original_casing_RGBA_conditions']==352 and count['actual_readback_PNGs_exact']==44
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
result={'passed':True,'scope':'시부키 기본·포스 공중22참조 작업 ARC의 독립 읽기 검사. 제작·정합·패킹 함수를 호출하지 않았다.','source_arc':rel(oldpath),'source_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),'targets_lock':rel(T/'LOCK.json'),'targets_lock_sha256':sha((T/'LOCK.json').read_bytes()),'counts':dict(count),'native_tile_count_changes':tile_changes,'canonical_casing_source34_reconstruction':True,'casing_vs_current_old_clothing':casing_diffs,'all_audio_palette_static_other_entries_exact':True,'bank_boundaries_exact':True,'original_reserved_data_exact':True,'actual_MIPS_test_performed_here':False,'gameplay_runtime_verified':False,'source_files_unchanged':True,'producer_functions_called':False,'visual_review_pending':True}
out=D/'shibuki_air22_independent.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(count),'casing_diffs':casing_diffs}))
