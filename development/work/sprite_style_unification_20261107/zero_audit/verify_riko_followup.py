"""Independent Riko landing/saber10 readback; no producer imports or execution."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));W=ROOT/'work/sprite_style_unification_20261107';R=W/'riko';O=Path(__file__).parent/'riko_followup_independent';O.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda b:hashlib.sha256(b).hexdigest()
P=R/'prepared_air_special_v1';Q=R/'prepared_followup_cloth_v1';old=(P/'PL01_U.ARC').read_bytes();new=(Q/'PL01_U.ARC').read_bytes()
assert sha(old)=='4e751c0e13d6f68bbb02f285493fee75c263c7cc995a96615332935c358e7615';assert sha(new)=='105a7ba315a8dc0ef09d229770c4238fd8364adba43b483a5364c83f0ba79141'
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3);assert replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)and bank_offsets(c)==bank_offsets(nc)
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(p>>s&31)*255//31 for s in(0,5,10)]for p in pal]);front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
def shift(a,dx,dy):
 z=np.zeros_like(a);y,x=np.nonzero(a);assert np.all((x+dx>=0)&(x+dx<384)&(y+dy>=0)&(y+dy<384));z[y+dy,x+dx]=a[y,x];return z
expected={};masks={};contacts={};sources=[]
for folder in('followup_cloth05/registered03','saber_continuation06/registered01'):
 A=R/folder;reg=json.loads((A/'registration.json').read_text('utf8'));assert reg['source_sha256']==sha(old);gen=A.parent/'generated.png';assert sha(gen.read_bytes())==reg['generated_sha256']
 pixels=np.array(Image.open(gen).convert('RGBA').resize((288,96),Image.Resampling.NEAREST));labels=1+np.sum((pixels[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2,axis=3).argmin(2).astype(np.uint8);labels[pixels[:,:,3]<128]=0
 for cell,row in enumerate(reg['frames']):
  b,n=row['bank'],row['ref'];key=b,n;rawart=np.zeros((384,384),np.uint8);rawart[112:208,112:208]=labels[:,cell*96:(cell+1)*96];dx,dy=row['generated_translation'];authored=shift(rawart,dx,dy);assert np.array_equal(authored,np.array(Image.open(A/f'b{b}_{n:03}_authored.png')))
  path=ROOT/row['target'];assert sha(path.read_bytes())==row['target_sha256'];target=np.array(Image.open(path));before=render(old,b,b*5,n)[0];hx,hy=[160+v for v in row['source_head_anchor']];mask=np.zeros_like(target,bool)
  for y,rr in enumerate(front):
   xx=np.flatnonzero(rr)
   if len(xx):mask[hy+y,hx+xx.min():hx+xx.max()+1]=True
  assert int(mask.sum())==316;assert np.array_equal(mask,np.array(Image.open(A/f'b{b}_{n:03}_head_mask.png'))>0);assert np.array_equal(before[hy:hy+19,hx:hx+23][front>0],front[front>0]);assert np.array_equal(target[mask],before[mask])
  contact=np.zeros_like(mask)
  if n in(111,113,121,125):contact[161:169,124:144]=True
  if n==230:contact[153:159,137:145]=True
  want=authored.copy();want[mask]=before[mask];want[contact]=before[contact]
  if folder.startswith('saber_'):
   dxlower=-1 if n==113 else 0;baseold=render(old,0,0,111)[0];assert np.array_equal(before[169:],shift(baseold,dxlower,0)[169:]);want[169:]=shift(expected[0,111],dxlower,0)[169:]
  assert np.array_equal(want,target);assert np.array_equal(target[contact],before[contact])
  if n==230:continue
  expected[key]=target;masks[key]=mask;contacts[key]=contact;sources.append({'key':[b,n],'source_art_sha256':sha(gen.read_bytes()),'registered_sha256':sha(path.read_bytes()),'native_source_then_head_contact_registration_exact':True,'head_interior_cells':int(mask.sum()),'head_transparent_cells':int((mask&(before==0)).sum()),'contact_cells':int(contact.sum())})
variants=[]
for master,n,dx in[(113,115,1),(113,117,1),(113,119,1),(121,123,0),(125,127,0)]:
 oldref=render(old,0,0,n)[0];oldmaster=shift(render(old,0,0,master)[0],dx,0);delta=oldref!=oldmaster;y,x=np.nonzero(delta);assert len(x)>0 and x.min()>=137 and x.max()<=142 and y.min()>=163 and y.max()<=168
 target=shift(expected[0,master],dx,0);target[delta]=oldref[delta];expected[0,n]=target;masks[0,n]=shift(masks[0,master],dx,0);contacts[0,n]=shift(contacts[0,master],dx,0);variants.append({'ref':n,'master':master,'dx':dx,'original_hand_delta_pixels':int(delta.sum()),'delta_world_bbox':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]})
assert sorted(n for b,n in expected)==[34,*range(111,128,2)]
for (b,n),a in expected.items():assert np.array_equal(a,np.array(Image.open(R/f'saber_targets01/b{b}_{n:03}_indices.png')))
def sem(d,b,n):return[(p['flags'],p['tile'],p['x'],p['y'])for p in composition_frame(d,b,n)['parts']]
counts=collections.Counter();rows=[];changes=[];boundary=0
allowed={(0,113):{6,7},(0,115):{5,6},(0,117):{5,6}}
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;assert f['tile_count']==nf['tile_count']<=32;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
  pr,qr=sem(c,b*5,n),sem(nc,b*5,n);assert len(pr)==len(qr)
  for a,z in zip(pr,qr):
   if a!=z:assert key in allowed and a[1]in allowed[key]and z==(a[0],a[1],a[2]+1,a[3]);changes.append({'key':list(key),'old':a,'new':z})
  if key not in expected:assert raw==nr;counts['other_raw_exact']+=1
  else:
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   for p in composition_frame(nc,b*5,n)['parts']:
    t=p['tile'];y,x=t//16*16,t%16*16
    if t%16==0:assert np.array_equal(aa[y:y+16,x],zz[y:y+16,x]);boundary+=16
    if p['flip_y']and t//16%16==0:assert np.array_equal(aa[y,x:x+16],zz[y,x:x+16]);boundary+=16
  if b==1 and 42<=n<=49:assert raw==nr and pr==qr;counts['partial8_exact']+=1;continue
  before=render(old,b,b*5,n)[0];after=render(new,b,b*5,n)[0];counts['display']+=1;assert np.array_equal(after,expected.get(key,before))
  if key in expected:
   assert np.array_equal(after[masks[key]],before[masks[key]]);assert np.array_equal(after[contacts[key]],before[contacts[key]]);counts['authored_exact']+=1;rows.append({'key':list(key),'changed_pixels':int(np.count_nonzero(after!=before)),'head_and_hand_exact':True})
  else:counts['other_display_exact']+=1
assert len(changes)==6 and counts['raw']==444 and counts['display']==436 and counts['authored_exact']==10 and counts['other_raw_exact']==434 and counts['other_display_exact']==426
static=0
for b in(1,2,3,4,6):
 for n in range(composition_frame(c,b,0)['bank_frame_count']):assert sem(c,b,n)==sem(nc,b,n);static+=1
assert entry(old,0x10206)==entry(new,0x10206);rp=Q/'static_effects.json';recipe=json.loads(rp.read_text('utf8'));prior=json.loads((P/'static_effects.json').read_text('utf8'));assert recipe['parts_sha256']==sha(nc)
a=dict(recipe);z=dict(prior);a.pop('parts_sha256');z.pop('parts_sha256');assert a==z
for v in recipe['frames'].values():assert sha((Q/v['file']).read_bytes())==v['sha256']
native_path=W/'riko_followup_components_native_checks.json';native=json.loads(native_path.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
result={'passed':True,'source_arc_sha256':sha(old),'candidate_sha256':sha(new),'producer_functions_called':False,'counts':dict(counts),'source_registration':sources,'derived_hand_variants':variants,'art_rows':rows,'composition_edits':changes,'static_semantic_refs_exact':static,'static_texture_exact':True,'recipe_rebound_parts_only':True,'recipe_sha256':sha(rp.read_bytes()),'bank_boundaries_tilecounts_exact':True,'new_gpu_boundary_alpha':0,'boundary_samples':boundary,'palette_audio_other_entries_exact':True,'native_proof':str(native_path.relative_to(ROOT)),'native_sha256':sha(native_path.read_bytes()),'visual_review':['normal_readback_00.png','normal_readback_01.png','normal_readback_02.png'],'visual_finding':'기존 세밀한 머리와 손을 유지하면서 가슴·앞치마·부츠 명암이 새 의상으로 연결된다. 착지34와3타9에서 새 목 단절이나 타일 잘림은 보이지 않았다. 바닥의 세부 윤곽은 원화에 따라 일부1픽셀 달라져 실기 관찰은 별도다.','gameplay_runtime_verified':False,'full_art_unification_complete':False,'limitations':['b0_230 원화는 후보만 있으며 이번10참조에 넣지 않았음을 확인했다.','부분42..49 raw/조립은 그대로이며 모든 이전 VRAM 전이의 실기 검증을 뜻하지 않는다.']}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'candidate':sha(new)}))
