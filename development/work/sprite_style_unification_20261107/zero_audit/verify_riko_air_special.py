"""Independent readback of four new Riko clothing poses; no producer imports."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
W=ROOT/'work/sprite_style_unification_20261107';D=Path(__file__).parent;R=W/'riko'
OUT=D/'riko_air_special_independent';OUT.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
P=R/'prepared_burst_final_v1/PL01_U.ARC';Q=R/'prepared_air_special_v1/PL01_U.ARC'
old=P.read_bytes();new=Q.read_bytes()
assert sha(old)=='e871006eed3473bfe6716fc676fb0e4d638c62846de545186dd0de0f6a17e7fc'
assert sha(new)=='4e751c0e13d6f68bbb02f285493fee75c263c7cc995a96615332935c358e7615'
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
assert replace_entry(replace_entry(new,2,g),3,c)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
assert bank_offsets(c)==bank_offsets(nc)
ART=R/'air_special_cloth04/registered01';reg=json.loads((ART/'registration.json').read_text('utf8'))
assert reg['source_sha256']==sha(old)
source=ART.parent/'generated.png';assert sha(source.read_bytes())==reg['generated_sha256']
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(p>>s&31)*255//31 for s in(0,5,10)]for p in pal])
sample=np.array(Image.open(source).convert('RGBA').resize((192,64),Image.Resampling.NEAREST))
labels=1+np.sum((sample[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2,axis=3).argmin(2).astype(np.uint8)
labels[sample[:,:,3]<128]=0
master={};masks={};contacts={};source_proof=[]
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
wallmeta=json.loads((ROOT/'work/sprite_consistency_20261105/zero/riko/wall_fix/reproduced_v1/proposal.json').read_text('utf8'))
wall=np.array(Image.open(ROOT/wallmeta['head_file']))
for i,row in enumerate(reg['frames']):
 key=(row['bank'],row['ref']);p=ROOT/row['target'];assert sha(p.read_bytes())==row['target_sha256']
 target=np.array(Image.open(p));previous=render(old,key[0],key[0]*5,key[1])[0]
 authored=np.zeros_like(target);authored[128:192,112:208]=labels[:,96*i:96*(i+1)]
 assert np.array_equal(authored,np.array(Image.open(ART/f'b{key[0]}_{key[1]:03d}_authored.png')))
 if key==(0,213):hx,hy=-12,-23;head=front.copy()
 else:
  wr=next(r for r in wallmeta['frames']if r['id']=='b1_054');hx,hy=wr['new_head_anchor'];head=wall.copy()
  for x,y in wr['occluded_world_pixels']:head[y-hy,x-hx]=0
 mask=np.zeros_like(previous,dtype=bool)
 for y,rr in enumerate(head):
  xs=np.flatnonzero(rr)
  if len(xs):mask[160+hy+y,160+hx+xs.min():160+hx+xs.max()+1]=True
 assert np.array_equal(mask,np.array(Image.open(ART/f'b{key[0]}_{key[1]:03d}_head_mask.png'))>0)
 assert np.array_equal(previous[160+hy:160+hy+head.shape[0],160+hx:160+hx+head.shape[1]][head>0],head[head>0])
 assert np.array_equal(target[mask],previous[mask])
 contact=np.zeros_like(mask)
 if key==(0,213):contact[130:146,164:176]=True
 else:contact[130:145,163:179]=True;contact[147:155,136:147]=True
 assert np.array_equal(target[contact],previous[contact])
 master[key]=target;masks[key]=mask;contacts[key]=contact
 source_proof.append({'key':list(key),'source_nearest_native_exact':True,'registered_sha256':sha(p.read_bytes()),'head_region_cells':int(mask.sum()),'head_transparent_cells_exact':int(np.count_nonzero(mask&(previous==0))),'contact_cells_exact':int(contact.sum())})

def shifted(a,dx,dy):
 z=np.zeros_like(a);h,w=a.shape;sx=max(0,-dx);sy=max(0,-dy);ex=min(w,w-dx);ey=min(h,h-dy)
 z[sy+dy:ey+dy,sx+dx:ex+dx]=a[sy:ey,sx:ex];return z
def crop(a):
 yy,xx=np.nonzero(a)
 if not len(xx):return None
 return a[yy.min():yy.max()+1,xx.min():xx.max()+1],(int(xx.min()),int(yy.min()))
expected={};mapping={}
for b,n,k,dx,dy in [(0,213,(0,213),0,0),(1,54,(1,54),0,0),(1,56,(1,54),0,0),(1,160,(0,213),-9,-2)]:
 a,p=crop(render(old,b,b*5,n)[0]);m,q=crop(render(old,k[0],k[0]*5,k[1])[0])
 assert np.array_equal(a,m)and(p[0]-q[0],p[1]-q[1])==(dx,dy)
 expected[b,n]=shifted(master[k],dx,dy);mapping[b,n]=(k,dx,dy)
support={(0,214),(0,215),(0,216),(1,55)};changed=set(expected)|support
def sem(parts,b,n):return[(r['flags'],r['tile'],r['x'],r['y'])for r in composition_frame(parts,b,n)['parts']]
counts=collections.Counter();rows=[];composition_changes=[];boundary=0
for b in (0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;assert f['tile_count']==nf['tile_count']<=32
  raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
  nraw=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
  beforeparts=sem(c,b*5,n);afterparts=sem(nc,b*5,n)
  if key!=(1,160):assert beforeparts==afterparts
  else:
   assert len(beforeparts)==len(afterparts)
   for pr,qr in zip(beforeparts,afterparts):
    if pr!=qr:assert pr[1]in(8,9)and qr==(pr[0],pr[1],pr[2]-1,pr[3]);composition_changes.append({'ref':n,'before':pr,'after':qr})
  if key not in changed:assert raw==nraw;counts['non_target_raw_exact']+=1
  aa,_,height=indexed_atlas(raw,f['tile_count']);zz,_,_=indexed_atlas(nraw,nf['tile_count'])
  if raw!=nraw:
   counts['raw_changed_refs']+=1
   for ppart in composition_frame(nc,b*5,n)['parts']:
    tile=ppart['tile'];tx,ty=(tile%16)*16,(tile//16)*16
    edges=([(y,0)for y in range(16)]if tile%16==0 else [])+([(0,x)for x in range(16)]if ppart['flip_y']and tile//16%16==0 else [])
    for yy,xx in edges:
     idx=(ty+yy)*256+tx+xx;assert not(zz[idx]and not aa[idx]);boundary+=1
  if b==1 and 42<=n<=49:assert raw==nraw and beforeparts==afterparts;counts['partial_raw_parts_exact']+=1;continue
  previous=render(old,b,b*5,n)[0];current=render(new,b,b*5,n)[0];counts['display']+=1
  assert np.array_equal(current,expected.get(key,previous))
  if key in expected:
   k,dx,dy=mapping[key];mask=shifted(masks[k],dx,dy);contact=shifted(contacts[k],dx,dy)
   assert np.array_equal(current[mask],previous[mask]);assert np.array_equal(current[contact],previous[contact])
   counts['art_targets_exact']+=1;rows.append({'key':list(key),'changed_pixels':int(np.count_nonzero(previous!=current)),'master':list(k),'translation':[dx,dy],'head_contact_exact':True})
  else:counts['non_target_display_exact']+=1
  if key in support:counts['shared_support_display_parts_exact']+=1
assert len(composition_changes)==2
assert counts['raw']==444 and counts['display']==436 and counts['non_target_raw_exact']==436 and counts['non_target_display_exact']==432 and counts['art_targets_exact']==4 and counts['shared_support_display_parts_exact']==4
static_count=0
for b in (1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):assert sem(c,b,n)==sem(nc,b,n);static_count+=1
assert entry(old,0x10206)==entry(new,0x10206)
recipe=R/'prepared_air_special_v1/static_effects.json';j=json.loads(recipe.read_text('utf8'));previous=json.loads((R/'prepared_burst_final_v1/static_effects.json').read_text('utf8'))
assert j['parts_sha256']==sha(nc);a=dict(j);z=dict(previous);a.pop('parts_sha256');z.pop('parts_sha256');assert a==z
assert j['modified_texture_sha256']==sha(entry(new,0x10206))
for r in j['frames'].values():assert sha((recipe.parent/r['file']).read_bytes())==r['sha256']
native_path=W/'staging_br_v4_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'producer_functions_called':False,'counts':dict(counts),'art_rows':rows,'source_registration':source_proof,'composition_changes':composition_changes,'static_semantic_references_exact':static_count,'static_texture_exact':True,'static_recipe_rebound_only':True,'static_recipe_sha256':sha(recipe.read_bytes()),'new_gpu_boundary_alpha':0,'boundary_samples':boundary,'tile_counts_and_bank_boundaries_exact':True,'palette_audio_other_entries_exact':True,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'visual_review':{'actually_viewed':['riko/prepared_air_special_v1/normal_readback_00.png','riko/prepared_air_special_v1/black_readback_00.png'],'finding':'기존 세부 머리와 손잡이는 유지되고 가슴·소매·부츠 안쪽 명암이 늘었다. 네 그림에서 목·손목의 분리나 새 타일 잘림은 보이지 않았다. 실제 게임 판단은 별도다.'},'limitations':['부분 업로드42..49의 raw/조립은 보존한다. 앞선 새 동작의 VRAM 잔존까지 모든 외부 상태 전이를 실기 검증했다는 뜻은 아니다.','게임 BIN·저장자료를 수정하지 않았으며 실제 게임의 네 신규 동작은 아직 검증하지 않았다.'],'gameplay_runtime_verified':False}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'candidate':sha(new),'report':str((OUT/'report.json').relative_to(ROOT))}))
