"""Independent read-only 77->80/capsule atlas review, no producer calls."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;W=D.parent;R=W/'riko';OUT=D/'riko_burst_independent';OUT.mkdir(exist_ok=True)
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from scripts.c01_audio_build import read_disc
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_static_effect import compose_static
sha=lambda b:hashlib.sha256(b).hexdigest()
P=R/'prepared_ceremony_v2/PL01_U.ARC';Q=R/'prepared_burst_final_v1/PL01_U.ARC'
old=P.read_bytes();new=Q.read_bytes();assert sha(old)=='590ed75799910795db7f237688bbd10ef3a282a7d12910956d798f497e67f818';assert sha(new)=='e871006eed3473bfe6716fc676fb0e4d638c62846de545186dd0de0f6a17e7fc'
g,c,t=entry(old,2),entry(old,3),entry(old,0x10206);ng,nc,nt=entry(new,2),entry(new,3),entry(new,0x10206)
assert replace_entry(replace_entry(replace_entry(new,2,g),3,c),0x10206,t)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True);assert bank_offsets(c)==bank_offsets(nc)
reg=json.loads((R/'burst_cape_variants01/native02/registration.json').read_text('utf8'));targets={}
assert sha((R/'burst_cape_variants01/generated.png').read_bytes())==reg['generated_sha256'];assert reg['parent_sha256']==sha(old)
for row in reg['frames']:
 p=ROOT/row['target'];assert sha(p.read_bytes())==row['sha256'];targets[row['ref']]=np.array(Image.open(p))
targets[184]=targets[182];targets[183]=render(old,1,5,183)[0]
def semantics(parts,b,n):return [(p['flags'],p['tile'],p['x'],p['y'])for p in composition_frame(parts,b,n)['parts']]
counts=collections.Counter();rows=[];positions=[]
for b in (0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];a=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;z=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;chosen=b==1 and n in targets;counts['raw']+=1
  assert nf['tile_count']<=32
  if chosen:
   assert nf['tile_count']==18;positions.append(nf['offset']);assert len(semantics(c,5,n))==len(semantics(nc,5,n))
   parts=composition_frame(nc,5,n)['parts'];assert all(p['flags']==0 and 0<p['tile']<16 for p in parts)
  else:
   assert a==z and f['tile_count']==nf['tile_count'];assert semantics(c,b*5,n)==semantics(nc,b*5,n);counts['non_target_raw_parts_exact']+=1
  if b==1 and 42<=n<=49:counts['partial_raw_parts_exact']+=1;continue
  previous=render(old,b,b*5,n)[0];current=render(new,b,b*5,n)[0];counts['display']+=1
  assert np.array_equal(current,targets[n] if chosen else previous)
  if chosen:rows.append({'bank':b,'ref':n,'changed_display_pixels':int(np.count_nonzero(previous!=current)),'old_tiles':f['tile_count'],'new_tiles':nf['tile_count']});counts['selected_art_exact']+=1
  else:counts['non_target_display_exact']+=1
assert len(set(positions))==1
assert dict(counts)=={'raw':444,'non_target_raw_parts_exact':440,'display':436,'non_target_display_exact':432,'partial_raw_parts_exact':8,'selected_art_exact':4}
assert rows[1]['ref']==183 and rows[1]['changed_display_pixels']==0
static_rows=[];static_total=0;static_changed=[];modified_locations={(i,s)for i,(a,b)in enumerate(zip(t,nt))for s in(0,4)if(a>>s&15)!=(b>>s&15)};allowed_locations=set();boundary_checks=0
native=ROOT/'MegaMan X4.bin';assert sha(native.read_bytes())=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
vanilla=read_disc(native,('PL01_U.ARC',))[0]['PL01_U.ARC'];original_texture=entry(vanilla,0x10206)
original_body=np.roll(render(vanilla,1,5,182)[0],-1,axis=0)
old_recipe=json.loads((ROOT/'work/ver_buki_riko/art_pilot/rakuhouha_v2/static_effects.json').read_text('utf8'))
for bank in (1,2,3,4,6):
 for n in range(composition_frame(nc,bank,0)['bank_frame_count']):
  assert semantics(c,bank,n)==semantics(nc,bank,n);comp=composition_frame(nc,bank,n);static_total+=1
  # Non-target CLUT/unknown flags cannot be fed to the restricted preview
  # reader. Inspect every addressed nibble directly instead; no rendering
  # semantics are changed or guessed for those references.
  if not(bank==6 and n in(23,24)):
   used=set()
   for p in comp['parts']:
    tile=p['page']*256+p['tile']
    for y in range(16):
     for x in range(16):
      off=(tile//16*16+y)*128+tile%16*8+x//2
      if off<len(t):used.add((off,(x%2)*4))
   assert not(modified_locations&used)
   continue
  before,size,bb,locations=compose_static(t,comp);after=compose_static(nt,comp)[0]
  used=set(loc for ls in locations for loc in ls);is_target=bank==6 and n in (23,24)
  if not is_target:assert before==after and not(modified_locations&used)
  else:
   allowed_locations|=used;static_changed.append([bank,n]);aa=np.frombuffer(before,np.uint8).reshape(size[1],size[0]);zz=np.frombuffer(after,np.uint8).reshape(aa.shape)
   body=185 if n==23 else 182;ys=slice(160+bb[1],160+bb[3]);xs=slice(160+bb[0],160+bb[2]);oldbody=render(old,1,5,body)[0][ys,xs];newbody=render(new,1,5,body)[0][ys,xs]
   oo=np.frombuffer(compose_static(original_texture,comp)[0],np.uint8).reshape(aa.shape);freq=collections.Counter(loc for ls in locations for loc in ls);unique=np.array([len(ls)==1 and freq[ls[0]]==1 for ls in locations]).reshape(aa.shape)
   maskold=(oldbody>0)&(oo>0)&unique;masknew=(newbody>0)&(oo>0)&unique;maps=np.array([old_recipe['frames'][str(n)]['tint_map'][str(i)]for i in range(16)],np.uint8)
   assert np.array_equal(zz[masknew],maps[newbody[masknew]]);assert np.array_equal(aa[maskold],maps[oldbody[maskold]])
   assert np.array_equal(aa[~(maskold|masknew)],zz[~(maskold|masknew)]);assert np.array_equal(aa>0,zz>0)
   # Independently rebuild the established dome background from original pixels.
   remove=(original_body[ys,xs]>0)&(oo>0);remove[:max(0,-17-bb[1])]=False;assert not np.any(remove&~unique);bg=oo.copy()
   for yy,xx in zip(*np.nonzero(remove)):
    mirror=-12-xx-2*bb[0]
    if 0<=mirror<size[0] and not remove[yy,mirror] and oo[yy,mirror]:bg[yy,xx]=oo[yy,mirror]
    else:
     available=[i for i in range(size[0])if not remove[yy,i]and oo[yy,i]]
     if not available:bg[yy,xx]=0
     elif n==24 and any(oo[yy,i]==13 for i in available):bg[yy,xx]=13
     else:bg[yy,xx]=oo[yy,min(available,key=lambda i:(abs(i-xx),i))]
   expected_old=bg.copy();expected_old[maskold]=maps[oldbody[maskold]];assert np.array_equal(expected_old,aa)
   expected_new=bg.copy();expected_new[masknew]=maps[newbody[masknew]];assert np.array_equal(expected_new,zz)
   png=np.array(Image.open(R/f'prepared_burst_final_v1/effect_{n}.png'));assert np.array_equal(png,zz)
   static_rows.append({'ref':n,'body_ref':body,'changed_pixels':int(np.count_nonzero(aa!=zz)),'old_reconstruction_exact':True,'new_body_exact':True,'outside_body_and_entire_alpha_exact':True})
  for p in comp['parts']:
   tile=p['page']*256+p['tile'];y0,x0=tile//16*16,tile%16*16
   for yy,xx in ([(y,0)for y in range(16)]if tile%16==0 else [])+([(0,x)for x in range(16)]if p['flip_y'] and tile//16%16==0 else []):
    off=(y0+yy)*128+(x0+xx)//2;sft=(xx%2)*4;assert(t[off]>>sft&15)==(nt[off]>>sft&15);boundary_checks+=1
assert modified_locations<=allowed_locations and static_changed==[[6,23],[6,24]]
native_path=W/'riko_burst_components_native_checks.json';native_proof=json.loads(native_path.read_text('utf8'));assert native_proof['passed'];assert native_proof['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
report={'passed':True,'parent':str(P.relative_to(ROOT)),'parent_sha256':sha(old),'candidate':str(Q.relative_to(ROOT)),'candidate_sha256':sha(new),'producer_functions_called':False,'main_counts':dict(counts),'main_rows':rows,'shared_182_185_count':18,'shared_stream':True,'bank_boundaries_exact':True,'palette_audio_non_target_entries_exact':True,'static_references_checked':static_total,'static_rows':static_rows,'changed_texture_nibbles':len(modified_locations),'changed_texture_bytes':sum(a!=b for a,b in zip(t,nt)),'static_gpu_boundary_samples_exact':boundary_checks,'native_proof':str(native_path.relative_to(ROOT)),'native_proof_sha256':sha(native_path.read_bytes()),'limitations':['부분42..49 raw/조립은 보존하지만182..185 이후 남는 VRAM은 바뀔 수 있다. 차량 부분참조의 모든 외부 상태 전이가 재현됐다는 뜻은 아니다.','낙봉파103의 실제 시퀀스와 원래 디코더/GPU 증거는 별도이며 실제 게임 신규 미술 수용은 아직 미확인이다.'],'gameplay_runtime_verified':False,'game_or_save_changed':False}
report['visual_review']={'actually_viewed':['riko/prepared_burst_variants_v2/normal_readback_00.png','riko/prepared_burst_variants_v2/black_readback_00.png','riko/prepared_burst_final_v1/effect_comparison.png'],'finding':'새 소매·치맛단·부츠와 위쪽 망토 변형이 연결돼 보이며, 반투명 돔의 몸체도 새 의상으로 동기화된다. 183 본체가 그대로 유지되는 것은 별도 픽셀 대조로 확인했다. 실기 수용 판단은 포함하지 않는다.'}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'static':static_rows,'sha':sha(new)}))
