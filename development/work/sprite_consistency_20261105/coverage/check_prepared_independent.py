"""두 담당자가 준비한 국소 교정의 실제 자원·조립·픽셀을 독립적으로 검사."""
import importlib.util,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('cov',ROOT/'scripts/audit_sprite_consistency_coverage.py');cov=importlib.util.module_from_spec(s);s.loader.exec_module(cov)
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,bank_offsets
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static
OUT=Path(__file__).resolve().parent

def es(arc):return {t:cov.unique_entry(arc,t)for t in(2,3,9)}
def records(c,b,n):return [(p['flags'],p['tile'],p['x'],p['y'])for p in composition_frame(c,b,n)['parts']]
def all_nonentries(before,after,allowed):
 a,b=cov.psx_arc(before),cov.psx_arc(after)
 assert [(e['type'],e['offset'],e['size'])for e in a]==[(e['type'],e['offset'],e['size'])for e in b]
 for e in a:
  if int(e['type'],16)not in allowed:assert before[e['offset']:e['offset']+e['size']]==after[e['offset']:e['offset']+e['size']]

def raw(es,b,n):
 f=graphics_bank(es[2],b,allow_bank_aliases=True)['frames'][n]
 return decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data,f

def layer(es,b,cb,n):
 packed,f=raw(es,b,n);comp=composition_frame(es[3],cb,n)
 if b==0 and cb in(5,6,7,8):comp=local_composition(comp)
 arr=np.zeros((384,384),np.uint8)
 if comp['parts']:
  pix,size,bb,_=compose_indices(packed,f['tile_count'],comp,allowed_cluts={0,1,2,3})
  arr[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])
 return arr

def composite(layers,pal,mask,arm):
 out=np.zeros((384,384),np.uint32)
 for bit,b in[(0,0),(8,8),(1,5),(4,7),(2,6)]:
  if bit and not mask&bit:continue
  a=layers[b];base=0 if b==0 else 32 if b==7 and arm==2 else 16
  colors=np.array(pal[base:],np.uint32)+1
  out[a>0]=colors[a[a>0]]
 return out

def ui_layer(menu,tex,b,n):
 cp=aliased_composition(menu,b,n);out=np.zeros((384,384),np.uint8)
 if cp['parts']:
  px,size,bb,_=compose_static(tex,local_composition(cp));out[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
 return out

def ui_equipment(menu,tex,mask,arm):
 out=np.zeros((384,384),np.uint32);paloff=struct.unpack_from('<I',menu,4)[0]
 for bit,n in[(0,44),(1,45),(2,46),(4,47),(8,48)]:
  if bit and not mask&bit:continue
  cp=aliased_composition(menu,2,n)
  for p in cp['parts']:
   colors=np.array(struct.unpack_from('<16H',menu,paloff+((10 if bit==4 and arm==2 else 8)+p['clut'])*32),np.uint32)+1
   px,size,bb,_=compose_static(tex,local_composition({**cp,'parts':[p]}));a=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);region=out[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]];region[a>0]=colors[a[a>0]]
 return out

def nana():
 p=ROOT/'work/sprite_consistency_20261105/x/nana_parts_fix/proposal.json';q=json.loads(p.read_text('utf8'))
 source=ROOT/q['baseline'];assert cov.file_sha(source)==q['baseline_sha256']
 old,_=cov.read_assets(source,[*q['files'],'SLUS_005.61']);new={n:(ROOT/v['path']).read_bytes()for n,v in q['files'].items()}
 for n,r in q['files'].items():assert cov.sha(old[n])==r['before']and cov.sha(new[n])==r['after']and len(new[n])==len(old[n])==r['size']
 a,b=es(old['PL00_U.ARC']),es(new['PL00_U.ARC']);all_nonentries(old['PL00_U.ARC'],new['PL00_U.ARC'],{2,3})
 assert bank_offsets(a[2],allow_aliases=True)==bank_offsets(b[2],allow_aliases=True)and bank_offsets(a[3])==bank_offsets(b[3])
 refs={r['ref']:r for r in q['game_checks']['transfers']};expected_refs={0,85,86,87,92,115,116,117,118,119};assert set(refs)==expected_refs
 changed=[];total=0
 for gb in range(len(bank_offsets(a[2],allow_aliases=True))):
  for f in graphics_bank(a[2],gb,allow_bank_aliases=True)['frames']:
   n=f['index'];x,xf=raw(a,gb,n);y,yf=raw(b,gb,n);assert xf['tile_count']==yf['tile_count'];total+=1
   if x!=y:changed.append([gb,n]);assert gb==0 and n in refs
 for cb in range(len(bank_offsets(a[3]))):
  for n in range(composition_frame(a[3],cb,0)['bank_frame_count']):
   aa,bb=records(a[3],cb,n),records(b[3],cb,n)
   if cb==5 and n in refs:
    pts=refs[n]['points_world'];assert bb==aa+[(0,16,min(x for x,y in pts),min(y for x,y in pts))]
   else:assert aa==bb
 masks=0;pal=struct.unpack_from('<64H',a[9]);assert a[9]==b[9]
 for n in sorted(refs):
  points=refs[n]['points_world'];oldlayers={cb:layer(a,0,cb,n)for cb in(0,5,6,7,8)};newlayers={cb:layer(b,0,cb,n)for cb in(0,5,6,7,8)}
  for cb in oldlayers:
   want=oldlayers[cb].copy()
   if cb in(5,8):
    for x,y in points:want[y+160,x+160]=1 if cb==5 else 0
   assert np.array_equal(want,newlayers[cb])
  for arm in(1,2):
   for mask in range(16):
    before=composite(oldlayers,pal,mask,arm);after=composite(newlayers,pal,mask,arm);wanted=before.copy()
    for x,y in points:
     if mask&1:wanted[y+160,x+160]=int(pal[17])+1
     elif mask&8:wanted[y+160,x+160]=0
    assert np.array_equal(after,wanted)
    if mask in(0,15):assert np.array_equal(before,after)
    masks+=1
 menu0,menu1=old['MOJIPAT.ARC'],new['MOJIPAT.ARC'];all_nonentries(old['LOAD_U.ARC'],new['LOAD_U.ARC'],{0x10008})
 tex0=cov.unique_entry(old['LOAD_U.ARC'],0x10008);tex1=cov.unique_entry(new['LOAD_U.ARC'],0x10008)
 offsets=bank_offsets(menu0);assert offsets==bank_offsets(menu1)and menu0[:offsets[2]]==menu1[:offsets[2]]and menu0[offsets[3]:]==menu1[offsets[3]:]
 checks=0;points=[(11,-14),(11,-13)]
 for cb in(0,2,3):
  for n in range(aliased_composition(menu0,cb,0)['bank_frame_count']):
   before=ui_layer(menu0,tex0,cb,n);after=ui_layer(menu1,tex1,cb,n);want=before.copy()
   if cb==2 and n in(45,48):
    for x,y in points:want[y+160,x+160]=1 if n==45 else 0
   assert np.array_equal(want,after);checks+=1
 used=set()
 for cb in(0,2,3):
  for n in range(aliased_composition(menu0,cb,0)['bank_frame_count']):
   used|={p['page']*256+p['tile']for p in aliased_composition(menu0,cb,n)['parts']}
 assert 255 not in used
 direct={y*16+x for y in range(13,16)for x in range(13)}
 exe=old['SLUS_005.61'];assert cov.sha(exe)=='1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab'
 for row in range(9):
  x,y,t,w,h,clut=struct.unpack_from('<hhBBBB',exe,0xDED04+row*8)
  starts=exe[0xDED04+72:0xDED04+84]if row==6 else[t]
  direct|={start+dy*16+dx for start in starts for dy in range(h)for dx in range(w)}
 changedtiles=[t for t in range(256)if tile_pixels(tex0,t)!=tile_pixels(tex1,t)]
 assert changedtiles==[196,255]and not set(changedtiles)&direct
 smasks=0;po=struct.unpack_from('<I',menu0,4)[0];color=struct.unpack_from('<H',menu0,po+9*32+2)[0]+1
 for arm in(1,2):
  for mask in range(16):
   before=ui_equipment(menu0,tex0,mask,arm);after=ui_equipment(menu1,tex1,mask,arm);want=before.copy()
   for x,y in points:
    if mask&1:want[y+160,x+160]=color
    elif mask&8:want[y+160,x+160]=0
   assert np.array_equal(want,after);smasks+=1
 return dict(passed=True,resource_hashes={n:cov.sha(v)for n,v in new.items()},all_decoded_refs=total,changed_raw_refs=changed,
  selected_equipment_checks=masks,unselected_graphics_and_compositions_exact=True,base_and_full_exact=True,
  ui_all_composed_frames=checks,save_equipment_checks=smasks,direct_UV_and_other_tiles_preserved=True,changed_ui_tiles=changedtiles,
  source_black_palette_sound_animation_exact=True,actual_gameplay_tested=False)

def riko():
 d=ROOT/'work/sprite_consistency_20261105/zero/riko/wall_fix/prepared_v1';q=json.loads((d/'proposal.json').read_text('utf8'))
 path=ROOT/q['source_bin'];assert cov.file_sha(path)==q['source_sha256']
 old=cov.read_assets(path,['PL01_U.ARC'])[0]['PL01_U.ARC'];new=(ROOT/q['resource']).read_bytes()
 assert cov.sha(old)==q['source_arc_sha256']and cov.sha(new)==q['after_sha256']
 a,b=es(old),es(new);all_nonentries(old,new,{2});assert a[3]==b[3]and a[9]==b[9]
 assert bank_offsets(a[2])==bank_offsets(b[2]);heads=np.asarray(Image.open(ROOT/q['head_file']));assert cov.file_sha(ROOT/q['head_file'])==q['head_sha256']
 rows={r['id']:r for r in q['frames']};checks=0;changes=[]
 assert set(rows)=={f'b0_{n:03}'for n in range(38,44)}|{f'b1_{n:03}'for n in[50,51,53,54,56,57,59,61,63,65]}
 binding=ROOT/'work/sprite_consistency_20261105/zero/riko/wall_fix/binding'
 for gb in(0,1):
  cb=0 if gb==0 else 5
  for f in graphics_bank(a[2],gb)['frames']:
   n=f['index'];oa,_=raw(a,gb,n);na,nf=raw(b,gb,n);assert nf['tile_count']==f['tile_count']<=32
   if gb==1 and n in range(42,50):assert oa==na;continue
   before=layer(a,gb,cb,n);after=layer(b,gb,cb,n);key=f'b{gb}_{n:03}'
   if key in rows:
    owned=np.asarray(Image.open(binding/f'{key}_head_mask.png'))>0;protected=(before>0)&~owned
    target=before.copy();target[owned]=0;x,y=rows[key]['new_head_anchor'];nh=np.zeros_like(before);nh[160+y:160+y+heads.shape[0],160+x:160+x+heads.shape[1]]=heads
    visible=(nh>0)&~protected;target[visible]=nh[visible]
    assert np.array_equal(target,after)and np.array_equal(after[protected],before[protected]);changes.append([gb,n,int((before!=after).sum())])
   else:assert np.array_equal(before,after)
   checks+=1
 return dict(passed=True,resource_sha256=cov.sha(new),all_graphics_decoded=444,display_checks=checks,head_changed_refs=changes,
  source_limbs_body_opaque_preserved=True,original_composition_palette_sound_static_effects_exact=True,
  original_partial42_49_raw_exact=True,max_tiles_unchanged_at_most32=True,actual_gameplay_tested=False)

report={'nana_parts':nana(),'riko_wall':riko(),'scope':'Prepared-resource independent readback only; no active files/emu input/writes.',
 'game_or_art_original_modified':False}
cov.write(OUT/'prepared_independent.json',report)
print(json.dumps({'nana':report['nana_parts']['passed'],'riko':report['riko_wall']['passed']}))
